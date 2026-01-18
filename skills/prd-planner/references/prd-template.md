# PRD Template

Copy and adapt this template for new planning documents.

---

# [Feature/Project Name] Implementation Plan

## Objective

[1-2 sentence description of what this plan accomplishes and why it matters]

## Current State Snapshot

[Describe what exists today and the pain points being addressed]

- `path/to/relevant/file.py:line` - [what it does currently]
- `path/to/another/file.py:line` - [current behavior]
- **Pain points**:
  - [Issue 1]
  - [Issue 2]

## Key Questions

[List questions that need answers before or during implementation]

1. **[Question]?** [Answer or "TBD - decide in Thread N"]
2. **[Question]?** [Answer]

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

## Shared Resources for All Threads

[List files and resources that multiple threads will reference]

- Repository root: `[path]`
- Key config: `[path/to/config.yaml]`
- Database models: `[path/to/models.py]`
- Tests: `[path/to/tests/]`
- Documentation: `[path/to/docs/]`

## Sequential Thread Plan

---

### Thread 1 — [Descriptive Name] — Reasoning Effort: [level]

- **Purpose**: [One sentence goal]
- **Actions**:
  - [Specific action 1]
  - [Specific action 2]
  - [Specific action 3]
- **Reference material**:
  - `path/to/file1.py:1` - [why to read it]
  - `path/to/file2.py:50-100` - [relevant section]
- **Validation targets**:
  - [How to verify action 1 worked]
  - [How to verify action 2 worked]
- **Deliverables**: [What gets created/modified]
- **Reasoning effort**: [level] ([Haiku/Sonnet/Opus] recommended)

---

### Thread 2 — [Descriptive Name] — Reasoning Effort: [level]

- **Purpose**: [One sentence goal]
- **Depends on**: Thread 1 (if applicable)
- **Actions**:
  - [Specific action 1]
  - [Specific action 2]
- **Reference material**:
  - `path/to/file.py:1`
- **Key Decision**: [If a choice must be made]
  - **Option A**: [Description] ✅ RECOMMENDED
  - **Option B**: [Description]
  - **Recommendation**: [Reasoning]
- **Validation targets**:
  - [Verification method]
- **Deliverables**: [Outputs]
- **Reasoning effort**: [level] ([model] recommended)

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

### Rollback Plan

If issues arise:
1. [Step to revert change 1]
2. [Step to revert change 2]
3. [Verification after rollback]

---

## Acceptance Criteria

- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Testable criterion 3]
- [ ] [End-to-end flow works: action → result]

---

## How to Execute Threads

1. Read this PRD fully before starting any thread
2. Execute ONE thread per conversation
3. Start by stating: "Executing Thread N: [Name]"
4. Read all reference material listed for the thread
5. Complete all actions listed
6. Verify all validation targets
7. Update this PRD with completion log (see format below)
8. End by stating: "Thread N complete. Next: Thread N+1"

### Completion Log Format

Add this section below the thread when completed:

```
**Completion Log — Thread N** ✅ COMPLETED (YYYY-MM-DD)
- ✅ [What was done - specific files, line numbers]
- ✅ [Changes made with details]
- ✅ [Tests run and results]
- **Notes**: [Deviations from plan, decisions made, discoveries]
- **Next**: Thread N+1
```

---

## Completion Checklist

| Thread | Name | Status | Date |
|--------|------|--------|------|
| 1 | [Name] | ⬜ PENDING | - |
| 2 | [Name] | ⬜ PENDING | - |
| 3 | [Name] | ⬜ PENDING | - |
| N | [Name] | ⬜ PENDING | - |

---

## Open Decisions

[Document decisions that need to be made during implementation]

- [Decision 1]? [Options and current thinking]
- [Decision 2]? [Options]

Document owner: **[Name/TBD]**. Update this plan as tasks progress.
