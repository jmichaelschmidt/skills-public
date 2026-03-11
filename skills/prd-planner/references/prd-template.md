# PRD Template

Copy and adapt this template for new planning documents.

---

# [Feature/Project Name] Implementation Plan

## Objective

[1-2 sentence description of what this plan accomplishes and why it matters]

## Definition of Done

[Describe the end state in present tense as if it's already complete. This is the goal we're working backwards from.]

- Users can [capability]
- System shows [behavior]
- Tests verify [criteria]
- Documentation reflects [changes]

### Working Backwards

From the done state, what's the last thing that needs to happen?
→ [Final step]
  ← What must exist for that?
    → [Prerequisite]
      ← What must exist for that?
        → [Earlier prerequisite]

---

## Risk Assessment

### Blast Radius

| Dimension | Assessment |
|-----------|------------|
| **Files touched** | [count] files across [count] services |
| **Services affected** | [list services] |
| **Data at risk** | [tables/records that could be corrupted] |
| **User-facing impact** | [what users would see if this fails] |
| **Rollback complexity** | Easy / Medium / Hard |

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [What could go wrong] | Low/Med/High | Low/Med/High | [How to prevent or recover] |
| [Another risk] | Low/Med/High | Low/Med/High | [Mitigation] |

### Rollback Plan

If issues arise after deployment:
1. [Step to revert change 1]
2. [Step to revert change 2]
3. [Verification after rollback]

---

## Execution Contract

### Implementation Home

- Repository root: `[absolute/path/to/repo]`
- Working directory for execution: `[absolute/path]`

### Branch Strategy

- Base branch: `[main|trunk|other]`
- Feature branch: `[codex/feature-name]`
- Branch creation required before edits: Yes / No
- Execution allowed on `main`: Yes / No

### Repo Preconditions

- Refresh required before branching: Yes / No
- If behind upstream: `[fetch/pull/rebase/stop-and-ask]`
- Dirty worktree policy: `[allowed/disallowed/allowed only for unrelated files]`

### Execution Environment

- Primary runtime: `[Codex app | CLI | Claude Code | OpenClaw | other]`
- Subagents expected: Yes / No
- Special tooling assumptions: `[tooling or runtime prerequisites]`

### Secrets / Config Preconditions

- Required env vars: `[VAR_1, VAR_2]`
- Required secret sources: `[Infisical path, local file, etc.]`
- Required setup checks: `[command or validation step]`

### Operator Safety Rules

- `[What should cause execution to stop and ask instead of proceeding]`

### First Command

- `[The exact first operational step the executor should take]`

---

## Current State Snapshot

[Describe what exists today and the pain points being addressed]

- `path/to/relevant/file.py:line` - [what it does currently]
- `path/to/another/file.py:line` - [current behavior]
- **Pain points**:
  - [Issue 1]
  - [Issue 2]

---

## Key Questions

[List questions that need answers before or during implementation]

1. **[Question]?** [Answer or "TBD - decide in Thread N"]
2. **[Question]?** [Answer]

---

## Architecture Decisions

### [Decision Area 1]

**Pattern**: [Chosen approach]
- [Explanation of pattern]
- [How it will be implemented]

**Benefits**:
- [Benefit 1]
- [Benefit 2]

### [Decision Area 2]

**Choice**: [Option selected]
- **Option A**: [Description] ✅ SELECTED
- **Option B**: [Description]
- **Rationale**: [Why Option A was chosen]

---

## Shared Resources for All Threads

[List files and resources that multiple threads will reference]

- Repository root: `[path]`
- Key config: `[path/to/config.yaml]`
- Database models: `[path/to/models.py]`
- Tests: `[path/to/tests/]`
- Documentation: `[path/to/docs/]`

## Optional Execution Manifest

Emit this only when the plan has enough coordination overhead to justify it.

- Path: `[same-directory]/[plan-name].execution-manifest.json`
- Template: `references/execution-manifest-template.json`
- Purpose: compact machine-readable routing for `prd-executor`
- Rule: the PRD is still the source of truth; the manifest is an execution aid

---

## Sequential Thread Plan

---

### Thread P0 — Execution Preflight — Reasoning Effort: low

- **Purpose**: Verify repo, branch, freshness, runtime, and secrets/config before any code changes.
- **Claude hint**: Haiku or Sonnet
- **OpenAI hint**: GPT-5.4 low
- **Ownership hint**: orchestrator
- **Actions**:
  - Confirm implementation repo path exists and is correct
    - *Verify*: `git rev-parse --show-toplevel` matches `Implementation Home`
  - Confirm branch policy before edits
    - *Verify*: current branch and branch creation state match `Branch Strategy`
  - Confirm repo freshness requirement
    - *Verify*: refresh step is complete if the execution contract requires it
  - Confirm required secrets/config are present
    - *Verify*: setup check or env validation passes
  - Record the starting execution state
    - *Verify*: PRD or ledger notes starting branch, repo state, and setup status
- **Reference material**:
  - `[repo path or setup doc]`
- **Deliverables**: preflight log and go/no-go decision
- **Output artifact**: `[optional ledger entry or setup report]`
- **Reasoning effort**: low

---

### Thread 0 — Investigation — Reasoning Effort: medium-high

> **Include this thread when**: Bug without clear cause, performance issue without profiling, "it's broken" without specifics, or feature that might already exist.

