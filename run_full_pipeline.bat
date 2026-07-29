@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set TP=0& set TF=0

REM Determine Python interpreter (prefer project venv)
if exist "bitbucket-qa\venv\Scripts\python.exe" (
    set "PYTHON=bitbucket-qa\venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo.
echo ========================================
echo   🚀 Full Pipeline QA Suite
echo ========================================
echo.

REM 1/9
echo ========================================
echo   1/9  Precheck ^& Unit Tests
echo ========================================
%PYTHON% -m pytest bitbucket-qa\test_precheck.py bitbucket-qa\tests\ -v --tb=short --junitxml=test-results/precheck.xml
if !ERRORLEVEL! equ 0 ( echo   [PASS] Tests & set /a TP+=1 ) else ( echo   [FAIL] Tests & set /a TF+=1 )

REM 2/9
echo ========================================
echo   2/9  Lint ^& Format
echo ========================================
%PYTHON% -m black --check bitbucket-qa --diff --exclude venv 2>nul
set B=!ERRORLEVEL!
%PYTHON% -m isort --check-only bitbucket-qa --diff --skip venv 2>nul
set I=!ERRORLEVEL!
%PYTHON% -m flake8 bitbucket-qa --max-line-length=120 --statistics --exclude venv 2>nul
set F=!ERRORLEVEL!
if !B! equ 0 if !I! equ 0 if !F! equ 0 ( echo   [PASS] Lint ^& Format & set /a TP+=1 ) else ( echo   [FAIL] Lint ^& Format & set /a TF+=1 )

REM 3/9
echo ========================================
echo   3/9  Type Checking
echo ========================================
%PYTHON% -m mypy bitbucket-qa --ignore-missing-imports --strict --exclude venv 2>nul
if !ERRORLEVEL! equ 0 ( echo   [PASS] Type check & set /a TP+=1 ) else ( echo   [FAIL] Type check & set /a TF+=1 )

REM 4/9
echo ========================================
echo   4/9  Security Scan
echo ========================================
%PYTHON% -m bandit -r bitbucket-qa -ll -f json -o bitbucket-qa\bandit-report.json --exclude venv 2>nul
set B=!ERRORLEVEL!
%PYTHON% -m pip_audit --requirement bitbucket-qa\requirements.txt -f json -o bitbucket-qa\pip-audit.json 2>nul
set P=!ERRORLEVEL!
if !B! equ 0 if !P! equ 0 ( echo   [PASS] Security & set /a TP+=1 ) else ( echo   [FAIL] Security & set /a TF+=1 )

REM 5/9
echo ========================================
echo   5/9  Complexity ^& Dead Code
echo ========================================
%PYTHON% -m radon cc bitbucket-qa -s -n B --json > bitbucket-qa\radon-report.json 2>nul
set R=!ERRORLEVEL!
%PYTHON% -m vulture bitbucket-qa --min-confidence 80 2>nul > bitbucket-qa\vulture-report.txt
set V=!ERRORLEVEL!
if !R! equ 0 if !V! equ 0 ( echo   [PASS] Complexity & set /a TP+=1 ) else ( echo   [FAIL] Complexity & set /a TF+=1 )

REM 6/9
echo ========================================
echo   6/9  Tests ^& Coverage
echo ========================================
%PYTHON% -m pytest bitbucket-qa\tests\ -n auto --dist loadscope --cov=bitbucket-qa --cov-report=xml --cov-report=html --cov-fail-under=30 --junitxml=bitbucket-qa\test-results\results.xml --html=bitbucket-qa\test-results\report.html --self-contained-html 2>nul
if !ERRORLEVEL! equ 0 ( echo   [PASS] Coverage ^>=^ 30 & set /a TP+=1 ) else ( echo   [FAIL] Coverage & set /a TF+=1 )

REM 7/9
echo ========================================
echo   7/9  Performance Benchmark
echo ========================================
%PYTHON% bitbucket-qa\performance_benchmark.py --run-benchmarks --generate-report 2>nul
set BM=!ERRORLEVEL!
%PYTHON% bitbucket-qa\performance_benchmark.py --compare-baseline 2>nul
set BC=!ERRORLEVEL!
if !BM! equ 0 if !BC! equ 0 ( echo   [PASS] Benchmark & set /a TP+=1 ) else ( echo   [FAIL] Benchmark & set /a TF+=1 )

REM 8/9
echo ========================================
echo   8/9  Dependency Health
echo ========================================
%PYTHON% bitbucket-qa\dependency_health.py --check-all --generate-report 2>nul
if !ERRORLEVEL! equ 0 ( echo   [PASS] Dependency health & set /a TP+=1 ) else ( echo   [FAIL] Dependency health & set /a TF+=1 )

REM 9/9
echo ========================================
echo   9/9  Pipeline Dashboard
echo ========================================
%PYTHON% bitbucket-qa\pipeline_dashboard.py --record-metrics --simulate-data 2>nul
set DR=!ERRORLEVEL!
%PYTHON% bitbucket-qa\pipeline_dashboard.py --generate-dashboard --days 30 2>nul
set DG=!ERRORLEVEL!
if !DR! equ 0 if !DG! equ 0 ( echo   [PASS] Dashboard & set /a TP+=1 ) else ( echo   [FAIL] Dashboard & set /a TF+=1 )

echo.
echo ========================================
echo   📊 Summary - Passed: !TP!  Failed: !TF!
echo ========================================
if !TF! gtr 0 ( echo   Some checks failed - review above ) else ( echo   All checks passed! )
echo ========================================
