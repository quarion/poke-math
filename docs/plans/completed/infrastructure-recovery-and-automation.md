# Infrastructure Recovery and Automation Plan

Status: completed

Completed: 2026-07-19

Implementation: `0b9c059` (`Restore and codify production infrastructure`)

Follow-on work: [`../cost-abuse-hardening.md`](../cost-abuse-hardening.md)

Last verified: 2026-07-19

## Execution checklist

This checklist is the durable source of truth for recovery progress. A step is
marked complete only after its verification evidence is recorded here.

| ID | Status | Work item | Verification / gate |
|---|---|---|---|
| R1 | Complete | Reopen billing and confirm the outage cause | Billing enabled; logs identified disabled billing |
| R2 | Complete | Make recovery private and cost-bounded | Public Invoker removed; Cloud Run min 0/max 1 |
| R3 | Complete | Inventory live infrastructure and Terraform drift | Live resources, state, IAM, registry, Firebase, DNS, and build trigger recorded below |
| R4 | Complete | Add billing visibility | 10 PLN project budget with 10%, 90%, and 100% alerts |
| A0 | Complete | Retire the superseded GitHub token | Local `.env` removed, helper migrated to `gh api`, and owner confirmed the GitHub account has no tokens |
| A1 | Complete | Remove hard-coded Flask/CSRF secrets and harden cookies | 66 unit tests pass; production config regression tests pass |
| A2 | Complete | Exclude credentials and local/IaC files from Docker context | Upload list excludes both credential files; reduced image built successfully |
| A3 | Complete | Remove sensitive/excessive authentication logging | Header, UID, user-name, and raw exception logging removed; CSRF regression test passes |
| A4 | Complete | Retire the user-managed Firebase key | Cloud key and local JSON deleted; zero user-managed keys remain; ADC-only initialization tested |
| I1 | Complete | Model least-privilege runtime and build identities | Dedicated build succeeded; runtime retains only Datastore user + secret accessor |
| I2 | Complete | Modernize Terraform and reconcile imported live resources | Provider 7.40 resources imported/applied; production plan reports no changes |
| I3 | Complete | Review and activate Artifact Registry cleanup | Owner approved keep-2/delete-older-than-7-days; exact plan applied with no service changes |
| I4 | Complete | Add state-bucket safeguards and project budget to IaC | Versioning, soft delete, uniform/public protection, operator IAM, and preserved budget converge |
| I5 | Complete | Automate validation/deploy and document unavoidable manual steps | Check script reaches no-change plan; deploy script syntax and workflow verified |
| D1 | Complete | Deploy remediated image while Cloud Run remains private | ADC-only revision 39 ready; authenticated endpoints 200; both public URLs 403 |
| D2 | Complete | Test Google login, guest login, and Firestore persistence | Both providers passed privately; guest write/reload and existing Google profile read passed |
| P1 | Complete | Restore public Invoker | Owner approved; exact one-binding Terraform plan applied on 2026-07-19 |
| P2 | Complete | Verify generated and custom URLs, rollback, and final docs | Both URLs 200; guest/Google persistence passed; rollback runbook and no-drift check verified |

Status meanings: **Pending** has not started; **In progress** is active work;
**Blocked** has an explicit gate; **Complete** includes recorded evidence.

### Implementation log

#### 2026-07-18 — application security pass

- Production now fails fast unless `FLASK_SECRET_KEY` is injected; local
  development receives an ephemeral key rather than a checked-in placeholder.
- CSRF protection is initialized once and enabled by default, including for the
  Firebase authentication callback. Secure, HTTP-only, SameSite=Lax cookies are
  enabled in production.
- Authentication no longer dumps request headers, user IDs, display names, or
  raw Firebase errors. Anonymous status is derived from the verified Firebase
  token instead of trusting the request body.
- Added `/readyz`, which does not call Firebase or Firestore. `/healthz` was
  avoided after the Cloud Run frontend intercepted it with its own 404 response.
