---
name: prd-executor
description: Execute an existing PRD or implementation plan by acting as the orchestrator. Reads the plan, determines runnable threads, spawns bounded subagents when appropriate, tracks status, integrates results, and verifies completion. Use when users say "execute this PRD", "run this plan", "orchestrate these threads", "delegate this implementation plan", or "work through this PRD".
---

# PRD Executor

Execute an existing PRD as the orchestrator. This skill assumes the plan already exists and is written as discrete threads with dependencies, verification steps, and reasoning levels.

Use this skill after `prd-planner`, or whenever the user already has a thread-based plan.

## Core Contract

The main session is the orchestrator. It owns:

- reading the full plan before execution
- deciding which threads are runnable now
- choosing whether work stays local or goes to a subagent
- integrating results from subagents
- running cross-thread verification and rollout checks
- updating execution state so future threads do not lose context

Subagents are disposable workers, not permanent personas. Specialization comes from thread scope, file ownership, reference material, and risk level.

## When To Use

Use `prd-executor` when the user wants to:

- execute a PRD or implementation plan
- assign threads to subagents
- run work in waves while preserving dependencies
- track thread status and outputs
- minimize context rot by isolating work per thread

If the plan does not exist yet, use `prd-planner` first.

## Execution Workflow

### 1. Read And Normalize The Plan

Read the PRD fully. Extract:

- objective and definition of done
- thread IDs and names
- dependencies
- reasoning effort
- reference material
- deliverables
- verification steps

If the PRD is missing dependency or verification detail, repair the execution view before spawning agents. Do not delegate from a vague plan.

If a sibling execution manifest exists, use it as a compact routing aid for status, dependencies, owner hints, and output artifacts. The PRD still wins if the two disagree.

For complex plans, create a compact execution ledger using [references/execution-ledger-template.md](references/execution-ledger-template.md).

### 2. Decide Execution Mode

Use one of three modes:

- **Sequential**: default for risky or tightly coupled plans
- **Wave-based**: when multiple threads are independent and have disjoint ownership
- **Hybrid**: sequential backbone with parallel side threads

Prefer the smallest amount of parallelism that still improves throughput.

### 3. Map Threads To Execution Shape

Use this default routing:

| Thread type | Recommended owner |
|-------------|-------------------|
| Investigation / read-only tracing | `explorer` subagent or local if urgent |
| Minimal / low implementation | `worker` subagent |
| Medium implementation | `worker` subagent with explicit file ownership |
| Medium-high cross-cutting change | usually one `worker`, reviewed by orchestrator before integration |
| High-risk security / architecture / rollout | orchestrator-led, with optional `explorer` sidecars |

Do not delegate the immediate blocking step if the orchestrator needs that result right away to keep moving.

### 4. Package Thread Context

Each subagent prompt must be self-contained. Include only:

- a short project/repo bootstrap
- the exact thread section
- dependencies already completed and their concrete outputs
- explicit file ownership
- expected deliverables
- required verification

Use [references/thread-prompt-template.md](references/thread-prompt-template.md) as the default shape.

If a manifest is present, include only the current thread's manifest entry plus the exact PRD thread section, not the full manifest.

### 5. Spawn, Review, Integrate

For each runnable thread:

1. Spawn at most one implementation subagent per write scope.
2. Let the subagent complete its bounded task.
3. Review the result before moving on.
4. Integrate any cross-thread changes in the main session.
5. Update the execution ledger and PRD checklist.

Do not allow multiple workers to edit the same files unless the overlap is trivial and intentional.

### 6. Verify At Two Levels

Every thread must pass:

- thread-level verification from the PRD
- plan-level verification against the Definition of Done

For security-sensitive, rollout, or production-impacting plans, add an orchestrator-owned verification pass even if a subagent already tested its own thread.

## Status Tracking

Track each thread as one of:

