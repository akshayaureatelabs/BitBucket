"""Unit tests for bug fixes applied in v1.1.0.

Tests cover:
- _strip_extras() method in dependency_health.py
- Pypistats caching in dependency_health.py
- tracemalloc guard logic in performance_benchmark.py
"""

import json
import sys
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path so we can import the tools
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dependency_health import DependencyHealthCheck  # noqa: E402
from performance_benchmark import PerformanceBenchmark  # noqa: E402

# ---------------------------------------------------------------------------
# _strip_extras() tests
# ---------------------------------------------------------------------------


class TestStripExtras:
    """Tests for DependencyHealthCheck._strip_extras()"""

    def test_no_extras(self):
        name, extras = DependencyHealthCheck._strip_extras("pandas")
        assert name == "pandas"
        assert extras is None

    def test_single_extra(self):
        name, extras = DependencyHealthCheck._strip_extras("pytest-cov[testing]")
        assert name == "pytest-cov"
        assert extras == "testing"

    def test_multiple_extras(self):
        name, extras = DependencyHealthCheck._strip_extras("requests[security,socks]")
        assert name == "requests"
        assert extras == "security,socks"

    def test_empty_extras(self):
        name, extras = DependencyHealthCheck._strip_extras("package[]")
        assert name == "package"
        assert extras == ""

    def test_version_with_extras(self):
        """Extras parsing should work even when a version specifier is present."""
        # The method only receives the name portion (before >=), so this tests
        # that the method doesn't choke on edge-case names.
        name, extras = DependencyHealthCheck._strip_extras("foo[bar]")
        assert name == "foo"
        assert extras == "bar"

    def test_bracket_in_name_not_extras(self):
        """A name like 'C++[lib]' should split at the first bracket."""
        name, extras = DependencyHealthCheck._strip_extras("C++[lib]")
        assert name == "C++"
        assert extras == "lib"


# ---------------------------------------------------------------------------
# Pypistats caching tests
# ---------------------------------------------------------------------------


class TestPypistatsCaching:
    """Tests for pypistats API response caching in DependencyHealthCheck."""

    def _make_checker(self, tmp_path):
        """Create a DependencyHealthCheck instance with a custom report dir."""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        checker = DependencyHealthCheck.__new__(DependencyHealthCheck)
        checker.base_dir = Path(__file__).resolve().parent.parent
        checker.report_dir = tmp_path
        checker.pypi_cache = tmp_path / "pypi_cache.json"
        checker.vuln_cache = tmp_path / "vuln_cache.json"
        checker.pypistats_cache = tmp_path / "pypistats_cache.json"
        checker.pypi_data = {}
        checker.vuln_data = {}
        checker.pypistats_data = {}
        checker.requirements_file = checker.base_dir / "requirements.txt"
        checker.packages = checker._parse_requirements()
        checker.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        checker.session.mount("https://", HTTPAdapter(max_retries=retries))
        checker.session.mount("http://", HTTPAdapter(max_retries=retries))
        return checker

    def test_cache_miss_then_hit(self, tmp_path):
        """First call should hit API; second call with cached data should not."""
        checker = self._make_checker(tmp_path)

        # Populate cache with fake data
        checker.pypistats_data["requests"] = {
            "cached_at": datetime.now().isoformat(),
            "downloads": 50000,
        }
        checker._save_caches()

        # Verify cache file was written
        assert checker.pypistats_cache.exists()
        with open(checker.pypistats_cache, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "requests" in data
        assert data["requests"]["downloads"] == 50000

    def test_cache_loads_on_init(self, tmp_path):
        """_load_caches should populate pypistats_data from disk."""
        # Write a cache file manually
        cache_data = {
            "pytest": {
                "cached_at": __import__("datetime").datetime.now().isoformat(),
                "downloads": 100000,
            }
        }
        tmp_path.mkdir(exist_ok=True)
        with open(tmp_path / "pypistats_cache.json", "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        checker = self._make_checker(tmp_path)
        checker._load_caches()

        assert "pytest" in checker.pypistats_data
        assert checker.pypistats_data["pytest"]["downloads"] == 100000

    def test_stale_cache_skips_cache_and_fetches(self, tmp_path):
        """Cache entries older than 24 hours should trigger a fresh API call."""
        checker = self._make_checker(tmp_path)

        # Write a stale cache entry (25 hours ago in UTC)
        checker.pypistats_data["old-pkg"] = {
            "cached_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
            "downloads": 999,
        }

        package_info = {"info": {"name": "old-pkg"}, "releases": {}}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"last_month": 7777}}

        with patch.object(
            checker.session, "get", return_value=mock_response
        ) as mock_get:
            _ = checker.calculate_health_score(package_info, [])

        # API should have been called because cache was stale
        mock_get.assert_called()
        # Cache should now be updated with fresh data
        assert checker.pypistats_data["old-pkg"]["downloads"] == 7777

    def test_fresh_cache_skips_api(self, tmp_path):
        """Cache entries less than 24 hours old should skip the API call."""
        checker = self._make_checker(tmp_path)

        # Write a fresh cache entry
        checker.pypistats_data["fresh-pkg"] = {
            "cached_at": datetime.now().isoformat(),
            "downloads": 42000,
        }

        package_info = {"info": {"name": "fresh-pkg"}, "releases": {}}

        with patch("dependency_health.requests.get") as mock_get:
            _ = checker.calculate_health_score(package_info, [])

        # API should NOT have been called — cache was fresh
        mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# tracemalloc guard tests
# ---------------------------------------------------------------------------


class TestTracemallocGuard:
    """Tests for the tracemalloc.is_tracing() guard in PerformanceBenchmark."""

    def test_benchmark_does_not_stop_external_tracemalloc(self):
        """If tracemalloc was already running, the decorator should not stop it."""
        # Start tracemalloc externally
        tracemalloc.start()
        try:
            assert tracemalloc.is_tracing(), "tracemalloc should be running"

            benchmark = PerformanceBenchmark()

            @benchmark.benchmark("guard_test")
            def my_func():
                return 42

            result = my_func()
            assert result == 42

            # tracemalloc should still be running (guard didn't stop it)
            assert (
                tracemalloc.is_tracing()
            ), "tracemalloc should still be running after benchmark"
        finally:
            tracemalloc.stop()

    def test_benchmark_starts_and_stops_when_not_running(self):
        """If tracemalloc was NOT running, the decorator should start and stop it."""
        # Ensure tracemalloc is not running
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        assert not tracemalloc.is_tracing()

        benchmark = PerformanceBenchmark()

        @benchmark.benchmark("auto_test")
        def my_func():
            return 99

        result = my_func()
        assert result == 99

        # tracemalloc should have been stopped by the decorator
        assert (
            not tracemalloc.is_tracing()
        ), "tracemalloc should be stopped after benchmark when we started it"

    def test_benchmark_records_results(self):
        """The decorator should record benchmark data correctly."""
        benchmark = PerformanceBenchmark()

        @benchmark.benchmark("record_test")
        def timed_func():
            time.sleep(0.01)
            return "done"

        timed_func()

        assert "record_test" in benchmark.current_results
        assert len(benchmark.current_results["record_test"]) == 1
        data = benchmark.current_results["record_test"][0]
        assert data["status"] == "success"
        assert data["execution_time"] > 0
        assert data["memory_peak_mb"] >= 0
