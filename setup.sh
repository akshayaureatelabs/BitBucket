cd "$(dirname "$0")"

echo "========================================"
echo "🚀 PHASE 1 - COMPLETE SETUP"
echo "========================================"
echo ""

echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📁 Your files are ready"
echo ""
echo "🚀 Run tests locally:"
echo "   pytest test_precheck.py -v"
echo "   python smart_test_selector.py --summary"
echo "   python performance_benchmark.py --run-benchmarks"
echo ""