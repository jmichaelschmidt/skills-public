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

## PRD Creation Process

1. **Understand the scope** - Gather requirements, constraints, and success criteria
2. **Analyze complexity** - Identify discrete work units and their dependencies
3. **Assign reasoning levels** - Estimate cognitive load per task
4. **Generate the PRD** - Use the template structure from [references/prd-template.md](references/prd-template.md)
5. **Validate completeness** - Ensure each thread is self-contained

## Reasoning Level Guidelines

Assign reasoning levels based on task characteristics. See [references/reasoning-levels.md](references/reasoning-levels.md) for detailed guidance.

| Level | Characteristics | Model Recommendation |
|-------|-----------------|---------------------|
| **Minimal** | Procedural, well-documented, single-file | Haiku |
| **Low** | Clear patterns, limited decisions, 2-3 files | Haiku or Sonnet |
| **Medium** | Code comprehension, refactoring, integration | Sonnet |
| **Medium-High** | Architecture decisions, test orchestration | Sonnet or Opus |
| **High** | Novel problems, system design, complex debugging | Opus |

## Thread Structure Requirements

Every thread in the PRD MUST include:

1. **Thread identifier** - Numbered for tracking (e.g., "Thread 3" or "Step 15")
2. **Purpose statement** - Clear goal in one sentence
3. **Actions/Changes** - Specific work to perform
4. **Reference material** - File paths to read first (use `file.py:1` format for line hints)
5. **Validation targets** - How to verify completion
6. **Deliverables** - Expected outputs
7. **Reasoning effort** - Level with model recommendation

### Optional Thread Fields (include when applicable)

- **Key decisions** - Choices with options and recommendations
- **Acceptance criteria** - Testable success metrics
- **Dependencies** - Prerequisite threads
- **Migration notes** - Backward compatibility, rollback plans

## PRD Document Structure

Use this structure for all PRDs. See [references/prd-template.md](references/prd-template.md) for full template.

```markdown
# [Feature/Project Name] Plan

## Objective
[1-2 sentence goal]

## Current State Snapshot
[What exists today, pain points]

## Architecture Decisions
[Key choices made, with rationale]

## Sequential Thread Plan

### Thread 1 — [Name] — Reasoning Effort: [level]
- **Purpose**: [goal]
- **Actions**: [specific work]
- **Reference material**: [file paths]
- **Validation targets**: [how to verify]
- **Deliverables**: [outputs]
- **Reasoning effort**: [level] ([model] recommended)

### Thread 2 — [Name] — Reasoning Effort: [level]
[...]

## Acceptance Criteria
[Overall success metrics]

## Completion Checklist
Thread 1 — [Name] — [ ] PENDING / [x] COMPLETED (date)
Thread 2 — [Name] — [ ] PENDING
[...]
```

## Completion Log Format

When a thread is completed, the PRD should be updated with implementation details:

```markdown
### Thread 3 — [Name] — Reasoning Effort: medium

[thread details...]

**Completion Log — Thread 3** ✅ COMPLETED (2025-01-15)
- ✅ [What was implemented with specifics]
- ✅ [Files modified with line references]
- ✅ [Tests added/passed]
- ✅ [Validation performed]
- **Notes**: [Any deviations, decisions made, follow-ups identified]
- **Next**: Thread 4
```

## Instructing the Executor

Include these instructions in the PRD so that executing agents know how to work:

```markdown
## How to Execute Threads

1. Read this PRD fully before starting
2. Execute ONE thread per conversation
3. Start your thread by stating: "Executing Thread N: [Name]"
4. Read all reference material listed for the thread
5. Complete all actions and validation targets
6. Update the PRD with completion log before ending
7. State: "Thread N complete. Next: Thread N+1"
```

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

## Self-Contained Thread Checklist

Before finalizing a thread, verify:

- [ ] Can someone start a fresh conversation and execute this thread with ONLY the PRD?
- [ ] Are all file paths specified (not "the config file" but `config/settings.py:45`)?
- [ ] Is the reasoning level justified by the task complexity?
- [ ] Are validation targets specific and testable?
- [ ] Does the thread avoid scope creep (one focused outcome)?

## Example PRDs

See [references/examples.md](references/examples.md) for excerpts from production PRDs demonstrating these patterns.
