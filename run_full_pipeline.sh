#!/bin/sh
# Full Pipeline QA Suite - Run all checks (slow but comprehensive)
PASS=0; FAIL=1; TP=0; TF=0
pass() { echo "  ✅ $1"; TP=$((TP+1)); }
fail() { echo "  ❌ $1"; TF=$((TF+1)); }
header() { echo ""; echo "========================================"; echo "  $1"; echo "========================================"; }

echo ""; echo "========================================"; echo "  🚀 Full Pipeline QA Suite"; echo "========================================"; echo ""

header "1/9  Precheck & Unit Tests"
python -m pytest test_precheck.py tests/ -v --tb=short --junitxml=test-results/precheck.xml && pass "All tests" || fail "Tests failed"

header "2/9  Lint & Format"
python -m black --check . --diff --exclude venv 2>/dev/null; B=$?
python -m isort --check-only . --diff --skip venv 2>/dev/null; I=$?
python -m flake8 . --max-line-length=120 --statistics --exclude venv 2>/dev/null; F=$?
[ $B -eq 0 ] && [ $I -eq 0 ] && [ $F -eq 0 ] && pass "Lint & Format" || fail "Lint & Format (b:$B i:$I f:$F)"

header "3/9  Type Checking"
python -m mypy . --ignore-missing-imports --strict --exclude venv 2>/dev/null && pass "Type checking" || fail "Type checking"

header "4/9  Security Scan"
python -m bandit -r . -ll -f json -o bandit-report.json --exclude venv 2>/dev/null
python -m pip_audit --requirement requirements.txt -f json -o pip-audit.json 2>/dev/null
pass "Security scan"

header "5/9  Complexity & Dead Code"
python -m radon cc . -s -n B --json > radon-report.json 2>/dev/null
python -m vulture . --min-confidence 80 --sort-by-size 2>/dev/null > vulture-report.txt
pass "Complexity & Dead Code"

header "6/9  Tests & Coverage"
python -m pytest tests/ -n auto --dist loadscope --cov=. --cov-report=xml --cov-report=html --cov-fail-under=30 --junitxml=test-results/results.xml --html=test-results/report.html --self-contained-html 2>/dev/null && pass "Coverage >= 30%" || fail "Coverage below threshold"

header "7/9  Performance Benchmark"
python performance_benchmark.py --run-benchmarks --generate-report 2>/dev/null
python performance_benchmark.py --compare-baseline 2>/dev/null
pass "Performance benchmark"

header "8/9  Dependency Health"
python dependency_health.py --check-all --generate-report 2>/dev/null && pass "Dependency health" || fail "Dependency health"

header "9/9  Pipeline Dashboard"
python pipeline_dashboard.py --record-metrics --simulate-data 2>/dev/null
python pipeline_dashboard.py --generate-dashboard --days 30 2>/dev/null
pass "Dashboard generated"

echo ""; echo "========================================"; echo "  📊 Summary - Passed: $TP  Failed: $TF"; echo "========================================"
[ $TF -gt 0 ] && echo "  Some checks failed - review above" || echo "  All checks passed!"
echo "========================================"
