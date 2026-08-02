# Matt skills workflow adoption

## Scope

This document is exclusively about learning, adopting, evaluating, and potentially adapting Matt Pocock's skills workflow. Product sessions should not load it unless workflow adoption is explicitly in scope.

The equation-generation project is the working example, but the workflow-learning goal is secondary to the product goal and must not distract agents working on the product increment.

## Goal

Understand the Matt skills approach through real use, learn how it can support the user's personal and departmental work, and only then decide whether explicit adaptations are desirable.

## Strict fidelity requirement

Adopt each selected skill verbatim first. The installed skill source at the selected pinned revision is authoritative.

Agents must not paraphrase, simplify, reinterpret, blend, or silently improve an adopted skill's instructions. This includes replacing its workflow with a summary, borrowing only selected ideas, changing interaction cadence, or combining it with another workflow because the agent believes the result is more efficient.

Any deviation or adaptation requires an explicit user request. When an adaptation is requested, record what differs from the upstream skill and why. Until then, observed friction is evaluation evidence, not permission to change the workflow.

This requirement is especially important for models that tend to paraphrase instructions or reproduce the apparent spirit of a skill without following its exact process.

## User context

The user has already tried `grilling` and `domain-modeling` and found them highly effective for day-job work.

The user did not like the experience of `to-spec` because it produced documents too large to review comfortably and reduced the user's sense of control over the specification. This is an important observation, but it does not authorize changing `to-spec` before first adopting and evaluating the relevant workflow verbatim.

The desired long-term workflow should preserve human ownership of consequential decisions and produce artifacts the user can realistically review. Whether that requires replacing, constraining, or adapting `to-spec` remains an open question.

## Local source and version findings

The skills repository is cloned at `C:\Users\Filip\Projects\mattpocock\skills`. At inspection time, local `main` was `2ab9580` and `origin/release/v1.2` was `4128367`.

At those revisions, `wayfinder`, `setup-matt-pocock-skills`, and `domain-modeling` have no content differences between `main` and `release/v1.2`.

The material workflow difference is `grilling`. On `main`, it asks one question at a time. On `release/v1.2`, it models a dependency-aware design tree and asks the entire currently unblocked frontier in numbered rounds. Questions that depend on an unsettled answer remain for a later round.

The setup skill is prompt-driven rather than a deterministic installer. It inspects the repository, asks for tracker configuration, establishes domain-document conventions, previews proposed edits, and writes only after confirmation.

## Current repository findings

- The product repository uses GitHub at `quarion/poke-math`.
- It has an existing root `AGENTS.md` with no Matt-skills configuration block.
- It has no `docs/agents/` tracker or domain configuration.
- It has no established root `CONTEXT.md`, `CONTEXT-MAP.md`, or `docs/adr/`.
- It is a single-context repository rather than a monorepo.
- The Matt skills are not exposed in the current Codex session.
- The Matt `triage` skill is not installed, so its label setup is not currently required.

## Open adoption decisions

- Which minimal set of skills should be installed for the trial?
- Should GitHub Issues be the canonical tracker, as the setup skill would recommend from the repository remote?
- How should workflow observations be recorded without contaminating product artifacts?
- After a faithful trial, what explicit criteria should determine whether a skill is retained verbatim, adapted, or replaced?

## Decisions so far

- The first faithful trial will use `release/v1.2` pinned at commit `41283677d63b8f658e6c94b3519f556a1831f9ad`.
- The initial trial installs `setup-matt-pocock-skills`, `wayfinder`, `grilling`, `domain-modeling`, `prototype`, and `research` as complete, unmodified skill directories in the personal Codex skills directory.
- The initial installation was completed on 2026-08-02 from the pinned commit. Repository-specific setup has not yet been run.
- Designing an upgradable customization mechanism, potentially based on tracked patches or Git merges, is deferred until after the verbatim trial provides concrete evidence about what should change.

## Installed initial skill set

The installed set is `setup-matt-pocock-skills`, `wayfinder`, `grilling`, `domain-modeling`, `prototype`, and `research`.

`to-spec` is not part of the candidate initial set. Its omission is intended to keep the first experiment focused, not to redefine or partially adopt it.