- `PENDING`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`

For each thread, record:

- owner
- dependency status
- output artifact or changed files
- verification result
- blockers or follow-ups

The ledger can live in a separate doc or as completion logs appended to the PRD. Keep it concise and current.

If a manifest exists, update its thread `status` values alongside the ledger or PRD completion log.

## GSD-Inspired Patterns To Adopt

These patterns from `gsd-build/get-shit-done` are worth adopting:

- **Operator loop**: one orchestrator decides the next wave after reviewing current results
- **Explicit state file**: do not rely on conversation memory for what is done or blocked
- **Verifier handoff**: for risky changes, have the orchestrator or a separate read-only pass validate the implementation
- **Fast path vs full path**: simple plans can run with minimal ceremony; risky plans need a ledger, review gates, and tighter prompts

Do not copy XML-heavy plan formats or build a command framework inside the skill. Reuse the existing markdown PRD format.

## Reasoning Effort Policy

Reasoning effort in the PRD is a routing hint, not a guarantee of a specific model in this interface.

Use it to decide:

- whether to delegate
- how much context to include
- how tight the file ownership should be
- how much review the orchestrator should perform
- **which model can handle the context volume** (see Context Volume below)

Default policy:

- **Minimal / Low**: delegate freely if ownership is clear
- **Medium**: delegate one bounded thread at a time
- **Medium-High**: delegate only with strong references and explicit deliverables
- **High**: keep the design and security decisions with the orchestrator

### Context Volume Assessment

Before spawning any subagent, estimate the total context the thread requires:

1. **Count reference material**: sum the size of all files the thread must read (upstream deliverables, source docs, specs)
2. **Add output space**: the agent needs room to write its deliverable after reading inputs

Apply these routing rules based on context volume:

| Context Volume | Routing |
|---|---|
| **Under 50KB** total input | Standard delegation -- any model handles this |
| **50-100KB** total input | Prefer Opus; Sonnet may work if output is short |
| **Over 100KB** total input | **Require Opus**, or keep the thread in the orchestrator session where context is already loaded |
| **Synthesis threads** (must read all upstream deliverables) | **Always Opus or orchestrator-local**. These threads are the most likely to fail on smaller context windows. |

### Identifying Synthesis Threads

A thread is a synthesis thread if any of these are true:

- Its reference material includes "all upstream thread deliverables" or lists 4+ prior thread outputs
- It is the final thread in the plan and its purpose is integration, reconciliation, or roadmap creation
- Its actions include "surface conflicts between upstream threads" or "synthesize all prior work"

Synthesis threads should be flagged in commentary before dispatch. If the orchestrator already has upstream context loaded from reviewing prior threads, keeping the synthesis local is often faster and more reliable than delegating.

## Execution Rules

- Read the full plan before starting any thread.
- Execute only runnable threads whose dependencies are satisfied.
- Keep prompts narrow. Do not dump the whole PRD into every subagent.
- Prefer `explorer` for read-only repo questions.
- Prefer `worker` for bounded implementation with disjoint ownership.
- Whenever a subagent is spawned, announce it in commentary with the thread number, agent type, and owned files or output artifact.
- When a subagent finishes, announce that and summarize what it produced before integrating.
- If the orchestrator keeps a thread local, say so explicitly in commentary.
- Review worker results before starting dependent threads.
- Update status after every completed thread or decision.
- If the plan becomes inaccurate, patch the plan or ledger before continuing.

## Typical Outputs

- updated PRD checklist or completion log
- updated execution manifest (if present)
- execution ledger
- thread-specific artifacts
- integrated code changes
- final verification summary

## References

- [references/execution-ledger-template.md](references/execution-ledger-template.md): compact state tracker for live execution
- [references/execution-manifest-template.json](references/execution-manifest-template.json): optional machine-readable routing view emitted by `prd-planner`
- [references/thread-prompt-template.md](references/thread-prompt-template.md): prompt shape for per-thread subagents
- [references/adoption-notes.md](references/adoption-notes.md): why this skill borrows some GSD patterns but stays markdown-first
