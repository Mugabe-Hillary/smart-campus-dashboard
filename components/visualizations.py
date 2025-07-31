"""
Data visualization components for Smart Campus Dashboard
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, Tuple, List
from datetime import datetime


def create_environmental_chart(df: pd.DataFrame) -> Optional[go.Figure]:
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


def create_light_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """Create light level chart."""
    if df.empty or "light_level" not in df.columns:
        return None

    fig = px.line(
        df,
        x=df.index,
        y="light_level",
        title="💡 Light Level Trends - Uganda Time (EAT)",
        color_discrete_sequence=["#ffa726"],
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


def evaluate_status(value, thresholds: dict) -> Tuple[str, str]:
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


def display_data_status(is_fresh: bool, message: str, conn_status: bool) -> None:
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


def render_live_status(
    df_env: pd.DataFrame, df_class: pd.DataFrame, df_sec: pd.DataFrame, is_fresh: bool
) -> List[str]:
    """Render live sensor status and return active alerts."""
    st.header("📊 Live Sensor Status")

    # Uganda-specific thresholds
    temp_thresholds = {"good": (22, 28), "warning": (20, 32)}
    hum_thresholds = {"good": (40, 75), "warning": (30, 85)}
    light_thresholds = {"good": (200, 800), "warning": (100, 1000)}

    # Get latest readings
    latest_env = df_env.iloc[-1] if not df_env.empty else None
    latest_class = df_class.iloc[-1] if not df_class.empty else None
    latest_sec = df_sec.iloc[-1] if not df_sec.empty else None

    col1, col2, col3, col4 = st.columns(4)

    # Temperature
    with col1:
        temp_val = (
            latest_env["temperature"]
            if latest_env is not None and "temperature" in latest_env
            else "N/A"
        )
        temp_status, temp_icon = evaluate_status(temp_val, temp_thresholds)

        temp_display = f"{temp_val}°C" if temp_val != "N/A" else "N/A"
        if not is_fresh and temp_val != "N/A":
            temp_display += " ⏰"

        st.metric("🌡️ Temperature", temp_display, delta=None)
        st.write(f"{temp_icon} Status")

    # Humidity
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

    # Light Level
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

    # Motion
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

    # Return active alerts
    alerts = []
    if temp_status == "danger":
        alerts.append("🌡️ Temperature is outside safe range!")
    if hum_status == "danger":
        alerts.append("💧 Humidity levels are concerning!")
    if light_status == "danger":
        alerts.append("💡 Light levels need attention!")

    return alerts


def render_quick_stats(
    df_env: pd.DataFrame, df_class: pd.DataFrame, df_sec: pd.DataFrame
) -> None:
    """Render quick statistics summary."""
    if all(df.empty for df in [df_env, df_class, df_sec]):
        return

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


def render_security_data(
    df_sec: pd.DataFrame, sec_error: Optional[str], has_permission: bool
) -> None:
    """Render security data with permission checking."""
    if not has_permission:
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
