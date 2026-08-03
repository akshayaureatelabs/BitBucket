"""
Performance Benchmarking - Track code performance over time
Phase 1 Feature: Performance Monitoring

Author: Sr. QA Tester - Akshaykumar Dudhwala
"""

import argparse
import html as html_module
import json
import logging
import sys
import time
import tracemalloc
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, Optional

import psutil

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.benchmark_dir = self.base_dir / ".benchmarks"
        self.benchmark_dir.mkdir(exist_ok=True)

        self.baseline_file = self.benchmark_dir / "baseline.json"
        self.current_results = {}
        self.results_history = []

    def benchmark(self, name: Optional[str] = None):
        """Decorator for benchmarking functions"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                tracemalloc_running = tracemalloc.is_tracing()
                if not tracemalloc_running:
                    try:
                        tracemalloc.start()
                    except Exception:
                        logger.warning("Failed to start tracemalloc — memory tracking disabled")
                process = psutil.Process()

                mem_before = process.memory_info().rss / 1024 / 1024
                process.cpu_percent(interval=None)

                start_time = time.perf_counter()
                start_cpu = time.process_time()
                cpu_before = process.cpu_percent(interval=None)

                try:
                    result = func(*args, **kwargs)
                    status = "success"
                except Exception:
                    status = "failed"
                    raise
                finally:
                    end_time = time.perf_counter()
                    end_cpu = time.process_time()

                    mem_after = process.memory_info().rss / 1024 / 1024
                    cpu_after = process.cpu_percent(interval=None)

                    current, peak = tracemalloc.get_traced_memory()
                    if not tracemalloc_running:
                        tracemalloc.stop()

                    benchmark_data = {
                        "name": name or func.__name__,
                        "timestamp": datetime.now().isoformat(),
                        "status": status,
                        "execution_time": end_time - start_time,
                        "cpu_time": end_cpu - start_cpu,
                        "memory_before_mb": mem_before,
                        "memory_after_mb": mem_after,
                        "memory_peak_mb": peak / 1024 / 1024,
                        "memory_increase_mb": mem_after - mem_before,
                        "cpu_percent": cpu_after - cpu_before,
                        "args": str(args),
                        "kwargs": str(kwargs),
                    }

                    result_key = name or func.__name__
                    if result_key not in self.current_results:
                        self.current_results[result_key] = []
                    self.current_results[result_key].append(benchmark_data)

                    self.results_history.append(benchmark_data)
                    self._save_current()

                return result

            return wrapper

        return decorator

    def _save_current(self):
        """Save current benchmark results"""
        with open(self.benchmark_dir / "current.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "results": self.current_results,
                    "history": self.results_history[-100:],
                },
                f,
                indent=2,
            )

    def load_baseline(self) -> Dict:
        """Load baseline benchmarks"""
        if self.baseline_file.exists():
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_baseline(self):
        """Save as new baseline"""
        baseline = {
            "timestamp": datetime.now().isoformat(),
            "results": self.current_results,
            "summary": self.generate_summary(),
        }

        with open(self.baseline_file, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2)

        backup_file = (
            self.benchmark_dir
            / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2)

    def compare_with_baseline(self) -> Dict:
        """Compare current results with baseline"""
        baseline = self.load_baseline()
        if not baseline:
            return {"status": "no_baseline", "message": "No baseline found"}

        comparisons = {}
        regressions = []
        improvements = []

        for func_name, current_runs in self.current_results.items():
            if func_name in baseline.get("results", {}):
                baseline_runs = baseline["results"][func_name]

                if current_runs and baseline_runs:
                    current_avg = sum(r["execution_time"] for r in current_runs) / len(
                        current_runs
                    )
                    baseline_avg = sum(
                        r["execution_time"] for r in baseline_runs
                    ) / len(baseline_runs)

                    diff = current_avg - baseline_avg
                    diff_percent = (
                        (diff / baseline_avg) * 100 if baseline_avg > 0 else 0
                    )

                    comparisons[func_name] = {
                        "baseline_avg": baseline_avg,
                        "current_avg": current_avg,
                        "diff": diff,
                        "diff_percent": diff_percent,
                        "status": (
                            "regression"
                            if diff_percent > 10
                            else "improvement" if diff_percent < -5 else "stable"
                        ),
                    }

                    if diff_percent > 10:
                        regressions.append(
                            {
                                "function": func_name,
                                "diff_percent": diff_percent,
                                "current": current_avg,
                                "baseline": baseline_avg,
                            }
                        )
                    elif diff_percent < -5:
                        improvements.append(
                            {
                                "function": func_name,
                                "diff_percent": diff_percent,
                                "current": current_avg,
                                "baseline": baseline_avg,
                            }
                        )

        return {
            "timestamp": datetime.now().isoformat(),
            "comparisons": comparisons,
            "regressions": regressions,
            "improvements": improvements,
            "total_functions": len(comparisons),
        }

    def generate_summary(self) -> Dict:
        """Generate summary statistics"""
        summary = {
            "total_benchmarks": len(self.results_history),
            "unique_functions": len(self.current_results),
            "slowest_functions": [],
            "memory_hungry": [],
            "timeline": [],
        }

        all_runs = []
        for func_name, runs in self.current_results.items():
            if runs:
                avg_time = sum(r["execution_time"] for r in runs) / len(runs)
                all_runs.append((func_name, avg_time))

        all_runs.sort(key=lambda x: x[1], reverse=True)
        summary["slowest_functions"] = [
            {"function": name, "avg_time": time} for name, time in all_runs[:5]
        ]

        memory_runs = []
        for func_name, runs in self.current_results.items():
            if runs:
                avg_memory = sum(r["memory_increase_mb"] for r in runs) / len(runs)
                memory_runs.append((func_name, avg_memory))

        memory_runs.sort(key=lambda x: x[1], reverse=True)
        summary["memory_hungry"] = [
            {"function": name, "avg_memory_mb": mem} for name, mem in memory_runs[:5]
        ]

        for result in self.results_history[-10:]:
            summary["timeline"].append(
                {
                    "timestamp": result["timestamp"],
                    "function": result["name"],
                    "execution_time": result["execution_time"],
                }
            )

        return summary

    def generate_html_report(self) -> str:
        """Generate HTML report"""
        summary = self.generate_summary()
        comparison = self.compare_with_baseline()

        slowest_rows = ""
        for func in summary["slowest_functions"]:
            slowest_rows += f"<tr><td>{html_module.escape(func['function'])}</td><td>{func['avg_time']:.3f}</td></tr>"

        memory_rows = ""
        for func in summary["memory_hungry"]:
            memory_rows += f"<tr><td>{html_module.escape(func['function'])}</td><td>{func.get('avg_memory_mb', 0):.2f}</td></tr>"

        regression_rows = ""
        if comparison.get("regressions"):
            for reg in comparison["regressions"]:
                regression_rows += f"""
                <tr class="bad">
                    <td>{html_module.escape(reg['function'])}</td>
                    <td>{reg['diff_percent']:.1f}%</td>
                    <td>{reg['current']:.3f}</td>
                    <td>{reg['baseline']:.3f}</td>
                </tr>"""

        improvement_rows = ""
        if comparison.get("improvements"):
            for imp in comparison["improvements"]:
                improvement_rows += f"""
                <tr class="good">
                    <td>{html_module.escape(imp['function'])}</td>
                    <td>{imp['diff_percent']:.1f}%</td>
                    <td>{imp['current']:.3f}</td>
                    <td>{imp['baseline']:.3f}</td>
                </tr>"""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Performance Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .good {{ color: green; }}
        .bad {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Performance Benchmark Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p>Total Benchmarks: {summary['total_benchmarks']}</p>
        <p>Unique Functions: {summary['unique_functions']}</p>
    </div>

    <h2>Slowest Functions</h2>
    <table><tr><th>Function</th><th>Avg Time (s)</th></tr>{slowest_rows}</table>

    <h2>Memory Usage</h2>
    <table><tr><th>Function</th><th>Avg Memory Increase (MB)</th></tr>{memory_rows}</table>

    <h2>Comparison with Baseline</h2>"""

        if comparison.get("regressions"):
            html += f"""
            <h3 class="bad">Regressions Detected</h3>
            <table><tr><th>Function</th><th>Change (%)</th><th>Current (s)</th><th>Baseline (s)</th></tr>{regression_rows}</table>"""

        if comparison.get("improvements"):
            html += f"""
            <h3 class="good">Improvements</h3>
            <table><tr><th>Function</th><th>Change (%)</th><th>Current (s)</th><th>Baseline (s)</th></tr>{improvement_rows}</table>"""

        html += "</body></html>"

        report_file = self.benchmark_dir / "performance-report.html"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html)

        return str(report_file)

    def check_regressions(self, threshold: float = 10.0) -> bool:
        """Check if any regressions exceed threshold"""
        comparison = self.compare_with_baseline()
        found = False

        if comparison.get("regressions"):
            for reg in comparison["regressions"]:
                if reg["diff_percent"] > threshold:
                    logger.error(
                        "Regression in %s: %.1f%% slower",
                        reg["function"],
                        reg["diff_percent"],
                    )
                    found = True
        return found


