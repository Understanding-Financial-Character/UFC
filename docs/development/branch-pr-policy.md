# Branch and PR Policy

## Branch Rules

- Start from an up-to-date `main`.
- Use one branch per phase or focused sub-phase.
- Do not commit directly to `main`.
- Do not mix unrelated phase work into a PR.
- Do not copy code from an unmerged PR into another phase branch unless explicitly approved.

## PR Rules

- PR titles should identify the phase or focused change.
- Implementation, contract updates, tests, and verification should move together.
- Document intentionally deferred work.
- Record review-driven troubleshooting when the issue can recur.

## Completion Rules

A phase becomes `COMPLETED` only when:

- Completion criteria are met.
- Verification is executed and recorded.
- The PR is merged.
- Merge commit and completion date are recorded.
