@echo off
cd /d "%~dp0"
echo Starting cross-platform setup...
echo.
python setup_all.py %*
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Setup failed! Check the output above.
)
pause
