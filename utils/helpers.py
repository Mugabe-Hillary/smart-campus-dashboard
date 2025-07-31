"""
Utility functions for Smart Campus Dashboard
"""

import numpy as np
import streamlit as st
from typing import Tuple


def get_calibrated_reading(
    raw_dht11_temp: float, raw_dht11_humidity: float
) -> Tuple[float, float]:
    """Apply calibration algorithm to raw sensor data with bounds checking."""
    try:
        calibrated_temp = max(-40, min(85, raw_dht11_temp * 0.95 + 1.1))
        calibrated_humidity = max(0, min(100, raw_dht11_humidity * 1.05 - 2.0))
        return round(calibrated_temp, 2), round(calibrated_humidity, 2)
    except Exception as e:
        st.error(f"Calibration error: {e}")
        return raw_dht11_temp, raw_dht11_humidity


def init_refresh_states() -> None:
    """Initialize session state variables for selective refresh."""
    refresh_keys = ["refresh_environment", "refresh_classroom", "refresh_security"]
    for key in refresh_keys:
        if key not in st.session_state:
            st.session_state[key] = False


def render_sidebar_controls(conn_status: bool, conn_msg: str) -> Tuple[str, bool, int]:
    """Render sidebar controls and return settings."""
    st.title("⚙️ Dashboard Controls")

    # Connection test
    st.subheader("🔌 Connection Status")
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
        "Last 24 Hours": "-24h",
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

    return selected_range, auto_refresh, refresh_rate, data_status_placeholder


def render_footer(
    selected_range: str,
    conn_status: bool,
    is_fresh: bool,
    freshness_msg: str,
    df_env,
    df_class,
    df_sec,
) -> None:
    """Render dashboard footer with system information."""
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📊 Dashboard Info")
        st.markdown(
            f"""
        - **Version:** 2.1 (Modular)
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
        from datetime import datetime
        from database import UGANDA_TZ

        st.markdown("#### ⏰ Timestamps (EAT)")
        uganda_time = datetime.now(UGANDA_TZ)
        st.markdown(
            f"""
        - **Page Loaded:** {uganda_time.strftime('%H:%M:%S')}
        - **Date:** {uganda_time.strftime('%Y-%m-%d')}
        - **Last Data:** {freshness_msg.split('(')[0] if '(' in freshness_msg else freshness_msg}
        """
        )

    # Final footer
    uganda_time = datetime.now(UGANDA_TZ)
    st.markdown(
        f"""
    <div style='text-align: center; color: #666; padding: 1rem; margin-top: 2rem; border-top: 1px solid #eee;'>
        <small>
            🏫 <strong>Smart Campus Dashboard</strong> | 
            Built with Streamlit & InfluxDB | 
            Last refresh: {uganda_time.strftime('%Y-%m-%d %H:%M:%S EAT')}
        </small>
    </div>
    """,
        unsafe_allow_html=True,
    )
