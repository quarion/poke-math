[CmdletBinding()]
param(
    [string]$ProjectId = "pokemath-451818",
    [string]$Region = "europe-west1",
    [string]$BuildServiceAccount = "poke-math-build@pokemath-451818.iam.gserviceaccount.com"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
$python = Join-Path $repoRoot "venv/Scripts/python.exe"

Push-Location $repoRoot
try {
    if (Test-Path -LiteralPath $python) {
        & $python -m pytest tests/unit -q
        if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }
    }
    else {
        throw "Expected local Python environment at $python"
    }

    $uploadFiles = gcloud.cmd meta list-files-for-upload
    $sensitiveFiles = $uploadFiles | Select-String -Pattern `
        '(^|[\\/])(firebase-credentials\.json|\.env|terraform\.tfvars|backend\.hcl)$'
    if ($sensitiveFiles) {
        throw "Sensitive local files would be uploaded: $sensitiveFiles"
    }

    $revisionTag = "manual-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $serviceAccountResource = `
        "projects/$ProjectId/serviceAccounts/$BuildServiceAccount"

    $buildId = gcloud.cmd builds submit . `
        --project=$ProjectId `
        --region=global `
        --config=cloudbuild.yaml `
        --service-account=$serviceAccountResource `
        --substitutions="COMMIT_SHA=$revisionTag,_REGION=$Region" `
        --async `
        --format="value(id)"
    if ($LASTEXITCODE -ne 0) { throw "Cloud Build submission failed" }

    Write-Output "Build submitted: $buildId"
    Write-Output "Inspect: gcloud builds describe $buildId --project=$ProjectId --region=global"
}
finally {
    Pop-Location
}