def main():
    parser = argparse.ArgumentParser(description="Performance Benchmarking")
    parser.add_argument(
        "--run-benchmarks", action="store_true", help="Run performance benchmarks"
    )
    parser.add_argument(
        "--compare-baseline", action="store_true", help="Compare with baseline"
    )
    parser.add_argument(
        "--save-baseline", action="store_true", help="Save current as baseline"
    )
    parser.add_argument(
        "--generate-report", action="store_true", help="Generate HTML report"
    )
    parser.add_argument(
        "--check-regressions",
        type=float,
        default=None,
        help="Check for regressions (threshold percent)",
    )

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parser.parse_args()
    benchmark = PerformanceBenchmark()

    if args.run_benchmarks:
        @benchmark.benchmark("example_function")
        def example_function():
            time.sleep(0.1)
            return "done"

        logger.info("Running benchmarks...")
        for i in range(5):
            example_function()
        logger.info("Benchmarks complete")

    if args.compare_baseline:
        logger.info("Comparing with baseline...")
        comparison = benchmark.compare_with_baseline()
        if comparison.get("comparisons"):
            for func, data in comparison["comparisons"].items():
                level = (
                    logging.INFO
                    if data["status"] == "stable"
                    else (
                        logging.WARNING
                        if data["status"] == "regression"
                        else logging.INFO
                    )
                )
                logger.log(
                    level,
                    "%s: %+.1f%% (%.3fs vs %.3fs)",
                    func,
                    data["diff_percent"],
                    data["current_avg"],
                    data["baseline_avg"],
                )

    if args.save_baseline:
        benchmark.save_baseline()
        logger.info("Baseline saved")

    if args.generate_report:
        report = benchmark.generate_html_report()
        logger.info("Report generated: %s", report)

    if args.check_regressions is not None:
        if benchmark.check_regressions(args.check_regressions):
            logger.error("Regressions exceed %.1f%% threshold", args.check_regressions)
            sys.exit(1)
        else:
            logger.info("No regressions above %.1f%% threshold", args.check_regressions)


if __name__ == "__main__":
    main()
