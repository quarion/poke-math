# Equation generation wayfinding bootstrap

## Status

This document preserves the product wayfinding state as of 2026-07-30. It is a bootstrap artifact for creating the canonical Wayfinder map after the repository's tracker is configured. It contains product context only; workflow adoption and skills experimentation are deliberately kept elsewhere so product sessions can load this document without unrelated goals.

## Destination

Design and deliver a real product increment for a configurable equation-generation system that consistently produces good educational exercises with a gradual difficulty curve. Reach an evidence-backed understanding of educational difficulty, establish a repeatable way to evaluate generated exercises, agree on a generator architecture and configuration model, validate the design with representative prototypes, and implement the resulting improvement.

The exact boundary between wayfinding and implementation remains open. Wayfinder normally ends when the route to implementation is clear, but its Notes may explicitly permit implementation within the map. This must be decided during charting without losing the ultimate product outcome.

## Notes

The current generator is mathematically valid in many normal cases, but mathematical validity is not sufficient for a good educational experience. The user has observed that the highest difficulty can sometimes produce trivial exercises, although recent testing was brief and a representative baseline does not yet exist.

Several implementation defects were identified during the initial review: displayed and stored values can diverge for multi-element mixed-operation basic equations, seeded simple-quiz generation can recurse indefinitely, grade-school bounds are ineffective, and decimal answers are incompatible with the application's answer path. Most of these defects do not surface under the current production configuration, so correcting them alone would not address the observed quality problem.

Difficulty should reflect the reasoning required from the learner rather than only surface parameters such as operator lists, maximum values, equation count, or variable count. Four concerns should eventually be explicit: the educational model, the generation model, the quality policy, and the calibration experience used to discover and refine preferences.

The desired output is not precise enough to encode directly. A vibe-check loop using concrete generated examples is part of product discovery rather than merely final QA. A promising evaluation artifact is an equation observatory or gallery that presents stable seeded samples, reveals solutions and diagnostics on demand, supports simple judgments or reason tags, and enables pairwise comparison between exercises or difficulty levels.

A promising engine hypothesis is a hybrid of learning-objective or solving-plan archetypes, constructive solution-first generation, objective feature measurement, hard validation, and scoring or rejection to preserve difficulty and variety. This is an idea to test, not a selected architecture.

The baseline analysis, educational domain modeling, and observatory prototype may need to be combined, separated, or sequenced differently. Their boundaries and dependencies must be clarified before turning them into implementation-shaped work.

## Decisions so far

- This product problem is large and uncertain enough to require a persistent Wayfinder map across sessions and context compactions.
- Discovery must precede a production generator rewrite.
- User judgment against concrete samples is necessary because the desired quality and progression cannot yet be specified confidently in the abstract.
- Educational difficulty must account for solving structure and learner effort, not merely numeric ranges and permitted operators.
- The map must preserve unresolved uncertainty rather than prematurely converting every suspected area into a backlog item.

## Candidate frontier for charting

These are candidate product questions, not yet canonical Wayfinder tickets:

1. **Characterize the current output** — What does each configured difficulty actually produce across a representative sample, and which measurable structures correlate with trivial or poor exercises?
2. **Define educational difficulty** — What learner actions, concepts, and reasoning steps should distinguish successive levels?
3. **Choose the first evidence loop** — Should baseline analysis, educational modeling, and the first observatory prototype be separate investigations, a combined prototype-led investigation, or another sequence?
4. **Define the smallest useful calibration experience** — What concrete sample-review interaction will let the user express why exercises feel trivial, appropriate, awkward, repetitive, or too difficult?

## Not yet specified

- The canonical educational vocabulary and difficulty dimensions
- The intended progression across named levels
- How solving steps or structural complexity should be represented and measured
- Whether a difficulty should be a strict band, a probability distribution, or both
- The balance between templates, constructive solving plans, and generate-score-reject strategies
- The configuration schema and compatibility policy
- Variety, repetition, and anti-triviality policies
- Golden examples, property tests, statistical distribution tests, and subjective review cadence
- Migration, rollout, observability, and fallback behavior
- The final boundary between the Wayfinder map and implementation planning or execution

## Out of scope during initial charting

- Rewriting the production generator before the destination and frontier are settled
- Treating the proposed observatory or hybrid generator as an approved design
- Modifying or deploying infrastructure

## Continuation protocol

1. Read this product artifact at the start of equation-generation wayfinding sessions.
2. Do not load workflow-adoption notes unless the session is explicitly about workflow adoption.
3. Treat candidate frontier items and architectural hypotheses as proposals, not approved decisions.
4. After tracker setup, create exactly one canonical Wayfinder map and link this bootstrap artifact as its starting context.
5. Keep the canonical map concise and store detailed resolutions in their named tickets.
