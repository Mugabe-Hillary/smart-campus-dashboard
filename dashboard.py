"""
Smart Campus Dashboard - Modular Version
Main application entry point with modular architecture.
"""

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- Page Configuration (MUST BE FIRST) ---
st.set_page_config(
    page_title="Smart Campus Dashboard",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Import modular components with explicit path handling
import sys
import os

# Ensure the current directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from auth import (
        UserManager,
        render_login_form,
        render_user_management,
        check_permission,
    )
    from database import DatabaseManager, check_data_freshness, UGANDA_TZ
    from components import (
        create_environmental_chart,
        create_light_chart,
        display_data_status,
        render_live_status,
        render_quick_stats,
        render_security_data,
    )
    from utils import init_refresh_states, render_sidebar_controls, render_footer
    from styles import get_dashboard_styles
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.error("Please check that all required modules are installed and accessible.")
    st.info(f"Current working directory: {os.getcwd()}")
    st.info(f"Python path: {sys.path}")
    st.stop()

# Apply CSS styles
st.markdown(get_dashboard_styles(), unsafe_allow_html=True)


# Initialize managers
@st.cache_resource
def initialize_managers():
    """Initialize user manager and database manager."""
    user_manager = UserManager()
    db_manager = DatabaseManager()
    return user_manager, db_manager


user_manager, db_manager = initialize_managers()


def load_data_selectively(db_manager: DatabaseManager) -> tuple:
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
            st.session_state.df_env, st.session_state.env_error = (
                db_manager.get_environment_data(st.session_state.time_range)
            )
        st.session_state.refresh_environment = False

    if first_load or st.session_state.refresh_classroom:
        with st.spinner("📚 Refreshing classroom data..."):
            st.session_state.df_class, st.session_state.class_error = (
                db_manager.get_classroom_data(st.session_state.time_range)
            )
        st.session_state.refresh_classroom = False

    if first_load or st.session_state.refresh_security:
        with st.spinner("🔒 Refreshing security data..."):
            st.session_state.df_sec, st.session_state.sec_error = (
                db_manager.get_security_data(st.session_state.time_range)
            )
        st.session_state.refresh_security = False

    return (
        st.session_state.df_env,
        st.session_state.df_class,
        st.session_state.df_sec,
        st.session_state.env_error,
        st.session_state.class_error,
        st.session_state.sec_error,
    )


def main():
    """Main application logic."""

    # Authentication check
    if not render_login_form(user_manager):
        st.stop()

    # Add user management tab for admins
    if st.session_state.user_info and st.session_state.user_info.get("role") == "admin":
        # Add user management option in sidebar
        with st.sidebar:
            st.markdown("---")
            st.subheader("👥 Admin Panel")
            if st.button(
                "🔧 Manage Users", key="user_mgmt_btn", use_container_width=True
            ):
                st.session_state.show_user_management = True

    # Check if user management should be shown
    if st.session_state.get("show_user_management", False):
        # Render user management and check if user wants to return to dashboard
        return_to_dashboard = render_user_management(user_manager)

        if return_to_dashboard:
            st.session_state.show_user_management = False
            st.rerun()

        st.stop()  # Don't show dashboard when in user management mode

    # Initialize session state for settings
    if "time_range" not in st.session_state:
        st.session_state.time_range = "-24h"  # Default to 24 hours
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True

    # --- Enhanced Sidebar ---
    with st.sidebar:
        conn_status, conn_msg = db_manager.test_connection()
        selected_range, auto_refresh, refresh_rate, data_status_placeholder = (
            render_sidebar_controls(conn_status, conn_msg)
        )

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
    # Check permissions before loading data
    if not check_permission("dashboard"):
        st.error("❌ You don't have permission to access this dashboard.")
        st.stop()

    # Use selective refresh data loading
    df_env, df_class, df_sec, env_error, class_error, sec_error = load_data_selectively(
        db_manager
    )

    # --- Check Data Freshness and Display Status ---
    is_fresh, freshness_msg = check_data_freshness([df_env, df_class, df_sec])
    display_data_status(is_fresh, freshness_msg, conn_status)

    # Update sidebar data status
    with data_status_placeholder:
        if is_fresh:
            st.success("🟢 Live updates active")
        else:
            st.warning("⏰ Historical data shown")

    # --- Quick Stats Summary ---
    render_quick_stats(df_env, df_class, df_sec)

    # --- Live Status Display ---
    alerts = render_live_status(df_env, df_class, df_sec, is_fresh)

    # Display alerts if any
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
                    df_env.tail(50).sort_index(ascending=False),
                    use_container_width=True,
                )

    with tab2:
        if not df_class.empty and not class_error:
            fig_light = create_light_chart(df_class)
            if fig_light:
                st.plotly_chart(fig_light, use_container_width=True)

            with st.expander("📋 Classroom Data", expanded=False):
                st.dataframe(
                    df_class.tail(50).sort_index(ascending=False),
                    use_container_width=True,
                )
        else:
            st.warning(class_error or "No classroom data available")

    with tab3:
        render_security_data(df_sec, sec_error, check_permission("sensors"))

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
    render_footer(
        selected_range, conn_status, is_fresh, freshness_msg, df_env, df_class, df_sec
    )


if __name__ == "__main__":
    main()
