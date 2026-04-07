# Repo Hygiene Policy

Purpose: define the baseline Git and worktree discipline expected by the starter-pack.

## Baseline Rules

- check `git status --short --branch` before starting significant work
- prefer dedicated task branches and worktrees over editing from a primary checkout
- do not start unrelated work on top of unrelated dirt
- run relevant validation before commit, push, or merge
- do not rewrite shared history without explicit approval

## Expected Output

`repo-hygiene` should report:

- current branch and worktree context
- whether the repo is dirty
- whether the dirt is in-scope or unrelated
- whether validation appears to be missing
- the next safe cleanup or bootstrap step
