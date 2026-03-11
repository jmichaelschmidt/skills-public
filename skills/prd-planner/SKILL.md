---
name: prd-planner
description: Generate structured PRD (Product Requirements Document) planning documents optimized for AI-assisted development. Creates discrete, single-conversation tasks with reasoning level estimates to optimize token usage and model selection. Use when users want to plan implementation work, break down features into tasks, create implementation roadmaps, or structure development work for AI pair programming. Triggers on phrases like "create a PRD", "plan this feature", "break down this task", "implementation plan", "create threads for", or "help me plan".
---

# PRD Planner

Generate structured planning documents that optimize AI-assisted development by breaking work into discrete, context-efficient conversation threads.

## Core Principles

1. **Thread Isolation** - Each task is scoped for a single conversation to minimize context carryover
2. **Reasoning Economy** - Match model capability to task complexity (don't waste high reasoning on low tasks)
3. **Self-Contained Context** - Every thread has all information needed to execute without external reference
4. **Progressive Tracking** - Checklist format enables clear progress visibility and serves as context for subsequent threads
5. **Goal-Backwards Design** - Start from the end state and work backward to determine thread sequence

## PRD Creation Process

1. **Discuss phase (if needed)** - Clarify requirements before planning (see below)
2. **Define done** - Write the end state before any threads
3. **Work backwards** - Identify dependencies from goal to starting point
4. **Analyze complexity** - Identify discrete work units and assign reasoning levels
5. **Define the execution contract** - Document repo path, branch strategy, refresh policy, runtime expectations, and secret/config prerequisites
6. **Generate the PRD** - Use the template structure from [references/prd-template.md](references/prd-template.md)
7. **Assess risk** - Document blast radius and rollback plan
8. **Validate completeness** - Ensure each thread is self-contained
9. **Optionally emit an execution manifest** - For plans with 3+ threads, dependencies, or intended subagent execution, also produce a compact manifest using [references/execution-manifest-template.json](references/execution-manifest-template.json)

---

## Discuss Phase (Pre-Planning)

Before creating threads, run a discuss phase when ANY of these are true:
- Requirements are ambiguous or came from someone other than the executor
- Multiple valid approaches exist with significant tradeoffs
- The change touches unfamiliar parts of the codebase
- Novel problem domain you haven't solved before
- High-stakes change (production data, auth, payments)

### When to Skip Discuss Phase

Skip directly to planning when:
- User says "skip discuss" or "I know what I want"
- Requirements are crystal clear with specific acceptance criteria
- Following an established pattern with no decisions to make
- Small scope (1-2 threads, single service)

### Discuss Phase Questions

Ask these to surface assumptions:

1. **Success definition**: "What does done look like? How will you know this worked?"
2. **Constraints**: "Are there approaches that are off the table? Performance/cost/timeline limits?"
3. **Stakeholders**: "Who else touches this code or cares about this change?"
4. **Risk tolerance**: "What's the worst thing that could happen? How bad would that be?"
5. **Prior art**: "Has something similar been tried before? What happened?"

### Discuss Phase Output

```markdown
## Discuss Phase Summary

**Assumptions confirmed**:
- [What the user validated]

**Assumptions made** (user didn't specify):
- [What you're assuming - flag for review]

**Risks identified**:
- [What could go wrong]

**Approach selected**:
- [Brief description of chosen direction and why]

**Open questions** (to resolve during execution):
- [What still needs answers]
```

---

## Debug-First Pattern (Thread 0)

For bugs, performance issues, or unclear problems, insert an investigation thread BEFORE implementation threads.

### When to Use Thread 0

- Bug reports without clear reproduction steps
- Performance issues without profiling data
- Errors in production logs you haven't traced
- Feature requests that might already be partially implemented
- "It's broken" without specifics

### Thread 0 Template

```markdown
### Thread 0 — Investigation — Reasoning Effort: medium-high

- **Purpose**: Gather information and document findings. DO NOT fix anything.
- **Actions**:
  - Reproduce the issue (or document why it can't be reproduced)
  - Read relevant logs, trace code paths
  - Identify root cause or narrow down candidates
  - Document what you found
- **Reference material**: [logs, error messages, user reports]
- **Deliverables**: Investigation report with:
  - Steps to reproduce (if possible)
  - Root cause (confirmed or candidates)
  - Recommended fix approach
  - Files that will need changes
- **Reasoning effort**: Medium-High (Sonnet or Opus)
- **Output feeds**: Thread 1 design decisions

**Important**: Thread 0 produces a REPORT, not code. Implementation starts in Thread 1.
```

---

## Execution Contract (Required For Runnable PRDs)

If a PRD might be executed in a fresh thread, by `prd-executor`, or from a different runtime than the planner session, it MUST include an explicit execution contract.

### Required Execution Contract Fields

Include these sections in the PRD:

- **Implementation Home** - exact repo path or workspace root where changes should happen
- **Branch Strategy** - target branch name, whether to create a new branch before edits, and whether execution is allowed on `main`
- **Repo Preconditions** - whether the executor must refresh/fetch/pull first, what to do if the repo is behind upstream, and dirty-worktree policy
- **Execution Environment** - whether the plan expects Codex app, CLI, Claude Code, OpenClaw, or another runtime; note if subagents are expected
- **Secrets / Config Preconditions** - required env vars, Infisical paths, setup checks, or local files that must exist before execution
- **Operator Safety Rules** - what should cause execution to stop and ask instead of proceeding
- **First Command** - the first operational step the executor should take before starting implementation threads

### Execution Preflight Pattern

For any repo-changing plan, add a dedicated preflight step before implementation starts:

```markdown
### Thread P0 — Execution Preflight — Reasoning Effort: low

- **Purpose**: Verify repo, branch, freshness, runtime, and secrets/config before any code changes.
- **Actions**:
  - Confirm implementation repo path exists and is the correct repo
    - *Verify*: `git rev-parse --show-toplevel` matches the PRD
  - Confirm branch/base policy
    - *Verify*: current branch and branch creation state match the PRD contract
  - Confirm repo freshness requirement
    - *Verify*: refresh/pull/fetch step completed if required by the plan
  - Confirm required secrets/config are present
    - *Verify*: setup check or env validation passes
  - Record starting execution state in the ledger or PRD
    - *Verify*: starting branch, repo state, and prerequisites are written down
- **Deliverables**: Preflight log and go/no-go decision for implementation
- **Reasoning effort**: Low
```

If the execution contract is missing for a runnable plan, the planner should treat that as an incomplete PRD.

---

## Reasoning Level Guidelines

Assign reasoning levels based on task characteristics. See [references/reasoning-levels.md](references/reasoning-levels.md) for detailed guidance.

`Reasoning effort` is the canonical planning field. Vendor model names are only hints for the environment that will execute the thread.

| Level | Characteristics | Claude Hint | OpenAI Hint |
|-------|-----------------|-------------|-------------|
| **Minimal** | Procedural, well-documented, single-file | Haiku | GPT-5.4 low |
| **Low** | Clear patterns, limited decisions, 2-3 files | Haiku or Sonnet | GPT-5.4 low |
| **Medium** | Code comprehension, refactoring, integration | Sonnet | GPT-5.4 medium |
| **Medium-High** | Architecture decisions, test orchestration, investigation | Sonnet or Opus | GPT-5.4 high |
| **High** | Novel problems, system design, complex debugging | Opus | GPT-5.4 high |

---

## Thread Structure Requirements

Every thread in the PRD MUST include:

1. **Thread identifier** - Numbered for tracking (e.g., "Thread 3" or "Step 15")
2. **Purpose statement** - Clear goal in one sentence
3. **Actions with inline verification** - Specific work with verify steps (see below)
4. **Reference material** - File paths to read first (use `file.py:1` format for line hints)
5. **Deliverables** - Expected outputs
6. **Reasoning effort** - Vendor-neutral level

For executable plans, the PRD as a whole MUST also include the execution contract above. A plan is not self-contained if the executor still has to guess the repo path, branch policy, refresh policy, or required setup.

### Inline Verification (New Pattern)

Instead of listing validation targets at the end, embed verification after each action:

```markdown
- **Actions**:
  - Add `platform` column to posts table
    - *Verify*: `\d posts` shows platform column with TEXT type
  - Update Post ORM model with platform field
    - *Verify*: `python -c "from shared.db.models import Post; print(Post.platform)"`
  - Create Alembic migration
    - *Verify*: `alembic history` shows new migration at head
  - Run migration on dev database
    - *Verify*: `alembic current` matches head revision
```

**Why inline verify matters**: If step 2's verify fails, you stop before doing steps 3-4. Catches problems earlier.

### Optional Thread Fields (include when applicable)

- **Key decisions** - Choices with options and recommendations
- **Acceptance criteria** - Testable success metrics
- **Dependencies** - Prerequisite threads
- **Blocks** - Threads that depend on this one
- **Claude hint** - Suggested Claude model family for this thread
- **OpenAI hint** - Suggested OpenAI reasoning level or model tier for this thread
- **Ownership hint** - Suggested owner such as orchestrator, `worker`, or `explorer`
- **Output artifact** - File or artifact the thread should produce if execution tracking will be automated

---

## Optional Execution Manifest

When the plan is likely to be executed by `prd-executor`, emit a compact JSON manifest next to the PRD.

Use a manifest when any of these are true:

- 3 or more threads
- explicit dependencies between threads
- planned subagent delegation
- wave-based execution
- non-trivial verification or rollout

Do not emit a manifest for tiny 1-2 thread plans unless the user asks for it.

The PRD remains the human-readable source of truth. The manifest is only a machine-friendly execution view.

When the PRD has an execution contract, the manifest should carry the same implementation home and branch intent at a compact level so `prd-executor` can validate preflight consistently.

Use [references/execution-manifest-template.json](references/execution-manifest-template.json).

---

## PRD Document Structure

Use this structure for all PRDs. See [references/prd-template.md](references/prd-template.md) for full template.

```markdown
# [Feature/Project Name] Plan

## Objective
[1-2 sentence goal]

## Definition of Done
[End state written in present tense, as if already complete]

## Risk Assessment
[Blast radius, rollback complexity - see template]

## Execution Contract
[Repo path, branch strategy, refresh policy, runtime assumptions, secret/config prerequisites, safety rules, first command]

## Current State Snapshot
[What exists today, pain points]

## Architecture Decisions
[Key choices made, with rationale]

## Sequential Thread Plan

### Thread P0 — Execution Preflight — Reasoning Effort: low
[Required for repo-changing plans]

### Thread 0 — Investigation — Reasoning Effort: medium-high
[If needed - for bugs/unclear problems]

### Thread 1 — [Name] — Reasoning Effort: [level]
- **Purpose**: [goal]
- **Actions**:
  - [action 1]
    - *Verify*: [how to check it worked]
  - [action 2]
    - *Verify*: [check]
- **Reference material**: [file paths]
- **Deliverables**: [outputs]
- **Claude hint**: [Haiku/Sonnet/Opus or N/A]
- **OpenAI hint**: [GPT-5.4 low/medium/high or strongest available model]
- **Reasoning effort**: [level]

### Thread 2 — [Name] — Reasoning Effort: [level]
[...]

## Acceptance Criteria
[Overall success metrics]

## Completion Checklist
Thread 0 — Investigation — [ ] PENDING (if applicable)
Thread 1 — [Name] — [ ] PENDING
Thread 2 — [Name] — [ ] PENDING
[...]
```

When emitting a manifest, store it beside the PRD using a matching basename, for example:

- `docs/plans/feature-x-plan.md`
- `docs/plans/feature-x-plan.execution-manifest.json`

---

## Completion Log Format

When a thread is completed, the PRD should be updated with implementation details:

```markdown
### Thread 3 — [Name] — Reasoning Effort: medium

[thread details...]

**Completion Log — Thread 3** ✅ COMPLETED (2025-01-15)
- ✅ [What was implemented with specifics]
- ✅ [Files modified with line references]
- ✅ [Tests added/passed]
- ✅ [All verify steps passed]
- **Notes**: [Any deviations, decisions made, follow-ups identified]
- **Next**: Thread 4
```

---

Include the preflight completion log when Thread P0 is used so later executors know the starting repo/branch state.

---

## Instructing the Executor

Include these instructions in the PRD so that executing agents know how to work:

```markdown
## How to Execute Threads

1. Read this PRD fully before starting
2. Execute ONE thread per conversation
3. Start your thread by stating: "Executing Thread N: [Name]"
4. Read all reference material listed for the thread
5. For each action:
   a. Perform the action
   b. Run the verify step immediately
   c. If verify fails, stop and troubleshoot before continuing
6. Update the PRD with completion log before ending
7. State: "Thread N complete. Next: Thread N+1"
```

For runnable plans, also include:

```markdown
## Execution Preflight Rules

- Do not start implementation until Thread P0 or equivalent preflight is complete.
- If the repo/branch/refresh policy is missing, patch the PRD before proceeding.
- Never assume execution on `main` is allowed unless the PRD says so explicitly.
- If required secrets/config are missing, stop and resolve that before spawning implementation subagents.
```

For plans intended for `prd-executor`, also include a delegation visibility block so the user can tell from terminal commentary when work is actually being delegated:

```markdown
## Delegation Visibility Rules

- Whenever you spawn a subagent, announce it in commentary with the thread number, agent type, and owned files or output artifact.
- When a subagent returns, announce that too and summarize what it produced.
- If no subagent is used for a thread, say that the orchestrator is handling it locally.
```

---

## Key Patterns from Effective PRDs

### Pattern: Decision Documentation

When threads involve choices, document options with recommendations:

```markdown
**Key Decision**: Sequence numbering
- **Option A**: Restart per platform (LinkedIn_1, LinkedIn_2; YouTube_1, YouTube_2) ✅ RECOMMENDED
- **Option B**: Continuous across platforms (LinkedIn_1, LinkedIn_2; YouTube_3, YouTube_4)
- **Rationale**: Option A keeps each platform's batch self-contained
```

### Pattern: Migration Safety

For changes affecting production systems:

```markdown
## Migration Notes

### Backward Compatibility
- Existing records: [How handled]
- Transition period: [Strategy]

### Rollback Plan
1. [Step to revert]
2. [Verification after rollback]
```

### Pattern: Thread Dependencies

When threads must be executed in order:

```markdown
### Thread 5 — Database Migration — Reasoning Effort: low
- **Depends on**: Thread 4 (schema design must be finalized)
- **Blocks**: Threads 6, 7, 8 (all require new schema)
```

---

## Self-Contained Thread Checklist

Before finalizing a thread, verify:

- [ ] Can someone start a fresh conversation and execute this thread with ONLY the PRD?
- [ ] Are all file paths specified (not "the config file" but `config/settings.py:45`)?
- [ ] Is the reasoning level justified by the task complexity?
- [ ] Does each action have an inline verify step?
- [ ] Does the thread avoid scope creep (one focused outcome)?

---

## Example PRDs

See [references/examples.md](references/examples.md) for excerpts from production PRDs demonstrating these patterns.
