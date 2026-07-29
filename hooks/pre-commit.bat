@echo off
REM Pre-commit quality gate for bitbucket-qa.
REM Fast checks on STAGED files only - catches mistakes before commit.
REM Heavy checks (tests, coverage) happen in pre-push.

setlocal enabledelayedexpansion

set "REPO_ROOT=%cd%"
set "QA_DIR=%REPO_ROOT%\bitbucket-qa"

if not exist "%QA_DIR%" (
    echo WARNING: bitbucket-qa/ not found - skipping pre-commit check.
    exit /b 0
)

cd /d "%QA_DIR%"

REM Detect the venv Python
set "PYTHON=python"
if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
) else (
    echo WARNING: bitbucket-qa venv not found; using system python.
)

echo.
echo ========================================
echo   Pre-commit Quality Gate
echo ========================================
echo.

REM -------------------------------------------------------
REM STEP 1: Syntax check on staged Python files
REM -------------------------------------------------------
echo ^>^>^> 1/2 Syntax check (staged .py files)...

set "ERRORS=0"
set "HAS_STAGED=0"

for /f "delims=" %%f in ('git diff --cached --name-only --diff-filter=ACM -- "*.py" 2^>nul') do (
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

REM -------------------------------------------------------
REM STEP 2: Code scanner on staged files
REM -------------------------------------------------------
echo ^>^>^> 2/2 Code scanner (staged files)...

if "%HAS_STAGED%"=="0" (
    echo   No staged Python files - skipping scanner.
) else (
    %PYTHON% code_scanner.py "%REPO_ROOT%"
    if !errorlevel! neq 0 (
        echo.
        echo COMMIT BLOCKED - Fix scanner errors above before committing.
        echo.
        exit /b 1
    )
)
echo.

echo ========================================
echo   Pre-commit checks passed
echo ========================================
echo.
exit /b 0