"""
Utils module initialization - Enhanced with monitoring and error handling
"""

from .helpers import (
    get_calibrated_reading,
    init_refresh_states,
    render_sidebar_controls,
    render_footer,
)

from .logging_config import (
    DashboardLogger,
    log_info,
    log_warning,
    log_error,
    log_debug,
    log_audit,
    log_user_action,
    log_security_event,
)

from .error_handling import (
    DashboardError,
    DatabaseError,
    AuthenticationError,
    ValidationError,
    PermissionError,
    handle_errors,
    validate_data_types,
    require_permission,
    require_authentication,
    error_tracker,
    display_error_summary,
    safe_execute,
)

from .performance import (
    PerformanceMonitor,
    monitor_performance,
    CacheManager,
    performance_monitor,
    cache_manager,
    get_system_metrics,
    display_performance_dashboard,
    optimize_streamlit_performance,
)

from .health_monitor import (
    SystemHealthMonitor,
    HealthStatus,
    HealthCheck,
    health_monitor,
    display_health_status,
    get_health_endpoint,
)

__all__ = [
    # Helpers
    "get_calibrated_reading",
    "init_refresh_states",
    "render_sidebar_controls",
    "render_footer",
    # Logging
    "DashboardLogger",
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
    "log_audit",
    "log_user_action",
    "log_security_event",
    # Error Handling
    "DashboardError",
    "DatabaseError",
    "AuthenticationError",
    "ValidationError",
    "PermissionError",
    "handle_errors",
    "validate_data_types",
    "require_permission",
    "require_authentication",
    "error_tracker",
    "display_error_summary",
    "safe_execute",
    # Performance
    "PerformanceMonitor",
    "monitor_performance",
    "CacheManager",
    "performance_monitor",
    "cache_manager",
    "get_system_metrics",
    "display_performance_dashboard",
    "optimize_streamlit_performance",
    # Health Monitoring
    "SystemHealthMonitor",
    "HealthStatus",
    "HealthCheck",
    "health_monitor",
    "display_health_status",
    "get_health_endpoint",
]
