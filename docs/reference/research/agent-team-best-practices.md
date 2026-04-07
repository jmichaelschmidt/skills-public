# Agent Team Best Practices

Adapted from research and operating practice on building reusable agent teams. This guide preserves the core design guidance in a portable form.

## Big-Picture Best Practices

Modern coding agents work best when you treat them like junior developers inside a strict process, not like magical swarms.

The strongest portable practices are:

- single-responsibility agents
- plan -> validate -> execute
- file-based project memory
- default serial, explicit parallel
- human-in-the-loop for high-impact actions
- least-privilege security

These patterns are portable across Claude Code, Codex, custom runtimes, and multi-agent operator setups.

## 1. Single-Responsibility Agents

Each agent or subagent should have:

- one clear goal
- one clear input contract
- one clear output artifact
- one clear definition of done

Examples:

- implement a bounded spec
- write or repair tests
- run a focused security review
- synthesize a research packet

If an agent has too many unrelated responsibilities, split it.

## 2. Plan -> Validate -> Execute

The safest pattern is:

1. produce a structured plan
2. name the validation path
3. execute incrementally

That plan may be markdown, JSON, or a repo-owned task artifact, but it should be durable enough that another operator could pick it up midstream.

Execution without a clear validation path creates false confidence. Validation is part of the work, not a separate optional cleanup step.

## 3. File-Based Project Memory

Encode rules, workflows, and context in version-controlled files rather than relying on transient chat history.

Useful examples:

- `AGENTS.md`
- durable design docs
- plans and execution manifests
- validation helpers
- run logs and handoff notes

Chat memory is a cache. Project memory should survive the thread that created it.

## 4. Default Serial, Explicit Parallel

Most implementation work should stay serial by default.

Parallelism is helpful when the work is clearly independent, such as:

- review sidecars
- security audit passes
- research synthesis
- architecture comparison

Do not use parallelism as a default just because a task is large. Use it when the ownership boundary is already clear.

## 5. Human-In-The-Loop For High-Impact Actions

Keep explicit human approval for:

- shell commands with real blast radius
- destructive file operations
- network calls that leave the local environment
- deploy or publish steps
- permission widening and secret handling

The operator should remain the manager of the system, not a passive observer of agent autonomy.

## 6. Least-Privilege Security

A serious agent setup should:

- restrict filesystem scope where possible
- keep network access narrow
- use scoped credentials
- disable unnecessary tools
- preserve logs or other artifact trails for review

If you cannot explain what an agent can access, the architecture is not finished.

## 7. Build Persistence Before Sophistication

Get the durable foundation right before adding more agents or more tooling:

- stable workspace layout
- repeatable setup
- clear instructions
- resumable context
- documented escalation points

A smaller durable system is more valuable than a large fragile swarm.

## 8. Separate Orchestration From Execution

One common failure mode is letting the coordinator also become the main worker.

Prefer:

- an orchestrator that sequences and integrates
- bounded workers that execute
- reviewers or verifiers that independently confirm outcomes

That separation makes debugging easier and reduces the chance that one thread silently becomes the entire system.

## 9. Optimize For Real Work, Not Demo Work

Healthy agent systems help with:

- shipping changes
- producing clear briefs
- reducing dropped operational balls
- making verification routine
- turning recurring work into durable process

Unhealthy systems optimize for:

- theatrical agent counts
- vague autonomy claims
- unclear ownership
- constant human cleanup

## 10. Start Small And Add Roles Only When The Job Is Stable

A strong small team often beats a large weak swarm.

Start with a compact set such as:

- one orchestrator
- one worker
- one reviewer or verifier
- one research or docs role if the workflow actually needs it

Add another role only when:

- the responsibility recurs
- the job description is stable
- a separate context window clearly improves outcomes

## Design Consequence For This Repo

These principles are the reason the public starter-pack favors:

- a small core role set
- explicit repo refresh and validation
- durable docs over chat-only memory
- serial-by-default delegation
- optional skills for reusable workflow patterns instead of more permanent global roles
