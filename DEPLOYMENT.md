# Smart Campus Dashboard - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Smart Campus Dashboard in both development and production environments.

## Prerequisites

### System Requirements

-   Python 3.8 or higher
-   pip package manager
-   Git (for version control)
-   InfluxDB Cloud account (or local InfluxDB instance)

### Environment Setup

1. **Create a virtual environment**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2. **Install dependencies**:

    ```bash
    # For modular version (recommended)
    pip install -r requirements-modular.txt

    # For stable version
    pip install -r requirements-stable.txt
    ```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your specific values:

```env
# InfluxDB Configuration
INFLUX_URL=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX_TOKEN=your_influx_token_here
INFLUX_ORG=your_organization
INFLUX_BUCKET=your_bucket_name

# Application Settings
APP_TITLE=Smart Campus Dashboard
APP_DEBUG=false
PAGE_REFRESH_INTERVAL=30

# User Management
USERS_FILE=users.json
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=change_this_password

# Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=detailed
ENABLE_AUDIT_LOG=true
LOG_RETENTION_DAYS=30
```

### 2. Create Initial Admin User

The system will automatically create a default admin user on first run. **Change the default password immediately!**

## Running the Application

### Development Mode

```bash
# Original version
streamlit run dashboard.py

# Modular version with enhanced features
streamlit run dashboard_modular.py
```

### Production Mode

#### Option 1: Direct Deployment

```bash
# Set production environment
export APP_DEBUG=false

# Run with production settings
streamlit run dashboard_modular.py --server.port 8501 --server.address 0.0.0.0
```

#### Option 2: Docker Deployment

```bash
# Build the image
docker build -f Dockerfile.production -t smart-campus-dashboard .

# Run the container
docker run -p 8501:8501 -e INFLUX_TOKEN=your_token smart-campus-dashboard
```

#### Option 3: Cloud Deployment (Streamlit Cloud)

1. Push code to GitHub repository
2. Connect Streamlit Cloud to your repository
3. Set environment variables in Streamlit Cloud settings
4. Deploy using `dashboard_modular.py` as the main file

## Security Considerations

### 1. Password Security

-   Change default admin password immediately
-   Use strong passwords for all users
-   Consider implementing password policies

### 2. Network Security

-   Use HTTPS in production
-   Configure firewall rules
-   Consider VPN access for sensitive data

### 3. Data Protection

-   Secure InfluxDB credentials
-   Regular backup of user data
-   Monitor access logs

## Monitoring and Maintenance

### 1. Health Monitoring

The application includes built-in health checks:

-   Database connectivity
-   System resources
-   Application performance

Access health status at: `http://your-app/health`

### 2. Logging

Logs are stored in the `logs/` directory:

-   `app.log`: Application logs
-   `audit.log`: User activity logs
-   `performance.log`: Performance metrics

### 3. Performance Optimization

-   Monitor query performance
-   Check memory usage
-   Review connection pool settings

## Troubleshooting

### Common Issues

1. **InfluxDB Connection Failed**

    - Check network connectivity
    - Verify credentials
    - Confirm bucket exists

2. **Authentication Issues**

    - Check users.json file permissions
    - Verify password hashing
    - Review session state

3. **Performance Issues**

    - Check system resources
    - Review query complexity
    - Monitor data volume

4. **Module Import Errors**
    - Verify Python path
    - Check virtual environment
    - Confirm dependencies installed

### Debug Mode

Enable debug mode for detailed error information:

```env
APP_DEBUG=true
LOG_LEVEL=DEBUG
```

## Scaling Considerations

### High Traffic

-   Use load balancer
-   Consider multiple instances
-   Implement caching

### Large Datasets

-   Optimize InfluxDB queries
-   Implement data pagination
-   Use data aggregation

### Multiple Environments

-   Separate .env files
-   Use configuration management
-   Implement CI/CD pipeline

## Backup and Recovery

### User Data

```bash
# Backup users
cp users.json users_backup_$(date +%Y%m%d).json

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### Configuration

```bash
# Backup configuration
cp .env .env.backup
cp config.py config_backup.py
```

## Updates and Maintenance

### Application Updates

1. Backup current version
2. Pull latest changes
3. Update dependencies
4. Test in staging environment
5. Deploy to production

### Dependency Updates

```bash
# Check for updates
pip list --outdated

# Update specific packages
pip install --upgrade streamlit

# Update requirements file
pip freeze > requirements-updated.txt
```

## Support

For technical support or questions:

1. Check the troubleshooting section
2. Review application logs
3. Consult the modular documentation in README_MODULAR.md
4. Contact system administrator

## Additional Resources

-   [Streamlit Documentation](https://docs.streamlit.io/)
-   [InfluxDB Documentation](https://docs.influxdata.com/)
-   [Docker Documentation](https://docs.docker.com/)
