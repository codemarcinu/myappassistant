#!/usr/bin/env python3
"""
Skrypt do uruchamiania testów performance z memory profiling
Zgodnie z regułami MDC dla testowania i monitoringu
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

import structlog

logger = structlog.get_logger(__name__)


class PerformanceTestRunner:
    """Runner dla testów performance z memory profiling"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_path = project_root / "src" / "backend"
        self.results_dir = project_root / "test_results" / "performance"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_memory_profiling_tests(self, verbose: bool = False) -> bool:
        """Uruchamia testy memory profiling"""
        logger.info("Starting memory profiling tests")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(
                self.backend_path / "tests" / "performance" / "test_memory_profiling.py"
            ),
            "-v" if verbose else "",
            "--benchmark-only",
            "--benchmark-sort=mean",
            "--benchmark-min-rounds=5",
            f"--benchmark-json={self.results_dir / 'memory_profiling_benchmarks.json'}",
            "--tb=short",
        ]

        cmd = [arg for arg in cmd if arg]  # Remove empty strings

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("Memory profiling tests completed successfully")
                if verbose:
                    print(result.stdout)
                return True
            else:
                logger.error("Memory profiling tests failed", stderr=result.stderr)
                if verbose:
                    print(result.stderr)
                return False

        except Exception as e:
            logger.error("Failed to run memory profiling tests", error=str(e))
            return False

    def run_middleware_tests(self, verbose: bool = False) -> bool:
        """Uruchamia testy middleware"""
        logger.info("Starting middleware tests")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(
                self.backend_path
                / "tests"
                / "unit"
                / "test_memory_monitoring_middleware.py"
            ),
            "-v" if verbose else "",
            "--tb=short",
        ]

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("Middleware tests completed successfully")
                if verbose:
                    print(result.stdout)
                return True
            else:
                logger.error("Middleware tests failed", stderr=result.stderr)
                if verbose:
                    print(result.stderr)
                return False

        except Exception as e:
            logger.error("Failed to run middleware tests", error=str(e))
            return False

    def run_database_performance_tests(self, verbose: bool = False) -> bool:
        """Uruchamia testy performance bazy danych"""
        logger.info("Starting database performance tests")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.backend_path / "tests" / "performance" / "test_db_performance.py"),
            "-v" if verbose else "",
            "--benchmark-only",
            "--benchmark-sort=mean",
            f"--benchmark-json={self.results_dir / 'database_performance_benchmarks.json'}",
            "--tb=short",
        ]

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("Database performance tests completed successfully")
                if verbose:
                    print(result.stdout)
                return True
            else:
                logger.error("Database performance tests failed", stderr=result.stderr)
                if verbose:
                    print(result.stderr)
                return False

        except Exception as e:
            logger.error("Failed to run database performance tests", error=str(e))
            return False

    def run_memray_profiling(self, output_file: str = "memray_profile.bin") -> bool:
        """Uruchamia profiling z memray"""
        logger.info("Starting memray profiling")

        # Uruchom aplikację z memray
        cmd = [
            sys.executable,
            "-m",
            "memray",
            "run",
            "--output",
            str(self.results_dir / output_file),
            str(self.backend_path / "main.py"),
        ]

        try:
            # Uruchom w tle przez krótki czas
            process = subprocess.Popen(cmd, cwd=self.project_root)

            # Poczekaj chwilę na uruchomienie
            time.sleep(5)

            # Zatrzymaj proces
            process.terminate()
            process.wait(timeout=10)

            logger.info("Memray profiling completed")
            return True

        except Exception as e:
            logger.error("Failed to run memray profiling", error=str(e))
            return False

    def generate_memray_report(self, profile_file: str = "memray_profile.bin") -> bool:
        """Generuje raport z memray"""
        logger.info("Generating memray report")

        profile_path = self.results_dir / profile_file
        if not profile_path.exists():
            logger.error("Profile file not found", file=str(profile_path))
            return False

        # Generuj HTML report
        cmd = [
            sys.executable,
            "-m",
            "memray",
            "flamegraph",
            str(profile_path),
            "--output",
            str(self.results_dir / "memray_flamegraph.html"),
        ]

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("Memray report generated successfully")
                return True
            else:
                logger.error("Failed to generate memray report", stderr=result.stderr)
                return False

        except Exception as e:
            logger.error("Failed to generate memray report", error=str(e))
            return False

    def run_all_tests(
        self, verbose: bool = False, include_memray: bool = False
    ) -> bool:
        """Uruchamia wszystkie testy performance"""
        logger.info("Starting all performance tests")

        results = []

        # Testy memory profiling
        results.append(self.run_memory_profiling_tests(verbose))

        # Testy middleware
        results.append(self.run_middleware_tests(verbose))

        # Testy database performance
        results.append(self.run_database_performance_tests(verbose))

        # Memray profiling (opcjonalnie)
        if include_memray:
            results.append(self.run_memray_profiling())
            if results[-1]:  # Jeśli memray się udał
                results.append(self.generate_memray_report())

        success_count = sum(results)
        total_count = len(results)

        logger.info(
            "Performance tests completed",
            success_count=success_count,
            total_count=total_count,
            success_rate=f"{success_count/total_count*100:.1f}%",
        )

        return all(results)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Run performance tests with memory profiling"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--memray", action="store_true", help="Include memray profiling"
    )
    parser.add_argument(
        "--test-type",
        choices=["memory", "middleware", "database", "all"],
        default="all",
        help="Type of tests to run",
    )

    args = parser.parse_args()

    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get project root
    project_root = Path(__file__).parent.parent
    runner = PerformanceTestRunner(project_root)

    success = False

    if args.test_type == "memory":
        success = runner.run_memory_profiling_tests(args.verbose)
    elif args.test_type == "middleware":
        success = runner.run_middleware_tests(args.verbose)
    elif args.test_type == "database":
        success = runner.run_database_performance_tests(args.verbose)
    else:  # all
        success = runner.run_all_tests(args.verbose, args.memray)

    if success:
        logger.info("All performance tests passed")
        sys.exit(0)
    else:
        logger.error("Some performance tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
