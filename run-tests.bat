@echo off
REM ================================================
REM  BitBucket QA ? Run Tests (Independent)
REM  For developers who want to run tests separately
REM ================================================

echo.
echo ========================================
echo   BitBucket QA Test Runner
echo ========================================
echo.

cd /d "%~dp0"

REM Detect Python
set "PYTHON=python"
if exist "bitbucket-qa\venv\Scripts\python.exe" (
    set "PYTHON=bitbucket-qa\venv\Scripts\python.exe"
) else (
    echo WARNING: venv not found, using system python.
)

echo Running pre-commit validation tests...
echo.

REM STEP 1: Syntax + structure check
echo ^>^>^> 1/3 Precheck tests...
%PYTHON% -m pytest test_precheck.py -v --tb=short
if %errorlevel% neq 0 (
    echo.
    echo PRECHECK FAILED ? Fix errors above.
    echo.
    pause
    exit /b 1
)
echo.

REM STEP 2: Full test suite
echo ^>^>^> 2/3 Full test suite...
%PYTHON% -m pytest tests/ -v --tb=short
if %errorlevel% neq 0 (
    echo.
    echo TESTS FAILED ? Fix errors above.
    echo.
    pause
    exit /b 1
)
echo.

REM STEP 3: Coverage check
echo ^>^>^> 3/3 Coverage check (30%% minimum)...
%PYTHON% -m pytest tests/ --cov=. --cov-report=term --cov-fail-under=30
if %errorlevel% neq 0 (
    echo.
    echo COVERAGE FAILED ? Below 30%% threshold.
    echo.
    pause
    exit /b 1
)
echo.

echo ========================================
echo   All tests passed!
echo ========================================
echo.
pause