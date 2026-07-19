[CmdletBinding()]
param(
    [string]$Environment = "prod"
)

$ErrorActionPreference = "Stop"
$infrastructureDir = Split-Path -Parent $PSScriptRoot
$variableFile = Join-Path $infrastructureDir "environments/$Environment.tfvars"
$backendFile = Join-Path $infrastructureDir "backend.hcl"

if (-not (Test-Path -LiteralPath $variableFile)) {
    throw "Missing Terraform variable file: $variableFile"
}

Push-Location $infrastructureDir
try {
    terraform init "-backend-config=$backendFile"
    if ($LASTEXITCODE -ne 0) { throw "terraform init failed" }

    terraform fmt -check -recursive
    if ($LASTEXITCODE -ne 0) { throw "terraform fmt check failed" }

    terraform validate
    if ($LASTEXITCODE -ne 0) { throw "terraform validate failed" }

    terraform plan "-var-file=$variableFile"
    if ($LASTEXITCODE -ne 0) { throw "terraform plan failed" }
}
finally {
    Pop-Location
}
