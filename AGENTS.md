# Repository agent instructions

## Markdown writing

- Write each paragraph or list item as a continuous line. Do not hard-wrap Markdown at a fixed line length.
- Add manual line breaks only when they improve the flow or express meaningful structure.

## Validation

- Install dependencies with `uv sync --locked --all-groups`.
- Run `uv run pytest tests/unit -q`.
- Run `docker build --build-arg COMMIT_SHA=local --tag poke-math:local .`.
- Ruff has a known baseline of pre-existing findings and is not a required delivery check until that baseline is deliberately cleaned up.

## Delivery boundaries

- Deliver changes through a pull request against `main`; do not merge or deploy from an agent task.
- Do not modify infrastructure unless the task specifically requires it.
- Never add production credentials to the repository, logs, pull requests, or agent environment.
