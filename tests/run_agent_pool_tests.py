#!/usr/bin/env python3
"""
Comprehensive Test Runner for Agent Pool Discovery System

This script provides a comprehensive testing framework for the agent pool discovery
system with detailed reporting, performance analysis, and coverage metrics.

Usage:
    python run_agent_pool_tests.py [options]

Options:
    --verbose, -v       Verbose output
    --performance, -p   Run performance tests
    --integration, -i   Run integration tests
    --manual, -m        Run manual tests only
    --coverage, -c      Generate coverage report
    --html              Generate HTML coverage report
    --benchmark, -b     Run benchmark tests
    --stress, -s        Run stress tests
    --quick, -q         Run quick tests only
    --help, -h          Show this help message
"""

import asyncio
import argparse
import sys
import time
import traceback
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_pool_tests.log')
    ]
)
logger = logging.getLogger(__name__)

# Try to import required modules
try:
    import pytest
    import coverage
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    logger.warning("PyTest not available - using manual tests only")

try:
    from agentical.agents.pool_discovery import AgentPoolDiscoveryService
    from agentical.agents.capability_matcher import AdvancedCapabilityMatcher, MatchingAlgorithm
    from agentical.agents.playbook_capabilities import (
        AgentPoolEntry, CapabilityFilter, MatchingContext,
        HealthStatus, PlaybookCapabilityType, CapabilityComplexity, PlaybookCapability
    )
    from agentical.tests.test_agent_pool_discovery import run_manual_tests
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    logger.error(f"Agent pool dependencies not available: {e}")


