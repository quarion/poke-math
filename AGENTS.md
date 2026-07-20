# Repository agent instructions

## Markdown writing

- Write each paragraph or list item as a continuous line. Do not hard-wrap Markdown at a fixed line length.
- Add manual line breaks only when they improve the flow or express meaningful structure.

## Environment and validation

- Use Python 3.11. The production Docker image and continuous integration use this version.
- Install the locked project environment with `uv sync --locked --all-groups`.
- Run the required unit suite with `uv run pytest tests/unit -q`.
- Validate production packaging with `docker build --build-arg COMMIT_SHA=local --tag poke-math:local .`.
- Ruff has a known baseline of pre-existing findings and is not a required delivery check until that baseline is deliberately cleaned up.

## Delivery and security boundaries

- Work on a feature branch and open a pull request against `main`. Do not merge your own pull request.
- Do not modify infrastructure unless the task specifically requires it. Review production-impacting changes separately from application changes.
- Do not add Google Cloud, Firebase, Terraform, or other production credentials to the repository, Codex cloud environment, logs, or pull requests.
- Pull requests must pass the `unit-tests` and `docker-build` checks before the owner merges them. A merge to `main` is the only normal application-deployment path.

## Codex cloud environment

- Pin Python 3.11 and use `uv sync --locked --all-groups` as the environment setup command.
- Keep agent-phase internet access disabled unless a task needs a concrete, restricted allowlist.
- The cloud agent may create branches and pull requests, but it must not receive direct production deployment authority or production cloud credentials.
