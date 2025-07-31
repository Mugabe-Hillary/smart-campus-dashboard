#!/usr/bin/env python3
"""
Wrapper script to ensure proper Python path setup before running the dashboard.
This addresses module import issues in production deployments.
"""

import sys
import os
import subprocess

# Ensure the app directory is in Python path
app_dir = "/app"
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Set current working directory
os.chdir(app_dir)

# Set environment variables
os.environ["PYTHONPATH"] = app_dir
os.environ["PYTHONUNBUFFERED"] = "1"

# Debug information
print("=== Python Path Setup ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print(f"PYTHONPATH env: {os.environ.get('PYTHONPATH', 'Not set')}")

# Test imports before starting Streamlit
try:
    print("=== Testing Module Imports ===")
    import auth

    print("✓ auth module imported successfully")

    import database

    print("✓ database module imported successfully")

    import components

    print("✓ components module imported successfully")

    import utils

    print("✓ utils module imported successfully")

    import styles

    print("✓ styles module imported successfully")

    print("=== All modules imported successfully ===")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("=== Available files in /app ===")
    for item in os.listdir("/app"):
        print(f"  {item}")
    print("=== Available Python modules ===")
    for path in sys.path:
        if os.path.exists(path):
            print(f"  {path}: {os.listdir(path) if os.path.isdir(path) else 'FILE'}")
    sys.exit(1)

# Start Streamlit with the dashboard
print("=== Starting Streamlit Dashboard ===")
cmd = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "dashboard.py",
    "--server.port=8501",
    "--server.address=0.0.0.0",
    "--server.headless=true",
]

try:
    subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    print(f"❌ Error starting Streamlit: {e}")
    sys.exit(1)
