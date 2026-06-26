@echo off
cd /d "%~dp0"

echo ========================================
echo 🧪 TESTING PHASE 1
echo ========================================
echo.

call venv\Scripts\activate

echo 1️⃣ Testing Original Precheck...
pytest test_precheck.py -v
if %errorlevel% neq 0 (
    echo ❌ Original tests failed!
    exit /b %errorlevel%
) else (
    echo ✅ Original tests passed!
)
echo.

echo 2️⃣ Testing Smart Test Selector...
python smart_test_selector.py --summary --generate-matrix
echo.

echo 3️⃣ Testing Performance Benchmark...
python performance_benchmark.py --run-benchmarks --generate-report
echo.

echo 4️⃣ Testing Dependency Health...
python dependency_health.py --check-all --generate-report
echo.

echo 5️⃣ Testing Pipeline Dashboard...
python pipeline_dashboard.py --simulate-data --generate-dashboard
echo.

echo ========================================
echo ✅ ALL TESTS COMPLETED!
echo ========================================
echo.
echo 📊 Open dashboard: start dashboard\dashboard.html
echo.

pause