- `.dockerignore` now excludes the Firebase credential, environment files,
  Terraform/local-agent files, tests, tools, and documentation.
- Fixed invalid TOML booleans and current Ruff configuration. Updated four stale
  SymPy tests that incorrectly compared SymPy `BooleanTrue` by Python identity.
- Verification: `pytest tests/unit -q` reports 66 passed; Ruff passes for every
  changed Python file; `git diff --check` passes except for line-ending notices.
- Manual security gate discovered: the ignored local `.env` contains a GitHub
  personal access token. It must be revoked by the owner and must not be migrated
  into infrastructure configuration.
- Follow-up inspection found exactly one consumer of `GITHUB_TOKEN`: the optional
  `tools/get_pr_comments.py` helper. The application, Terraform, Cloud Build, and
  production runtime do not use it. GitHub CLI is installed; its authenticated
  credential store plus `gh api` is the recommended replacement for the helper.

#### 2026-07-18 — Terraform modernization plan

- Pinned Google provider 7.40.0 and checked in its dependency lock file.
- Split the configuration by responsibility and added declarative migrations
  for the live Cloud Run service, Firestore database, state bucket, billing
  budget, Cloud Build trigger, repository, and runtime identity. The first
  remote plan proposes no resource replacements.
- Public Cloud Run access is now an explicit boolean release gate whose default
  is false. Cloud Run v2 has deletion protection, min 0/max 1 scaling, CPU idle,
  a runtime Secret Manager binding, and Terraform ignores only image promotion.
- Added a dedicated build/deploy service account with Artifact Registry writer,
  Logging writer, Cloud Run developer, and `actAs` only on the runtime identity.
  The plan removes redundant runtime Firebase/Datastore admin roles and the old
  Cloud Build service account's broad deploy permissions.
- The existing budget is imported. Its console-created email-recipient rule is
  deliberately ignored by Terraform because provider 7.40 cannot represent
  that rule without also adding Pub/Sub or Monitoring notification channels.
- State bucket changes are in-place: enable versioning, uniform bucket-level
  access, and public-access prevention while retaining seven-day soft delete.
- Registry policy is dry-run only: keep two recent PokeMath versions and match
  all older versions after seven days for deletion. No image deletion is
  authorized yet.
- Cloud Build now uses immutable commit-SHA tags and updates only the Cloud Run
  image; it no longer contains `--allow-unauthenticated`. The production image
  installs a minimal dependency set and no compiler/debug/test tooling.
- Verification: `terraform validate` succeeds. Remote planning successfully
  resolved all declarative imports and showed only in-place safeguards, IAM
  reductions, new dedicated identities/secret, and state bookkeeping changes.

#### 2026-07-18 — reconciliation and private deployment

- Applied the reviewed migration with no replacements. Imported six live
  resources, created the dedicated build identity/secret bindings, enabled
  Firestore and secret deletion protection, and removed five obsolete IAM
  grants. Registry cleanup remains dry-run, so no image was deleted.
- Enabling uniform bucket access revealed that the previous backend depended on
  a legacy object ACL. Restored and codified a bucket-scoped
  `roles/storage.objectAdmin` operator binding before continuing. The state
  bucket now has explicit access, versioning, public-access prevention, and
  seven-day soft delete.
- The first custom-service-account build proved it also needed read access to
  the Cloud Build staging object. Added only bucket-scoped
  `roles/storage.objectViewer`; the next build completed all build, push, and
  private-deploy steps successfully.
- `gcloud meta list-files-for-upload` reported 1,110 source files; explicit
  checks found neither `.env`, `firebase-credentials.json`, `terraform.tfvars`,
  nor `backend.hcl` in the upload set.
- Revision `poke-math-00038-h7z` runs immutable image tag
  `manual-20260718-3`. Authenticated `/readyz` and `/login` return 200;
  unauthenticated generated and custom URLs return 403.
- Removed the completed one-time import/move declarations and stopped managing
  the immutable App Engine bootstrap artifact without deleting it. Running
  `infrastructure/scripts/check.ps1` now ends with `No changes` against live
  production.
