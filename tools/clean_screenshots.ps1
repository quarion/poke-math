# PowerShell script to clean up the screenshots directory

param(
    [Parameter(Mandatory=$false)]
    [switch]$Force = $false
)

$screenshotsDir = "tests/e2e/screenshots"

# Check if the screenshots directory exists
if (-not (Test-Path $screenshotsDir)) {
    Write-Host "Screenshots directory does not exist." -ForegroundColor Yellow
    exit 0
}

# Count the number of screenshots
$screenshots = Get-ChildItem -Path $screenshotsDir -Filter "*.png"
$count = $screenshots.Count

if ($count -eq 0) {
    Write-Host "No screenshots to clean up." -ForegroundColor Green
    exit 0
}

# Confirm deletion
if (-not $Force) {
    $confirm = Read-Host "Are you sure you want to delete $count screenshots? (y/n)"
    if ($confirm -ne "y") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Delete the screenshots
Remove-Item -Path "$screenshotsDir\*.png" -Force
Write-Host "Deleted $count screenshots." -ForegroundColor Green 