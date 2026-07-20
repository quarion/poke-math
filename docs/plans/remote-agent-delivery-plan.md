# Remote-agent delivery plan

Status: in progress

Created: 2026-07-20

## Objective

Enable PokeMath development from a phone or any other device while the local PC is turned off. Codex should work in an OpenAI-managed cloud environment, create a branch and pull request, run repository checks, and hand the change to GitHub and Google Cloud for controlled deployment.

The work is divided into two milestones. Milestone 1 establishes a safe, dependable pull-request-to-production flow. Milestone 2 adds a preview or development environment after practical experience with the first flow clarifies whether simultaneous per-PR previews are worth their additional complexity.

## Target operating model

```text
Phone or browser
    -> Codex cloud environment
    -> agent branch and pull request
    -> GitHub CI and protected main branch
    -> human merge or approval
    -> Google Cloud Build
    -> Cloud Run
```

The coding agent owns changes on a feature branch. GitHub owns review and merge policy. Google Cloud Build owns deployment. Codex must not receive production deployment credentials.

## Current repository baseline

- The repository is hosted at `github.com/quarion/poke-math` and uses `main` as its default deployment branch.
- Terraform declares a Google Cloud Build trigger for pushes to `main` in `infrastructure/build.tf`.
- `cloudbuild.yaml` builds and pushes an immutable image tagged with the commit SHA, then updates the Cloud Run service immediately.
- The Cloud Run service currently sends 100% of traffic to the latest deployed revision.
- The production container uses Python 3.11.
- As of 2026-07-20, all 74 unit tests pass locally.
- Ruff reports 16 pre-existing findings, so linting must not become a required check until those findings are fixed or an intentionally scoped lint policy is defined.
- A GitHub Actions workflow defines the `unit-tests` and `docker-build` checks for pull requests and pushes to `main`; its first hosted run and required-check configuration still need verification.
- The root `AGENTS.md` contains Markdown guidance but does not yet document setup, validation, or delivery expectations for coding agents.

## Security and delivery principles

- Codex cloud may receive GitHub permission sufficient to create branches and pull requests, but it must not receive Firebase service-account keys, Google Cloud service-account keys, Terraform credentials, or direct production deployment authority.
- Production changes must reach `main` through a pull request with required checks.
- CI jobs for untrusted pull requests must not receive cloud deployment credentials.
- Existing Google Cloud service accounts remain the deployment and runtime identities.
- Prefer short-lived identity federation over stored service-account JSON keys if GitHub Actions later needs Google Cloud access.
- Use immutable commit-SHA image tags and retain a documented rollback path.
- Preview testing must not silently read or mutate production Firestore data.

## Milestone 1: working pull-request flow

### Goal

From the ChatGPT mobile experience or another remote client, start a Codex task while the local PC is off, let the agent implement and validate a change in an OpenAI-managed environment, receive a pull request, review its checks, merge it, and observe the existing Cloud Build deployment to production.

### Repository changes

1. Extend the root `AGENTS.md` with the supported Python version, dependency installation command, required unit-test command, Docker build command, and delivery constraints. Agents should be instructed to work on a branch, open a pull request, avoid merging their own change, and avoid modifying infrastructure unless the task requires it.
2. Add `.github/workflows/ci.yml` for pull requests targeting `main` and pushes to `main`.
3. Run CI with Python 3.11 to match the production container.
4. Make the initial required checks `python -m pytest tests/unit -q` and a production Docker image build.
5. Do not make Ruff required during this milestone. Track cleanup of the 16 baseline findings separately, then enable Ruff when the repository passes cleanly.
6. Add a unit-test step to `cloudbuild.yaml` before build, push, and deploy so production deployment has a final repository-owned safety check even if GitHub configuration is accidentally weakened.
7. Document the Codex cloud environment setup, including the setup script and the rule that no Google Cloud or Firebase production credentials belong in the agent environment.

### External configuration

1. Connect the GitHub repository in Codex settings and create an OpenAI-managed cloud environment for PokeMath.
2. Pin Python 3.11 in the environment and use the following setup command:

