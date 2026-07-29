#!/bin/sh
# ================================================
#  BitBucket QA — Run Tests (Independent)
#  For developers who want to run tests separately
# ================================================

echo ""
echo "========================================"
echo "  BitBucket QA Test Runner"
echo "========================================"
echo ""

REPO_ROOT=$(dirname "$0")
cd "$REPO_ROOT" || exit 1

# Detect Python
PYTHON="python"
if [ -f "bitbucket-qa/venv/Scripts/python.exe" ]; then
    PYTHON="bitbucket-qa/venv/Scripts/python.exe"
elif [ -f "bitbucket-qa/venv/bin/python" ]; then
    PYTHON="bitbucket-qa/venv/bin/python"
else
    echo "WARNING: venv not found, using system python."
fi

echo "Running pre-commit validation tests..."
echo ""

# STEP 1: Syntax + structure check
echo ">>> 1/3 Precheck tests..."
$PYTHON -m pytest test_precheck.py -v --tb=short
if [ $? -ne 0 ]; then
    echo ""
    echo "PRECHECK FAILED — Fix errors above."
    echo ""
    exit 1
fi
echo ""

# STEP 2: Full test suite
echo ">>> 2/3 Full test suite..."
$PYTHON -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo ""
    echo "TESTS FAILED — Fix errors above."
    echo ""
    exit 1
fi
echo ""

# STEP 3: Coverage check
echo ">>> 3/3 Coverage check (30% minimum)..."
$PYTHON -m pytest tests/ --cov=. --cov-report=term --cov-fail-under=30
if [ $? -ne 0 ]; then
    echo ""
    echo "COVERAGE FAILED — Below 30% threshold."
    echo ""
    exit 1
fi
echo ""

echo "========================================"
echo "  All tests passed!"
echo "========================================"
echo ""