- Added `infrastructure/README.md`, a committed production variable file, a
  validation/plan script, and a private-deploy script. The runbook covers cost
  controls, public release, credential rotation, manual trust boundaries, and
  rollback.
- Cleanup inventory after the private deployments: 34 digests total. Keeping
  the active image and one hardened rollback retains about 211 MiB; the 32
  older digests account for roughly 6.7 GiB of logical image size. The revised
  policy was reviewed in dry-run mode, explicitly approved by the owner, and
  activated on 2026-07-19. Artifact Registry performs matching deletions
  asynchronously; no Cloud Run or Firestore resource changed during activation.
- Private browser tests used a localhost authenticated forwarder while Cloud Run
  remained private. Anonymous Firebase login succeeded, trainer name
  `CodexSmoke20260719` was written and survived a redirect plus reload, proving
  runtime Firestore read/write. Google login succeeded with the owner's account,
  loaded existing trainer name `Ash`, and retained it after reload.
- The optional Google Cloud CLI `cloud-run-proxy` component is installed. The
  repository's custom authenticated proxy remains documented because it also
  supports the browser test workflow used here.
- The ignored `firebase-credentials.json` belongs to the Firebase Admin SDK
  service account. Its matching user-managed key was created on 2025-02-26 and
  had no expiry. Revision 38 proved that production uses ADC; after explicit
  owner approval, the cloud key and local JSON were deleted on 2026-07-19.
  Verification found zero remaining user-managed keys on that service account.
- A live Cloud Run inspection confirmed that revision 38 has only
  `FLASK_SECRET_KEY` and `APP_ENVIRONMENT` environment entries and runs as
  `poke-math-service@pokemath-451818.iam.gserviceaccount.com`; it has no
  `GOOGLE_APPLICATION_CREDENTIALS` reference. Repository search also found no
  Terraform or Cloud Build dependency on the Firebase JSON key.
- Removed the file-based Firebase credential fallback from application code.
  Cloud Run and local development now share the ADC path; local setup uses
  `gcloud auth application-default login` and never downloads a service-account
  key. All 66 unit tests and Ruff passed after this simplification.
- Built and privately deployed ADC-only revision `poke-math-00039-rtw` after
  deleting the cloud key. Authenticated `/readyz` and `/login` returned 200;
  unauthenticated generated and custom URLs remained 403. A disposable guest
  session wrote a uniquely named Firestore profile, the document was verified
  through the Firestore API, and both the document and anonymous Firebase user
  were removed. A final query found zero remaining test documents, and Terraform
  again reported no changes.

#### 2026-07-19 — public release

- After explicit owner approval, changed the committed production release gate
  to `public_access_enabled = true`. The saved Terraform plan added only the
  `allUsers` Cloud Run Invoker binding: one add, zero changes, zero destroys.
- Unauthenticated `/readyz` and `/login` returned 200 on both the generated
  Cloud Run hostname and `https://pokemath.quarion.dev`.
- Public guest login wrote trainer `PublicSmoke20260719`, survived reload, and
  was then fully cleaned up: the exact Firestore document and anonymous Firebase
  account were deleted and verified absent.
- Public Google login loaded existing trainer `Ash`, survived reload, and showed
  no browser errors. The final Terraform check reported no changes.
- Removed the local `.env` token copy and migrated `tools/get_pr_comments.py`
  from a plaintext `GITHUB_TOKEN` to paginated `gh api` calls. Remote revocation
  was considered complete after the owner confirmed that GitHub lists no tokens.

#### 2026-07-19 — cost and abuse audit

- The Firebase Blaze upgrade email is expected: linking Cloud Billing for Cloud
  Run automatically upgrades the associated Firebase project to Blaze. Blaze
  retains free allowances but charges usage beyond them and has no hard usage
  or spending cap.
