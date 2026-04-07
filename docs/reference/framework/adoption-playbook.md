# Agent Framework Adoption Playbook

Adapted from framework research on agent runtimes and orchestration. This guide preserves the core adoption patterns in a portable form.

## Objective

Adopt the framework extracted from this repo for your own agent team without copying repo-specific implementation details. The target operating model is:

- one lead orchestrator
- bounded specialist agents
- role-based tool access
- durable handoff artifacts
- mandatory verification before completion or publish

## What To Reuse

Reuse these patterns directly:

- a single orchestrator loop owns turn progression
- specialist agents are defined by capability boundaries
- delegation creates durable artifacts, not just transient prompts
- permissions and hooks wrap tool execution
- session history is compacted into resumable summaries
- release completion requires verification, not just task completion

Replace these with your own stack-specific implementations:

- model provider client
- CLI and terminal renderer
- plugin marketplace mechanics
- local path conventions
- slash command surface

## Operating Principles

1. The orchestrator owns the truth.
2. Roles are capability budgets, not personality labels.
3. Durable artifacts beat chat memory.
4. Validation gates close work; execution alone does not.
5. Code truth beats narrative docs when they conflict.
6. Parallelism is a tool, not the default.

## Recommended Team Roles

| Role | Main job | Allowed capability profile | Should edit files? | Primary output |
| --- | --- | --- | --- | --- |
| Lead orchestrator | Owns plan, sequencing, integration, and closeout | Full view across runtime, backlog, validation, and release state | Yes | final merged result and execution decisions |
| Explorer | Gathers evidence, traces code paths, compares options | read/search/web/structured-output only | No | investigation notes and grounded recommendations |
| Planner | Converts evidence into explicit next actions and checklists | read/search/todo/structured-output/user-message | No | execution-ready plan or thread package |
| General worker | Implements bounded changes with explicit ownership | read/write/edit/shell/search | Yes | code or docs within owned scope |
| Verifier | Confirms behavior, tests, regressions, and completion gates | shell/read/search/structured-output; no write by default | No | pass/fail verification report |

Map these roles to the repo patterns as follows:

- Explorer <- `Explore`
- Planner <- `Plan`
- Verifier <- `Verification`
- General worker <- `general-purpose`
- Lead orchestrator <- main runtime session, not a delegated child

## Reference Control Loop

Use this loop for every non-trivial task:

1. Load repo instructions, current state, and relevant history.
2. Decide whether the task stays local or is split into bounded delegated units.
3. Package any delegated unit with role, scope, tool budget, done checks, and expected artifact.
4. Run the assigned work.
5. Apply permission policy and hooks around tool execution.
6. Persist outputs, status, and failures as durable artifacts.
7. Integrate completed results back into the primary execution state.
8. Verify thread-level completion.
9. Verify task-level completion before closeout or publish.
10. Compact context when history grows, while preserving pending work and recent messages.

## Delegation Rules

Delegate only when one of these is true:

- the work is read-only and evidence gathering
- the write scope is narrow and clearly owned
- a separate verification pass is needed
- parallel review materially shortens cycle time

Keep work with the orchestrator when one of these is true:

- the result is needed immediately to decide the next step
- the change crosses multiple write scopes
- the work is security-sensitive or architecture-defining
- the task needs judgment across several partial outputs

Never allow overlapping write scopes between active workers unless the overlap is trivial and intentional.

## Handoff Contract

Every delegated unit should include the same fields, regardless of stack:

```text
Task ID:
Role:
Objective:
Owned scope:
Out-of-scope:
Inputs and references:
Allowed tools:
Permission level:
Expected output artifact:
Validation checks:
Completion rule:
Escalation rule:
```

Required constraints:

- objective must be one sentence
- owned scope must name the files or artifact boundary
- allowed tools must be explicit
- validation checks must be concrete
- completion rule must define what "done" means

## Validation And Completion Discipline

Use two validation levels:

### Thread-Level Validation

This proves the delegated unit did what it was supposed to do.

Examples:

- tests for the edited module pass
- output artifact exists and matches the requested structure
- investigation report cites the requested evidence
- no unexpected files were changed

### Task-Level Validation

This proves the whole task is complete.

Examples:

- definition of done is satisfied
- integration still works after merging delegated results
- release or publication gates pass
- residual risks are documented if something could not be verified

No task is complete until both levels pass.

## Artifact And Memory Strategy

Store these artifacts durably:

- system and project instruction sources
- session history in structured form
- compacted continuation summaries
- delegated task manifests
- delegated output files
- todo or execution ledger
- verification reports
- final closeout summary

Treat chat memory as a cache, not the system of record.

## Failure And Recovery Rules

### Tool denied by permission policy

- stop the action
- record the denied tool and requested escalation
- either re-run with approval or change approach

### Hook denies or modifies execution

- treat hook output as governing feedback
- preserve the hook message in the artifact trail
- do not silently retry around the hook

### Subagent fails

- persist failure state
- review whether the failure is environmental, prompt-related, or due to missing capability
- either retry with a narrower task or pull the work back to the orchestrator

### Context pressure rises

- compact older history into a resumable summary
- preserve recent messages verbatim
- retain pending work and key file references in the summary

### Docs and code disagree

- prefer code as the runtime source of truth
- keep the doc discrepancy as an explicit note for follow-up

## Parallel Review And Persistent Execution

Translate the documented OmX patterns into stack-neutral team rules:

| OmX pattern in README | Portable team behavior |
| --- | --- |
| `$team` parallel review | run read-only review or architecture sidecars in parallel with active execution |
| `$ralph` persistent execution | keep one operator lane responsible for following work through verification and completion |
| architect-level verification | require a final integration review before closeout |
| cleanroom passes | schedule dedicated naming, QA, and publish-readiness passes |

Do not overfit to the OmX mode names. Preserve the behaviors.

## Mandatory Vs Optional Framework Parts

Mandatory for v1:

- orchestrator-owned control loop
- typed session state
- role-based tool budgets
- permission policy
- durable delegation artifacts
- verification gate before completion

Optional for v1:

- plugin marketplace
- remote transport layer
- live skill reload
- background scheduling tools
- notebook and REPL tool families

## What To Copy, Replace, And Avoid

| Decision | Keep | Replace | Avoid |
| --- | --- | --- | --- |
| Delegation model | explicit manifest plus output artifact | path format and storage location | ad hoc child prompts with no record |
| Role system | capability-based roles | exact role labels if your team uses different language | persona-heavy roles with identical permissions |
| Governance | central permission and hook layers | prompt UI or approval UX | embedding policy logic inside each tool |
| Memory | structured session plus compaction | serialization format | raw transcript replay as the only history strategy |
| Validation | thread-level and task-level gates | specific CI commands | "looks done" as the completion rule |

## Minimum Viable Adoption Sequence

1. Stand up the orchestrator loop with structured session state.
2. Add a small built-in tool surface with explicit permissions.
3. Add delegation with role-based tool allowlists and durable manifests.
4. Add a verifier role and make verification mandatory for closeout.
5. Add compaction and resume summaries.
6. Add plugin, remote, or marketplace features only after the core loop is reliable.

## Reference Operating Model

Use this model as the default team shape:

- One lead orchestrator owns sequencing, integration, and final decisions.
- Explorers run read-only evidence passes.
- Planners convert evidence into precise executable work packets.
- Workers own narrow write scopes.
- Verifiers run independent read-only confirmation before publish.
- Every delegated unit leaves behind an artifact trail.
- Every task closes with explicit verification or a documented gap.
