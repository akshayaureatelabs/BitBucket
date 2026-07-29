@echo off
REM Run QA tests from project root — no venv activation needed
REM Usage: run

cd /d "%~dp0"
bitbucket-qa\venv\Scripts\python -m pytest bitbucket-qa\test_precheck.py bitbucket-qa\tests\ -v --tb=short
