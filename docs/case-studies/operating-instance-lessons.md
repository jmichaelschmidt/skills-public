# Operating Instance Lessons

This note distills lessons from a real multi-repo operating environment without carrying over its private names, internal paths, or product-specific docs.

For the fuller public-safe reference material behind these lessons, see:

- [Reference Docs Index](../reference/README.md)
- [Agent Team Best Practices](../reference/research/agent-team-best-practices.md)
- [Operating Instance Assessment](../reference/framework/operating-instance-assessment.md)

## 1. The Brief Matters More Than The Agent Label

The most reliable delegation pattern was not “find the smartest role.” It was:

- define done
- define context
- define constraints
- keep the owned scope narrow
- name the validation command

The role helps, but the brief is what makes delegation hold.

## 2. Repo Hygiene Should Be A First-Class Concern

When multiple short-lived branches and worktrees are normal, a hygiene pass is not overhead. It is a safety rail. A starter-pack benefits from having one role that explicitly asks:

- is this a safe start state
- is the current dirt in scope
- is validation missing
- should branch or worktree cleanup happen before publication

## 3. Research And Artifact Work Need Different Contracts Than Code Work

One of the sharpest lessons was that non-code work fails when it is treated like ordinary implementation. Research and artifact handling need:

- explicit output destinations
- non-destructive behavior
- move logs or output inventories
- reusable reference material

That is why the public starter-pack now includes an optional artifact-workflow reference and why research outputs are expected to preserve evidence quality.

## 4. Durable Ops Docs Should Be Layered

A reusable starter-pack should own only the shared layer:

- agent prompts
- generic workflow docs
- validation helpers

Repo-specific doctrine, manifests, runbooks, and deployment policies belong to the repo. Blurring those layers makes sharing harder and upgrades noisier.

## 5. Human-In-The-Manager-Seat Scales Better

The operating environment worked best when the human remained responsible for:

- choosing the next thread
- approving escalations
- deciding when a result was ready to publish

The agents handled bounded work. They did not become autonomous owners of the whole system.

## 6. Small Durable Improvements Compound

The biggest gains did not come from inventing exotic new roles. They came from steady doctrine improvements:

- better handoff contracts
- stronger validation
- clearer lane boundaries
- better artifact storage conventions

That makes the public lesson simple: stability usually comes from contract quality, not from adding more agent variety.