- Cloud Monitoring reported only 18 Firestore reads, 3 writes, 2 deletes, and
  about 1.30 MiB of data/index storage over the observed seven-day period. The
  free allowances are 50,000 reads/day, 20,000 writes/day, 20,000 deletes/day,
  and 1 GiB storage for this single `(default)` database.
- Cloud Run reported 817 requests and about 52.5 billable instance-seconds over
  seven days. Request-based billing, min 0, max 1, 1 vCPU, and 512 MiB remain
  active. Max 1 strongly bounds compute amplification but is not a complete
  request, egress, or application-layer DoS spending cap.
- The project-scoped 10 PLN monthly budget is live with actual-spend thresholds
  at 10%, 90%, and 100%. Google budgets alert but do not stop usage, and billing
  data/notifications can lag by hours.
- The immediate manual kill switch is to set `public_access_enabled = false` in
  `infrastructure/environments/prod.tfvars` and apply the reviewed Terraform
  plan. Recommended next KISS hardening is application-level rate limiting on
  login/Firestore/write routes plus lower Cloud Run concurrency/timeout. A more
  complex option is a Monitoring-triggered IAM kill switch or an external load
  balancer with Cloud Armor; budget-triggered billing disablement is deliberately
  not recommended because it is delayed and can stop/delete project resources.

## Objective

Restore PokeMath safely, keep normal usage within Google Cloud's free allowances,
and make the infrastructure reproducible with the smallest practical amount of
manual console work.

## Confirmed live state

- GCP project: `pokemath-451818` (`991216996410`), region `europe-west1`.
- The billing account was reopened on 2026-07-18 and the project now reports
  `billingEnabled: true`. Billing is on the Blaze/pay-as-you-go plan; free usage
  allowances still apply, but they are not a hard cap.
- Cloud Run logs confirmed that billing suspension caused the outage. Hardened
  revision `poke-math-00039-rtw` is public and healthy; both generated and
  custom hostnames pass readiness, login, and browser authentication tests.
- Cloud Run uses the dedicated
  `poke-math-service@pokemath-451818.iam.gserviceaccount.com` identity, and is
  configured for 1 CPU, 512 MiB, concurrency 80, timeout 300 seconds, minimum 0
  instances, and maximum 1 instance. Public Invoker access was restored through
  the explicit Terraform release gate on 2026-07-19.
- `pokemath.quarion.dev` is a healthy Cloud Run domain mapping with a provisioned
  certificate. DNS is hosted by Cloudflare.
- Firestore `(default)` is Native mode in `eur3` and is free-tier eligible.
- The GitHub Cloud Build trigger is managed by Terraform, deploys pushes to
  `main`, and runs as a dedicated least-privilege build service account.
- Terraform state is stored in `gs://tfstate-pokemath-europe-prod`. The bucket
  has versioning, uniform bucket-level access, public-access prevention,
  explicit operator access, and seven-day soft delete.
- Artifact Registry cleanup is active: retain the two most recent versions and
  delete older versions after seven days. Cleanup execution is asynchronous.
- Firebase Authentication has Email/Password, Google, and Anonymous providers
  enabled. Both the generated Cloud Run hostname and `pokemath.quarion.dev` are
  authorized OAuth domains. The project has not been upgraded to Identity
  Platform, and there is currently no reason to add that complexity.
- A project-scoped monthly budget named `PokeMath monthly guardrail` is active:
  target 10 PLN, actual-spend alerts at 10%, 90%, and 100%, emailed to billing
  administrators/users and project owners. A budget alerts but does not stop
  resources automatically.

## Initial security and cost blockers (resolved during recovery)

1. Flask session and CSRF placeholders were replaced with a generated Secret
   Manager value injected into Cloud Run; secure cookie/CSRF defaults are tested.
2. `firebase-credentials.json` was ignored by Git but was not excluded from the
   Docker build context. It is now excluded and deleted, and its cloud key has
   been revoked.
3. Redundant runtime owner/admin roles were removed; runtime retains only
   Datastore user plus access to the Flask secret.
