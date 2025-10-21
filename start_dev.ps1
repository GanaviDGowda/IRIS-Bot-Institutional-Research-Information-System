# PowerShell script to start Research Paper Browser in development mode
Write-Host "Starting Research Paper Browser in Development Mode..." -ForegroundColor Green
Write-Host "Hot reload is enabled - code changes will be automatically detected" -ForegroundColor Yellow
Write-Host ""

# Set development environment variable
$env:RESEARCH_PAPER_BROWSER_DEV = "true"

# Run the development launcher
python run_dev.py

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")



