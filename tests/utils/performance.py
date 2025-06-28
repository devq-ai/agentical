"""
Performance Testing Utilities and Constants for Agentical Framework

This module provides comprehensive performance testing utilities, benchmarking
tools, load testing helpers, and performance monitoring for the Agentical
framework testing suite.

Features:
- Performance benchmarking utilities
- Load testing and stress testing tools
- Memory and CPU monitoring
- Database performance testing
- API response time measurement
- Concurrent execution testing
- Performance regression detection
"""

import asyncio
import gc
import psutil
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
import logging

import pytest
from fastapi.testclient import TestClient
import httpx

from agentical.db.models.base import BaseModel


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    execution_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    peak_memory_mb: float = 0.0
    operations_per_second: float = 0.0
    success_rate: float = 0.0
    error_count: int = 0
    total_operations: int = 0
    percentiles: Dict[str, float] = field(default_factory=dict)
    timestamps: List[datetime] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def add_custom_metric(self, name: str, value: Any):
        """Add custom metric to results."""
        self.custom_metrics[name] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "execution_time": self.execution_time,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "peak_memory_mb": self.peak_memory_mb,
            "operations_per_second": self.operations_per_second,
            "success_rate": self.success_rate,
            "error_count": self.error_count,
            "total_operations": self.total_operations,
            "percentiles": self.percentiles,
            "custom_metrics": self.custom_metrics
        }


