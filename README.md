# Smart Campus Dashboard

A real-time IoT dashboard for monitoring campus environmental data, security systems, and classroom conditions.

## Features

-   **Real-time Monitoring**: Live sensor data from InfluxDB
-   **Environmental Tracking**: Temperature, humidity, and air quality
-   **Security Management**: Motion detection, RFID access control
-   **Classroom Analytics**: Light levels and occupancy
-   **Mobile Responsive**: Works on all devices
-   **Smart Alerts**: Automated notifications for critical conditions

## Quick Start

### Option 1: Digital Ocean App Platform (Recommended)

1. Fork this repository
2. Connect to Digital Ocean App Platform
3. Set environment variable: `DASHBOARD_PASSWORD=your_secure_password`
4. Deploy automatically

### Option 2: Docker Deployment

```bash
# Build and run
docker build -f Dockerfile.production -t smart-campus-dashboard .
docker run -p 8501:8501 -e DASHBOARD_PASSWORD=your_password smart-campus-dashboard
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DASHBOARD_PASSWORD=your_password

# Run the dashboard
streamlit run dashboard.py
```

## Configuration

-   **DASHBOARD_PASSWORD**: Set via environment variable (default: cisco1234)
-   **InfluxDB**: Pre-configured for cloud instance
-   **Auto-refresh**: Configurable refresh intervals

## Data Sources

The dashboard connects to InfluxDB measurements:

-   `environment`: Temperature, humidity sensors
-   `classroom`: Light levels, occupancy data
-   `security`: Motion detection, RFID access logs

## Security

-   Password-protected access
-   Environment variable configuration
-   Secure InfluxDB token management

## Tech Stack

-   **Frontend**: Streamlit
-   **Database**: InfluxDB Cloud
-   **Visualization**: Plotly
-   **Deployment**: Docker, Digital Ocean
-   **Monitoring**: Real-time auto-refresh

## License

MIT License - see LICENSE file for details.
