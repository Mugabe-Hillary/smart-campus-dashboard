"""
Performance monitoring and optimization utilities
"""

import time
import functools
import psutil
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import streamlit as st
from utils.logging_config import log_info, log_warning


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""

    function_name: str
    execution_time: float
    timestamp: datetime
    memory_usage: float
    user: Optional[str] = None
    parameters: Optional[Dict] = None


class PerformanceMonitor:
    """Monitor and track application performance."""

    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.slow_queries: List[PerformanceMetric] = []
        self.threshold_slow_query = 2.0  # seconds
        self._lock = threading.Lock()

    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)

            # Track slow queries
            if metric.execution_time > self.threshold_slow_query:
                self.slow_queries.append(metric)
                log_warning(
                    f"Slow operation detected: {metric.function_name}",
                    duration=metric.execution_time,
                    memory=metric.memory_usage,
                )

            # Keep only last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]

            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {}

        recent_metrics = [
            m for m in self.metrics if m.timestamp > datetime.now() - timedelta(hours=1)
        ]

        if not recent_metrics:
            return {}

        execution_times = [m.execution_time for m in recent_metrics]
        memory_usage = [m.memory_usage for m in recent_metrics]

        return {
            "total_operations": len(recent_metrics),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "avg_memory_usage": sum(memory_usage) / len(memory_usage),
            "slow_queries_count": len(
                [
                    m
                    for m in recent_metrics
                    if m.execution_time > self.threshold_slow_query
                ]
            ),
            "operations_by_function": self._get_operations_by_function(recent_metrics),
        }

    def _get_operations_by_function(
        self, metrics: List[PerformanceMetric]
    ) -> Dict[str, int]:
        """Group operations by function name."""
        operations = {}
        for metric in metrics:
            operations[metric.function_name] = (
                operations.get(metric.function_name, 0) + 1
            )
        return operations


# Global performance monitor
performance_monitor = PerformanceMonitor()


def monitor_performance(
    track_memory: bool = True,
    log_slow_queries: bool = True,
    include_parameters: bool = False,
):
    """Decorator to monitor function performance."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = (
                psutil.Process().memory_info().rss / 1024 / 1024 if track_memory else 0
            )

            try:
                result = func(*args, **kwargs)

                end_time = time.time()
                end_memory = (
                    psutil.Process().memory_info().rss / 1024 / 1024
                    if track_memory
                    else 0
                )

                execution_time = end_time - start_time
                memory_delta = end_memory - start_memory if track_memory else 0

                # Create performance metric
                metric = PerformanceMetric(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    memory_usage=memory_delta,
                    user=st.session_state.get("username"),
                    parameters=kwargs if include_parameters else None,
                )

                performance_monitor.record_metric(metric)

                return result

            except Exception as e:
                # Still record the metric even if function fails
                end_time = time.time()
                execution_time = end_time - start_time

                metric = PerformanceMetric(
                    function_name=f"{func.__name__}_FAILED",
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    memory_usage=0,
                    user=st.session_state.get("username"),
                )

                performance_monitor.record_metric(metric)
                raise

        return wrapper

    return decorator


class CacheManager:
    """Enhanced caching with performance monitoring."""

    def __init__(self):
        self.cache_stats = {"hits": 0, "misses": 0, "total_requests": 0}

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.cache_stats["total_requests"] == 0:
            return 0.0

        return self.cache_stats["hits"] / self.cache_stats["total_requests"]

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_stats["hits"] += 1
        self.cache_stats["total_requests"] += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_stats["misses"] += 1
        self.cache_stats["total_requests"] += 1


# Global cache manager
cache_manager = CacheManager()


def get_system_metrics() -> Dict[str, Any]:
    """Get current system performance metrics."""
    try:
        process = psutil.Process()

        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "process_memory_mb": process.memory_info().rss / 1024 / 1024,
            "process_cpu_percent": process.cpu_percent(),
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "load_average": (
                psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
            ),
        }
    except Exception as e:
        log_warning(f"Failed to get system metrics: {e}")
        return {}


def display_performance_dashboard() -> None:
    """Display performance monitoring dashboard for admins."""
    if not st.session_state.get("user_info", {}).get("role") == "admin":
        return

    with st.expander("📊 Performance Dashboard", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Application Performance")

            summary = performance_monitor.get_performance_summary()
            if summary:
                st.metric("Total Operations (1h)", summary.get("total_operations", 0))
                st.metric(
                    "Avg Execution Time", f"{summary.get('avg_execution_time', 0):.3f}s"
                )
                st.metric("Slow Queries", summary.get("slow_queries_count", 0))

                # Cache performance
                hit_rate = cache_manager.get_cache_hit_rate()
                st.metric("Cache Hit Rate", f"{hit_rate*100:.1f}%")
            else:
                st.info("No performance data available yet")

        with col2:
            st.subheader("System Resources")

            metrics = get_system_metrics()
            if metrics:
                st.metric("CPU Usage", f"{metrics.get('cpu_percent', 0):.1f}%")
                st.metric("Memory Usage", f"{metrics.get('memory_percent', 0):.1f}%")
                st.metric(
                    "Process Memory", f"{metrics.get('process_memory_mb', 0):.1f} MB"
                )
                st.metric("Disk Usage", f"{metrics.get('disk_usage_percent', 0):.1f}%")

        # Recent slow queries
        if performance_monitor.slow_queries:
            st.subheader("Recent Slow Operations")
            recent_slow = performance_monitor.slow_queries[-5:]  # Last 5

            for query in recent_slow:
                st.write(
                    f"⚠️ {query.function_name}: {query.execution_time:.2f}s at {query.timestamp.strftime('%H:%M:%S')}"
                )


def optimize_streamlit_performance() -> None:
    """Apply Streamlit-specific performance optimizations."""
    # Configure Streamlit for better performance
    if "performance_optimized" not in st.session_state:
        # Enable compression
        st.set_option("server.enableCORS", False)
        st.set_option("server.enableXsrfProtection", False)

        # Mark as optimized
        st.session_state.performance_optimized = True

        log_info("Streamlit performance optimizations applied")
