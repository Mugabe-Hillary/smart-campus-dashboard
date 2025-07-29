FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages step by step
COPY requirements.txt .
RUN pip install --upgrade pip

# Install packages individually to avoid conflicts
RUN pip install --no-cache-dir streamlit==1.28.1
RUN pip install --no-cache-dir pandas==2.0.3
RUN pip install --no-cache-dir plotly==5.17.0
RUN pip install --no-cache-dir influxdb-client==1.38.0
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir streamlit-autorefresh==0.0.1
RUN pip install --no-cache-dir requests==2.31.0
RUN pip install --no-cache-dir altair==5.1.2

# Copy application files
COPY dashboard.py .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
ENTRYPOINT ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]