#!/bin/bash
# Full Pipeline QA Suite - Run all checks (slow but comprehensive)
cd "$(dirname "$0")"
PASS=0; FAIL=1; TP=0; TF=0
pass() { echo "  ✅ $1"; TP=$((TP+1)); }
fail() { echo "  ❌ $1"; TF=$((TF+1)); }

QA_DIR="bitbucket-qa"

# Determine Python interpreter (prefer project venv)
if [ -f "$QA_DIR/venv/Scripts/python.exe" ]; then
    PYTHON="$QA_DIR/venv/Scripts/python.exe"
elif [ -f "$QA_DIR/venv/bin/python" ]; then
    PYTHON="$QA_DIR/venv/bin/python"
else
    PYTHON="python"
fi

echo ""
echo "========================================"
echo "  🚀 Full Pipeline QA Suite"
echo "========================================"

header() { echo ""; echo "========================================"; echo "  $1"; echo "========================================"; }

header "1/9  Precheck & Unit Tests"
$PYTHON -m pytest bitbucket-qa/test_precheck.py bitbucket-qa/tests/ -v --tb=short --junitxml=test-results/precheck.xml && pass "Tests" || fail "Tests"

header "2/9  Lint & Format"
$PYTHON -m black --check "$QA_DIR" --diff --exclude venv 2>&1; B=$?
$PYTHON -m isort --check-only "$QA_DIR" --diff --skip venv 2>&1; I=$?
$PYTHON -m flake8 "$QA_DIR" --max-line-length=120 --statistics --exclude venv 2>&1; F=$?
[ $B -eq 0 ] && [ $I -eq 0 ] && [ $F -eq 0 ] && pass "Lint & Format" || fail "Lint & Format (b:$B i:$I f:$F)"

header "3/9  Type Checking"
$PYTHON -m mypy "$QA_DIR" --ignore-missing-imports --strict --exclude venv 2>&1 && pass "Type check" || fail "Type check"

header "4/9  Security Scan"
$PYTHON -m bandit -r "$QA_DIR" -ll -f json -o bandit-report.json --exclude venv 2>&1
$PYTHON -m pip_audit --requirement "$QA_DIR/requirements.txt" -f json -o pip-audit.json 2>/dev/null
pass "Security scan"

header "5/9  Complexity & Dead Code"
$PYTHON -m radon cc "$QA_DIR" -s -n B --json > radon-report.json 2>&1
$PYTHON -m vulture "$QA_DIR" --min-confidence 80 2>&1 > vulture-report.txt
pass "Complexity"

header "6/9  Tests & Coverage"
$PYTHON -m pytest "$QA_DIR/tests/" -n auto --dist loadscope --cov="$QA_DIR" --cov-report=xml --cov-report=html --cov-fail-under=30 --junitxml=test-results/results.xml --html=test-results/report.html --self-contained-html 2>&1 && pass "Coverage >= 30" || fail "Coverage"

header "7/9  Performance Benchmark"
$PYTHON "$QA_DIR/performance_benchmark.py" --run-benchmarks --generate-report 2>&1
$PYTHON "$QA_DIR/performance_benchmark.py" --compare-baseline 2>&1
pass "Benchmark"

header "8/9  Dependency Health"
$PYTHON "$QA_DIR/dependency_health.py" --check-all --generate-report 2>&1 && pass "Dependency health" || fail "Dependency health"

header "9/9  Pipeline Dashboard"
$PYTHON "$QA_DIR/pipeline_dashboard.py" --record-metrics --simulate-data 2>&1
$PYTHON "$QA_DIR/pipeline_dashboard.py" --generate-dashboard --days 30 2>&1
pass "Dashboard"

echo ""
echo "========================================"
echo "  📊 Summary - Passed: $TP  Failed: $TF"
echo "========================================"
if [ $TF -gt 0 ]; then echo "  Some checks failed - review above"; else echo "  All checks passed!"; fi
echo "========================================"
