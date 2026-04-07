# Agent Framework Implementation Backlog

Adapted from framework research on agent runtimes and orchestration. This guide preserves the implementation sequencing and interfaces in a portable form.

## Objective

This backlog turns the extracted framework into buildable epics for another stack. It assumes you are building an agent-team platform, not just a single-agent CLI.

Implementation order matters. Build the kernel first, then delegation, then governance, then operator ergonomics.

## Sequencing

Use this rollout order:

1. Orchestration kernel
2. Role system and delegation API
3. Permission and policy layer
4. Session history, compaction, and resume
5. Verification workflow
6. Hook and plugin extension points

This order preserves a usable core even if later epics slip.

## Epic 1: Orchestration Kernel

### Goal

Create the main runtime loop that owns assistant turns, tool calls, and continuation decisions.

### Required interfaces

- `ApiClient.stream(request) -> events`
- `ConversationRuntime.run_turn(input) -> turn_summary`
- `ToolExecutor.execute(tool_name, input) -> result`
- `Session`
- `ConversationMessage`
- `ContentBlock`

### Minimum acceptable behavior

- system prompt and session history are sent together on each turn
- assistant output is translated into typed events
- tool calls are extracted from assistant output
- tool results are appended back into session state
- the loop continues until no pending tool calls remain
- max-iteration protection prevents runaway loops

### Dependencies

- none

### Defer to v2

- remote transport modes
- advanced provider routing
- rich streaming UX

## Epic 2: Role System And Delegation API

### Goal

Create bounded specialist agents with explicit tool budgets and durable handoff artifacts.

### Required interfaces

- `spawn_agent(task_packet) -> agent_manifest`
- `allowed_tools_for_role(role) -> tool_set`
- `normalize_role(label) -> canonical_role`
- `AgentManifest`
- `AgentOutputArtifact`

### Minimum acceptable behavior

- delegated work requires a description and objective
- every delegated unit has a role, tool set, and status
- child agents run in isolated sessions
- delegated output is persisted to durable artifacts
- failure state is recorded, not swallowed

### Dependencies

- Epic 1

### Defer to v2

- dynamic role definitions from external registries
- long-lived agent daemons
- automatic retry policy

## Epic 3: Permission And Policy Layer

### Goal

Centralize governance for tool execution.

### Required interfaces

- `PermissionPolicy`
- `PermissionMode`
- `authorize(tool_name, input) -> allow or deny`
- optional `PermissionPrompter`

### Minimum acceptable behavior

- each tool has a required permission level
- runtime has an active permission mode
- escalations are explicit and reviewable
- denied actions return structured reasons
- tools do not embed their own approval policy

### Dependencies

- Epic 1
- Epic 2

### Defer to v2

- org-wide policy sync
- fine-grained path or domain restrictions
- policy analytics

## Epic 4: Session History, Compaction, And Resume

### Goal

Make long-running agent work resumable without losing intent.

### Required interfaces

- `Session.save`
- `Session.load`
- `compact_session(session, config) -> compacted_session`
- `estimate_session_tokens(session) -> count`

### Minimum acceptable behavior

- session history is stored as typed messages
- token or size pressure can trigger compaction
- recent messages remain verbatim
- compacted summaries capture pending work, key files, and recent requests
- resumed sessions include a direct continuation instruction

### Dependencies

- Epic 1

### Defer to v2

- semantic retrieval over archived sessions
- shared team memory service
- cross-session graph search

## Epic 5: Verification Workflow

### Goal

Make completion dependent on verification, not only execution.

### Required interfaces

- `VerificationTask`
- `VerificationReport`
- `task_status = pending | in_progress | blocked | done`
- `closeout_gate(task, reports) -> pass or fail`

### Minimum acceptable behavior

- thread-level checks can be attached to a delegated unit
- task-level checks are owned by the orchestrator
- verification output is persisted
- failed verification blocks completion
- unverified gaps are documented explicitly

### Dependencies

- Epic 1
- Epic 2
- Epic 4

### Defer to v2

- automated canary rollout checks
- scheduled verification jobs
- quality scoring dashboards

## Epic 6: Hook And Plugin Extension Points

### Goal

Allow governance and extension logic to attach around tool execution without rewriting the kernel.

### Required interfaces

- `HookRunner`
- `run_pre_tool_use`
- `run_post_tool_use`
- `PluginManifest`
- `PluginToolManifest`
- `PluginCommandManifest`

### Minimum acceptable behavior

- pre-tool hooks can deny execution
- post-tool hooks can annotate or reject results
- plugin manifests can declare hooks, commands, and tools
- runtime can load extension metadata without destabilizing the kernel

### Dependencies

- Epic 1
- Epic 3

### Defer to v2

- plugin marketplace
- signed plugin distribution
- hot reload for runtime extensions

## Cross-Epic Acceptance Scenarios

The implementation is ready for first use when these scenarios pass:

1. A lead orchestrator can delegate research to an explorer, implementation to a worker, and verification to a verifier using different tool budgets.
2. A child agent failure produces a durable failed manifest and does not corrupt the parent session.
3. A denied tool call stops execution and records the denial reason.
4. A long-running session can be compacted and resumed without losing pending work.
5. A task cannot be marked complete until verification artifacts exist.

## Suggested Delivery Waves

### Wave 1: Core runtime

- Epic 1
- Epic 3
- Epic 4

Outcome:

- usable single-agent runtime with permissions and resumable history

### Wave 2: Team execution

- Epic 2
- Epic 5

Outcome:

- bounded multi-agent execution with explicit closeout discipline

### Wave 3: Extensibility

- Epic 6

Outcome:

- framework can grow without rewriting the orchestration kernel

## Final Guidance

If schedule pressure forces tradeoffs, protect these four things first:

- the orchestrator loop
- role-based capability boundaries
- durable handoff artifacts
- verification before completion

Those four elements are the minimum framework that makes an agent team reliable instead of merely busy.
