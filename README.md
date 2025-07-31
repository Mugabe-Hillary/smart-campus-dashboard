# 🏫 Smart Campus Dashboard - Uganda

A real-time IoT sensor monitoring dashboard for smart campus environments, optimized for Uganda's climate conditions.

## ✨ Features

### 🔐 **Multi-User Authentication**

-   Role-based access control (Admin, User, Viewer)
-   Secure password hashing with salt
-   Session management with timeout
-   Admin user management panel

### 📊 **Real-Time Monitoring**

-   Live sensor data visualization
-   Uganda-specific weather thresholds (22-28°C optimal temperature)
-   Humidity monitoring (40-75% optimal range)
-   Automatic alerts for threshold violations
-   Historical data analysis with trend indicators

### 🏗️ **Modular Architecture**

-   Clean separation of concerns
-   Easy maintenance and extensibility
-   Environment-based configuration
-   Comprehensive logging and monitoring

### 🌍 **Uganda Climate Optimization**

-   Temperature thresholds adjusted for tropical climate
-   Local timezone support (EAT - UTC+3)
-   Weather patterns suitable for Kampala region

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and setup
git clone <repository-url>
cd smart-campus-dashboard

# Run automated setup
chmod +x setup.sh
./setup.sh
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your InfluxDB credentials
nano .env
```

### 3. Run

```bash
# Activate virtual environment
source venv/bin/activate

# Start the dashboard
streamlit run dashboard.py
```

### 4. Access

-   Open: http://localhost:8501
-   Default admin: `admin` / `cisco6776` (⚠️ **Change immediately!**)

## 📋 Requirements

-   Python 3.8+
-   InfluxDB Cloud account
-   Modern web browser

## 🏗️ Architecture

```
smart-campus-dashboard/
├── dashboard.py              # Main application entry point
├── config.py                # Environment configuration
├── auth/                    # Authentication system
├── database/               # Database connections
├── components/             # UI components
├── utils/                  # Utilities and helpers
└── styles/                 # CSS styling
```

## 🔧 Configuration

Key environment variables in `.env`:

```env
# InfluxDB
INFLUX_URL=your_influx_url
INFLUX_TOKEN=your_token
INFLUX_ORG=your_organization
INFLUX_BUCKET=your_bucket

# Security
DEFAULT_ADMIN_PASSWORD=change_this_password
PASSWORD_SALT=your_unique_salt

# Application
APP_TITLE=Smart Campus Dashboard
DEBUG=false
```

## 🛡️ Security Features

-   **Password Salting**: Secure password storage with unique salt
-   **Session Management**: Automatic timeout and security checks
-   **Rate Limiting**: Protection against brute force attacks
-   **Audit Logging**: Complete activity tracking
-   **Role-Based Access**: Granular permission system

## 📊 Monitoring & Analytics

-   **Performance Monitoring**: Query execution times and system metrics
-   **Health Checks**: Automated system health verification
-   **Audit Trails**: Complete user activity logging
-   **Error Tracking**: Comprehensive error handling and reporting

## 🌡️ Uganda-Specific Features

### **Climate Thresholds**

-   **Temperature**: 22-28°C (Good), >30°C (High Alert)
-   **Humidity**: 40-75% (Optimal for tropical climate)
-   **Timezone**: Africa/Kampala (EAT - UTC+3)

### **Local Optimization**

-   Weather patterns suitable for Uganda
-   Regional alert thresholds
-   Local time display and scheduling

## 📚 Documentation

-   **[Deployment Guide](DEPLOYMENT.md)**: Production deployment instructions
-   **[Modular Architecture](README_MODULAR.md)**: Detailed architecture documentation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📞 Support

-   **Technical Issues**: Check DEPLOYMENT.md troubleshooting section
-   **Documentation**: Review README_MODULAR.md for detailed information
-   **Configuration**: Refer to .env.example for all available settings

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🇺🇬 Built for Smart Campus Initiative - Uganda**
