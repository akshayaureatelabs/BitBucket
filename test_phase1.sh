#!/bin/bash
cd "$(dirname "$0")"

# Use the venv inside bitbucket-qa/
if [ -f "bitbucket-qa/venv/bin/python" ]; then
    PYTHON="bitbucket-qa/venv/bin/python"
elif [ -f "bitbucket-qa/venv/Scripts/python.exe" ]; then
    PYTHON="bitbucket-qa/venv/Scripts/python.exe"
else
    PYTHON="python"
    echo "WARNING: bitbucket-qa venv not found; using system python."
fi

echo "========================================"
echo "TESTING PHASE 1"
echo "========================================"
echo ""

echo "1/5 Testing Original Precheck..."
$PYTHON -m pytest test_precheck.py -v
if [ $? -ne 0 ]; then
    echo "FAIL: Original tests failed!"
    exit 1
else
    echo "PASS: Original tests passed!"
fi
echo ""

echo "2/5 Testing Smart Test Selector..."
$PYTHON smart_test_selector.py --summary --generate-matrix
echo ""

echo "3/5 Testing Performance Benchmark..."
$PYTHON performance_benchmark.py --run-benchmarks --generate-report
echo ""

echo "4/5 Testing Dependency Health..."
$PYTHON dependency_health.py --check-all --generate-report
echo ""

echo "5/5 Testing Pipeline Dashboard..."
$PYTHON pipeline_dashboard.py --simulate-data --generate-dashboard
echo ""

echo "========================================"
echo "ALL TESTS COMPLETED!"
echo "========================================"
echo ""
echo "Open dashboard: open dashboard/dashboard.html"
echo ""
