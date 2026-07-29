@echo off
cd /d "%~dp0"

echo ========================================
echo 🧪 TESTING PHASE 1
echo ========================================
echo.

REM Use the venv inside bitbucket-qa/
if exist "bitbucket-qa\venv\Scripts\python.exe" (
    set "PYTHON=bitbucket-qa\venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
    echo WARNING: bitbucket-qa venv not found; using system python.
)

echo 1️⃣ Testing Original Precheck...
%PYTHON% -m pytest test_precheck.py -v
if %errorlevel% neq 0 (
    echo ❌ Original tests failed!
    exit /b %errorlevel%
) else (
    echo ✅ Original tests passed!
)
echo.

echo 2️⃣ Testing Smart Test Selector...
%PYTHON% smart_test_selector.py --summary --generate-matrix
echo.

echo 3️⃣ Testing Performance Benchmark...
%PYTHON% performance_benchmark.py --run-benchmarks --generate-report
echo.

echo 4️⃣ Testing Dependency Health...
%PYTHON% dependency_health.py --check-all --generate-report
echo.

echo 5️⃣ Testing Pipeline Dashboard...
%PYTHON% pipeline_dashboard.py --simulate-data --generate-dashboard
echo.

echo ========================================
echo ✅ ALL TESTS COMPLETED!
echo ========================================
echo.
echo 📊 Open dashboard: start dashboard\dashboard.html
echo.

pause