```bash
uv sync --locked --group dev
```

3. Leave agent-phase internet access disabled unless a task has a concrete reason to enable a restricted allowlist.
4. Protect `main` in GitHub: require a pull request, require the unit-test and Docker-build checks, require conversation resolution, and block force pushes and deletion.
5. Optionally require one human approval. For this personal repository, the minimum human gate is that Codex does not merge its own pull request and the owner explicitly performs the merge.
6. Verify that the Terraform-declared Cloud Build trigger is active and that the GitHub connection still has access to the repository.
7. Reauthenticate the local GitHub CLI before using it for repository administration; the credential observed during planning was expired.

### Implementation status: 2026-07-20

- Completed in the repository: Python dependencies are managed by `uv` with a committed lockfile; root agent guidance documents Python 3.11, setup, validation, cloud-environment, and delivery boundaries; CI defines `unit-tests` and `docker-build`.
- Cloud Build correction in progress: the initial deployment of merge commit `0068fc45c9b69887a988b5ea136f29d37d8b5b74` failed before tests because the selected `ghcr.io/astral-sh/uv:0.11.26-python3.11-bookworm-slim` manifest does not exist. The correction makes Cloud Build build the Dockerfile's `test` target, which uses the same pinned Python 3.11 and `uv` setup as the runtime target, adds only locked development dependencies, and runs the unit suite before the production image build. Hosted verification remains required before Cloud Build can be recorded as passing.
- Verified locally in a managed Python 3.11 environment: `uv lock --check` and `uv run --locked --group dev pytest tests/unit -q` (74 passed). The Docker build remains to be run by GitHub Actions or a Docker-capable environment.
- Still external and intentionally not changed: personal GitHub CLI reauthentication, Codex cloud-repository/environment setup, GitHub `main` branch protection, Cloud Build trigger/connection verification, remote pull-request rehearsal, production deployment observation, and rollback rehearsal.

### End-to-end validation scenario

1. With the development PC turned off, start a small Codex cloud task from the ChatGPT mobile experience.
2. Ask Codex to create a branch, make a harmless visible change, run the required checks, and open a pull request without merging it.
3. Confirm the pull request displays the required GitHub checks and cannot merge while a required check is failing or pending.
4. Review the diff and merge from the phone.
5. Confirm that the merge to `main` triggers Cloud Build.
6. Confirm that Cloud Build runs tests before building and deploying.
7. Verify `/readyz`, the custom production URL, and the deployed commit version after the build completes.
8. Exercise the documented rollback procedure once with a known-safe revision or in a non-disruptive rehearsal so it is not being discovered for the first time during an incident.

### Milestone 1 acceptance criteria

- A Codex task can run without relying on the local PC.
- Codex can create a pull request from its cloud environment.
- Required unit tests and the Docker build run automatically on the pull request.
- Direct or unchecked changes to `main` are blocked by repository policy.
- Codex has no production deployment credential.
- Merging a passing pull request triggers Cloud Build and deploys the immutable commit image.
- A failed test prevents deployment.
- Production health and deployed version can be verified after deployment.
- The workflow and any remaining manual setup are documented well enough to repeat for another repository.

### Explicitly out of scope for milestone 1

- Per-pull-request preview environments.
- A persistent development deployment.
- Production traffic splitting or canary rollout.
- Automatic merging by Codex.
- Automatic deployment from untrusted fork pull requests.
- Making the existing Ruff baseline a required check.
- Full Firebase-backed browser E2E tests in CI.

## Milestone 2: preview and environment strategy

### Goal

Add a non-production place to inspect and exercise changes before a live swap. Choose the topology only after milestone 1 has been used for real changes and the expected concurrency is known.

### Option A: per-pull-request previews

Each eligible pull request deploys an isolated Cloud Run preview, for example `poke-math-pr-123`, and publishes its URL on the pull request. Closing or merging the pull request removes or expires the preview.

Advantages:

- Multiple feature versions can be tested simultaneously.
- A preview corresponds directly to a pull request and commit.
- Reviewers can inspect changes without replacing a shared development environment.

