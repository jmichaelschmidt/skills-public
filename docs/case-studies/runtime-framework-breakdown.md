# Runtime Framework Breakdown

This note distills lessons from an open-source agent runtime and orchestration codebase that was studied as a framework reference.

For the fuller reference set, see:

- [Reference Docs Index](../reference/README.md)
- [Architecture Brief](../reference/framework/architecture-brief.md)
- [Adoption Playbook](../reference/framework/adoption-playbook.md)
- [Implementation Backlog](../reference/framework/implementation-backlog.md)
- [Operating Instance Assessment](../reference/framework/operating-instance-assessment.md)

## Core Takeaways

### One orchestrator loop should own turn progression

The strongest reusable pattern was a single conversation loop that owns:

- request assembly
- tool execution sequencing
- permission checks
- hook execution
- continuation

That architecture is more reliable than scattering orchestration logic across many tools.

### Roles are concrete when they map to tool budgets

A useful agent framework does not stop at role names. It gives each role a capability boundary. That idea reinforced the starter-pack approach of keeping roles distinct by job and output, then optionally tightening tool budgets at runtime.

### Delegation should produce artifacts, not just transient prompts

The studied runtime treated delegation as durable work packaging with manifests, outputs, and status. That strongly supports the starter-pack emphasis on:

- explicit briefs
- durable docs
- validation artifacts
- resumable operating state

### Governance belongs around tools, not inside each tool

Permission policy and hook behavior were more reusable when they wrapped tool execution from the outside. The public lesson is to keep governance centralized rather than embedding ad hoc safety logic in every individual skill or prompt.

### Compaction is part of execution quality

Context compression is not just a token-saving trick. It needs to preserve:

- pending work
- key file references
- recent state
- a clear resume path

That supports the starter-pack bias toward durable summaries and docs rather than relying on raw thread history.

## How It Shaped This Starter-Pack

The runtime study reinforced several existing choices:

- use specialist roles instead of one broad super-agent
- keep one orchestrator in the manager seat
- prefer bounded delegation over uncontrolled fan-out
- treat validation as an architectural concern
- preserve durable artifacts for handoff and recovery

It also clarified a limit: a reusable starter-pack does not need to recreate a full runtime harness. It needs to make delegation and closeout legible inside the tools people already have.
