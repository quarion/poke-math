# PowerShell script to run the e2e tests

param(
    [Parameter(Mandatory=$false)]
    [string]$TestPath = "tests/e2e",
    
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:8080",
    
    [Parameter(Mandatory=$false)]
    [switch]$Headless = $false
)

# Check if Playwright is installed
$playwrightInstalled = python -c "import importlib.util; print(importlib.util.find_spec('playwright') is not None)" 2>$null

if ($playwrightInstalled -ne "True") {
    Write-Host "Installing Playwright..." -ForegroundColor Yellow
    pip install playwright
    python -m playwright install
    Write-Host "Playwright installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Playwright is already installed." -ForegroundColor Green
}

# Check if the application is running
try {
    $response = Invoke-WebRequest -Uri $BaseUrl -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "Application is running at $BaseUrl" -ForegroundColor Green
    $appRunning = $true
} catch {
    Write-Host "Application is not running at $BaseUrl" -ForegroundColor Red
    $appRunning = $false
}

# Start the application if it's not running
if (-not $appRunning) {
    Write-Host "Starting the application..." -ForegroundColor Yellow
    
    # Start the application in a new PowerShell window
    $appProcess = Start-Process powershell -ArgumentList "-Command `"cd $(Get-Location); `$env:FLASK_ENV='development'; python -m src.app`"" -PassThru
    
    # Wait for the application to start
    Write-Host "Waiting for the application to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Check if the application is running now
    try {
        $response = Invoke-WebRequest -Uri $BaseUrl -TimeoutSec 5 -ErrorAction SilentlyContinue
        Write-Host "Application is now running at $BaseUrl" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start the application at $BaseUrl" -ForegroundColor Red
        exit 1
    }
}

# Set environment variables for the tests
$env:BASE_URL = $BaseUrl
$env:HEADLESS = $Headless.ToString().ToLower()

# Run the tests
Write-Host "Running e2e tests..." -ForegroundColor Cyan
python -m pytest $TestPath -v

# Stop the application if we started it
if (-not $appRunning -and (Get-Variable -Name appProcess -ErrorAction SilentlyContinue)) {
    Write-Host "Stopping the application..." -ForegroundColor Yellow
    Stop-Process -Id $appProcess.Id -Force
    Write-Host "Application stopped." -ForegroundColor Green
} 