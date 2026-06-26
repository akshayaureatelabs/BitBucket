cd "$(dirname "$0")"
source venv/bin/activate

echo "========================================"
echo "🧪 TESTING PHASE 1"
echo "========================================"
echo ""

echo "1️⃣ Testing Original Precheck..."
pytest test_precheck.py -v
if [ $? -ne 0 ]; then
    echo "❌ Original tests failed!"
    exit 1
else
    echo "✅ Original tests passed!"
fi
echo ""

echo "2️⃣ Testing Smart Test Selector..."
python smart_test_selector.py --summary --generate-matrix
echo ""

echo "3️⃣ Testing Performance Benchmark..."
python performance_benchmark.py --run-benchmarks --generate-report
echo ""

echo "4️⃣ Testing Dependency Health..."
python dependency_health.py --check-all --generate-report
echo ""

echo "5️⃣ Testing Pipeline Dashboard..."
python pipeline_dashboard.py --simulate-data --generate-dashboard
echo ""

echo "========================================"
echo "✅ ALL TESTS COMPLETED!"
echo "========================================"
echo ""
echo "📊 Open dashboard: open dashboard/dashboard.html"
echo ""