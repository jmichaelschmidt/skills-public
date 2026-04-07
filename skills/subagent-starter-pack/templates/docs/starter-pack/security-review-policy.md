# Security Review Policy

Purpose: define the baseline review lens for high-impact changes.

## Focus Areas

- secrets exposure
- unsafe shell execution
- auth or permission widening
- cron or automation blast radius
- network or external-system risk

## Expected Output

`security-reviewer` should return:

- only real security or operational safety findings
- the concrete file, command, or interface involved
- the consequence and the missing guard or mitigation
