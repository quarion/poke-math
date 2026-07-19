# Cost and Abuse Hardening Plan

Status: completed

Started: 2026-07-19

Completed: 2026-07-19

Baseline commit: `0b9c059` (`Restore and codify production infrastructure`)

Implementation: Cloud Build `67591851-9160-4b73-938d-4ec1a7d2c513`, Cloud Run revision `poke-math-00041-trm`

## Objective

Reduce the chance that application-layer abuse, accidental loops, or a traffic spike can turn PokeMath's public Blaze/Cloud Run deployment into a surprise bill, while preserving the KISS architecture and normal guest/Google use.

## Constraints and decisions

- Firebase Blaze and Google Cloud budgets have no hard monetary spending cap.
- Avoid a load balancer, Cloud Armor, Redis, or another fixed-cost service until observed traffic justifies that complexity.
- Keep Cloud Run request-based billing, minimum instances 0, maximum instances 1, 1 vCPU, and 512 MiB.
- One Gunicorn worker with eight threads makes a process-local, thread-safe global limiter an intentional cost fuse.
- Rejected traffic must avoid Firebase/Firestore, SymPy work, template rendering, and large static responses whenever possible.
- Availability may degrade under attack; bounded cost is more important for this personal project than serving every abusive request.
- Every live mutation requires an exact saved plan or immutable image, bounded verification, and a documented rollback.

## Baseline evidence

- Firestore, previous seven days: 18 reads, 3 writes, 2 deletes, about 1.30 MiB.
- Cloud Run, previous seven days: 817 requests and about 52.5 billable seconds.
- Firestore free allowance: 50,000 reads/day, 20,000 writes/day, 20,000 deletes/day, and 1 GiB storage.
- Cloud Run: max 1 instance, request concurrency 80, Gunicorn capacity 8 threads, request timeout 300 seconds, and no application rate limiter.
- Budget: 10 PLN/month, actual-spend alerts at 10%, 90%, and 100%; alerts can lag and do not stop usage.

## Execution checklist

| ID | Status | Work item | Acceptance / evidence |
|---|---|---|---|
| H1 | Complete | Measure amplification and define limits | Route costs, seven-day usage, static sizes, proxy identity, and legitimate burst reviewed |
| H2 | Complete | Add a cheap process-global and per-client request fuse | Sliding windows, bounded client LRU, non-evictable global counters, early 429, deterministic tests |
| H3 | Complete | Add tighter limits to auth and write routes | Auth 60/10 and writes 120/30 global/client per minute; live auth sequence returned ten 400 responses then 429 |
| H4 | Complete | Align Cloud Run capacity with Gunicorn | Live Cloud Run and Docker specify concurrency 8 and timeout 60 seconds |
| H5 | Complete | Add near-real-time usage alerts | Owner email channel and Cloud Run request/billable-time and Firestore read/write policies are live |
| H6 | Complete | Deploy and verify | 74 tests pass; public health/login 200; Ash profile persists with no browser errors; Terraform reports no changes |
| H7 | Complete | Document rollback and residual risk | Runbook states kill switch, limiter reset behavior, and when Cloud Armor is justified |
| H8 | Complete | Audit durable documentation | Runbook and architecture describe current state without relying on plan history; completed plans archived |

## Limit design

- The global 300-request/minute sliding window caps total work admitted by the single Gunicorn process. Excess requests return a small `429` before session, auth, Firestore, SymPy, templates, or static-file work.
- The 120-request/minute per-client window prevents one ordinary source from consuming the global budget. Production uses Cloud Run's forwarded client address; this is best-effort attribution, never the cost boundary.
- Identity cardinality is bounded to 4,096 LRU buckets. The global counter is stored separately and cannot be evicted or bypassed by rotating identities.
- Authentication callback limits are 60/minute globally and 10/minute per client. State-changing route limits are 120/minute globally and 30/minute per client.
- Monitoring alerts are detection and notification, not a hard cap. Automated public-IAM shutdown is a separate decision; billing-account disablement remains out of scope because it is delayed and can stop or eventually remove project resources.

## Rollback

1. Revert the hardening commit and deploy its predecessor image if legitimate users are incorrectly throttled.
2. Revert only Terraform concurrency/timeout values if long-running legitimate requests fail.
3. Emergency cost stop: set `public_access_enabled = false`, review and apply the saved plan, and verify both public URLs return 403.

## Residual risk

Application limits reduce expensive work and response size after traffic reaches the container; those requests can still count toward Cloud Run request billing. Strong enforcement before Cloud Run requires an external load balancer plus Cloud Armor and disabling the default `run.app` URL, which adds recurring cost and infrastructure. Revisit that option if monitoring shows hostile traffic or if this becomes more than a low-traffic personal project.