4. The build trigger now uses a dedicated least-privilege build identity.
5. Cloud Run uses request-based billing, minimum instances 0, and maximum 1.
6. Artifact Registry cleanup is active with two-version retention.
7. A 10 PLN project budget has 10%, 90%, and 100% actual-spend alerts. Budgets
   are alerts, not an instantaneous hard spending cap.

## Safe recovery sequence

Do not reorder these steps without reassessing exposure.

1. [Complete 2026-07-18] Remove the public Cloud Run Invoker binding while
   billing remains disabled.
2. [Complete 2026-07-18] Owner manually reopens the billing account/payment
   profile.
3. [Complete 2026-07-18] Verify the project is billing-enabled, while Cloud Run
   remains private; cap Cloud Run at one instance and create the 10 PLN budget.
4. [Complete 2026-07-18] Inventory Terraform state, Artifact Registry, Firebase
   Auth, budgets, and current drift.
5. [Complete 2026-07-19] Fix application secrets and Docker context; revoke the
   Firebase Admin key after private verification.
6. [Complete 2026-07-18] Apply cost controls and least-privilege IAM.
7. [Complete 2026-07-19] Modernize/import infrastructure and deploy the fixed
   revision privately.
8. [Complete 2026-07-19] Run login, Google, guest, and Firestore smoke tests.
9. [Complete 2026-07-19] Restore public Invoker access and verify both URLs.
10. [Complete 2026-07-19] Complete documentation and rollback instructions.

## Target automation boundary

### Bootstrap and validation

For this single small project, the KISS boundary is a runbook plus checked-in
validation/deploy scripts rather than a second bootstrap framework. `check.ps1`
initializes Terraform, validates configuration, and checks live drift;
`deploy-private.ps1` tests, checks the upload set, and submits a private build.
Creating/reopening a consumer billing account, entering payment details, initial
GitHub authorization, and creating the state bucket before its backend exists
remain documented one-time trust-boundary actions.

### Terraform

Use a current Google provider and import/manage:

- required project APIs;
- the Terraform state bucket and retention/versioning policy;
- Artifact Registry plus cleanup policies;
- dedicated runtime and build service accounts with narrow IAM;
- Firestore through `google_firestore_database` with deletion protection;
- supported Firebase/Identity Platform configuration;
- Secret Manager values and Cloud Run secret bindings;
- Cloud Run v2 settings and public-access policy;
- Cloud Build trigger after its one-time GitHub authorization;
- billing budget and alert thresholds;
- Cloud Run domain mapping;
- optionally Cloudflare DNS through a scoped API token.

The application image lifecycle must have one owner. Prefer Terraform for the
service configuration and Cloud Build for immutable image deployment, with the
image field deliberately ignored by Terraform after bootstrap.

### Manual runbook

Only these operations should remain manual unless later integrations justify
more machinery:

- entering or updating payment information and reopening a billing account;
- one-time GitHub authorization for Cloud Build;
- one-time Google domain ownership verification;
- supplying a scoped Cloudflare API token if DNS is managed by Terraform.
- revoking superseded personal-access tokens in the owning GitHub account.

## Free-usage guardrails

- Cloud Run: request-based billing, min 0, max 1, no always-on CPU.
- Firestore: one free-tier database; avoid paid backup, PITR, clone, and TTL
  features unless deliberately enabled.
- Firebase Auth: Google and anonymous/social authentication only; no SMS.
- Artifact Registry: retain only a small number of deployable images.
- Cloud Build: main-branch deployments only; avoid unnecessary rebuild loops.
- Internet egress can still be billable, particularly from a European region.
  Optimize/cache large static assets if usage grows.

## Current follow-up

Production release, application/IAM hardening, Terraform reconciliation, cost
controls, credential removal, registry policy, Google login, guest login, and
Firestore persistence are complete. Artifact Registry cleanup is active but may
take roughly a day to remove eligible images. The owner should decide whether to
add the documented application-level abuse limits and/or automated IAM kill
switch; current usage is far inside every free allowance, but Blaze has no true
hard spending cap.
