# PowerShell script to start the server with visible logs

param(
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:8080"
)

# Extract host and port from BaseUrl
$uri = [System.Uri]$BaseUrl
$serverHost = $uri.Host
$serverPort = $uri.Port

# Check if the application is already running
try {
    $response = Invoke-WebRequest -Uri $BaseUrl -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "Application is already running at $BaseUrl" -ForegroundColor Yellow
    Write-Host "Please stop the existing instance before starting a new one." -ForegroundColor Red
    exit 1
} catch {
    Write-Host "Starting new application instance..." -ForegroundColor Green
}

# Set environment variables
$env:FLASK_ENV = "development"

# Start the application in the current window to see logs
Write-Host "Starting server at $BaseUrl" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Run the Flask application using the correct command
flask --app src.app.app run --host $serverHost --port $serverPort --debug --exclude-patterns "`tests\*"