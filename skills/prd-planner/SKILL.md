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
5. **Generate the PRD** - Use the template structure from [references/prd-template.md](references/prd-template.md)
6. **Assess risk** - Document blast radius and rollback plan
7. **Validate completeness** - Ensure each thread is self-contained
8. **Optionally emit an execution manifest** - For plans with 3+ threads, dependencies, or intended subagent execution, also produce a compact manifest using [references/execution-manifest-template.json](references/execution-manifest-template.json)

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

### Context Volume Tag

In addition to reasoning level, every thread should be tagged with its **context volume** -- the estimated total size of reference material the executing agent must read. This drives model selection during execution.

| Tag | Meaning | Execution Implication |
|-----|---------|----------------------|
| **Light** (under 50KB) | Reads a few focused files | Any model handles this |
| **Heavy** (50-100KB) | Reads several reference docs or upstream deliverables | Prefer larger context model |
| **Synthesis** (over 100KB or reads all upstream deliverables) | Must hold entire prior work in context to integrate | **Require largest context model or execute in orchestrator session** |

**When to apply the Synthesis tag:** A thread is a synthesis thread if it reads 4+ upstream deliverables, integrates or reconciles prior work, or is the capstone/final thread in a multi-thread plan. Always flag these explicitly -- they are the most likely to fail when delegated to a standard-context agent.

Format in the PRD: append the context tag after reasoning effort, e.g.:
- `Reasoning effort: Medium (Sonnet) | Context: Light`
- `Reasoning effort: High (Opus) | Context: Synthesis`

---

## Thread Structure Requirements

Every thread in the PRD MUST include:

1. **Thread identifier** - Numbered for tracking (e.g., "Thread 3" or "Step 15")
2. **Purpose statement** - Clear goal in one sentence
3. **Actions with inline verification** - Specific work with verify steps (see below)
4. **Reference material** - File paths to read first (use `file.py:1` format for line hints)
5. **Deliverables** - Expected outputs
6. **Reasoning effort** - Vendor-neutral level with context volume tag

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

## Current State Snapshot
[What exists today, pain points]

## Architecture Decisions
[Key choices made, with rationale]

## Sequential Thread Plan

### Thread 0 — Investigation — Reasoning Effort: medium-high
[If needed - for bugs/unclear problems]

### Thread 1 — [Name] — Reasoning Effort: [level] | Context: [Light/Heavy/Synthesis]
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
- **Reasoning effort**: [level] | **Context volume**: [Light/Heavy/Synthesis]

### Thread 2 — [Name] — Reasoning Effort: [level] | Context: [Light/Heavy/Synthesis]
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
