#!/bin/bash

# Smart Campus Dashboard - Enhanced Setup Script
# This script automates the initial setup process

set -e  # Exit on any error

echo "🚀 Smart Campus Dashboard - Enhanced Setup"
echo "=========================================="

# Check Python version
check_python() {
    echo "📋 Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo "✅ Python $PYTHON_VERSION found"
        
        # Check if version is 3.8 or higher
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            echo "✅ Python version is compatible"
        else
            echo "❌ Python 3.8 or higher is required"
            exit 1
        fi
    else
        echo "❌ Python3 not found. Please install Python 3.8 or higher"
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    echo "🐍 Setting up virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo "✅ Virtual environment activated"
}

# Install dependencies
install_deps() {
    echo "📦 Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Check which requirements file to use
    if [ -f "requirements-modular.txt" ]; then
        echo "📋 Installing modular version dependencies..."
        pip install -r requirements-modular.txt
    elif [ -f "requirements.txt" ]; then
        echo "📋 Installing standard dependencies..."
        pip install -r requirements.txt
    else
        echo "❌ No requirements file found"
        exit 1
    fi
    
    echo "✅ Dependencies installed successfully"
}

# Setup configuration
setup_config() {
    echo "⚙️  Setting up configuration..."
    
    # Create .env file from example
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "✅ Created .env file from template"
            echo "⚠️  Please edit .env file with your actual configuration values"
        else
            echo "⚠️  .env.example not found, creating basic .env file"
            cat > .env << EOF
# InfluxDB Configuration - PLEASE UPDATE THESE VALUES
INFLUX_URL=https://your-influx-url.com
INFLUX_TOKEN=your_token_here
INFLUX_ORG=your_organization
INFLUX_BUCKET=your_bucket_name

# Application Settings
APP_TITLE=Smart Campus Dashboard
APP_DEBUG=false
PAGE_REFRESH_INTERVAL=30

# User Management - CHANGE DEFAULT PASSWORD!
USERS_FILE=users.json
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=change_this_password

# Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOG=true
EOF
        fi
    else
        echo "✅ .env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    
    # Create logs directory
    if [ ! -d "logs" ]; then
        mkdir -p logs
        echo "✅ Created logs directory"
    fi
    
    # Create data directory if needed
    if [ ! -d "data" ]; then
        mkdir -p data
        echo "✅ Created data directory"
    fi
    
    # Setup Streamlit configuration
    mkdir -p ~/.streamlit/
    
    echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > ~/.streamlit/credentials.toml

    echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = \$PORT\n\
" > ~/.streamlit/config.toml
    
    echo "✅ Directories and Streamlit config setup complete"
}

# Test installation
test_installation() {
    echo "🧪 Testing installation..."
    
    # Test Python imports
    python3 -c "
import streamlit
import pandas
import plotly
import influxdb_client
print('✅ Core dependencies import successfully')
"
    
    # Check if modular version exists
    if [ -f "dashboard.py" ]; then
        echo "✅ Enhanced modular dashboard available"
        MAIN_FILE="dashboard.py"
    else
        echo "❌ No main dashboard file found"
        exit 1
    fi
    
    echo "✅ Installation test passed"
}

# Display final instructions
show_instructions() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Next steps:"
    echo "1. Edit the .env file with your InfluxDB credentials:"
    echo "   nano .env"
    echo ""
    echo "2. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "3. Start the application:"
    echo "   streamlit run dashboard.py"
    echo ""
    echo "   (Enhanced modular version with advanced features)"
    echo ""
    echo "4. Open your browser and go to: http://localhost:8501"
    echo ""
    echo "⚠️  Important Security Notes:"
    echo "   - Change the default admin password immediately"
    echo "   - Update your InfluxDB credentials in .env"
    echo "   - Review security settings before production deployment"
    echo ""
    echo "📚 Documentation:"
    echo "   - README_MODULAR.md: Modular architecture guide"
    echo "   - DEPLOYMENT.md: Production deployment guide"
    echo ""
}

# Main execution
main() {
    echo "Starting setup process..."
    echo ""
    
    check_python
    setup_venv
    install_deps
    setup_config
    create_directories  
    test_installation
    show_instructions
}

# Handle script arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "test")
        echo "🧪 Running installation test..."
        source venv/bin/activate 2>/dev/null || true
        test_installation
        ;;
    "clean")
        echo "🧹 Cleaning up installation..."
        read -p "This will remove venv, logs, and .env files. Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv logs .env
            echo "✅ Cleanup complete"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Smart Campus Dashboard Setup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup (default) : Run full setup process"
        echo "  test           : Test current installation"
        echo "  clean          : Clean up installation files"
        echo "  help           : Show this help message"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
