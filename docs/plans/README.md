# Implementation plans

This directory contains implementation plans used by coding agents and human contributors.

## Active plans

Markdown files directly in this directory are active. They describe work that is being designed, implemented, or verified and may be updated as the work progresses.

Once implementation and verification are complete, move the plan to [`completed/`](completed/). Before archiving it, move any knowledge that is still authoritative into the appropriate architecture document, requirement, or operational runbook. A completed plan records what happened; it should not be the only source of current operating instructions.

## Completed plans

The `completed/` directory is a historical archive for debugging, auditing, and project archaeology. Its plans are kept in Git but are not part of the default context for new work.

Completed plans should normally remain unchanged. If a historical correction is necessary, add a dated note rather than rewriting the original account. Retain an issue or pull request reference when one already exists and provides useful context, but do not add placeholders or create follow-up changes solely to reference the implementation commit.

Each plan should make its status clear near the top. An archived plan should also record its completion date, for example:

```markdown
Status: completed
Completed: 2026-07-19
```
