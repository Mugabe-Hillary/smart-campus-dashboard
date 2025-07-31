"""
Health monitoring and system status for Smart Campus Dashboard
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import streamlit as st
from database import DatabaseManager
from utils.logging_config import log_info, log_warning, log_error
from utils.performance import get_system_metrics
from config import get_config


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""

    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None
    timestamp: Optional[datetime] = None


class SystemHealthMonitor:
    """Monitor overall system health."""

    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.last_check_time: Optional[datetime] = None
        self.db_manager = DatabaseManager()

    def run_all_checks(self) -> List[HealthCheck]:
        """Run all health checks."""
        self.checks = []

        # Database connectivity check
        self.checks.append(self._check_database())

        # System resources check
        self.checks.append(self._check_system_resources())

        # Application health check
        self.checks.append(self._check_application_health())

        # User session health
        self.checks.append(self._check_user_sessions())

        # Data freshness check
        self.checks.append(self._check_data_freshness())

        self.last_check_time = datetime.now()

        # Log overall health status
        critical_count = len(
            [c for c in self.checks if c.status == HealthStatus.CRITICAL]
        )
        warning_count = len(
            [c for c in self.checks if c.status == HealthStatus.WARNING]
        )

        if critical_count > 0:
            log_error(f"System health check: {critical_count} critical issues found")
        elif warning_count > 0:
            log_warning(f"System health check: {warning_count} warnings found")
        else:
            log_info("System health check: All systems healthy")

        return self.checks

    def _check_database(self) -> HealthCheck:
        """Check database connectivity and performance."""
        start_time = time.time()

        try:
            success, message = self.db_manager.test_connection()
            response_time = time.time() - start_time

            if success:
                if response_time > 5.0:  # Slow response
                    return HealthCheck(
                        name="Database Connection",
                        status=HealthStatus.WARNING,
                        message=f"Database responding slowly ({response_time:.2f}s)",
                        response_time=response_time,
                        timestamp=datetime.now(),
                    )
                else:
                    return HealthCheck(
                        name="Database Connection",
                        status=HealthStatus.HEALTHY,
                        message="Database connection successful",
                        response_time=response_time,
                        timestamp=datetime.now(),
                    )
            else:
                return HealthCheck(
                    name="Database Connection",
                    status=HealthStatus.CRITICAL,
                    message=f"Database connection failed: {message}",
                    response_time=response_time,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            return HealthCheck(
                name="Database Connection",
                status=HealthStatus.CRITICAL,
                message=f"Database check failed: {str(e)}",
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage."""
        try:
            metrics = get_system_metrics()

            if not metrics:
                return HealthCheck(
                    name="System Resources",
                    status=HealthStatus.UNKNOWN,
                    message="Unable to retrieve system metrics",
                    timestamp=datetime.now(),
                )

            # Check critical thresholds
            cpu_percent = metrics.get("cpu_percent", 0)
            memory_percent = metrics.get("memory_percent", 0)
            disk_percent = metrics.get("disk_usage_percent", 0)

            critical_issues = []
            warnings = []

            if cpu_percent > 90:
                critical_issues.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                warnings.append(f"CPU usage high: {cpu_percent:.1f}%")

            if memory_percent > 95:
                critical_issues.append(f"Memory usage critical: {memory_percent:.1f}%")
            elif memory_percent > 85:
                warnings.append(f"Memory usage high: {memory_percent:.1f}%")

            if disk_percent > 95:
                critical_issues.append(f"Disk usage critical: {disk_percent:.1f}%")
            elif disk_percent > 90:
                warnings.append(f"Disk usage high: {disk_percent:.1f}%")

            if critical_issues:
                return HealthCheck(
                    name="System Resources",
                    status=HealthStatus.CRITICAL,
                    message="; ".join(critical_issues),
                    details=metrics,
                    timestamp=datetime.now(),
                )
            elif warnings:
                return HealthCheck(
                    name="System Resources",
                    status=HealthStatus.WARNING,
                    message="; ".join(warnings),
                    details=metrics,
                    timestamp=datetime.now(),
                )
            else:
                return HealthCheck(
                    name="System Resources",
                    status=HealthStatus.HEALTHY,
                    message="System resources within normal limits",
                    details=metrics,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            return HealthCheck(
                name="System Resources",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {str(e)}",
                timestamp=datetime.now(),
            )

    def _check_application_health(self) -> HealthCheck:
        """Check application-specific health."""
        try:
            # Check session state
            if not hasattr(st, "session_state"):
                return HealthCheck(
                    name="Application Health",
                    status=HealthStatus.CRITICAL,
                    message="Streamlit session state not available",
                    timestamp=datetime.now(),
                )

            # Check configuration
            config_errors = []

            influx_config = get_config("influx")
            if not influx_config.get("url") or not influx_config.get("token"):
                config_errors.append("InfluxDB configuration incomplete")

            if config_errors:
                return HealthCheck(
                    name="Application Health",
                    status=HealthStatus.CRITICAL,
                    message="; ".join(config_errors),
                    timestamp=datetime.now(),
                )

            return HealthCheck(
                name="Application Health",
                status=HealthStatus.HEALTHY,
                message="Application running normally",
                timestamp=datetime.now(),
            )

        except Exception as e:
            return HealthCheck(
                name="Application Health",
                status=HealthStatus.CRITICAL,
                message=f"Application health check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def _check_user_sessions(self) -> HealthCheck:
        """Check user session health."""
        try:
            active_sessions = 0
            authenticated_sessions = 0

            # This is a simplified check - in a real multi-user environment,
            # you'd check actual session storage
            if st.session_state.get("authenticated"):
                active_sessions = 1
                authenticated_sessions = 1

            return HealthCheck(
                name="User Sessions",
                status=HealthStatus.HEALTHY,
                message=f"Active sessions: {active_sessions}, Authenticated: {authenticated_sessions}",
                details={
                    "active_sessions": active_sessions,
                    "authenticated_sessions": authenticated_sessions,
                },
                timestamp=datetime.now(),
            )

        except Exception as e:
            return HealthCheck(
                name="User Sessions",
                status=HealthStatus.WARNING,
                message=f"Session check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def _check_data_freshness(self) -> HealthCheck:
        """Check if data is fresh and up-to-date."""
        try:
            from database import check_data_freshness

            # Try to get recent data
            df_env, _ = self.db_manager.get_environment_data("-1h")
            df_class, _ = self.db_manager.get_classroom_data("-1h")
            df_sec, _ = self.db_manager.get_security_data("-1h")

            is_fresh, message = check_data_freshness([df_env, df_class, df_sec])

            if is_fresh:
                return HealthCheck(
                    name="Data Freshness",
                    status=HealthStatus.HEALTHY,
                    message="Data is fresh and up-to-date",
                    details={"freshness_message": message},
                    timestamp=datetime.now(),
                )
            else:
                # Determine severity based on data age
                if "24hr history" in message:
                    return HealthCheck(
                        name="Data Freshness",
                        status=HealthStatus.WARNING,
                        message="Data is stale - showing historical data",
                        details={"freshness_message": message},
                        timestamp=datetime.now(),
                    )
                else:
                    return HealthCheck(
                        name="Data Freshness",
                        status=HealthStatus.CRITICAL,
                        message="No recent data available",
                        details={"freshness_message": message},
                        timestamp=datetime.now(),
                    )

        except Exception as e:
            return HealthCheck(
                name="Data Freshness",
                status=HealthStatus.UNKNOWN,
                message=f"Data freshness check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.checks:
            return HealthStatus.UNKNOWN

        # If any check is critical, overall status is critical
        if any(check.status == HealthStatus.CRITICAL for check in self.checks):
            return HealthStatus.CRITICAL

        # If any check has warnings, overall status is warning
        if any(check.status == HealthStatus.WARNING for check in self.checks):
            return HealthStatus.WARNING

        # If all checks are healthy or unknown, status is healthy
        return HealthStatus.HEALTHY

    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of health check results."""
        if not self.checks:
            return {}

        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: 0,
        }

        for check in self.checks:
            status_counts[check.status] += 1

        return {
            "overall_status": self.get_overall_status(),
            "total_checks": len(self.checks),
            "healthy_checks": status_counts[HealthStatus.HEALTHY],
            "warning_checks": status_counts[HealthStatus.WARNING],
            "critical_checks": status_counts[HealthStatus.CRITICAL],
            "unknown_checks": status_counts[HealthStatus.UNKNOWN],
            "last_check": self.last_check_time,
            "checks": self.checks,
        }


# Global health monitor
health_monitor = SystemHealthMonitor()


def display_health_status() -> None:
    """Display system health status in the UI."""
    if not st.session_state.get("user_info", {}).get("role") == "admin":
        return

    with st.expander("🏥 System Health Status", expanded=False):
        if st.button("🔄 Run Health Check", key="health_check_btn"):
            with st.spinner("Running health checks..."):
                health_monitor.run_all_checks()

        summary = health_monitor.get_health_summary()

        if summary:
            overall_status = summary["overall_status"]

            # Display overall status
            status_colors = {
                HealthStatus.HEALTHY: "🟢",
                HealthStatus.WARNING: "🟡",
                HealthStatus.CRITICAL: "🔴",
                HealthStatus.UNKNOWN: "⚪",
            }

            st.write(
                f"**Overall Status:** {status_colors[overall_status]} {overall_status.value.title()}"
            )

            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Healthy", summary["healthy_checks"])
            with col2:
                st.metric("Warnings", summary["warning_checks"])
            with col3:
                st.metric("Critical", summary["critical_checks"])
            with col4:
                st.metric("Unknown", summary["unknown_checks"])

            # Display individual check results
            st.write("**Individual Checks:**")
            for check in summary["checks"]:
                status_icon = status_colors[check.status]
                st.write(f"{status_icon} **{check.name}**: {check.message}")

                if check.response_time:
                    st.caption(f"Response time: {check.response_time:.3f}s")
        else:
            st.info(
                "No health check data available. Click 'Run Health Check' to start monitoring."
            )


def get_health_endpoint() -> Dict[str, Any]:
    """Get health status for API endpoints."""
    health_monitor.run_all_checks()
    summary = health_monitor.get_health_summary()

    return {
        "status": summary.get("overall_status", HealthStatus.UNKNOWN).value,
        "timestamp": datetime.now().isoformat(),
        "checks": [
            {
                "name": check.name,
                "status": check.status.value,
                "message": check.message,
                "response_time": check.response_time,
            }
            for check in summary.get("checks", [])
        ],
    }