class TestResult:
    """Test result container."""

    def __init__(self, name: str, success: bool, duration: float,
                 error: Optional[str] = None, details: Optional[Dict] = None):
        self.name = name
        self.success = success
        self.duration = duration
        self.error = error
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class TestSuite:
    """Main test suite runner."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    def log(self, message: str, level: str = "info"):
        """Log message with appropriate level."""
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)

        if self.verbose:
            print(f"[{level.upper()}] {message}")

    def add_result(self, result: TestResult):
        """Add test result."""
        self.results.append(result)

        status = "✅ PASS" if result.success else "❌ FAIL"
        self.log(f"{status} {result.name} ({result.duration:.2f}s)")

        if not result.success and result.error:
            self.log(f"Error: {result.error}", "error")

    async def run_manual_tests(self) -> TestResult:
        """Run manual tests."""
        if not DEPENDENCIES_AVAILABLE:
            return TestResult(
                "Manual Tests",
                False,
                0.0,
                "Dependencies not available"
            )

        start_time = time.time()
        try:
            success = await run_manual_tests()
            duration = time.time() - start_time
            return TestResult("Manual Tests", success, duration)
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                "Manual Tests",
                False,
                duration,
                str(e)
            )

    async def run_performance_tests(self) -> List[TestResult]:
        """Run performance-specific tests."""
        if not DEPENDENCIES_AVAILABLE:
            return [TestResult(
                "Performance Tests",
                False,
                0.0,
                "Dependencies not available"
            )]

        results = []

        # Test 1: Large agent pool performance
        start_time = time.time()
        try:
            discovery_service = AgentPoolDiscoveryService()
            await discovery_service.initialize()

            # Create 1000 agents
            for i in range(1000):
                agent = AgentPoolEntry(
                    agent_id=f"perf_agent_{i:04d}",
                    agent_type=f"type_{i % 10}",
                    agent_name=f"Performance Agent {i}",
                    description=f"Performance test agent {i}",
                    health_status=HealthStatus.HEALTHY if i % 5 != 0 else HealthStatus.WARNING
                )
                discovery_service.agent_pool[agent.agent_id] = agent

            # Test statistics performance
            stats_start = time.time()
            stats = await discovery_service.get_pool_statistics()
            stats_duration = time.time() - stats_start

            success = stats["total_agents"] == 1000 and stats_duration < 2.0
            duration = time.time() - start_time

            results.append(TestResult(
                "Large Pool Statistics",
                success,
                duration,
                None if success else f"Stats took {stats_duration:.2f}s (limit: 2.0s)",
                {"agent_count": 1000, "stats_duration": stats_duration}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(TestResult(
                "Large Pool Statistics",
                False,
                duration,
                str(e)
            ))

        # Test 2: Concurrent operations
        start_time = time.time()
        try:
            discovery_service = AgentPoolDiscoveryService()
            await discovery_service.initialize()

            # Add test agents
            for i in range(10):
                agent = AgentPoolEntry(
                    agent_id=f"concurrent_agent_{i}",
                    agent_type="concurrent",
                    agent_name=f"Concurrent Agent {i}",
                    description=f"Agent for concurrency testing {i}",
                    health_status=HealthStatus.HEALTHY
                )
                discovery_service.agent_pool[agent.agent_id] = agent

            # Run concurrent heartbeat updates
            async def update_heartbeat(agent_id):
                return await discovery_service.update_agent_heartbeat(agent_id)

            tasks = [update_heartbeat(f"concurrent_agent_{i}") for i in range(10)]
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)

            success = all(r is True for r in concurrent_results if not isinstance(r, Exception))
            duration = time.time() - start_time

            results.append(TestResult(
                "Concurrent Operations",
                success,
                duration,
                None if success else "Some concurrent operations failed",
                {"operations": len(tasks), "success_rate": sum(1 for r in concurrent_results if r is True) / len(tasks)}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(TestResult(
                "Concurrent Operations",
                False,
                duration,
                str(e)
            ))

        return results

    async def run_stress_tests(self) -> List[TestResult]:
        """Run stress tests."""
        if not DEPENDENCIES_AVAILABLE:
            return [TestResult(
                "Stress Tests",
                False,
                0.0,
                "Dependencies not available"
            )]

        results = []

        # Stress Test 1: Memory usage under load
        start_time = time.time()
        try:
            discovery_service = AgentPoolDiscoveryService()
            await discovery_service.initialize()

            # Add and remove agents in cycles
            for cycle in range(20):
                # Add 50 agents
                for i in range(50):
                    agent = AgentPoolEntry(
                        agent_id=f"stress_agent_{cycle}_{i}",
                        agent_type="stress",
                        agent_name=f"Stress Agent {cycle}-{i}",
                        description="Agent for stress testing",
                        health_status=HealthStatus.HEALTHY
                    )
                    discovery_service.agent_pool[agent.agent_id] = agent

                # Perform operations
                await discovery_service.get_pool_statistics()
                await discovery_service.get_available_agents()

                # Remove agents
                for i in range(50):
                    agent_id = f"stress_agent_{cycle}_{i}"
                    if agent_id in discovery_service.agent_pool:
                        del discovery_service.agent_pool[agent_id]

            # Verify cleanup
            final_stats = await discovery_service.get_pool_statistics()
            success = final_stats["total_agents"] == 0
            duration = time.time() - start_time

            results.append(TestResult(
                "Memory Stress Test",
                success,
                duration,
                None if success else f"Final agent count: {final_stats['total_agents']}",
                {"cycles": 20, "agents_per_cycle": 50}
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(TestResult(
                "Memory Stress Test",
                False,
                duration,
                str(e)
            ))

        return results

    async def run_benchmark_tests(self) -> List[TestResult]:
        """Run benchmark tests."""
        if not DEPENDENCIES_AVAILABLE:
            return [TestResult(
                "Benchmark Tests",
                False,
                0.0,
                "Dependencies not available"
            )]

        results = []

        # Benchmark 1: Algorithm comparison
        start_time = time.time()
        try:
            matcher = AdvancedCapabilityMatcher()

            # Create test agents
            agents = []
            for i in range(100):
                agent = AgentPoolEntry(
                    agent_id=f"benchmark_agent_{i}",
                    agent_type="benchmark",
                    agent_name=f"Benchmark Agent {i}",
                    description=f"Agent for benchmarking {i}",
                    health_status=HealthStatus.HEALTHY,
                    current_load=i % 5,
                    available_tools=[f"tool_{i % 3}"],
                    capabilities=[
                        PlaybookCapability(
                            name=f"benchmark_capability_{i}",
                            display_name=f"Benchmark Capability {i}",
                            description=f"Capability for benchmarking {i}",
                            capability_type=PlaybookCapabilityType.TASK_EXECUTION,
                            complexity=CapabilityComplexity.SIMPLE,
                            supported_step_types=["action"],
                            required_tools=[f"tool_{i % 3}"]
                        )
                    ]
                )
                agents.append(agent)

            requirements = CapabilityFilter(
                capability_types=[PlaybookCapabilityType.TASK_EXECUTION],
                step_types=["action"]
            )
            context = MatchingContext()

            # Benchmark different algorithms
            algorithm_results = {}
            algorithms = [
                MatchingAlgorithm.WEIGHTED_SCORE,
                MatchingAlgorithm.PERFORMANCE_OPTIMIZED,
                MatchingAlgorithm.LOAD_BALANCED
            ]

            for algorithm in algorithms:
                algo_start = time.time()
                matches = await matcher.find_best_matches(
                    agents=agents,
                    requirements=requirements,
                    context=context,
                    algorithm=algorithm,
                    max_results=10
                )
                algo_duration = time.time() - algo_start
                algorithm_results[algorithm.value] = {
                    "duration": algo_duration,
                    "matches": len(matches)
                }

            duration = time.time() - start_time
            success = all(r["duration"] < 1.0 for r in algorithm_results.values())

            results.append(TestResult(
                "Algorithm Benchmark",
                success,
                duration,
                None if success else "Some algorithms too slow",
                algorithm_results
            ))

        except Exception as e:
            duration = time.time() - start_time
            results.append(TestResult(
                "Algorithm Benchmark",
                False,
                duration,
                str(e)
            ))

        return results

    def run_pytest_tests(self, test_path: str = "agentical/tests/test_agent_pool_discovery.py") -> TestResult:
        """Run pytest tests."""
        if not PYTEST_AVAILABLE:
            return TestResult(
                "PyTest Suite",
                False,
                0.0,
                "PyTest not available"
            )

        start_time = time.time()
        try:
            # Run pytest with specific options
            cmd = [
                sys.executable, "-m", "pytest",
                test_path,
                "-v",
                "--tb=short",
                "--durations=10"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # Parse output for additional details
            details = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

            return TestResult(
                "PyTest Suite",
                success,
                duration,
                result.stderr if not success else None,
                details
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                "PyTest Suite",
                False,
                duration,
                "Test timeout (5 minutes exceeded)"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                "PyTest Suite",
                False,
                duration,
                str(e)
            )

    def generate_coverage_report(self, html: bool = False) -> TestResult:
        """Generate coverage report."""
        start_time = time.time()
        try:
            cov = coverage.Coverage()
            cov.start()

            # Import and run key modules to measure coverage
            if DEPENDENCIES_AVAILABLE:
                from agentical.agents import pool_discovery
                from agentical.agents import capability_matcher
                from agentical.agents import playbook_capabilities

            cov.stop()
            cov.save()

            # Generate report
            if html:
                cov.html_report(directory="htmlcov")
                report_path = "htmlcov/index.html"
            else:
                with open("coverage.txt", "w") as f:
                    cov.report(file=f)
                report_path = "coverage.txt"

            duration = time.time() - start_time

            return TestResult(
                "Coverage Report",
                True,
                duration,
                None,
                {"report_path": report_path, "format": "html" if html else "text"}
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                "Coverage Report",
                False,
                duration,
                str(e)
            )

    async def run_all_tests(self, options: Dict[str, bool]) -> Dict[str, Any]:
        """Run all requested tests."""
        self.start_time = datetime.utcnow()
        self.log("🧪 Starting comprehensive agent pool discovery tests...")

        # Run manual tests
        if options.get("manual", True):
            result = await self.run_manual_tests()
            self.add_result(result)

        # Run pytest tests
        if options.get("pytest", True) and PYTEST_AVAILABLE:
            result = self.run_pytest_tests()
            self.add_result(result)

        # Run performance tests
        if options.get("performance", False):
            performance_results = await self.run_performance_tests()
            for result in performance_results:
                self.add_result(result)

        # Run stress tests
        if options.get("stress", False):
            stress_results = await self.run_stress_tests()
            for result in stress_results:
                self.add_result(result)

        # Run benchmark tests
        if options.get("benchmark", False):
            benchmark_results = await self.run_benchmark_tests()
            for result in benchmark_results:
                self.add_result(result)

        # Generate coverage report
        if options.get("coverage", False):
            result = self.generate_coverage_report(html=options.get("html", False))
            self.add_result(result)

        self.end_time = datetime.utcnow()
        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - passed_tests

        total_duration = sum(r.duration for r in self.results)

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_duration": total_duration,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None
            },
            "results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "duration": r.duration,
                    "error": r.error,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ],
            "failed_tests": [
                {
                    "name": r.name,
                    "error": r.error,
                    "duration": r.duration
                }
                for r in self.results if not r.success
            ]
        }

        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print test summary."""
        summary = report["summary"]

        print("\n" + "="*60)
        print("AGENT POOL DISCOVERY TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")

        if summary["failed"] > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for failed in report["failed_tests"]:
                print(f"❌ {failed['name']}")
                if failed['error']:
                    print(f"   Error: {failed['error']}")
                print(f"   Duration: {failed['duration']:.2f}s")

        print("\nDETAILED RESULTS:")
        print("-" * 40)
        for result in report["results"]:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']} ({result['duration']:.2f}s)")

        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for agent pool discovery system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--performance", "-p", action="store_true", help="Run performance tests")
    parser.add_argument("--integration", "-i", action="store_true", help="Run integration tests")
    parser.add_argument("--manual", "-m", action="store_true", help="Run manual tests only")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--benchmark", "-b", action="store_true", help="Run benchmark tests")
    parser.add_argument("--stress", "-s", action="store_true", help="Run stress tests")
    parser.add_argument("--quick", "-q", action="store_true", help="Run quick tests only")
    parser.add_argument("--output", "-o", help="Output report to file")

    args = parser.parse_args()

    # Configure test options
    options = {
        "manual": args.manual or args.quick or not any([args.performance, args.benchmark, args.stress]),
        "pytest": not args.manual and not args.quick,
        "performance": args.performance,
        "benchmark": args.benchmark,
        "stress": args.stress,
        "coverage": args.coverage,
        "html": args.html
    }

    # Create test suite
    suite = TestSuite(verbose=args.verbose)

    # Run tests
    async def run_tests():
        try:
            report = await suite.run_all_tests(options)

            # Print summary
            suite.print_summary(report)

            # Save report to file
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\nReport saved to: {args.output}")

            # Return exit code based on results
            return 0 if report["summary"]["failed"] == 0 else 1

        except Exception as e:
            logger.error(f"Test runner failed: {e}")
            traceback.print_exc()
            return 1

    # Run async tests
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
