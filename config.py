"""
Configuration settings for Smart Campus Dashboard
Enhanced with environment variables and security features
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

# Base directory for the project
BASE_DIR = Path(__file__).parent


# --- Environment-based Configuration ---
def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable with validation."""
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


# --- InfluxDB Configuration ---
INFLUX_CONFIG = {
    "url": get_env_var("INFLUX_URL", "https://us-east-1-1.aws.cloud2.influxdata.com"),
    "token": get_env_var(
        "INFLUX_TOKEN",
        "WpYF8b3ShzDvGpaNFo8NZe-NISfwGbATTAC8jzid24wxZhhj9ztz1eOc3168Sk1xVHk3yXSX0IOz_tlZtU7TMQ==",
    ),
    "org": get_env_var("INFLUX_ORG", "NetlabsUG"),
    "bucket": get_env_var("INFLUX_BUCKET", "sensor-data"),
    "timeout": int(get_env_var("INFLUX_TIMEOUT", 30)),  # seconds
    "retry_attempts": int(get_env_var("INFLUX_RETRY_ATTEMPTS", 3)),
}

# --- Application Settings ---
APP_CONFIG = {
    "title": get_env_var("APP_TITLE", "Smart Campus Dashboard"),
    "version": "2.2-Enhanced",
    "environment": get_env_var(
        "ENVIRONMENT", "development"
    ),  # development, staging, production
    "debug": get_env_var("DEBUG", "false").lower() == "true",
    "default_time_range": get_env_var("DEFAULT_TIME_RANGE", "-24h"),
    "data_freshness_threshold": int(
        get_env_var("DATA_FRESHNESS_THRESHOLD", 600)
    ),  # 10 minutes in seconds
    "default_admin_password": get_env_var("DEFAULT_ADMIN_PASSWORD", "cisco1234"),
    "max_data_points": int(get_env_var("MAX_DATA_POINTS", 10000)),
    "cache_ttl": int(get_env_var("CACHE_TTL", 30)),  # seconds
}

# --- User Management Settings ---
USER_CONFIG = {
    "users_file": get_env_var("USERS_FILE", str(BASE_DIR / "users.json")),
    "password_salt": get_env_var("PASSWORD_SALT", "smart_campus_salt"),
    "default_permissions": ["dashboard", "sensors"],
    "session_timeout": int(get_env_var("SESSION_TIMEOUT", 3600)),  # 1 hour in seconds
    "max_failed_attempts": int(get_env_var("MAX_FAILED_ATTEMPTS", 5)),
    "lockout_duration": int(get_env_var("LOCKOUT_DURATION", 300)),  # 5 minutes
}

# --- Logging Configuration ---
LOGGING_CONFIG = {
    "level": get_env_var("LOG_LEVEL", "INFO"),
    "file_path": get_env_var("LOG_FILE", str(BASE_DIR / "logs" / "dashboard.log")),
    "max_size": int(get_env_var("LOG_MAX_SIZE", 10485760)),  # 10MB
    "backup_count": int(get_env_var("LOG_BACKUP_COUNT", 5)),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "enable_console": get_env_var("LOG_CONSOLE", "true").lower() == "true",
}

# --- Security Settings ---
SECURITY_CONFIG = {
    "enable_rate_limiting": get_env_var("ENABLE_RATE_LIMITING", "true").lower()
    == "true",
    "max_requests_per_minute": int(get_env_var("MAX_REQUESTS_PER_MINUTE", 60)),
    "enable_audit_log": get_env_var("ENABLE_AUDIT_LOG", "true").lower() == "true",
    "sensitive_data_fields": ["password", "token", "api_key"],
}

# --- Performance Settings ---
PERFORMANCE_CONFIG = {
    "enable_compression": get_env_var("ENABLE_COMPRESSION", "true").lower() == "true",
    "enable_multi_threading": get_env_var("ENABLE_MULTI_THREADING", "false").lower()
    == "true",
    "max_concurrent_queries": int(get_env_var("MAX_CONCURRENT_QUERIES", 5)),
    "query_timeout": int(get_env_var("QUERY_TIMEOUT", 30)),
}

# --- Sensor Thresholds (Uganda-specific) ---
SENSOR_THRESHOLDS = {
    "temperature": {"good": (22, 28), "warning": (20, 32)},
    "humidity": {"good": (40, 75), "warning": (30, 85)},
    "light": {"good": (200, 800), "warning": (100, 1000)},
}

# --- UI Settings ---
UI_CONFIG = {
    "page_icon": get_env_var("PAGE_ICON", "🏫"),
    "layout": get_env_var("LAYOUT", "wide"),
    "sidebar_state": get_env_var("SIDEBAR_STATE", "collapsed"),
    "refresh_rates": [5, 10, 15, 30, 60],
    "default_refresh_rate": int(get_env_var("DEFAULT_REFRESH_RATE", 10)),
    "theme": get_env_var("THEME", "default"),  # default, dark, light
    "enable_animations": get_env_var("ENABLE_ANIMATIONS", "true").lower() == "true",
}

# --- Notification Settings ---
NOTIFICATION_CONFIG = {
    "enable_email_alerts": get_env_var("ENABLE_EMAIL_ALERTS", "false").lower()
    == "true",
    "smtp_server": get_env_var("SMTP_SERVER", ""),
    "smtp_port": int(get_env_var("SMTP_PORT", 587)),
    "smtp_username": get_env_var("SMTP_USERNAME", ""),
    "smtp_password": get_env_var("SMTP_PASSWORD", ""),
    "alert_recipients": (
        get_env_var("ALERT_RECIPIENTS", "").split(",")
        if get_env_var("ALERT_RECIPIENTS")
        else []
    ),
}


# --- Validation and Error Handling ---
def validate_config() -> Dict[str, Any]:
    """Validate configuration and return any errors."""
    errors = []
    warnings = []

    # Validate InfluxDB config
    if not INFLUX_CONFIG["url"]:
        errors.append("InfluxDB URL is required")
    if not INFLUX_CONFIG["token"]:
        errors.append("InfluxDB token is required")

    # Validate security settings
    if len(USER_CONFIG["password_salt"]) < 8:
        warnings.append("Password salt should be at least 8 characters long")

    # Check file permissions
    users_file = Path(USER_CONFIG["users_file"])
    if users_file.exists() and not os.access(users_file, os.R_OK | os.W_OK):
        errors.append(f"No read/write access to users file: {users_file}")

    return {"errors": errors, "warnings": warnings}


def get_config(section: str) -> Dict[str, Any]:
    """Get configuration for a specific section."""
    configs = {
        "influx": INFLUX_CONFIG,
        "app": APP_CONFIG,
        "user": USER_CONFIG,
        "thresholds": SENSOR_THRESHOLDS,
        "ui": UI_CONFIG,
        "logging": LOGGING_CONFIG,
        "security": SECURITY_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "notifications": NOTIFICATION_CONFIG,
    }
    return configs.get(section, {})


def get_all_configs() -> Dict[str, Dict[str, Any]]:
    """Get all configuration sections."""
    return {
        "influx": INFLUX_CONFIG,
        "app": APP_CONFIG,
        "user": USER_CONFIG,
        "thresholds": SENSOR_THRESHOLDS,
        "ui": UI_CONFIG,
        "logging": LOGGING_CONFIG,
        "security": SECURITY_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "notifications": NOTIFICATION_CONFIG,
    }
