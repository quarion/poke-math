# PokeMath infrastructure runbook

Terraform is the source of truth for production infrastructure. Cloud Build
owns immutable application-image promotion; Terraform deliberately ignores only
the Cloud Run image field.

The durable recovery status and historical evidence are in
[`../docs/plans/infrastructure-recovery-and-automation.md`](../docs/plans/infrastructure-recovery-and-automation.md).

## Prerequisites and manual boundaries

Install `gcloud` and Terraform, authenticate both with the same Google account,
and make sure that account can administer project `pokemath-451818`.

These operations remain manual because they cross account or payment trust
boundaries:

1. Create/reopen the billing account and enter payment details.
2. Authorize the GitHub repository once in Cloud Build.
3. Verify the custom domain once with Google and configure its DNS in Cloudflare.
4. Revoke credentials found outside Terraform, such as local personal-access
   tokens or old service-account keys.

Do not upgrade Firebase Authentication to Identity Platform unless a feature
requires it. PokeMath currently needs only Google and anonymous authentication.

## Initialize and plan

The backend configuration is intentionally local and gitignored:

```hcl
bucket = "tfstate-pokemath-europe-prod"
prefix = "terraform/state"
```

Save that as `infrastructure/backend.hcl`, then run:

```powershell
.\infrastructure\scripts\check.ps1
```

The script initializes the backend, checks formatting, validates the provider
schema, and runs a plan with `environments/prod.tfvars`. A routine plan must not
replace Cloud Run, Firestore, the registry, the state bucket, or the secret.

For a new project, create the billing account, project, backend bucket, and
GitHub connection first. Create the Flask secret container and its first version
without printing the value, then import the pre-bootstrap bucket/secret before
the first full apply. No secret value belongs in `.tfvars` or Terraform state.

## Private deployment

Run:

```powershell
.\infrastructure\scripts\deploy-private.ps1
```

This runs unit tests, verifies that the gcloud upload set excludes local
credentials, and submits an asynchronous build under the dedicated build
identity. The build uses a unique immutable tag and updates only the Cloud Run
image. It never changes public IAM.

Inspect the returned build ID:

```powershell
gcloud builds describe BUILD_ID --project=pokemath-451818 --region=global
```

Private verification requires a Google identity token:

```powershell
$serviceUrl = gcloud run services describe poke-math `
  --project=pokemath-451818 --region=europe-west1 `
  --format="value(status.url)"
$token = gcloud auth print-identity-token
curl.exe -H "Authorization: Bearer $token" "$serviceUrl/readyz"
curl.exe -H "Authorization: Bearer $token" "$serviceUrl/login"
```

For a browser-based private test, run
`python tools/private_cloud_run_proxy.py $serviceUrl --port 8081` and open
`http://localhost:8081/login`. The proxy keeps the service private and injects
only a short-lived gcloud identity token into upstream requests.

Also verify that unauthenticated requests to both the generated URL and
`https://pokemath.quarion.dev/login` return 403 while the release gate is closed.

## Public release gate

Public release is deliberately a configuration change, not a build flag:

1. Complete A1–A4, I1–I5, D1, and D2 in the recovery checklist.
2. Obtain explicit owner approval.
3. Change `public_access_enabled` to `true` in `environments/prod.tfvars`.
4. Save and review a Terraform plan, then apply that exact saved plan.
5. Verify Google login, guest login, Firestore persistence, both hostnames, and
   the 10 PLN budget notification configuration.

Set it back to `false` and apply if public access must be closed quickly.

## Cost controls

- Cloud Run uses request-based billing, CPU throttling, min 0, and max 1.
- The project budget target is 10 PLN with actual-spend alerts at 10%, 90%, and
  100%. Budgets send alerts; they do not stop consumption.
- Firestore PITR and paid backup features are disabled.
- Artifact Registry cleanup keeps two recent versions and deletes older images
  after seven days. It was activated only after dry-run inventory review and
  explicit owner approval. Re-review retention before changing these values.
- The state bucket has versioning, seven-day soft delete, uniform access, public
  access prevention, and an explicit operator binding. Never enable uniform
  access without first creating the operator binding.

### Abuse and spending boundary

The Firebase Blaze plan retains the Firestore free allowance, but it has no hard
usage or spending cap. The 10 PLN budget is an alerting threshold, not a payment
limit; cost reporting and notifications can lag by hours.

Live audit on 2026-07-19 found 18 reads, 3 writes, 2 deletes, and about 1.30 MiB
of Firestore storage over the observed seven-day period, versus free allowances
of 50,000 reads/day, 20,000 writes/day, 20,000 deletes/day, and 1 GiB storage.
Cloud Run recorded 817 requests and about 52.5 billable instance-seconds.

Existing safeguards are request-based billing, min 0/max 1, 1 vCPU, 512 MiB,
ADC-only Firestore access, and authentication before all Firestore-backed routes.
They strongly constrain compute/database amplification but do not constitute a
strict cap on requests or outbound transfer.

Emergency public-access kill switch:

1. Set `public_access_enabled = false` in `environments/prod.tfvars`.
2. Save and review a Terraform plan.
3. Apply that exact plan; verify both URLs return 403.

Recommended next KISS hardening is in-application per-IP and global rate limits
on authentication, Firestore, and write routes, together with Cloud Run
concurrency aligned to Gunicorn's eight threads and a shorter request timeout.
If stronger edge enforcement becomes necessary, place Cloud Run behind an
external load balancer/Cloud Armor and disable the default `run.app` URL; that
adds fixed infrastructure cost and complexity. Do not automate disabling the
billing account: billing notifications are delayed, and disabling billing can
stop services and eventually remove resources.

## Credential rotation

Cloud Run uses Application Default Credentials through
`poke-math-service@pokemath-451818.iam.gserviceaccount.com`; it does not need a
downloaded Firebase JSON key. The legacy user-managed key and local JSON were
deleted on 2026-07-19 after private Google/guest/Firestore verification. Do not
recreate them. Local development uses ADC after running:

```powershell
gcloud auth application-default login
gcloud auth application-default set-quota-project pokemath-451818
```

The Flask session key lives in Secret Manager as
`poke-math-flask-secret-key`. Rotating it logs out existing browser sessions:

1. Add a new generated secret version without printing it.
2. Deploy a new private revision referencing `latest`.
3. Verify login and disable the previous version.

## Rollback

List revisions and move traffic to the last known-good revision:

```powershell
gcloud run revisions list --service=poke-math --region=europe-west1 `
  --project=pokemath-451818
gcloud run services update-traffic poke-math --region=europe-west1 `
  --project=pokemath-451818 --to-revisions=REVISION=100
```

Rollback does not change IAM. Keep the service private until the rolled-back
revision is verified, then use the Terraform release gate for public access.