class PerformanceTestHelper:
    """Helper class for performance testing operations."""

    def __init__(self):
        self.process = psutil.Process()
        self.baseline_metrics = None
        self.measurement_history = []

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics."""
        memory_info = self.process.memory_info()
        cpu_percent = self.process.cpu_percent()

        return {
            "memory_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": cpu_percent,
            "timestamp": time.time()
        }

    def set_baseline(self):
        """Set baseline metrics for comparison."""
        gc.collect()  # Force garbage collection
        time.sleep(0.1)  # Let CPU settle
        self.baseline_metrics = self.get_current_metrics()

    def measure_function_performance(
        self,
        func: Callable,
        *args,
        iterations: int = 1,
        warmup_iterations: int = 0,
        **kwargs
    ) -> PerformanceMetrics:
        """Measure performance of a function over multiple iterations."""

        # Warmup iterations
        for _ in range(warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception:
                pass

        # Actual measurements
        execution_times = []
        memory_measurements = []
        errors = 0
        start_memory = self.get_current_metrics()["memory_mb"]

        overall_start = time.perf_counter()

        for i in range(iterations):
            gc.collect()

            # Measure memory before
            pre_memory = self.get_current_metrics()["memory_mb"]

            # Execute function
            func_start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                func_end = time.perf_counter()
                execution_times.append(func_end - func_start)
            except Exception as e:
                errors += 1
                func_end = time.perf_counter()
                execution_times.append(func_end - func_start)

            # Measure memory after
            post_memory = self.get_current_metrics()["memory_mb"]
            memory_measurements.append(post_memory - pre_memory)

        overall_end = time.perf_counter()
        end_memory = self.get_current_metrics()["memory_mb"]

        # Calculate metrics
        total_time = overall_end - overall_start
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        memory_delta = end_memory - start_memory
        peak_memory = max(memory_measurements) if memory_measurements else 0
        ops_per_second = iterations / total_time if total_time > 0 else 0
        success_rate = ((iterations - errors) / iterations * 100) if iterations > 0 else 0

        # Calculate percentiles
        percentiles = {}
        if execution_times:
            percentiles = {
                "p50": statistics.median(execution_times),
                "p90": self._percentile(execution_times, 90),
                "p95": self._percentile(execution_times, 95),
                "p99": self._percentile(execution_times, 99)
            }

        return PerformanceMetrics(
            execution_time=avg_execution_time,
            memory_usage_mb=memory_delta,
            cpu_usage_percent=self.process.cpu_percent(),
            peak_memory_mb=peak_memory,
            operations_per_second=ops_per_second,
            success_rate=success_rate,
            error_count=errors,
            total_operations=iterations,
            percentiles=percentiles
        )

    async def measure_async_function_performance(
        self,
        func: Callable,
        *args,
        iterations: int = 1,
        warmup_iterations: int = 0,
        **kwargs
    ) -> PerformanceMetrics:
        """Measure performance of an async function over multiple iterations."""

        # Warmup iterations
        for _ in range(warmup_iterations):
            try:
                await func(*args, **kwargs)
            except Exception:
                pass

        # Actual measurements
        execution_times = []
        memory_measurements = []
        errors = 0
        start_memory = self.get_current_metrics()["memory_mb"]

        overall_start = time.perf_counter()

        for i in range(iterations):
            gc.collect()

            # Measure memory before
            pre_memory = self.get_current_metrics()["memory_mb"]

            # Execute function
            func_start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                func_end = time.perf_counter()
                execution_times.append(func_end - func_start)
            except Exception as e:
                errors += 1
                func_end = time.perf_counter()
                execution_times.append(func_end - func_start)

            # Measure memory after
            post_memory = self.get_current_metrics()["memory_mb"]
            memory_measurements.append(post_memory - pre_memory)

        overall_end = time.perf_counter()
        end_memory = self.get_current_metrics()["memory_mb"]

        # Calculate metrics
        total_time = overall_end - overall_start
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        memory_delta = end_memory - start_memory
        peak_memory = max(memory_measurements) if memory_measurements else 0
        ops_per_second = iterations / total_time if total_time > 0 else 0
        success_rate = ((iterations - errors) / iterations * 100) if iterations > 0 else 0

        # Calculate percentiles
        percentiles = {}
        if execution_times:
            percentiles = {
                "p50": statistics.median(execution_times),
                "p90": self._percentile(execution_times, 90),
                "p95": self._percentile(execution_times, 95),
                "p99": self._percentile(execution_times, 99)
            }

        return PerformanceMetrics(
            execution_time=avg_execution_time,
            memory_usage_mb=memory_delta,
            cpu_usage_percent=self.process.cpu_percent(),
            peak_memory_mb=peak_memory,
            operations_per_second=ops_per_second,
            success_rate=success_rate,
            error_count=errors,
            total_operations=iterations,
            percentiles=percentiles
        )

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    @contextmanager
    def memory_monitoring(self):
        """Context manager for monitoring memory usage."""
        initial_memory = self.get_current_metrics()["memory_mb"]
        peak_memory = initial_memory

        def monitor():
            nonlocal peak_memory
            while getattr(monitor, 'running', True):
                current_memory = self.get_current_metrics()["memory_mb"]
                if current_memory > peak_memory:
                    peak_memory = current_memory
                time.sleep(0.01)  # Check every 10ms

        monitor.running = True
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

        try:
            yield lambda: peak_memory - initial_memory
        finally:
            monitor.running = False
            monitor_thread.join(timeout=1.0)


class LoadTestRunner:
    """Load testing and stress testing utilities."""

    def __init__(self, client: TestClient = None):
        self.client = client
        self.results = []

    def run_load_test(
        self,
        test_function: Callable,
        concurrent_users: int = 10,
        duration_seconds: int = 30,
        ramp_up_seconds: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """Run load test with specified parameters."""

        results = []
        errors = []
        start_time = time.time()
        end_time = start_time + duration_seconds

        def worker(user_id: int):
            """Worker function for individual user simulation."""
            user_results = []
            user_errors = []

            # Ramp up delay
            if ramp_up_seconds > 0:
                delay = (user_id / concurrent_users) * ramp_up_seconds
                time.sleep(delay)

            while time.time() < end_time:
                try:
                    operation_start = time.perf_counter()
                    test_function(**kwargs)
                    operation_end = time.perf_counter()

                    user_results.append({
                        "user_id": user_id,
                        "duration": operation_end - operation_start,
                        "timestamp": time.time(),
                        "success": True
                    })

                except Exception as e:
                    user_errors.append({
                        "user_id": user_id,
                        "error": str(e),
                        "timestamp": time.time()
                    })

                # Small delay to prevent overwhelming
                time.sleep(0.001)

            return user_results, user_errors

        # Execute load test with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(worker, user_id)
                for user_id in range(concurrent_users)
            ]

            for future in as_completed(futures):
                user_results, user_errors = future.result()
                results.extend(user_results)
                errors.extend(user_errors)

        # Analyze results
        total_operations = len(results) + len(errors)
        successful_operations = len(results)

        if results:
            response_times = [r["duration"] for r in results]
            avg_response_time = statistics.mean(response_times)
            p95_response_time = self._percentile(response_times, 95)
            throughput = successful_operations / duration_seconds
        else:
            avg_response_time = 0
            p95_response_time = 0
            throughput = 0

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": len(errors),
            "success_rate": (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "throughput_ops_per_sec": throughput,
            "concurrent_users": concurrent_users,
            "duration_seconds": duration_seconds,
            "errors": errors[:10]  # First 10 errors for analysis
        }

    def run_stress_test(
        self,
        test_function: Callable,
        max_users: int = 100,
        step_size: int = 10,
        step_duration: int = 60,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Run stress test with gradually increasing load."""

        stress_results = []

        for users in range(step_size, max_users + 1, step_size):
            print(f"Running stress test with {users} concurrent users...")

            result = self.run_load_test(
                test_function=test_function,
                concurrent_users=users,
                duration_seconds=step_duration,
                **kwargs
            )

            result["step"] = users // step_size
            stress_results.append(result)

            # Break if error rate becomes too high (>50%)
            if result["success_rate"] < 50:
                print(f"Stopping stress test due to high error rate at {users} users")
                break

        return stress_results

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]


