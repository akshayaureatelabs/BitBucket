@echo off
REM Reference pre-push hook for the bitbucket-qa suite.
REM This is OPTIONAL. To enable the push gate, copy this file to your repo's
REM .git\hooks\pre-push (one-time, manual step). The suite lives entirely in the
REM "bitbucket-qa" folder and NEVER modifies your project code.

for /f "tokens=*" %%i in ('git rev-parse --show-toplevel') do set REPO_ROOT=%%i
set "QA_DIR=%REPO_ROOT%\bitbucket-qa"

if not exist "%QA_DIR%" (
    echo WARNING: bitbucket-qa folder not found at %QA_DIR% - skipping QA gate (push allowed).
    exit /b 0
)

cd /d "%QA_DIR%" || exit /b 0

REM Detect the venv Python - prefer the repo-root venv (created by setup_all.py)
REM before the one inside bitbucket-qa/
set "PYTHON=python"
if exist "%REPO_ROOT%\venv\Scripts\python.exe" (
    set "PYTHON=%REPO_ROOT%\venv\Scripts\python.exe"
) else (
    if exist "%REPO_ROOT%\venv\bin\python" (
        set "PYTHON=%REPO_ROOT%\venv\bin\python"
    ) else (
        if exist "%QA_DIR%\venv\Scripts\python.exe" (
            set "PYTHON=%QA_DIR%\venv\Scripts\python.exe"
        ) else (
            if exist "%QA_DIR%\venv\bin\python" (
                set "PYTHON=%QA_DIR%\venv\bin\python"
            ) else (
                echo WARNING: bitbucket-qa venv not found; using system python.
            )
        )
    )
)

echo.
echo ========================================
echo   bitbucket-qa - Pre-Push Quality Gate
echo ========================================
echo.

REM 1. TESTS (blocking)
echo ^>^>^> 1/3 Tests (blocking^)...
%PYTHON% -m pytest test_precheck.py tests/ -v --tb=short --junitxml=test-results\precheck.xml
if %errorlevel% neq 0 (
    echo PUSH BLOCKED - fix failing tests
    exit /b 1
)
echo   Tests passed
echo.

REM 2. COVERAGE ^>= 30%% (blocking)
echo ^>^>^> 2/3 Coverage ^>= 30%% (blocking^)...
%PYTHON% -m pytest tests/ --cov=. --cov-report=xml --cov-report=html --cov-fail-under=30 --junitxml=test-results\results.xml 2>nul
if %errorlevel% neq 0 (
    echo PUSH BLOCKED - coverage below 30%%
    exit /b 1
)
echo   Coverage OK
echo.

REM 3. LINT ^& FORMAT (advisory)
echo ^>^>^> 3/3 Lint ^& Format (advisory^)...
%PYTHON% -m black --check . --diff --exclude venv 2>nul
set B=%errorlevel%
%PYTHON% -m isort --check-only . --diff --skip venv 2>nul
set I=%errorlevel%
%PYTHON% -m flake8 . --max-line-length=120 --statistics --exclude venv 2>nul
set F=%errorlevel%
if %B% neq 0 if %I% neq 0 if %F% neq 0 (
    echo   Lint issues found (advisory - push allowed^)
) else (
    echo   Lint clean
)
echo.

echo bitbucket-qa passed - push allowed
exit /b 0
