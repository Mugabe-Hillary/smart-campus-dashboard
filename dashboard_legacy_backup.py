# dashboard.py - Updated for Cloud InfluxDB

import streamlit as st

# --- Page Configuration (MUST BE FIRST) ---
st.set_page_config(
    page_title="Smart Campus Dashboard",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import os
import time
from datetime import datetime, timedelta
import numpy as np
import pytz
from influxdb_client import InfluxDBClient
import hashlib
import json

# --- Timezone Configuration ---
UGANDA_TZ = pytz.timezone("Africa/Kampala")  # Uganda timezone (EAT - UTC+3)

# --- InfluxDB Configuration ---
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "WpYF8b3ShzDvGpaNFo8NZe-NISfwGbATTAC8jzid24wxZhhj9ztz1eOc3168Sk1xVHk3yXSX0IOz_tlZtU7TMQ=="
INFLUX_ORG = "NetlabsUG"
INFLUX_BUCKET = "sensor-data"


# Initialize InfluxDB client
@st.cache_resource
def get_influx_client():
    """Create and return InfluxDB client."""
    try:
        client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        return client
    except Exception as e:
        # Don't use st.error here as it causes issues with page config
        return None


# Get client and query API
client = get_influx_client()
query_api = client.query_api() if client else None

# Custom CSS for better styling and responsiveness
st.markdown(
    """
<style>
    .main > div {
        padding-top: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-good { border-left: 5px solid #28a745; }
    .status-warning { border-left: 5px solid #ffc107; }
    .status-danger { border-left: 5px solid #dc3545; }
    
    /* Data freshness indicators */
    .stale-data {
        opacity: 0.7;
        border: 2px dashed #ffc107;
        border-radius: 8px;
        padding: 0.5rem;
        background-color: rgba(255, 193, 7, 0.1);
    }
    
    .live-data {
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 0.5rem;
        background-color: rgba(40, 167, 69, 0.1);
    }
    
    /* Enhanced alerts */
    .status-banner {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: bold;
        text-align: center;
    }
    
    .status-success {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
    }
    
    .status-warning {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
        color: #212529;
    }
    
    .status-error {
        background: linear-gradient(90deg, #dc3545, #e83e8c);
        color: white;
    }
    
    @media (max-width: 768px) {
        .element-container {
            width: 100% !important;
        }
    }
    
    .stAlert > div {
        padding: 0.5rem;
    }
    
    /* Pulse animation for live data indicators */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .live-indicator {
        animation: pulse 2s infinite;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- User Management System ---
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.load_users()
    
    def hash_password(self, password):
        """Hash password with salt."""
        return hashlib.sha256(f"{password}smart_campus_salt".encode()).hexdigest()
    
    def load_users(self):
        """Load users from JSON file."""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                # Initialize with default admin user
                self.users = {
                    "admin": {
                        "password": self.hash_password("cisco1234"),
                        "role": "admin",
                        "permissions": ["dashboard", "user_management", "all_sensors"],
                        "created_by": "system",
                        "created_at": datetime.now().isoformat(),
                        "active": True,
                        "last_login": None
                    }
                }
                self.save_users()
        except Exception as e:
            st.error(f"Error loading users: {e}")
            self.users = {}
    
    def save_users(self):
        """Save users to JSON file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            st.error(f"Error saving users: {e}")
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials."""
        if username in self.users:
            user = self.users[username]
            if user["active"] and user["password"] == self.hash_password(password):
                # Update last login
                self.users[username]["last_login"] = datetime.now().isoformat()
                self.save_users()
                return True, user
        return False, None
    
    def add_user(self, username, password, role, permissions, created_by):
        """Add new user (admin only)."""
        if username in self.users:
            return False, "User already exists"
        
        self.users[username] = {
            "password": self.hash_password(password),
            "role": role,
            "permissions": permissions,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "last_login": None
        }
        self.save_users()
        return True, "User created successfully"
    
    def update_user(self, username, **kwargs):
        """Update user details (admin only)."""
        if username not in self.users:
            return False, "User not found"
        
        for key, value in kwargs.items():
            if key == "password":
                self.users[username][key] = self.hash_password(value)
            else:
                self.users[username][key] = value
        
        self.save_users()
        return True, "User updated successfully"
    
    def deactivate_user(self, username):
        """Deactivate user (admin only)."""
        if username in self.users and username != "admin":
            self.users[username]["active"] = False
            self.save_users()
            return True, "User deactivated"
        return False, "Cannot deactivate admin or user not found"
    
    def get_all_users(self):
        """Get all users (admin only)."""
        return self.users

# Initialize user manager
user_manager = UserManager()


# --- Enhanced Authentication System ---
def check_authentication():
    """Enhanced authentication with user management."""
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "username" not in st.session_state:
        st.session_state.username = None

    def login_user():
        """Handle user login."""
        username = st.session_state.get("login_username", "")
        password = st.session_state.get("login_password", "")
        
        if username and password:
            success, user_info = user_manager.authenticate_user(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.user_info = user_info
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.login_error = "Invalid credentials or inactive account"
        else:
            st.session_state.login_error = "Please enter both username and password"

    def logout_user():
        """Handle user logout."""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.username = None
        if "login_username" in st.session_state:
            del st.session_state.login_username
        if "login_password" in st.session_state:
            del st.session_state.login_password
        st.rerun()

    # Show logout button if authenticated
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown("---")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"👤 **{st.session_state.username}**")
                st.caption(f"Role: {st.session_state.user_info.get('role', 'user')}")
            with col2:
                if st.button("🚪 Logout", key="logout_btn"):
                    logout_user()

    if not st.session_state.authenticated:
        # Login interface
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Smart Campus Dashboard Login")
            st.markdown("---")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_submitted = st.form_submit_button("🔑 Login", use_container_width=True)
                
                if login_submitted:
                    if username and password:
                        success, user_info = user_manager.authenticate_user(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_info = user_info
                            st.session_state.username = username
                            st.success(f"Welcome, {username}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials or inactive account")
                    else:
                        st.error("❌ Please enter both username and password")

            st.markdown("---")
            st.markdown("### 🌟 Dashboard Features")
            st.markdown("""
            - 📊 **Real-time monitoring** from IoT sensors
            - 🌡️ **Environmental tracking** (temperature, humidity)  
            - 💡 **Classroom analytics** (light levels, occupancy)
            - 🔒 **Security management** (motion, RFID access)
            - 📱 **Mobile responsive** design
            - ⚡ **Auto-refresh** capabilities
            - 👥 **Multi-user access** with role-based permissions
            """)
            
            st.info("💡 **Default Admin Access:** Username: `admin`, Password: `cisco1234`")

        return False
    
    return True


# --- User Management Interface (Admin Only) ---
def show_user_management():
    """Display user management interface for admins."""
    if not st.session_state.user_info or st.session_state.user_info.get("role") != "admin":
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    st.header("👥 User Management")
    
    tab1, tab2, tab3 = st.tabs(["👀 View Users", "➕ Add User", "✏️ Manage Users"])
    
    with tab1:
        st.subheader("📋 Current Users")
        users = user_manager.get_all_users()
        
        if users:
            users_data = []
            for username, user_info in users.items():
                users_data.append({
                    "Username": username,
                    "Role": user_info.get("role", "user"),
                    "Status": "🟢 Active" if user_info.get("active", False) else "🔴 Inactive",
                    "Created By": user_info.get("created_by", "Unknown"),
                    "Last Login": user_info.get("last_login", "Never")[:19] if user_info.get("last_login") else "Never",
                    "Permissions": ", ".join(user_info.get("permissions", []))
                })
            
            df_users = pd.DataFrame(users_data)
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("No users found.")
    
    with tab2:
        st.subheader("➕ Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username", placeholder="Enter unique username")
            new_password = st.text_input("Password", type="password", placeholder="Enter password")
            new_role = st.selectbox("Role", ["user", "admin", "viewer"])
            
            st.write("**Permissions:**")
            perm_dashboard = st.checkbox("Dashboard Access", value=True)
            perm_sensors = st.checkbox("Sensor Data Access", value=True)
            perm_user_mgmt = st.checkbox("User Management", value=False, disabled=(new_role != "admin"))
            perm_all_sensors = st.checkbox("All Sensors Access", value=True)
            
            add_user_submitted = st.form_submit_button("👤 Create User")
            
            if add_user_submitted:
                if new_username and new_password:
                    permissions = []
                    if perm_dashboard:
                        permissions.append("dashboard")
                    if perm_sensors:
                        permissions.append("sensors")
                    if perm_user_mgmt and new_role == "admin":
                        permissions.append("user_management")
                    if perm_all_sensors:
                        permissions.append("all_sensors")
                    
                    success, message = user_manager.add_user(
                        new_username, new_password, new_role, permissions, st.session_state.username
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please provide both username and password")
    
    with tab3:
        st.subheader("✏️ Manage Existing Users")
        
        users = user_manager.get_all_users()
        user_list = [u for u in users.keys() if u != "admin"]  # Don't allow managing admin
        
        if user_list:
            selected_user = st.selectbox("Select User to Manage", user_list)
            
            if selected_user:
                user_info = users[selected_user]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Current User Info:**")
                    st.write(f"Role: {user_info.get('role', 'user')}")
                    st.write(f"Status: {'Active' if user_info.get('active', False) else 'Inactive'}")
                    st.write(f"Permissions: {', '.join(user_info.get('permissions', []))}")
                
                with col2:
                    with st.form(f"manage_user_{selected_user}"):
                        st.write("**Update User:**")
                        new_role_update = st.selectbox("Role", ["user", "admin", "viewer"], 
                                                     index=["user", "admin", "viewer"].index(user_info.get('role', 'user')))
                        new_password_update = st.text_input("New Password (leave empty to keep current)", 
                                                          type="password", placeholder="Enter new password")
                        
                        col_update, col_deactivate = st.columns(2)
                        with col_update:
                            update_submitted = st.form_submit_button("🔄 Update User")
                        with col_deactivate:
                            deactivate_submitted = st.form_submit_button("� Deactivate User", 
                                                                       type="secondary")
                        
                        if update_submitted:
                            update_data = {"role": new_role_update}
                            if new_password_update:
                                update_data["password"] = new_password_update
                            
                            success, message = user_manager.update_user(selected_user, **update_data)
                            if success:
                                st.success(f"✅ {message}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        
                        if deactivate_submitted:
                            success, message = user_manager.deactivate_user(selected_user)
                            if success:
                                st.success(f"✅ {message}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
        else:
            st.info("No users to manage (excluding admin).")


# --- Permission Checker ---
def check_permission(permission):
    """Check if current user has specific permission."""
    if not st.session_state.authenticated:
        return False
    
    user_permissions = st.session_state.user_info.get("permissions", [])
    return permission in user_permissions or "all_sensors" in user_permissions


# --- Legacy check_password function (keeping for compatibility) ---
def check_password():
    """Legacy password check - redirects to new authentication system."""
    return check_authentication()


# --- Enhanced ML Model with Error Handling ---
def get_calibrated_reading(raw_dht11_temp, raw_dht11_humidity):
    """Apply calibration algorithm to raw sensor data with bounds checking."""
    try:
        calibrated_temp = max(-40, min(85, raw_dht11_temp * 0.95 + 1.1))
        calibrated_humidity = max(0, min(100, raw_dht11_humidity * 1.05 - 2.0))
        return round(calibrated_temp, 2), round(calibrated_humidity, 2)
    except Exception as e:
        st.error(f"Calibration error: {e}")
        return raw_dht11_temp, raw_dht11_humidity


# --- Optimized Data Fetching with Better Error Handling ---
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data_from_db(measurement, time_range="-1h"):
    """Fetch data from InfluxDB with enhanced error handling and data validation."""
    if not query_api:
        return pd.DataFrame(), "InfluxDB client not available"

    try:
        query = f"""
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "{measurement}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: false)
        """

        result = query_api.query_data_frame(query, org=INFLUX_ORG)

        if result is None or result.empty:
            return pd.DataFrame(), f"No data available for {measurement}"

        # Handle the case where result is a list of DataFrames
        if isinstance(result, list):
            if len(result) == 0:
                return pd.DataFrame(), f"No data available for {measurement}"
            df = result[0]  # Take the first DataFrame
        else:
            df = result

        if "_time" in df.columns:
            df["_time"] = pd.to_datetime(df["_time"])
            # Convert to Uganda timezone
            df["_time"] = df["_time"].dt.tz_convert(UGANDA_TZ)
            df = df.set_index("_time")

        # Remove metadata columns that aren't needed
        cols_to_drop = ["result", "table", "_start", "_stop", "_measurement"]
        df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

        # Data validation and cleaning
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(method="ffill").fillna(0)

        return df, None

    except Exception as e:
        error_msg = f"Database query error for {measurement}: {str(e)[:100]}..."
        return pd.DataFrame(), error_msg


# --- Smart Status Evaluation ---
def evaluate_status(value, thresholds):
    """Evaluate sensor status based on thresholds."""
    if value is None or value == "N/A" or pd.isna(value):
        return "unknown", "⚪"

    try:
        val = float(value)
        if val < thresholds["good"][0] or val > thresholds["good"][1]:
            return "danger", "🔴"
        elif val < thresholds["warning"][0] or val > thresholds["warning"][1]:
            return "warning", "🟡"
        else:
            return "good", "🟢"
    except:
        return "unknown", "⚪"


# --- Enhanced Chart Creation ---
def create_environmental_chart(df):
    """Create optimized environmental data chart."""
    if df.empty:
        return None

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=(
            "Temperature (°C) - Uganda Time (EAT)",
            "Humidity (%) - Uganda Time (EAT)",
        ),
        vertical_spacing=0.1,
        shared_xaxes=True,
    )

    if "temperature" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["temperature"],
                name="Temperature",
                line=dict(color="#ff6b6b", width=2),
            ),
            row=1,
            col=1,
        )

    if "humidity" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["humidity"],
                name="Humidity",
                line=dict(color="#4ecdc4", width=2),
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=400,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# --- Test InfluxDB Connection ---
def test_connection():
    """Test the InfluxDB connection."""
    if not client:
        return False, "Client not initialized"

    try:
        # Try a simple query to test connection
        query = f"""
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -5m)
          |> limit(n: 1)
        """
        result = query_api.query_data_frame(query, org=INFLUX_ORG)
        return True, "Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


# --- Selective Data Fetching Functions ---
def get_environment_data():
    """Fetch only environment data."""
    return fetch_data_from_db("environment", st.session_state.time_range)


def get_classroom_data():
    """Fetch only classroom data."""
    return fetch_data_from_db("classroom", st.session_state.time_range)


def get_security_data():
    """Fetch only security data."""
    return fetch_data_from_db("security", st.session_state.time_range)


# --- Initialize session state for selective refresh ---
def init_refresh_states():
    """Initialize session state variables for selective refresh."""
    refresh_keys = ["refresh_environment", "refresh_classroom", "refresh_security"]
    for key in refresh_keys:
        if key not in st.session_state:
            st.session_state[key] = False


# --- Smart Data Loading with Selective Refresh ---
def load_data_selectively():
    """Load data based on refresh states or initial load."""
    init_refresh_states()

    # Initialize session state variables if they don't exist
    if "df_env" not in st.session_state:
        st.session_state.df_env = pd.DataFrame()
        st.session_state.env_error = None
    if "df_class" not in st.session_state:
        st.session_state.df_class = pd.DataFrame()
        st.session_state.class_error = None
    if "df_sec" not in st.session_state:
        st.session_state.df_sec = pd.DataFrame()
        st.session_state.sec_error = None

    # Check if this is the first load or if data doesn't exist in session state
    first_load = (
        st.session_state.df_env.empty
        and st.session_state.df_class.empty
        and st.session_state.df_sec.empty
    )

    if first_load or st.session_state.refresh_environment:
        with st.spinner("🌡️ Refreshing environment data..."):
            st.session_state.df_env, st.session_state.env_error = get_environment_data()
        st.session_state.refresh_environment = False

    if first_load or st.session_state.refresh_classroom:
        with st.spinner("📚 Refreshing classroom data..."):
            st.session_state.df_class, st.session_state.class_error = (
                get_classroom_data()
            )
        st.session_state.refresh_classroom = False

    if first_load or st.session_state.refresh_security:
        with st.spinner("🔒 Refreshing security data..."):
            st.session_state.df_sec, st.session_state.sec_error = get_security_data()
        st.session_state.refresh_security = False

    return (
        st.session_state.df_env,
        st.session_state.df_class,
        st.session_state.df_sec,
        st.session_state.env_error,
        st.session_state.class_error,
        st.session_state.sec_error,
    )


# --- Data Freshness Check ---
def check_data_freshness(df_list):
    """Check if data is fresh (updated within last 10 minutes)."""
    if not any(not df.empty for df in df_list):
        return False, "No data available"

    latest_times = []
    for df in df_list:
        if not df.empty and hasattr(df.index, "max"):
            latest_times.append(df.index.max())

    if not latest_times:
        return False, "No valid timestamps found"

    latest_time = max(latest_times)
    # Convert to Uganda timezone for comparison
    if latest_time.tz is None:
        latest_time = latest_time.tz_localize("UTC").tz_convert(UGANDA_TZ)
    else:
        latest_time = latest_time.tz_convert(UGANDA_TZ)

    now = datetime.now(UGANDA_TZ)
    time_diff = now - latest_time

    # Check if data is older than 10 minutes
    if time_diff.total_seconds() > 600:  # 10 minutes = 600 seconds
        return (
            False,
            f"Last update: {latest_time.strftime('%H:%M:%S')} ({time_diff.total_seconds()/60:.1f} min ago) - Showing 24hr history",
        )

    return True, f"Live data (last update: {latest_time.strftime('%H:%M:%S')})"


# --- Enhanced Status Display ---
def display_data_status(is_fresh, message, conn_status):
    """Display a prominent data status banner."""
    if not conn_status:
        st.markdown(
            '<div class="status-banner status-error">🔴 Database Connection Lost - Unable to fetch live data</div>',
            unsafe_allow_html=True,
        )
    elif not is_fresh:
        st.markdown(
            f'<div class="status-banner status-warning">⚠️ Data Not Live - {message}</div>',
            unsafe_allow_html=True,
        )
        st.info(
            "💡 **Dashboard showing historical data** - Live sensors may be offline or experiencing connectivity issues. Data will automatically refresh when sensors come back online."
        )
        st.markdown(
            f"""
        📅 **Historical Period:** Past 24 hours  
        ⏰ **Data Age:** {message}  
        🔄 **Auto-refresh:** {'Enabled' if st.session_state.auto_refresh else 'Disabled'}
        """
        )
    else:
        st.markdown(
            f'<div class="status-banner status-success live-indicator">✅ Live Data Active - {message}</div>',
            unsafe_allow_html=True,
        )


# ==============================================================================
#  MAIN APP LOGIC
# ==============================================================================

if not check_authentication():
    st.stop()

# Add user management tab for admins
if st.session_state.user_info and st.session_state.user_info.get("role") == "admin":
    # Add user management option in sidebar
    with st.sidebar:
        st.markdown("---")
        st.subheader("👥 Admin Panel")
        if st.button("🔧 Manage Users", key="user_mgmt_btn", use_container_width=True):
            st.session_state.show_user_management = True

# Check if user management should be shown
if st.session_state.get("show_user_management", False):
    show_user_management()
    
    # Add back to dashboard button
    if st.button("📊 Back to Dashboard", key="back_to_dashboard"):
        st.session_state.show_user_management = False
        st.rerun()
    
    st.stop()  # Don't show dashboard when in user management mode

# Initialize session state for settings
if "time_range" not in st.session_state:
    st.session_state.time_range = (
        "-24h"  # Default to 24 hours for better historical view
    )
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

# --- Enhanced Sidebar ---
with st.sidebar:
    st.title("⚙️ Dashboard Controls")

    # Connection test
    st.subheader("🔌 Connection Status")
    conn_status, conn_msg = test_connection()
    if conn_status:
        st.success(f"✅ {conn_msg}")
    else:
        st.error(f"❌ {conn_msg}")

    # Data freshness info (will be updated after data fetch)
    st.subheader("📊 Data Status")
    data_status_placeholder = st.empty()
    st.caption("⏰ Shows 24-hour history when live data unavailable (>10min old)")
    st.caption("🔄 Auto-refresh attempts to restore live connection")
    st.caption("🌍 All times shown in East Africa Time (EAT/UTC+3)")

    # Settings section
    st.subheader("Settings")
    time_ranges = {
        "Last 15 Minutes": "-15m",
        "Last Hour": "-1h",
        "Last 6 Hours": "-6h",
        "Last 24 Hours": "-24h",  # Changed from -1d to -24h for consistency
        "Last Week": "-7d",
    }

    selected_range = st.selectbox(
        "Data Range",
        options=list(time_ranges.keys()),
        index=(
            list(time_ranges.values()).index(st.session_state.time_range)
            if st.session_state.time_range in time_ranges.values()
            else 3  # Default to "Last 24 Hours" (index 3)
        ),
    )
    st.session_state.time_range = time_ranges[selected_range]

    auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh

    if auto_refresh:
        refresh_rate = st.slider("Refresh Rate (seconds)", 5, 60, 10)
    else:
        refresh_rate = None

    if st.button("🔄 Manual Refresh"):
        st.cache_data.clear()
        st.rerun()

    # Selective refresh controls
    st.subheader("⚡ Selective Refresh")
    init_refresh_states()

    refresh_col1, refresh_col2 = st.columns(2)
    with refresh_col1:
        if st.button("🌡️ Environment", key="refresh_env"):
            st.session_state.refresh_environment = True

        if st.button("🔒 Security", key="refresh_sec"):
            st.session_state.refresh_security = True

    with refresh_col2:
        if st.button("🏫 Classroom", key="refresh_class"):
            st.session_state.refresh_classroom = True

        if st.button("🔄 All Data", key="refresh_all"):
            st.session_state.refresh_environment = True
            st.session_state.refresh_classroom = True
            st.session_state.refresh_security = True

    st.divider()

    # ML Model section
    st.subheader("🤖 Sensor Calibration")
    st.write("Input raw DHT11 data for calibrated readings:")

    with st.form("ml_form"):
        raw_temp = st.number_input(
            "Temperature (°C)", value=25.0, step=0.1, min_value=-40.0, max_value=85.0
        )
        raw_hum = st.number_input(
            "Humidity (%)", value=60.0, step=0.1, min_value=0.0, max_value=100.0
        )
        submitted = st.form_submit_button("🔧 Calibrate")

    if submitted:
        calibrated_t, calibrated_h = get_calibrated_reading(raw_temp, raw_hum)
        st.success(f"🌡️ **{calibrated_t}°C**")
        st.success(f"💧 **{calibrated_h}%**")

# --- Auto Refresh Logic ---
if auto_refresh and refresh_rate:
    refresh_interval = st_autorefresh(
        interval=refresh_rate * 1000, limit=None, key="dashboard_refresh"
    )

# --- Main Dashboard Header ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("🏫 Smart Campus Dashboard")
    # Show user info
    user_role = st.session_state.user_info.get("role", "user")
    st.caption(f"Welcome, **{st.session_state.username}** ({user_role})")
with col2:
    if conn_status:
        st.metric("Status", "🟢 Online")
    else:
        st.metric("Status", "🔴 Offline")
with col3:
    uganda_time = datetime.now(UGANDA_TZ)
    st.write(f"**Uganda Time:** {uganda_time.strftime('%H:%M:%S EAT')}")
    st.caption(f"Date: {uganda_time.strftime('%Y-%m-%d')}")

# --- Data Fetching with Selective Refresh ---
# Initialize refresh states if not already done
init_refresh_states()

# Check permissions before loading data
if not check_permission("dashboard"):
    st.error("❌ You don't have permission to access this dashboard.")
    st.stop()

# Use selective refresh data loading
df_env, df_class, df_sec, env_error, class_error, sec_error = load_data_selectively()

# --- Check Data Freshness and Display Status ---
is_fresh, freshness_msg = check_data_freshness([df_env, df_class, df_sec])
display_data_status(is_fresh, freshness_msg, conn_status)

# Update sidebar data status
with data_status_placeholder:
    if is_fresh:
        st.success("🟢 Live updates active")
    else:
        st.warning("⏰ Historical data shown")

# --- Quick Stats Summary (if data is available) ---
if not all(df.empty for df in [df_env, df_class, df_sec]):
    with st.expander("📈 Quick Data Summary", expanded=False):
        summary_col1, summary_col2, summary_col3 = st.columns(3)

        with summary_col1:
            if not df_env.empty and "temperature" in df_env.columns:
                st.metric("Avg Temperature", f"{df_env['temperature'].mean():.1f}°C")
                st.metric(
                    "Temperature Range",
                    f"{df_env['temperature'].max() - df_env['temperature'].min():.1f}°C",
                )

        with summary_col2:
            if not df_class.empty and "light_level" in df_class.columns:
                st.metric(
                    "Avg Light Level", f"{df_class['light_level'].mean():.0f} lux"
                )
                st.metric("Light Variation", f"{df_class['light_level'].std():.0f} lux")

        with summary_col3:
            total_records = sum(len(df) for df in [df_env, df_class, df_sec])
            st.metric("Total Data Points", f"{total_records:,}")
            if not df_sec.empty and "motion_detected" in df_sec.columns:
                motion_events = (
                    df_sec["motion_detected"].sum()
                    if "motion_detected" in df_sec.columns
                    else 0
                )
                st.metric("Motion Events", f"{motion_events}")

# --- Enhanced Live Status with Smart Alerts ---
st.header("📊 Live Sensor Status")

# Define thresholds for status evaluation - Adjusted for Uganda's tropical climate
temp_thresholds = {
    "good": (22, 28),
    "warning": (20, 32),
}  # More appropriate for Uganda's 20-30°C range
hum_thresholds = {
    "good": (40, 75),
    "warning": (30, 85),
}  # Higher humidity tolerance for tropical climate
light_thresholds = {"good": (200, 800), "warning": (100, 1000)}

# Get latest readings
latest_env = df_env.iloc[-1] if not df_env.empty else None
latest_class = df_class.iloc[-1] if not df_class.empty else None
latest_sec = df_sec.iloc[-1] if not df_sec.empty else None

col1, col2, col3, col4 = st.columns(4)

with col1:
    temp_val = (
        latest_env["temperature"]
        if latest_env is not None and "temperature" in latest_env
        else "N/A"
    )
    temp_status, temp_icon = evaluate_status(temp_val, temp_thresholds)

    # Add data freshness indicator to the display
    temp_display = f"{temp_val}°C" if temp_val != "N/A" else "N/A"
    if not is_fresh and temp_val != "N/A":
        temp_display += " ⏰"

    st.metric("🌡️ Temperature", temp_display, delta=None)
    st.write(f"{temp_icon} Status")

with col2:
    hum_val = (
        latest_env["humidity"]
        if latest_env is not None and "humidity" in latest_env
        else "N/A"
    )
    hum_status, hum_icon = evaluate_status(hum_val, hum_thresholds)

    hum_display = f"{hum_val}%" if hum_val != "N/A" else "N/A"
    if not is_fresh and hum_val != "N/A":
        hum_display += " ⏰"

    st.metric("💧 Humidity", hum_display)
    st.write(f"{hum_icon} Status")

with col3:
    light_val = (
        latest_class["light_level"]
        if latest_class is not None and "light_level" in latest_class
        else "N/A"
    )
    light_status, light_icon = evaluate_status(light_val, light_thresholds)

    light_display = f"{light_val} lux" if light_val != "N/A" else "N/A"
    if not is_fresh and light_val != "N/A":
        light_display += " ⏰"

    st.metric("💡 Light Level", light_display)
    st.write(f"{light_icon} Status")

with col4:
    motion_detected = (
        latest_sec is not None and latest_sec.get("motion_detected", False)
        if latest_sec is not None
        else False
    )
    motion_val = "🔴 Detected" if motion_detected else "🟢 Clear"
    if not is_fresh and latest_sec is not None:
        motion_val += " ⏰"

    st.metric("🚶 Motion", motion_val)

    # RFID status
    if latest_sec is not None and "access_status" in latest_sec:
        access_status = "🔓 Granted" if latest_sec["access_status"] else "🔒 Denied"
        st.write(f"Access: {access_status}")

# --- Alert System ---
alerts = []
if temp_status == "danger":
    alerts.append("🌡️ Temperature is outside safe range!")
if hum_status == "danger":
    alerts.append("💧 Humidity levels are concerning!")
if light_status == "danger":
    alerts.append("💡 Light levels need attention!")

if alerts:
    st.error("⚠️ **Active Alerts:**")
    for alert in alerts:
        st.write(f"• {alert}")

# --- Enhanced Data Visualization ---
st.header("📈 Historical Trends")

tab1, tab2, tab3, tab4 = st.tabs(
    ["🌿 Environment", "📚 Classroom", "🔒 Security", "📋 System Health"]
)

with tab1:
    col1, col2 = st.columns([3, 1])

    with col1:
        if not df_env.empty and not env_error:
            fig_env = create_environmental_chart(df_env)
            if fig_env:
                st.plotly_chart(fig_env, use_container_width=True)
        else:
            st.warning(env_error or "No environment data available")

    with col2:
        if not df_env.empty:
            st.subheader("📊 Statistics")
            if "temperature" in df_env.columns:
                st.metric("Avg Temp", f"{df_env['temperature'].mean():.1f}°C")
                st.metric(
                    "Min/Max",
                    f"{df_env['temperature'].min():.1f}°C / {df_env['temperature'].max():.1f}°C",
                )
            if "humidity" in df_env.columns:
                st.metric("Avg Humidity", f"{df_env['humidity'].mean():.1f}%")

    # Data table with pagination
    if not df_env.empty:
        with st.expander("📋 Raw Data", expanded=False):
            st.dataframe(
                df_env.tail(50).sort_index(ascending=False), use_container_width=True
            )

with tab2:
    if not df_class.empty and not class_error:
        if "light_level" in df_class.columns:
            fig_light = px.line(
                df_class,
                x=df_class.index,
                y="light_level",
                title="💡 Light Level Trends - Uganda Time (EAT)",
                color_discrete_sequence=["#ffa726"],
            )
            fig_light.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_light, use_container_width=True)

        with st.expander("📋 Classroom Data", expanded=False):
            st.dataframe(
                df_class.tail(50).sort_index(ascending=False), use_container_width=True
            )
    else:
        st.warning(class_error or "No classroom data available")

with tab3:
    if not check_permission("sensors"):
        st.warning("⚠️ You don't have permission to view security data.")
    elif not df_sec.empty and not sec_error:
        st.subheader("🔒 Recent Security Events")

        # Enhanced security display
        cols_to_show = [
            col
            for col in ["rfid_uid", "access_status", "motion_detected", "distance_cm"]
            if col in df_sec.columns
        ]

        if cols_to_show:
            sec_display = df_sec[cols_to_show].tail(20).sort_index(ascending=False)

            # Color code the display
            def highlight_security(row):
                colors = []
                for col in row.index:
                    if col == "access_status":
                        colors.append(
                            "background-color: lightgreen"
                            if row[col]
                            else "background-color: lightcoral"
                        )
                    elif col == "motion_detected":
                        colors.append(
                            "background-color: yellow"
                            if row[col]
                            else "background-color: lightblue"
                        )
                    else:
                        colors.append("")
                return colors

            st.dataframe(
                sec_display.style.apply(highlight_security, axis=1),
                use_container_width=True,
            )
        else:
            st.warning("Security data structure has changed")
    else:
        st.warning(sec_error or "No security data available")

with tab4:
    st.subheader("🖥️ System Health")

    col1, col2, col3 = st.columns(3)

    with col1:
        db_status = "🟢 Connected" if conn_status else "🔴 Disconnected"
        st.metric("Database", db_status)

    with col2:
        data_freshness = (
            "🟢 Fresh"
            if any([not df_env.empty, not df_class.empty, not df_sec.empty])
            else "🔴 Stale"
        )
        st.metric("Data Status", data_freshness)

    with col3:
        total_records = len(df_env) + len(df_class) + len(df_sec)
        st.metric("Records Loaded", f"{total_records:,}")

    # System errors
    errors = [e for e in [env_error, class_error, sec_error] if e]
    if errors:
        st.subheader("⚠️ System Errors")
        for error in errors:
            st.error(error)

# --- Enhanced Footer ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 📊 Dashboard Info")
    st.markdown(
        f"""
    - **Version:** 2.1
    - **Data Range:** {selected_range}
    - **Default Period:** Past 24 Hours
    - **Records:** {len(df_env) + len(df_class) + len(df_sec):,}
    """
    )

with col2:
    st.markdown("#### 🔧 System Status")
    st.markdown(
        f"""
    - **Database:** {'🟢 Connected' if conn_status else '🔴 Disconnected'}
    - **Data:** {'🟢 Live' if is_fresh else '⏰ Historical'}
    - **Auto-refresh:** {'🟢 On' if st.session_state.auto_refresh else '🔴 Off'}
    - **User:** {st.session_state.username} ({st.session_state.user_info.get('role', 'user')})
    """
    )

with col3:
    st.markdown("#### ⏰ Timestamps (EAT)")
    uganda_time = datetime.now(UGANDA_TZ)
    st.markdown(
        f"""
    - **Page Loaded:** {uganda_time.strftime('%H:%M:%S')}
    - **Date:** {uganda_time.strftime('%Y-%m-%d')}
    - **Last Data:** {freshness_msg.split('(')[0] if '(' in freshness_msg else freshness_msg}
    """
    )

st.markdown(
    f"""
<div style='text-align: center; color: #666; padding: 1rem; margin-top: 2rem; border-top: 1px solid #eee;'>
    <small>
        🏫 <strong>Smart Campus Dashboard</strong> | 
        Built with Streamlit & InfluxDB | 
        Last refresh: {datetime.now(UGANDA_TZ).strftime('%Y-%m-%d %H:%M:%S EAT')}
    </small>
</div>
""",
    unsafe_allow_html=True,
)
