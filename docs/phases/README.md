# Development Phases

## Purpose

Phase documents connect PRD, architecture, contracts, implementation work, and verification evidence.

## Phase File Standard

Each phase folder keeps three files:

- `plan.md`: goal, scope, exclusions, changed modules, prerequisites, completion criteria
- `progress.md`: status, implemented work, contract changes, remaining work, linked branch, PR, commits
- `verification.md`: commands, test results, API verification, screen or terminal evidence, known limitations

Troubleshooting details are not duplicated in phase folders. Link to `docs/troubleshooting` when a reusable issue is discovered.

## Branch and PR Rules

- Start from an up-to-date `main`.
- Create one branch per phase or focused sub-phase.
- Keep implementation, contract updates, and verification evidence in the same PR when they affect each other.
- Do not implement future phase features early.
- Update README only when entry-point commands or major document links change.

## MVP Exclusions

The following are excluded from all current MVP phases:

- Real bank account connection
- Transfer or automatic payment execution
- Credit score analysis
- Financial product recommendation
- Real personality diagnosis
- Large organization dues management
- Investment or asset management consulting
