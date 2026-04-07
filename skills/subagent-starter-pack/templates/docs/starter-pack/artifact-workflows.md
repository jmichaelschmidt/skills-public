# Artifact Workflows

Purpose: describe an optional workspace contract for repos that have non-code, artifact-heavy work such as research packets, file organization, document assembly, or other input-to-output pipelines.

This reference is advisory, not mandatory.

## When To Use This Pattern

Use this pattern only when the work is primarily about handling inputs and producing durable artifacts.

Good fits:

- research request packets
- document or slide generation
- file organization and routing
- multi-source synthesis outputs

Poor fits:

- ordinary code implementation
- tightly coupled debugging
- repos that do not have a real artifact pipeline

## Suggested Layout

```text
<workspace>/
├── inbox/
├── processed/
├── outputs/
└── reference/
```

Recommended meanings:

- `inbox/`: new request packets or raw inputs waiting to be handled
- `processed/`: completed request packets or consumed inputs after handling
- `outputs/`: generated handoffs, reports, logs, or other deliverables
- `reference/`: read-only supporting material that should inform the work but not be rewritten

## Default Rules

- default to non-destructive behavior
- say explicitly when files should move rather than be deleted
- state the destination for all new artifacts
- produce a move log, organization log, or output inventory when the workflow rewrites or reorganizes many files
- flag unresolved or unclear items instead of silently dropping them

## Delegation Guidance

When using this pattern, the delegated brief should make these explicit:

- what "done" looks like
- which folders are inputs versus outputs
- whether files may be renamed or only moved
- whether the worker should create a summary or change log
- what should happen to unresolved items
