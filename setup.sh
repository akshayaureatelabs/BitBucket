#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "========================================"
echo "  BitBucket QA Suite - One-Click Setup"
echo "========================================"
echo ""

# Check Python
echo "Checking Python..."
python3 --version
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.11+ first."
    exit 1
fi

# Step 1: Create venv
echo "[1/4] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "      venv already exists, recreating..."
    rm -rf venv
fi
python3 -m venv venv
echo "      OK"

# Step 2: Install dependencies
echo ""
echo "[2/4] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "      OK"

# Step 3: Run quick validation
echo ""
echo "[3/4] Running validation tests..."
echo ""
venv/bin/python -m pytest test_precheck.py tests/ -v --tb=short

# Step 4: Run tools quick check
echo ""
echo "[4/4] Verifying tools..."
venv/bin/python -c "from dependency_health import DependencyHealthCheck; c = DependencyHealthCheck(); pkgs = c._parse_requirements(); print(f'  dependency_health: OK ({len(pkgs)} packages)')"
venv/bin/python -c "from pipeline_dashboard import PipelineDashboard; d = PipelineDashboard(); print('  pipeline_dashboard: OK')"
venv/bin/python -c "from performance_benchmark import PerformanceBenchmark; b = PerformanceBenchmark(); print('  performance_benchmark: OK')"
venv/bin/python -c "from smart_test_selector import SmartTestSelector; print('  smart_test_selector: OK')"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Available commands:"
echo "  pytest test_precheck.py -v        Run precheck tests"
echo "  pytest tests/ -v                  Run all tests"
echo "  python smart_test_selector.py     Smart test selection"
echo "  python performance_benchmark.py   Run benchmarks"
echo "  python dependency_health.py       Check dependencies"
echo "  python pipeline_dashboard.py      Generate dashboard"
