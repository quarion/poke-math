# Personal-account handoff: remote-agent delivery

Date: 2026-07-20

## Purpose

Continue the PokeMath remote-agent delivery work from the personal Windows and ChatGPT account. The work-account task performed the initial research and created the active implementation plan, but milestone implementation should happen from the personal account so that Codex Cloud, GitHub authorization, mobile Remote access, and ongoing side-project usage share one identity.

## Repository

```text
https://github.com/quarion/poke-math.git
```

Clone it into the personal Windows profile rather than sharing the work account's checkout:

```powershell
git clone https://github.com/quarion/poke-math.git
Set-Location poke-math
```

## Authoritative plan

Read and follow `docs/plans/remote-agent-delivery-plan.md`. Implement milestone 1 only. Do not implement either milestone 2 preview strategy until milestone 1 has been exercised and the preview topology has been selected explicitly.

## Personal-account prerequisites

1. Sign in to the Codex desktop app with the personal ChatGPT account and confirm the active account and workspace before connecting anything.
2. Authenticate GitHub using the personal account that has write and repository-administration access to `quarion/poke-math`.
3. Connect this repository in Codex settings and create its OpenAI-managed cloud environment under the personal ChatGPT account.
4. Pin Python 3.11 and configure the environment setup command documented in the plan.
5. Pair the personal ChatGPT mobile app with the personal Codex setup. Do not reuse or depend on the work account's Remote pairing.
6. Keep production Google Cloud and Firebase credentials out of the Codex cloud environment.

## First task for Codex on the personal account

Use this prompt after cloning the repository:

> Read `AGENTS.md`, `docs/plans/AGENTS.md`, and `docs/plans/remote-agent-delivery-plan.md`. Inspect the current repository and implement milestone 1 of the remote-agent delivery plan. Keep the work scoped to the milestone, preserve the security boundaries in the plan, run all relevant checks, and update the plan as implementation facts become known. Separate repository changes from external GitHub, Codex Cloud, and Google Cloud configuration that requires my account access. Do not implement milestone 2 or choose a preview topology. Before making external configuration changes, show me the exact change and why it is needed. Create a feature branch and pull request; do not merge it.

## Expected milestone 1 outcomes

- Repository guidance documents the setup, test, build, and delivery expectations for agents.
- GitHub Actions runs unit tests and a production Docker build on pull requests.
- Cloud Build runs unit tests before deployment.
- `main` is protected by required pull-request checks.
- The Codex cloud environment can create and validate a pull request without the local PC.
- Merging an approved, passing pull request triggers the existing Cloud Build production deployment.

## Known baseline

- All 74 unit tests passed locally on 2026-07-20.
- Ruff had 16 pre-existing findings and must not become a required check until the baseline is cleaned up or deliberately scoped.
- The production Docker image uses Python 3.11.
- The work-account GitHub CLI credential was expired during research; authenticate independently in the personal Windows profile.
- The live GitHub branch-protection and Google Cloud trigger state was not verified during research and must be checked during milestone 1.

## Completion handling

When milestone 1 is complete, promote durable setup and validation commands into the root `AGENTS.md`, keep operational deployment details in `infrastructure/README.md`, update the active plan with verified results, and leave milestone 2 active for the later preview-strategy decision.