- **Purpose**: Gather information and document findings. DO NOT fix anything.
- **Actions**:
  - Reproduce the issue (or document why it can't be reproduced)
    - *Verify*: Issue observed with specific steps
  - Read relevant logs, trace code paths
    - *Verify*: Documented which files/functions are involved
  - Identify root cause or narrow down candidates
    - *Verify*: Can explain why the problem occurs
  - Document findings in investigation report
    - *Verify*: Report answers: what, where, why, how to fix
- **Reference material**: [logs, error messages, user reports]
- **Deliverables**: Investigation report with:
  - Steps to reproduce (if possible)
  - Root cause (confirmed or candidates)
  - Recommended fix approach
  - Files that will need changes
- **Claude hint**: Sonnet or Opus
- **OpenAI hint**: GPT-5.4 high
- **Reasoning effort**: medium-high
- **Output feeds**: Thread 1 design decisions

**Important**: Thread 0 produces a REPORT, not code. Implementation starts in Thread 1.

---

### Thread 1 — [Descriptive Name] — Reasoning Effort: [level]

- **Purpose**: [One sentence goal]
- **Claude hint**: [Haiku/Sonnet/Opus or N/A]
- **OpenAI hint**: [GPT-5.4 low/medium/high or strongest available model]
- **Ownership hint**: orchestrator | worker | explorer
- **Actions**:
  - [Specific action 1]
    - *Verify*: [How to check it worked - command, query, or observation]
  - [Specific action 2]
    - *Verify*: [Check]
  - [Specific action 3]
    - *Verify*: [Check]
- **Reference material**:
  - `path/to/file1.py:1` - [why to read it]
  - `path/to/file2.py:50-100` - [relevant section]
- **Deliverables**: [What gets created/modified]
- **Output artifact**: [Optional file/artifact path for execution tracking]
- **Reasoning effort**: [level]

---

### Thread 2 — [Descriptive Name] — Reasoning Effort: [level]

- **Purpose**: [One sentence goal]
- **Depends on**: Thread 1 (if applicable)
- **Claude hint**: [Haiku/Sonnet/Opus or N/A]
- **OpenAI hint**: [GPT-5.4 low/medium/high or strongest available model]
- **Ownership hint**: orchestrator | worker | explorer
- **Actions**:
  - [Specific action 1]
    - *Verify*: [Check]
  - [Specific action 2]
    - *Verify*: [Check]
- **Reference material**:
  - `path/to/file.py:1`
- **Key Decision**: [If a choice must be made]
  - **Option A**: [Description] ✅ RECOMMENDED
  - **Option B**: [Description]
  - **Recommendation**: [Reasoning]
- **Deliverables**: [Outputs]
- **Output artifact**: [Optional file/artifact path for execution tracking]
- **Reasoning effort**: [level]

---

### Thread N — [Descriptive Name] — Reasoning Effort: [level]

[Continue pattern for remaining threads...]

---

## Migration Notes

### Backward Compatibility

- [How existing data/behavior is preserved]
- [Transition strategy]

### Data Integrity

- [What remains unchanged]
- [What transforms and how]

---

## Acceptance Criteria

- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Testable criterion 3]
- [ ] [End-to-end flow works: action → result]

---

## How to Execute Threads

1. Read this PRD fully before starting any thread
2. Complete `Thread P0 — Execution Preflight` before any repo-changing implementation work
3. Execute ONE thread per conversation
4. Start by stating: "Executing Thread N: [Name]"
5. Read all reference material listed for the thread
6. For each action:
   a. Perform the action
   b. Run the verify step immediately
   c. If verify fails, STOP and troubleshoot before continuing
7. Update this PRD with completion log (see format below)
8. End by stating: "Thread N complete. Next: Thread N+1"

## Delegation Visibility Rules

- Whenever you spawn a subagent, announce it in commentary with the thread number, agent type, and owned files or output artifact.
- When a subagent returns, announce that too and summarize what it produced.
- If no subagent is used for a thread, say that the orchestrator is handling it locally.

### Completion Log Format

Add this section below the thread when completed:

```
**Completion Log — Thread N** ✅ COMPLETED (YYYY-MM-DD)
- ✅ [What was done - specific files, line numbers]
- ✅ [Changes made with details]
- ✅ [All verify steps passed]
- ✅ [Tests run and results]
- **Notes**: [Deviations from plan, decisions made, discoveries]
- **Next**: Thread N+1
```

---

## Completion Checklist

| Thread | Name | Status | Date |
|--------|------|--------|------|
| 0 | Investigation | ⬜ PENDING | - |
| 1 | [Name] | ⬜ PENDING | - |
| 2 | [Name] | ⬜ PENDING | - |
| N | [Name] | ⬜ PENDING | - |

---

## Open Decisions

[Document decisions that need to be made during implementation]

- [Decision 1]? [Options and current thinking]
- [Decision 2]? [Options]

---

## Optional Execution Manifest Template

When needed, emit a sibling file like:

```json
{
  "plan_path": "docs/plans/example-plan.md",
  "plan_version": "2026-03-08",
  "execution_mode": "sequential",
  "threads": [
    {
      "id": "thread-1",
      "label": "Thread 1",
      "name": "Example thread",
      "status": "PENDING",
      "reasoning_effort": "medium",
      "owner_hint": "worker",
      "depends_on": [],
      "reference_material": [
        "path/to/file.py:1"
      ],
      "deliverables": [
        "docs/context/example-output.md"
      ],
      "output_artifact": "docs/context/example-output.md",
      "verify": [
        "pytest path/to/test.py"
      ]
    }
  ]
}
```

Document owner: **[Name/TBD]**. Update this plan as tasks progress.
