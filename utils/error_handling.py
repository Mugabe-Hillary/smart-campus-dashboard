"""
Enhanced error handling and validation for Smart Campus Dashboard
"""

import functools
import traceback
from typing import Any, Callable, Optional, Tuple, Union
import streamlit as st
from datetime import datetime
from utils.logging_config import log_error, log_warning, log_security_event


class DashboardError(Exception):
    """Base exception class for dashboard-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[str] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.timestamp = datetime.now()
        super().__init__(self.message)


class DatabaseError(DashboardError):
    """Database-related errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class AuthenticationError(DashboardError):
    """Authentication-related errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "AUTH_ERROR", details)


class ValidationError(DashboardError):
    """Data validation errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class PermissionError(DashboardError):
    """Permission/authorization errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, "PERMISSION_ERROR", details)


def handle_errors(
    show_error: bool = True,
    log_error_details: bool = True,
    fallback_value: Any = None,
    error_message: Optional[str] = None,
):
    """Decorator for comprehensive error handling."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except DashboardError as e:
                # Handle custom dashboard errors
                if log_error_details:
                    log_error(
                        f"Dashboard error in {func.__name__}: {e.message}",
                        error_code=e.error_code,
                        details=e.details,
                        function=func.__name__,
                    )

                if show_error:
                    display_error = error_message or e.message
                    if e.error_code == "AUTH_ERROR":
                        st.error(f"🔐 Authentication Error: {display_error}")
                        log_security_event(
                            f"Authentication error: {e.message}", "ERROR"
                        )
                    elif e.error_code == "PERMISSION_ERROR":
                        st.error(f"🚫 Permission Error: {display_error}")
                        log_security_event(f"Permission error: {e.message}", "WARNING")
                    elif e.error_code == "DATABASE_ERROR":
                        st.error(f"💾 Database Error: {display_error}")
                    else:
                        st.error(f"⚠️ Error: {display_error}")

                return fallback_value

            except Exception as e:
                # Handle unexpected errors
                error_details = traceback.format_exc()

                if log_error_details:
                    log_error(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        function=func.__name__,
                        traceback=error_details,
                    )

                if show_error:
                    display_error = (
                        error_message or f"An unexpected error occurred: {str(e)}"
                    )
                    st.error(f"💥 System Error: {display_error}")

                    # Show details in debug mode
                    if st.session_state.get("debug_mode", False):
                        with st.expander("🔍 Error Details (Debug Mode)"):
                            st.code(error_details)

                return fallback_value

        return wrapper

    return decorator


def validate_data_types(**validations) -> Callable:
    """Decorator to validate function argument types."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Validate arguments
            for param_name, expected_type in validations.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not isinstance(value, expected_type):
                        raise ValidationError(
                            f"Parameter '{param_name}' must be of type {expected_type.__name__}, got {type(value).__name__}",
                            details=f"Function: {func.__name__}, Value: {value}",
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str) -> Callable:
    """Decorator to check user permissions before function execution."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from auth import check_permission

            if not check_permission(permission):
                raise PermissionError(
                    f"Access denied. Required permission: {permission}",
                    details=f"User: {st.session_state.get('username', 'anonymous')}, Function: {func.__name__}",
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_authentication(func: Callable) -> Callable:
    """Decorator to ensure user is authenticated."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated", False):
            raise AuthenticationError(
                "Authentication required", details=f"Function: {func.__name__}"
            )

        return func(*args, **kwargs)

    return wrapper


class ErrorTracker:
    """Track and analyze application errors."""

    def __init__(self):
        if "error_history" not in st.session_state:
            st.session_state.error_history = []

    def add_error(self, error: DashboardError) -> None:
        """Add error to tracking history."""
        error_record = {
            "timestamp": error.timestamp,
            "message": error.message,
            "error_code": error.error_code,
            "details": error.details,
            "user": st.session_state.get("username", "anonymous"),
        }

        st.session_state.error_history.append(error_record)

        # Keep only last 100 errors
        if len(st.session_state.error_history) > 100:
            st.session_state.error_history = st.session_state.error_history[-100:]

    def get_error_summary(self) -> dict:
        """Get summary of recent errors."""
        if not st.session_state.error_history:
            return {"total": 0, "by_type": {}, "recent": []}

        errors = st.session_state.error_history

        # Count by error type
        by_type = {}
        for error in errors:
            error_code = error["error_code"]
            by_type[error_code] = by_type.get(error_code, 0) + 1

        # Get recent errors (last 10)
        recent = errors[-10:] if len(errors) > 10 else errors

        return {"total": len(errors), "by_type": by_type, "recent": recent}


# Global error tracker
error_tracker = ErrorTracker()


def display_error_summary() -> None:
    """Display error summary for admins."""
    if not st.session_state.get("user_info", {}).get("role") == "admin":
        return

    summary = error_tracker.get_error_summary()

    if summary["total"] > 0:
        with st.expander(
            f"🔍 Error Summary ({summary['total']} errors)", expanded=False
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Errors by Type:**")
                for error_type, count in summary["by_type"].items():
                    st.write(f"- {error_type}: {count}")

            with col2:
                st.write("**Recent Errors:**")
                for error in summary["recent"][-5:]:  # Last 5 errors
                    st.write(
                        f"- {error['timestamp'].strftime('%H:%M:%S')}: {error['message'][:50]}..."
                    )


def safe_execute(
    func: Callable, fallback_value: Any = None, error_message: Optional[str] = None
) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func()
    except Exception as e:
        log_error(
            f"Safe execution failed: {str(e)}",
            function=func.__name__ if hasattr(func, "__name__") else "anonymous",
        )

        if error_message:
            st.error(error_message)

        return fallback_value
