[CmdletBinding()]
# Build and deploy an immutable application image without changing service IAM.
param(
    [string]$ProjectId = "pokemath-451818",
    [string]$Region = "europe-west1",
    [string]$BuildServiceAccount = "poke-math-build@pokemath-451818.iam.gserviceaccount.com"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
Push-Location $repoRoot
try {
    uv run --locked --group dev pytest tests/unit -q
    if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }

    $uploadFiles = gcloud.cmd meta list-files-for-upload
    $unexpectedFiles = $uploadFiles | Where-Object {
        $_ -notmatch '^src[\\/]' -and
        $_ -notmatch '^tests[\\/]' -and
        $_ -notmatch '^(\.dockerignore|Dockerfile|cloudbuild\.yaml|pyproject\.toml|pytest\.ini|uv\.lock)$'
    }
    if ($unexpectedFiles) {
        throw "Unexpected files would be uploaded: $unexpectedFiles"
    }

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
