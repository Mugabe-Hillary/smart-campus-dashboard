"""
Logging configuration and utilities for Smart Campus Dashboard
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import streamlit as st
from config import get_config


class DashboardLogger:
    """Enhanced logging system for the dashboard."""

    def __init__(self, name: str = "smart_campus_dashboard"):
        self.name = name
        self.config = get_config("logging")
        self.logger = self._setup_logger()
        self.audit_logger = self._setup_audit_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up the main application logger."""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.config["level"]))

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(self.config["format"])

        # Console handler
        if self.config["enable_console"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler with rotation
        log_file = Path(self.config["file_path"])
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config["max_size"],
            backupCount=self.config["backup_count"],
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _setup_audit_logger(self) -> logging.Logger:
        """Set up audit logging for security events."""
        audit_logger = logging.getLogger(f"{self.name}_audit")
        audit_logger.setLevel(logging.INFO)

        # Clear existing handlers
        audit_logger.handlers.clear()

        # Audit log file
        audit_file = Path(self.config["file_path"]).parent / "audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=self.config["max_size"],
            backupCount=self.config["backup_count"],
        )

        audit_formatter = logging.Formatter("%(asctime)s - AUDIT - %(message)s")
        audit_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_handler)

        return audit_logger

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(self._format_message(message, **kwargs))

    def audit(
        self, event: str, user: Optional[str] = None, details: Optional[str] = None
    ) -> None:
        """Log audit event."""
        user_info = user or st.session_state.get("username", "anonymous")
        session_id = id(st.session_state) if hasattr(st, "session_state") else "unknown"

        audit_message = f"Event: {event} | User: {user_info} | Session: {session_id}"
        if details:
            audit_message += f" | Details: {details}"

        self.audit_logger.info(audit_message)

    def _format_message(self, message: str, **kwargs) -> str:
        """Format log message with additional context."""
        context = []

        # Add user context if available
        if hasattr(st, "session_state") and st.session_state.get("username"):
            context.append(f"User: {st.session_state.username}")

        # Add session context
        if hasattr(st, "session_state"):
            context.append(f"Session: {id(st.session_state)}")

        # Add any additional kwargs
        for key, value in kwargs.items():
            context.append(f"{key}: {value}")

        if context:
            return f"{message} | {' | '.join(context)}"
        return message

    def log_database_operation(
        self,
        operation: str,
        measurement: str,
        success: bool,
        duration: Optional[float] = None,
    ) -> None:
        """Log database operations for monitoring."""
        status = "SUCCESS" if success else "FAILED"
        message = f"DB Operation: {operation} on {measurement} - {status}"

        if duration:
            message += f" (Duration: {duration:.2f}s)"

        if success:
            self.info(message)
        else:
            self.error(message)

    def log_user_action(self, action: str, details: Optional[str] = None) -> None:
        """Log user actions for audit trail."""
        self.audit(action, details=details)
        self.info(f"User action: {action}", details=details)

    def log_security_event(
        self, event: str, severity: str = "INFO", details: Optional[str] = None
    ) -> None:
        """Log security-related events."""
        message = f"SECURITY EVENT: {event}"

        self.audit(event, details=details)

        if severity == "CRITICAL":
            self.critical(message, details=details)
        elif severity == "ERROR":
            self.error(message, details=details)
        elif severity == "WARNING":
            self.warning(message, details=details)
        else:
            self.info(message, details=details)


# Global logger instance
logger = DashboardLogger()


# Convenience functions
def log_info(message: str, **kwargs) -> None:
    """Log info message."""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Log warning message."""
    logger.warning(message, **kwargs)


def log_error(message: str, **kwargs) -> None:
    """Log error message."""
    logger.error(message, **kwargs)


def log_debug(message: str, **kwargs) -> None:
    """Log debug message."""
    logger.debug(message, **kwargs)


def log_audit(
    event: str, user: Optional[str] = None, details: Optional[str] = None
) -> None:
    """Log audit event."""
    logger.audit(event, user, details)


def log_user_action(action: str, details: Optional[str] = None) -> None:
    """Log user action."""
    logger.log_user_action(action, details)


def log_security_event(
    event: str, severity: str = "INFO", details: Optional[str] = None
) -> None:
    """Log security event."""
    logger.log_security_event(event, severity, details)
