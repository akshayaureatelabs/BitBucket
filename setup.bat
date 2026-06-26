@echo off
cd /d "%~dp0"

echo ========================================
echo 🚀 PHASE 1 - COMPLETE SETUP
echo ========================================
echo.

echo 📦 Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo.
echo 📥 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ Setup Complete!
echo.
echo 📁 Your files:
echo   - requirements.txt (updated)
echo   - bitbucket-pipelines.yml (updated)
echo   - test_precheck.py (your original - preserved)
echo   - smart_test_selector.py (new)
echo   - performance_benchmark.py (new)
echo   - dependency_health.py (new)
echo   - pipeline_dashboard.py (new)
echo.
echo 🚀 Run tests locally:
echo   pytest test_precheck.py -v
echo   python smart_test_selector.py --summary
echo   python performance_benchmark.py --run-benchmarks
echo.
pause