class BenchmarkSuite:
    """Benchmark suite for performance regression testing."""

    def __init__(self):
        self.benchmarks = {}
        self.baseline_results = {}

    def register_benchmark(self, name: str, func: Callable, **kwargs):
        """Register a benchmark function."""
        self.benchmarks[name] = {
            "function": func,
            "kwargs": kwargs
        }

    def run_benchmark(self, name: str, iterations: int = 100) -> PerformanceMetrics:
        """Run a specific benchmark."""
        if name not in self.benchmarks:
            raise ValueError(f"Benchmark '{name}' not found")

        benchmark = self.benchmarks[name]
        helper = PerformanceTestHelper()

        return helper.measure_function_performance(
            benchmark["function"],
            iterations=iterations,
            **benchmark["kwargs"]
        )

    def run_all_benchmarks(self, iterations: int = 100) -> Dict[str, PerformanceMetrics]:
        """Run all registered benchmarks."""
        results = {}

        for name in self.benchmarks:
            print(f"Running benchmark: {name}")
            results[name] = self.run_benchmark(name, iterations)

        return results

    def set_baseline(self, results: Dict[str, PerformanceMetrics]):
        """Set baseline results for comparison."""
        self.baseline_results = {
            name: metrics.to_dict()
            for name, metrics in results.items()
        }

    def compare_to_baseline(
        self,
        current_results: Dict[str, PerformanceMetrics],
        tolerance_percent: float = 10.0
    ) -> Dict[str, Dict[str, Any]]:
        """Compare current results to baseline."""
        comparisons = {}

        for name, current_metrics in current_results.items():
            if name not in self.baseline_results:
                comparisons[name] = {"status": "no_baseline", "details": "No baseline available"}
                continue

            baseline = self.baseline_results[name]
            current = current_metrics.to_dict()

            # Compare key metrics
            comparison = {
                "status": "passed",
                "details": {},
                "regressions": []
            }

            key_metrics = ["execution_time", "memory_usage_mb", "operations_per_second"]

            for metric in key_metrics:
                baseline_value = baseline.get(metric, 0)
                current_value = current.get(metric, 0)

                if baseline_value > 0:
                    percent_change = ((current_value - baseline_value) / baseline_value) * 100

                    comparison["details"][metric] = {
                        "baseline": baseline_value,
                        "current": current_value,
                        "percent_change": percent_change
                    }

                    # Check for regression (higher is worse for time/memory, lower is worse for ops/sec)
                    if metric == "operations_per_second":
                        if percent_change < -tolerance_percent:
                            comparison["regressions"].append(f"{metric} decreased by {abs(percent_change):.1f}%")
                            comparison["status"] = "failed"
                    else:
                        if percent_change > tolerance_percent:
                            comparison["regressions"].append(f"{metric} increased by {percent_change:.1f}%")
                            comparison["status"] = "failed"

            comparisons[name] = comparison

        return comparisons


