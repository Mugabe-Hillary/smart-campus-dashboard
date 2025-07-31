FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy all files first to ensure requirements files are available
COPY . .

# Check which requirements file exists and use it
RUN if [ -f "requirements-modular.txt" ]; then \
    echo "Using requirements-modular.txt"; \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-modular.txt; \
    elif [ -f "requirements.txt" ]; then \
    echo "Using requirements.txt"; \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt; \
    else \
    echo "No requirements file found, installing basic dependencies"; \
    pip install --upgrade pip && \
    pip install streamlit pandas plotly influxdb-client numpy pytz requests altair; \
    fi

# Create necessary directories and set Python path
RUN mkdir -p logs data

# Set Python path explicitly and ensure modules are discoverable
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Add a root __init__.py to ensure app directory is treated as a package
RUN touch /app/__init__.py

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application directly with Streamlit
WORKDIR /app
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]