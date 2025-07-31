#!/bin/bash

# Build script for Smart Campus Dashboard deployment
# This script ensures all necessary files are present for deployment

set -e

echo "🚀 Smart Campus Dashboard - Build Script"
echo "========================================"

# Check current directory
echo "📁 Current directory: $(pwd)"
echo "📋 Files present:"
ls -la

# Ensure requirements files exist
echo "🔍 Checking requirements files..."

if [ -f "requirements-modular.txt" ]; then
    echo "✅ requirements-modular.txt found"
    REQUIREMENTS_FILE="requirements-modular.txt"
elif [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
    REQUIREMENTS_FILE="requirements.txt"
    # Create requirements-modular.txt from requirements.txt
    echo "📝 Creating requirements-modular.txt from requirements.txt"
    cp requirements.txt requirements-modular.txt
else
    echo "⚠️  No requirements file found, creating basic one"
    cat > requirements-modular.txt << EOF
# Smart Campus Dashboard - Core Dependencies
streamlit>=1.28.1
pandas>=2.1.0
plotly>=5.17.0
influxdb-client>=1.38.0
numpy>=1.25.0
pytz>=2023.3
requests>=2.31.0
altair>=5.1.2
psutil>=5.9.5
python-dotenv>=1.0.0
typing-extensions>=4.7.0
streamlit-autorefresh==0.0.1
EOF
    REQUIREMENTS_FILE="requirements-modular.txt"
fi

echo "📦 Using requirements file: $REQUIREMENTS_FILE"

# Validate main application file
if [ -f "dashboard.py" ]; then
    echo "✅ dashboard.py found"
else
    echo "❌ dashboard.py not found!"
    exit 1
fi

# Check for modular components
echo "🔍 Checking modular components..."
for dir in auth database components utils styles; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/ directory found"
    else
        echo "⚠️  $dir/ directory missing"
    fi
done

# Ensure config file exists
if [ -f "config.py" ]; then
    echo "✅ config.py found"
else
    echo "⚠️  config.py missing"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data
echo "✅ Created logs/ and data/ directories"

# Display final status
echo ""
echo "🎉 Build preparation complete!"
echo "✅ Requirements file: $REQUIREMENTS_FILE"
echo "✅ Main application: dashboard.py"
echo "✅ Directories created: logs/, data/"
echo ""
echo "Ready for deployment! 🚀"
