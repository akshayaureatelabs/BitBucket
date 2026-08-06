@echo off
REM Pre-commit quality gate for bitbucket-qa.
REM Fast checks on STAGED files only - catches mistakes before commit.
REM Heavy checks (full scanner, tests, coverage) happen in pre-push.

setlocal enabledelayedexpansion

for /f "tokens=*" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO_ROOT=%%i"
if "%REPO_ROOT%"=="" (
    echo WARNING: not a git repository - skipping pre-commit check.
    exit /b 0
)
set "QA_DIR=%REPO_ROOT%\bitbucket-qa"

if not exist "%QA_DIR%" (
    echo WARNING: bitbucket-qa/ not found - skipping pre-commit check.
    exit /b 0
)

cd /d "%QA_DIR%"

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
echo   Pre-commit Quality Gate
echo ========================================
echo.

REM -------------------------------------------------------
REM STEP 1/1: Syntax check on staged Python files only
REM -------------------------------------------------------
echo ^>^>^> 1/1 Syntax check (staged .py files)...

set "ERRORS=0"
set "HAS_STAGED=0"

for /f "delims=" %%f in ('git -C "%REPO_ROOT%" diff --cached --name-only --diff-filter=ACM -- "*.py" 2^>nul') do (
    set "HAS_STAGED=1"
    if exist "%REPO_ROOT%\%%f" (
        %PYTHON% -c "import ast; ast.parse(open(r'%REPO_ROOT%\%%f', encoding='utf-8').read())" 2>nul
        if !errorlevel! neq 0 (
            echo   SYNTAX ERROR: %%f
            set "ERRORS=1"
        )
    )
)

if "%HAS_STAGED%"=="0" (
    echo   No staged Python files - skipping syntax check.
) else (
    if "%ERRORS%"=="1" (
        echo.
        echo COMMIT BLOCKED - Fix syntax errors above before committing.
        echo.
        exit /b 1
    )
    echo   All staged files pass syntax check.
)
echo.

echo ========================================
echo   Pre-commit checks passed
echo ========================================
echo.
exit /b 0