Costs and risks:

- More Terraform or workflow logic, cleanup automation, IAM, DNS or URL handling, and operational cost.
- Public fork pull requests must never deploy with cloud credentials automatically.
- Firebase Authentication authorized domains and callback behavior need deliberate handling.
- A preview must use isolated test data; pointing several previews at production Firestore is not acceptable for destructive or stateful testing.
- Image and Cloud Run resource retention must be bounded.

This option is preferred when several changes are commonly active at once or when reviewers need stable, commit-specific URLs.

### Option B: persistent development and production environments

Maintain a `dev` branch that deploys to a persistent development Cloud Run service and keep `main` as the production branch. The normal linear flow becomes feature branch to `dev`, test on the development URL, then promote through a pull request from `dev` to `main`.

Advantages:

- Simpler deployment topology and cleanup.
- Fits a mostly linear personal development flow.
- One stable development URL is easy to bookmark and test from a phone.
- A separate development Firebase project and Firestore database can be configured once.

Costs and risks:

- Only one development version is available at a time.
- Concurrent changes can replace one another on the shared development service.
- Long-lived `dev` and `main` branches can drift or accumulate merge-only differences.
- Rebuilding after promotion can produce a different artifact unless promotion explicitly reuses the tested image digest.

If this option is selected, prefer promoting the exact tested container digest from development to production. If that is too complex for the educational first version, record that production rebuilds from the promoted commit and keep dependency resolution deterministic.

This is the leading option for the repository's current mostly linear workflow unless milestone 1 reveals a real need for concurrent previews.

### Alternative lightweight candidate revision

Cloud Run can deploy a revision with `--no-traffic` and a revision tag, exposing a tagged URL before production traffic is moved. This is useful for a release-candidate smoke test but is not a fully isolated environment if it inherits production Firebase and Firestore configuration. Treat it as a transitional option, not as the final professional design.

### Decision criteria

Before implementing milestone 2, answer these questions from observed use:

1. How often are two or more independent changes awaiting review simultaneously?
2. Is one stable `dev` URL sufficient for the owner and family testing workflow?
3. Does preview testing need writable Firebase or Firestore data?
4. Are Google and anonymous login required in preview, and which domains must Firebase authorize?
5. Should production deploy automatically after merge, wait for a manual approval, or promote a previously tested image digest?
6. What cleanup and spending limits are required for previews?
7. Should infrastructure changes use the same flow as application changes or require a separate approval policy?

### Milestone 2 acceptance criteria

- Every non-production deployment is clearly identified and cannot be mistaken for production.
- Preview or development traffic is isolated from production data when state-changing tests are permitted.
- Production deployment uses an explicit, documented promotion rule.
- Deployment credentials are short-lived or remain exclusively inside Google Cloud.
- Untrusted pull requests cannot invoke credentialed deployment jobs.
- The selected topology has documented creation, update, cleanup, rollback, and cost-control procedures.

## Reusable pattern for other repositories

The reusable core is not provider-specific: remote coding agent, feature branch, pull request, required CI, human-controlled merge or promotion, and deployment by a dedicated CI/CD identity. A small static React application can use the same Codex and GitHub flow with Vercel, Netlify, Cloudflare Pages, or another static host supplying PR previews. A professional service can replace those hosts with a staging project and workload identity federation without changing the agent trust boundary.

When this plan is complete, promote stable setup commands and delivery rules into `AGENTS.md`, move operational deployment knowledge into `infrastructure/README.md`, record the completion date, and move this file to `docs/plans/completed/`.

## References

- [OpenAI Codex cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment)
- [OpenAI: work with Codex from anywhere](https://openai.com/index/work-with-codex-from-anywhere/)
- [Codex code review in GitHub](https://learn.chatgpt.com/docs/third-party/github)
- [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Google Cloud Build triggers](https://docs.cloud.google.com/build/docs/triggers)
- [Google Cloud Run revisions and traffic migration](https://docs.cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)
- [Google Cloud workload identity federation for deployment pipelines](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)
