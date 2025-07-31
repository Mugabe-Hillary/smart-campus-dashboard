"""
Database connection and data fetching utilities for Smart Campus Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient
from datetime import datetime
import pytz
from typing import Tuple, Optional

# --- Timezone Configuration ---
UGANDA_TZ = pytz.timezone("Africa/Kampala")  # Uganda timezone (EAT - UTC+3)

# --- InfluxDB Configuration ---
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "WpYF8b3ShzDvGpaNFo8NZe-NISfwGbATTAC8jzid24wxZhhj9ztz1eOc3168Sk1xVHk3yXSX0IOz_tlZtU7TMQ=="
INFLUX_ORG = "NetlabsUG"
INFLUX_BUCKET = "sensor-data"


# Create cached InfluxDB client outside the class
@st.cache_resource
def get_influx_client():
    """Create and return InfluxDB client."""
    try:
        client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        return client
    except Exception as e:
        return None


class DatabaseManager:
    """Manages InfluxDB connections and data fetching."""

    def __init__(self):
        self.client = get_influx_client()
        self.query_api = self.client.query_api() if self.client else None

    def test_connection(self) -> Tuple[bool, str]:
        """Test the InfluxDB connection."""
        if not self.client:
            return False, "Client not initialized"

        try:
            # Try a simple query to test connection
            query = f"""
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: -5m)
              |> limit(n: 1)
            """
            result = self.query_api.query_data_frame(query, org=INFLUX_ORG)
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    @st.cache_data(ttl=30, show_spinner=False)
    def fetch_data_from_db(
        _self, measurement: str, time_range: str = "-1h"
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Fetch data from InfluxDB with enhanced error handling and data validation."""
        if not _self.query_api:
            return pd.DataFrame(), "InfluxDB client not available"

        try:
            query = f"""
            from(bucket: "{INFLUX_BUCKET}")
              |> range(start: {time_range})
              |> filter(fn: (r) => r._measurement == "{measurement}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> sort(columns: ["_time"], desc: false)
            """

            result = _self.query_api.query_data_frame(query, org=INFLUX_ORG)

            if result is None or result.empty:
                return pd.DataFrame(), f"No data available for {measurement}"

            # Handle the case where result is a list of DataFrames
            if isinstance(result, list):
                if len(result) == 0:
                    return pd.DataFrame(), f"No data available for {measurement}"
                df = result[0]  # Take the first DataFrame
            else:
                df = result

            if "_time" in df.columns:
                df["_time"] = pd.to_datetime(df["_time"])
                # Convert to Uganda timezone
                df["_time"] = df["_time"].dt.tz_convert(UGANDA_TZ)
                df = df.set_index("_time")

            # Remove metadata columns that aren't needed
            cols_to_drop = ["result", "table", "_start", "_stop", "_measurement"]
            df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

            # Data validation and cleaning
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            df[numeric_columns] = df[numeric_columns].fillna(method="ffill").fillna(0)

            return df, None

        except Exception as e:
            error_msg = f"Database query error for {measurement}: {str(e)[:100]}..."
            return pd.DataFrame(), error_msg

    def get_environment_data(
        self, time_range: str
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """Fetch only environment data."""
        return self.fetch_data_from_db("environment", time_range)

    def get_classroom_data(self, time_range: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """Fetch only classroom data."""
        return self.fetch_data_from_db("classroom", time_range)

    def get_security_data(self, time_range: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """Fetch only security data."""
        return self.fetch_data_from_db("security", time_range)


def check_data_freshness(df_list) -> Tuple[bool, str]:
    """Check if data is fresh (updated within last 10 minutes)."""
    if not any(not df.empty for df in df_list):
        return False, "No data available"

    latest_times = []
    for df in df_list:
        if not df.empty and hasattr(df.index, "max"):
            latest_times.append(df.index.max())

    if not latest_times:
        return False, "No valid timestamps found"

    latest_time = max(latest_times)
    # Convert to Uganda timezone for comparison
    if latest_time.tz is None:
        latest_time = latest_time.tz_localize("UTC").tz_convert(UGANDA_TZ)
    else:
        latest_time = latest_time.tz_convert(UGANDA_TZ)

    now = datetime.now(UGANDA_TZ)
    time_diff = now - latest_time

    # Check if data is older than 10 minutes
    if time_diff.total_seconds() > 600:  # 10 minutes = 600 seconds
        return (
            False,
            f"Last update: {latest_time.strftime('%H:%M:%S')} ({time_diff.total_seconds()/60:.1f} min ago) - Showing 24hr history",
        )

    return True, f"Live data (last update: {latest_time.strftime('%H:%M:%S')})"
