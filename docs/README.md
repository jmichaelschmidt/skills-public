# Docs

This docs surface serves two audiences:

- builders who want to install and use the public starter-pack
- builders who want to understand the agent-team design choices behind it

## Reading Paths

### Install It

Read in this order:

1. [Design Principles](design-principles.md)
2. [subagent-starter-pack](../skills/subagent-starter-pack/)
3. [Starter-Pack Setup](../skills/subagent-starter-pack/templates/docs/starter-pack/setup.md)
4. [Multi-Machine Setup](../skills/subagent-starter-pack/references/multi-machine-setup.md)

### Learn The Design

Read in this order:

1. [Design Principles](design-principles.md)
2. [Cowork Notes](research/ccforpms-cowork-notes.md)
3. [Cowork Implications](research/ccforpms-cowork-implications.md)
4. [Reference Docs Index](reference/README.md)
5. [Operating Instance Lessons](case-studies/operating-instance-lessons.md)
6. [Runtime Framework Breakdown](case-studies/runtime-framework-breakdown.md)

## What These Docs Try To Preserve

- the reasoning behind the six-role starter-pack
- the difference between machine install and repo refresh
- the evidence behind the changes made after external research
- lessons from a real multi-repo operating environment, adapted for general use
- lessons from an open-source runtime architecture without treating one codebase as sacred

## Source Map

This repo now has three learning surfaces:

- starter-pack operating docs inside `skills/subagent-starter-pack/`
- deeper reference docs in [reference/README.md](reference/README.md)
- shorter interpreted essays in `research/`, `case-studies/`, and [design-principles.md](design-principles.md)

Use the reference docs when you want source-faithful framework material. Use the essays when you want the distilled design read.

## Scope Boundary

These docs are intentionally public and generic.

They do not include:

- private compatibility profiles
- internal migration notes
- brand-specific job docs
- private repo path assumptions
