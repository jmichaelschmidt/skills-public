# Design Principles

This starter-pack is opinionated. The opinions are not about personality or agent theatrics. They are about making delegated work easier to scope, safer to validate, and easier to resume.

## 1. Roles Are Capability Budgets

The six core roles exist because they map to different kinds of work, not because they sound nice:

- `planner` scopes and sequences
- `implementer` changes the code or docs
- `reviewer` looks for correctness and regression risk
- `security-reviewer` checks trust boundaries and sensitive surfaces
- `docs-handoff` compresses context into durable artifacts
- `repo-hygiene` checks repo state before and after work

The important design choice is not the labels. It is the separation of jobs and outputs.

## 2. Serial By Default Beats Faux Swarms

Most repo work is not helped by uncontrolled parallelism. It is helped by:

- smaller contexts
- explicit handoffs
- one active write owner
- optional parallel sidecars for review, audit, research, or synthesis

The starter-pack uses delegated micro-threads for context control, not for theater.

## 3. Durable Artifacts Beat Chat Memory

Plans, validation commands, research notes, and closeout summaries should survive the thread that produced them. That is why the starter-pack materializes repo-local docs and validation tooling instead of keeping everything inside ephemeral prompt history.

## 4. Machine Install And Repo Refresh Are Different

Installing a skill onto a machine makes the skill available. It does not automatically make a repo conform to that skill.

For the starter-pack:

- machine install makes the shared package available to Claude and Codex
- repo refresh copies the managed files into a target repo
- repo validation proves the target repo still matches canonical templates

That split is deliberate. It keeps the shared source of truth centralized while still letting repos own their local overlays.

## 5. Validation Closes Work

Implementation is not the finish line. The finish line is:

- the requested artifact exists
- validation ran
- the closeout is legible to another operator

This is why the starter-pack ships repo-local validation helpers and why `planner` is expected to name validation commands up front.

## 6. Skills Are Better Than Role Proliferation

When a pattern is reusable across roles, it should usually be a skill rather than a new global role.

That is why research synthesis and artifact-heavy file handling became optional skills:

- many roles may need them
- they represent workflow patterns, not permanent team seats
- they keep the core starter-pack small

## 7. Context, Done, And Constraints Must Be Explicit

The most valuable briefing habit is the simplest one:

- say what done looks like
- say what context matters
- say what constraints matter

This cuts down failed delegation more than almost any prompt flourish.

## 8. Public Templates Should Stay Generic

A reusable starter-pack should not assume:

- one private repo topology
- one operator’s home directory
- one product name
- one migration story

The public version publishes the generic core only. Repo-specific compatibility layers belong somewhere else.