class MetricsCollector:
    """Collector for gathering and analyzing performance metrics."""

    def __init__(self):
        self.metrics_history = []
        self.thresholds = {}

    def collect_metrics(self, source: str, metrics: Dict[str, Any]):
        """Collect metrics from a source."""
        entry = {
            "timestamp": datetime.utcnow(),
            "source": source,
            "metrics": metrics
        }
        self.metrics_history.append(entry)

    def set_threshold(self, metric_name: str, max_value: float):
        """Set performance threshold for a metric."""
        self.thresholds[metric_name] = max_value

    def check_thresholds(self, metrics: Dict[str, Any]) -> List[str]:
        """Check if metrics exceed thresholds."""
        violations = []

        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                if value > threshold:
                    violations.append(f"{metric_name}: {value} > {threshold}")

        return violations

    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get summary of metrics within time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_metrics = [
            entry for entry in self.metrics_history
            if entry["timestamp"] >= cutoff_time
        ]

        if not recent_metrics:
            return {"message": "No metrics in time window"}

        # Aggregate metrics by source
        by_source = {}
        for entry in recent_metrics:
            source = entry["source"]
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(entry["metrics"])

        # Calculate summaries
        summary = {}
        for source, metrics_list in by_source.items():
            if metrics_list:
                # Average numeric metrics
                numeric_metrics = {}
                for metrics in metrics_list:
                    for key, value in metrics.items():
                        if isinstance(value, (int, float)):
                            if key not in numeric_metrics:
                                numeric_metrics[key] = []
                            numeric_metrics[key].append(value)

                source_summary = {}
                for key, values in numeric_metrics.items():
                    source_summary[key] = {
                        "avg": statistics.mean(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }

                summary[source] = source_summary

        return summary


# Performance testing constants
PERFORMANCE_THRESHOLDS = {
    "api_response_time_ms": 1000,      # Max 1 second response time
    "database_query_time_ms": 500,     # Max 500ms query time
    "memory_usage_mb": 100,            # Max 100MB memory usage
    "cpu_usage_percent": 80,           # Max 80% CPU usage
    "operations_per_second": 100,      # Min 100 ops/sec
    "success_rate_percent": 95,        # Min 95% success rate
    "concurrent_users": 50,            # Target concurrent users
    "load_test_duration_seconds": 300, # 5 minute load tests
}

BENCHMARK_CONFIGURATIONS = {
    "quick": {"iterations": 10, "warmup": 2},
    "standard": {"iterations": 100, "warmup": 10},
    "thorough": {"iterations": 1000, "warmup": 50},
    "stress": {"iterations": 5000, "warmup": 100}
}

LOAD_TEST_SCENARIOS = {
    "light": {"users": 10, "duration": 60},
    "moderate": {"users": 50, "duration": 300},
    "heavy": {"users": 100, "duration": 600},
    "extreme": {"users": 500, "duration": 300}
}


# Utility functions and decorators
def performance_test(
    max_execution_time: float = None,
    max_memory_mb: float = None,
    min_ops_per_second: float = None
):
    """Decorator for performance testing functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            helper = PerformanceTestHelper()
            metrics = helper.measure_function_performance(func, *args, **kwargs)

            # Check thresholds
            if max_execution_time and metrics.execution_time > max_execution_time:
                raise AssertionError(
                    f"Function exceeded max execution time: {metrics.execution_time:.3f}s > {max_execution_time}s"
                )

            if max_memory_mb and metrics.memory_usage_mb > max_memory_mb:
                raise AssertionError(
                    f"Function exceeded max memory usage: {metrics.memory_usage_mb:.2f}MB > {max_memory_mb}MB"
                )

            if min_ops_per_second and metrics.operations_per_second < min_ops_per_second:
                raise AssertionError(
                    f"Function below min ops/sec: {metrics.operations_per_second:.2f} < {min_ops_per_second}"
                )

            return metrics

        return wrapper
    return decorator


@contextmanager
def performance_monitoring():
    """Context manager for comprehensive performance monitoring."""
    helper = PerformanceTestHelper()
    collector = MetricsCollector()

    # Set default thresholds
    for metric, threshold in PERFORMANCE_THRESHOLDS.items():
        collector.set_threshold(metric, threshold)

    start_time = time.time()
    helper.set_baseline()

    try:
        yield {"helper": helper, "collector": collector}
    finally:
        end_time = time.time()
        duration = end_time - start_time

        final_metrics = helper.get_current_metrics()
        final_metrics["total_duration"] = duration

        collector.collect_metrics("test_session", final_metrics)

        # Check for threshold violations
        violations = collector.check_thresholds(final_metrics)
        if violations:
            logging.warning(f"Performance threshold violations: {violations}")


# Pytest fixtures for performance testing
@pytest.fixture
def performance_helper():
    """Fixture providing performance test helper."""
    return PerformanceTestHelper()


@pytest.fixture
def load_test_runner():
    """Fixture providing load test runner."""
    return LoadTestRunner()


@pytest.fixture
def benchmark_suite():
    """Fixture providing benchmark suite."""
    return BenchmarkSuite()


@pytest.fixture
def metrics_collector():
    """Fixture providing metrics collector."""
    return MetricsCollector()


@pytest.fixture(scope="session")
def performance_baseline():
    """Session-scoped fixture for performance baseline."""
    baseline = {}
    yield baseline

    # Save baseline results for future comparisons
    if baseline:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_baseline_{timestamp}.json"

        try:
            import json
            with open(f"reports/{filename}", "w") as f:
                json.dump(baseline, f, indent=2, default=str)
            print(f"Performance baseline saved to {filename}")
        except Exception as e:
            print(f"Failed to save performance baseline: {e}")
