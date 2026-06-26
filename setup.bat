@echo off
cd /d "%~dp0"

echo ========================================
echo   BitBucket QA Suite - One-Click Setup
echo ========================================
echo.

:: Check Python
echo Checking Python...
python --version
if %errorlevel% neq 0 (
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.11+ first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Step 1: Create venv
echo [1/4] Creating virtual environment...
if exist venv (
    echo       venv already exists, recreating...
    rmdir /s /q venv
)
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)
echo       OK

:: Step 2: Install dependencies
echo.
echo [2/4] Installing dependencies (this may take a minute)...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo       OK

:: Step 3: Run quick validation
echo.
echo [3/4] Running validation tests...
echo.
venv\Scripts\python.exe -m pytest test_precheck.py tests/ -v --tb=short
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Some tests failed! Check output above.
    pause
    exit /b 1
)

:: Step 4: Run tools quick check
echo.
echo [4/4] Verifying tools...
venv\Scripts\python.exe -c "from dependency_health import DependencyHealthCheck; c = DependencyHealthCheck(); pkgs = c._parse_requirements(); print(f'dependency_health: OK ({len(pkgs)} packages)')"
venv\Scripts\python.exe -c "from pipeline_dashboard import PipelineDashboard; d = PipelineDashboard(); print('pipeline_dashboard: OK')"
venv\Scripts\python.exe -c "from performance_benchmark import PerformanceBenchmark; b = PerformanceBenchmark(); print('performance_benchmark: OK')"
venv\Scripts\python.exe -c "from smart_test_selector import SmartTestSelector; print('smart_test_selector: OK')"

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Available commands:
echo   pytest test_precheck.py -v        Run precheck tests
echo   pytest tests/ -v                  Run all tests
echo   python smart_test_selector.py     Smart test selection
echo   python performance_benchmark.py   Run benchmarks
echo   python dependency_health.py       Check dependencies
echo   python pipeline_dashboard.py      Generate dashboard
echo.
pause
