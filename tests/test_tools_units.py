"""
Dynamic unit tests for the 4 QA tools' internal logic.

These exercise real code paths (no network) so coverage grows and behaviour
is locked down: requirement parsing, health-score inputs, dashboard DB
recording/metrics, and smart-test-selector mapping.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# dependency_health.py
# ---------------------------------------------------------------------------


def _make_checker(tmp_path):
    from dependency_health import DependencyHealthCheck
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    ch = DependencyHealthCheck.__new__(DependencyHealthCheck)
    ch.base_dir = tmp_path
    ch.report_dir = tmp_path
    ch.pypi_cache = tmp_path / "pypi_cache.json"
    ch.vuln_cache = tmp_path / "vuln_cache.json"
    ch.pypistats_cache = tmp_path / "pypistats_cache.json"
    ch.pypi_data = {}
    ch.vuln_data = {}
    ch.pypistats_data = {}
    ch.requirements_file = tmp_path / "requirements.txt"
    ch.packages = ch._parse_requirements()
    ch.session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    ch.session.mount("https://", HTTPAdapter(max_retries=retries))
    ch.session.mount("http://", HTTPAdapter(max_retries=retries))
    return ch


def test_parse_requirements_specifiers(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text(
        "pytest>=7.4.0,<9.0.0\nblack==23.11.0\nrequests[security,socks]>=2.31.0\nfoo\n"
    )
    ch = _make_checker(tmp_path)
    by_name = {p["name"]: p for p in ch.packages}

    assert by_name["pytest"]["specifier"] == ">="
    assert by_name["pytest"]["version"] == "7.4.0"
    assert by_name["black"]["specifier"] == "=="
    assert by_name["requests"]["extras"] == "security,socks"
    assert by_name["foo"]["version"] is None  # unpinned -> no version


def test_parse_requirements_skips_comments_and_blanks(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("# comment\n\npytest>=7.4.0\n")
    ch = _make_checker(tmp_path)
    assert [p["name"] for p in ch.packages] == ["pytest"]


def test_health_score_penalizes_vulnerabilities(tmp_path):
    from dependency_health import DependencyHealthCheck

    ch = _make_checker(tmp_path)
    info = {"info": {"name": "x", "version": "1.0"}, "releases": {}}
    clean = ch.calculate_health_score(info, [])
    vuln = ch.calculate_health_score(
        info, [{"id": "CVE-1", "severity": "high"}]
    )
    assert vuln["score"] < clean["score"]


def test_health_score_mature_bonus(tmp_path):
    from dependency_health import DependencyHealthCheck

    ch = _make_checker(tmp_path)
    info = {
        "info": {
            "name": "x",
            "version": "1.0",
            "classifiers": ["Development Status :: 6 - Mature"],
        },
        "releases": {},
    }
    score = ch.calculate_health_score(info, [])["score"]
    assert score >= 100  # bonus applied, clamped at 100


# ---------------------------------------------------------------------------
# pipeline_dashboard.py
# ---------------------------------------------------------------------------


def _make_dashboard(tmp_path):
    from pipeline_dashboard import PipelineDashboard

    d = PipelineDashboard.__new__(PipelineDashboard)
    d.base_dir = tmp_path
    d.db_path = tmp_path / "pipeline-metrics.db"
    d.dashboard_dir = tmp_path / "dashboard"
    d.dashboard_dir.mkdir(exist_ok=True)
    d._init_database()
    return d


def test_dashboard_record_and_metrics(tmp_path):
    d = _make_dashboard(tmp_path)
    d.record_run(
        {
            "run_id": "r1",
            "branch": "main",
            "status": "success",
            "duration": 10.0,
            "steps": [{"name": "x", "duration": 5, "status": "success"}],
            "test_results": {
                "total": 10,
                "passed": 9,
                "failed": 1,
                "skipped": 0,
                "coverage": 80,
                "duration": 5,
            },
        }
    )
    m = d.get_metrics(days=30)
    assert m["total_runs"] == 1
    assert m["successful_runs"] == 1
    assert m["success_rate"] == 100
    assert len(m["steps"]) == 1


def test_dashboard_failure_metrics(tmp_path):
    d = _make_dashboard(tmp_path)
    d.record_run(
        {
            "run_id": "r2",
            "branch": "feature/x",
            "status": "failed",
            "duration": 3.0,
            "steps": [],
        }
    )
    m = d.get_metrics(days=30)
    assert m["total_runs"] == 1
    assert m["successful_runs"] == 0
    assert m["success_rate"] == 0


# ---------------------------------------------------------------------------
# smart_test_selector.py
# ---------------------------------------------------------------------------


def test_selector_builds_mapping_for_known_module(tmp_path):
    from smart_test_selector import SmartTestSelector

    # Create a fake source module + a test file that imports it
    (tmp_path / "dependency_health.py").write_text("x = 1\n")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_dependency_health.py").write_text(
        "from dependency_health import DependencyHealthCheck\n"
    )

    sel = SmartTestSelector.__new__(SmartTestSelector)
    sel.base_dir = tmp_path
    sel.cache_dir = tmp_path / ".test-cache"
    sel.cache_dir.mkdir(exist_ok=True)
    sel.changed_files = []
    sel.test_mapping = sel._build_test_mapping()

    assert "dependency_health.py" in sel.test_mapping
    assert any(
        "test_dependency_health.py" in t for t in sel.test_mapping["dependency_health.py"]
    )


def test_selector_affected_tests_includes_changed_source(tmp_path):
    from smart_test_selector import SmartTestSelector

    (tmp_path / "performance_benchmark.py").write_text("x = 1\n")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_bench.py").write_text(
        "from performance_benchmark import PerformanceBenchmark\n"
    )

    sel = SmartTestSelector.__new__(SmartTestSelector)
    sel.base_dir = tmp_path
    sel.cache_dir = tmp_path / ".test-cache"
    sel.cache_dir.mkdir(exist_ok=True)
    sel.changed_files = ["performance_benchmark.py"]
    sel.changed_lines = {}
    sel.test_mapping = sel._build_test_mapping()

    affected = sel.get_affected_tests()
    # get_affected_tests returns TEST paths, not source paths
    assert any("test_bench.py" in t for t in affected)
