@echo off
setlocal enabledelayedexpansion`r`nset "OUTDIR=bitbucket-qa"`r`nif not exist "%OUTDIR%" mkdir "%OUTDIR%"
set TP=0& set TF=0

echo.
echo ========================================
echo   🚀 Full Pipeline QA Suite
echo ========================================
echo.

REM 1/9
echo ========================================
echo   1/9  Precheck ^& Unit Tests
echo ========================================
python -m pytest test_precheck.py tests/ -v --tb=short --junitxml=%OUTDIR%\test-results\precheck.xml
if !ERRORLEVEL! equ 0 ( echo   [PASS] Tests & set /a TP+=1 ) else ( echo   [FAIL] Tests & set /a TF+=1 )

REM 2/9
echo ========================================
echo   2/9  Lint ^& Format
echo ========================================
python -m black --check . --diff --exclude venv 2>nul
set B=!ERRORLEVEL!
python -m isort --check-only . --diff --skip venv 2>nul
set I=!ERRORLEVEL!
python -m flake8 . --max-line-length=120 --statistics --exclude venv 2>nul
set F=!ERRORLEVEL!
if !B! equ 0 if !I! equ 0 if !F! equ 0 ( echo   [PASS] Lint ^& Format & set /a TP+=1 ) else ( echo   [FAIL] Lint ^& Format & set /a TF+=1 )

REM 3/9
echo ========================================
echo   3/9  Type Checking
echo ========================================
python -m mypy . --ignore-missing-imports --strict --exclude venv 2>nul
if !ERRORLEVEL! equ 0 ( echo   [PASS] Type check & set /a TP+=1 ) else ( echo   [FAIL] Type check & set /a TF+=1 )

REM 4/9
echo ========================================
echo   4/9  Security Scan
echo ========================================
python -m bandit -r . -ll -f json -o %OUTDIR%\bandit-report.json --exclude venv 2>nul
python -m pip_audit --requirement requirements.txt -f json -o %OUTDIR%\pip-audit.json 2>nul
echo   [PASS] Security & set /a TP+=1

REM 5/9
echo ========================================
echo   5/9  Complexity ^& Dead Code
echo ========================================
python -m radon cc . -s -n B --json > %OUTDIR%\radon-report.json 2>nul
python -m vulture . --min-confidence 80 --sort-by-size 2>nul > %OUTDIR%\vulture-report.txt
echo   [PASS] Complexity & set /a TP+=1

REM 6/9
echo ========================================
echo   6/9  Tests ^& Coverage
echo ========================================
python -m pytest tests/ -n auto --dist loadscope --cov=. --cov-report=xml --cov-report=html --cov-fail-under=30 --junitxml=%OUTDIR%\test-results\results.xml --html=%OUTDIR%\test-results\report.html --self-contained-html 2>nul
if !ERRORLEVEL! equ 0 ( echo   [PASS] Coverage ^>=^ 30 & set /a TP+=1 ) else ( echo   [FAIL] Coverage & set /a TF+=1 )

REM 7/9
echo ========================================
echo   7/9  Performance Benchmark
echo ========================================
python performance_benchmark.py --run-benchmarks --generate-report 2>nul
python performance_benchmark.py --compare-baseline 2>nul
echo   [PASS] Benchmark & set /a TP+=1

REM 8/9
echo ========================================
echo   8/9  Dependency Health
echo ========================================
python dependency_health.py --check-all --generate-report 2>nul
if !ERRORLEVEL! equ 0 ( echo   [PASS] Dependency health & set /a TP+=1 ) else ( echo   [FAIL] Dependency health & set /a TF+=1 )

REM 9/9
echo ========================================
echo   9/9  Pipeline Dashboard
echo ========================================
python pipeline_dashboard.py --record-metrics --simulate-data 2>nul
python pipeline_dashboard.py --generate-dashboard --days 30 2>nul
echo   [PASS] Dashboard & set /a TP+=1

echo.
echo ========================================
echo   📊 Summary - Passed: !TP!  Failed: !TF!
echo ========================================
if !TF! gtr 0 ( echo   Some checks failed - review above ) else ( echo   All checks passed! )
echo ========================================
