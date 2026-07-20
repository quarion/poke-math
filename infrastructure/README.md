# PokeMath infrastructure runbook

This document describes the production system as it is operated. Terraform is the source of truth for Google Cloud resources and IAM. Cloud Build owns immutable application-image promotion; Terraform ignores only the Cloud Run container image field.

## Production topology

| Component | Current configuration |
|---|---|
| Project | `pokemath-451818` (`991216996410`) |
| Region | `europe-west1` |
| Public URLs | `https://pokemath.quarion.dev` and the generated Cloud Run URL |
| Runtime | Cloud Run service `poke-math`, request billing, min 0/max 1, 1 vCPU, 512 MiB, concurrency 8, timeout 60 s |
| Process | One Gunicorn worker with eight threads and a 60 s timeout |
| Data | Firestore Native database `(default)` in `eur3`, delete protection on, PITR off |
| Authentication | Firebase Authentication with Google and anonymous providers |
| Images | Artifact Registry repository `poke-math`; keep two recent deployable versions and delete versions older than seven days |
| Deployment | Cloud Build trigger `main` and `infrastructure/scripts/deploy.ps1` |
| State | GCS bucket `tfstate-pokemath-europe-prod`, versioning and seven-day soft delete |

The Cloud Run runtime identity is `poke-math-service@pokemath-451818.iam.gserviceaccount.com`. It has only Firestore user access and Secret Manager access to the Flask session key. The build identity is `poke-math-build@pokemath-451818.iam.gserviceaccount.com`.

## Manual account boundaries

Terraform does not cross these external trust boundaries:

1. Create or reopen the billing account and enter payment details.
2. Authorize the GitHub repository in the Cloud Build GitHub connection.
3. Verify ownership of `quarion.dev` with Google and configure the domain mapping's DNS records at the DNS provider.
4. Enable Google and anonymous providers in Firebase Authentication. Do not upgrade to Identity Platform unless a required feature depends on it.
5. Verify a Monitoring email channel if Google marks it `UNVERIFIED`.

The GCP project, backend bucket, billing attachment, and first secret value are bootstrap resources. Create them before the first full Terraform apply, then import the bucket and secret container. Secret values must never be placed in `.tfvars` or Terraform state.

## Authenticate and check infrastructure

Install the Google Cloud CLI and Terraform, then authenticate the operator:

```powershell
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project pokemath-451818
```

Create the gitignored `infrastructure/backend.hcl`:

```hcl
bucket = "tfstate-pokemath-europe-prod"
prefix = "terraform/state"
```

Run the read-only consistency check from the repository root:

```powershell
.\infrastructure\scripts\check.ps1
```

It initializes the backend, checks formatting, validates the provider schema, and plans with `infrastructure/environments/prod.tfvars`. A routine check should report no changes.

For a change, save and review the exact plan that will be applied:

```powershell
Set-Location infrastructure
terraform plan -var-file=environments/prod.tfvars -out=change.tfplan
terraform show change.tfplan
terraform apply change.tfplan
```

Plan files are gitignored. Do not apply a plan containing an unexplained replacement or deletion, especially for Cloud Run, Firestore, the registry, the state bucket, or the secret.

## Deploy application code

Run from the repository root:

```powershell
.\infrastructure\scripts\deploy.ps1
```

The script runs unit tests, verifies that `.gcloudignore` admits only the container recipe, locked dependency metadata, and `src/`, checks the upload set for local credentials, and submits an asynchronous build under the dedicated build identity. Cloud Build runs the same unit suite before it builds, pushes, and deploys. The Dockerfile copies only the application source and dependency metadata into the runtime image. The build tags the image immutably and updates only the Cloud Run image; it preserves the service's current public/private IAM state.

Inspect the returned build ID:

```powershell
gcloud builds describe BUILD_ID --project=pokemath-451818 --region=global
```

After a successful build, verify:

```powershell
$serviceUrl = gcloud run services describe poke-math `
  --project=pokemath-451818 --region=europe-west1 `
  --format="value(status.url)"
curl.exe "$serviceUrl/readyz"
curl.exe "https://pokemath.quarion.dev/login"
```

Then test Google login, guest login, a Firestore-backed read, and persistence after reload. Finish by running `check.ps1` and confirming no drift.

## Public access gate

`public_access_enabled` in `infrastructure/environments/prod.tfvars` controls the single `allUsers` Cloud Run Invoker binding. Production is public when this value is `true`.

Before changing it from `false` to `true`, verify the saved plan adds only the expected binding, then test both hostnames, both login providers, persistence, and monitoring. To test a private service from a browser, obtain the service URL and run:

```powershell
python tools/private_cloud_run_proxy.py $serviceUrl --port 8081
```

Open `http://localhost:8081/login`. The proxy injects a short-lived gcloud identity token into upstream requests.

## Cost and abuse controls

These controls bound amplification but do not create a monetary hard cap:

- Cloud Run uses request-based billing, CPU throttling, minimum zero instances, maximum one instance, concurrency eight, and a 60-second request timeout.
- The application admits at most 300 requests/minute globally and 120/minute per best-effort client identity. Authentication callbacks are limited to 60/minute globally and 10/minute per client; state-changing requests are limited to 120/minute globally and 30/minute per client.
- Limiter counters live in the single application process and reset when Cloud Run starts a new instance. The global counter cannot be evicted by rotating client identities. `/readyz` is exempt and performs no Firebase work.
- Monitoring emails on more than 1,000 Cloud Run requests in five minutes, more than five billable instance-minutes in 15 minutes, more than 5,000 Firestore reads/hour, or more than 2,000 Firestore writes/hour.
- The project budget is 10 PLN/month with actual-spend alerts at 10%, 90%, and 100%. Budgets and Monitoring alerts detect usage; they do not stop it, and notifications can lag.
- Firestore PITR and paid backups are disabled. Artifact Registry and Terraform state retention are bounded as described in the topology table.

Firebase Blaze retains the applicable no-cost Firestore quotas, but Blaze has no usage or spending ceiling. Requests rejected inside the container may still count as Cloud Run requests. Stronger enforcement before the container requires an external load balancer and Cloud Armor, plus disabling the default `run.app` URL; adopt that only if alerts show hostile traffic or availability becomes more important than the added fixed cost and complexity.

### Emergency public-access stop

1. Set `public_access_enabled = false` in `infrastructure/environments/prod.tfvars`.
2. Save and inspect a Terraform plan; it should remove one Invoker binding.
3. Apply that exact plan.
4. Confirm unauthenticated requests to both public URLs return `403`.

Do not automate disabling the billing account. Billing information is delayed, and disabling billing can stop services and eventually remove resources.

## Credentials and secret rotation

Cloud Run and local development use Application Default Credentials. Do not create or download a Firebase service-account JSON key.

The Flask session key is Secret Manager secret `poke-math-flask-secret-key`. Rotating it logs out browser sessions:

1. Add a generated secret version without printing the value.
2. Deploy a revision that references `latest`.
3. Verify both login flows.
4. Disable the prior secret version.

Personal GitHub access uses the authenticated `gh` CLI; do not put a personal access token in `.env`.

## Rollback

List revisions and move traffic to a known-good revision:

```powershell
gcloud run revisions list --service=poke-math --region=europe-west1 `
  --project=pokemath-451818
gcloud run services update-traffic poke-math --region=europe-west1 `
  --project=pokemath-451818 --to-revisions=REVISION=100
```

This changes the image receiving traffic, not IAM or Terraform-owned service settings. If the incident is cost or abuse related, close public access first.
