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
from influxdb_client import InfluxDBClient

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
    
    @media (max-width: 768px) {
        .element-container {
            width: 100% !important;
        }
    }
    
    .stAlert > div {
        padding: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- Enhanced Authentication ---
def check_password():
    """Returns `True` if the user has the correct password."""
    password = os.environ.get(
        "DASHBOARD_PASSWORD", "cisco1234"
    )  # Default password for demo

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            st.success("Authentication successful!")
            time.sleep(1)
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔐 Smart Campus Dashboard Access")
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter dashboard password",
        )
        st.info(
            "Default password: admin123 (change via DASHBOARD_PASSWORD env variable)"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter dashboard password",
        )
        st.error("😕 Incorrect password. Please try again.")
        return False
    else:
        return True


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
        subplot_titles=("Temperature (°C)", "Humidity (%)"),
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


# ==============================================================================
#  MAIN APP LOGIC
# ==============================================================================

if not check_password():
    st.stop()

# Initialize session state for settings
if "time_range" not in st.session_state:
    st.session_state.time_range = "-1h"
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

    # Settings section
    st.subheader("Settings")
    time_ranges = {
        "Last 15 Minutes": "-15m",
        "Last Hour": "-1h",
        "Last 6 Hours": "-6h",
        "Last 24 Hours": "-1d",
        "Last Week": "-7d",
    }

    selected_range = st.selectbox(
        "Data Range",
        options=list(time_ranges.keys()),
        index=(
            list(time_ranges.values()).index(st.session_state.time_range)
            if st.session_state.time_range in time_ranges.values()
            else 1
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
with col2:
    if conn_status:
        st.metric("Status", "🟢 Online")
    else:
        st.metric("Status", "🔴 Offline")
with col3:
    st.write(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

# --- Data Fetching with Progress Indicator ---
with st.spinner("Loading sensor data..."):
    df_env, env_error = fetch_data_from_db("environment", st.session_state.time_range)
    df_class, class_error = fetch_data_from_db("classroom", st.session_state.time_range)
    df_sec, sec_error = fetch_data_from_db("security", st.session_state.time_range)

# --- Enhanced Live Status with Smart Alerts ---
st.header("📊 Live Sensor Status")

# Define thresholds for status evaluation
temp_thresholds = {"good": (18, 26), "warning": (15, 30)}
hum_thresholds = {"good": (30, 70), "warning": (20, 80)}
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
    st.metric(
        "🌡️ Temperature", f"{temp_val}°C" if temp_val != "N/A" else "N/A", delta=None
    )
    st.write(f"{temp_icon} Status")

with col2:
    hum_val = (
        latest_env["humidity"]
        if latest_env is not None and "humidity" in latest_env
        else "N/A"
    )
    hum_status, hum_icon = evaluate_status(hum_val, hum_thresholds)
    st.metric("💧 Humidity", f"{hum_val}%" if hum_val != "N/A" else "N/A")
    st.write(f"{hum_icon} Status")

with col3:
    light_val = (
        latest_class["light_level"]
        if latest_class is not None and "light_level" in latest_class
        else "N/A"
    )
    light_status, light_icon = evaluate_status(light_val, light_thresholds)
    st.metric("💡 Light Level", f"{light_val} lux" if light_val != "N/A" else "N/A")
    st.write(f"{light_icon} Status")

with col4:
    motion_detected = (
        latest_sec is not None and latest_sec.get("motion_detected", False)
        if latest_sec is not None
        else False
    )
    motion_val = "🔴 Detected" if motion_detected else "🟢 Clear"
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
                title="💡 Light Level Trends",
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
    if not df_sec.empty and not sec_error:
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

# --- Footer ---
st.divider()
st.markdown(
    f"""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Smart Campus Dashboard v2.0 | Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data range: {selected_range}</small>
</div>
""",
    unsafe_allow_html=True,
)
