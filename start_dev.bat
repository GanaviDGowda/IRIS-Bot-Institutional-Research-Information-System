@echo off
echo Starting Research Paper Browser in Development Mode...
echo Hot reload is enabled - code changes will be automatically detected
echo.

REM Set development environment variable
set RESEARCH_PAPER_BROWSER_DEV=true

REM Run the development launcher
python run_dev.py

pause



