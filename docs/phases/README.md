# Development Phases

## Purpose

Phase documents connect PRD, architecture, contracts, implementation work, and verification evidence.

## Phase File Standard

Each phase folder keeps three files:

- `plan.md`: goal, scope, exclusions, changed modules, prerequisites, completion criteria
- `progress.md`: status, implemented work, contract changes, remaining work, linked branch, PR, commits
- `verification.md`: commands, test results, API verification, screen or terminal evidence, known limitations

Troubleshooting details are not duplicated in phase folders. Link to `docs/troubleshooting` when a reusable issue is discovered.

## Phase Status Model

Allowed phase status values:

- `NOT_STARTED`: No implementation branch has been created.
- `IN_PROGRESS`: Implementation, contract changes, or documentation updates are in progress.
- `BLOCKED`: Work cannot continue because of an external dependency or unmet prerequisite.
- `VERIFYING`: Implementation or document changes are complete, but review, merge, or completion evidence is still pending.
- `COMPLETED`: Completion criteria, verification evidence, and merge tracking are complete.
- `DEFERRED`: Work is explicitly postponed from the current MVP scope.

Status transition rules:

- `NOT_STARTED` -> `IN_PROGRESS` when a phase branch starts.
- `IN_PROGRESS` -> `BLOCKED` when a documented blocker prevents meaningful progress.
- `BLOCKED` -> `IN_PROGRESS` when the blocker is resolved.
- `IN_PROGRESS` -> `VERIFYING` when planned changes are implemented and local verification has run.
- `VERIFYING` -> `IN_PROGRESS` when review requires rework.
- `VERIFYING` -> `COMPLETED` only after all completion requirements are met.
- Any non-completed phase may move to `DEFERRED` when the work is explicitly postponed.

`COMPLETED` requires all of the following:

1. `plan.md` completion criteria are satisfied.
2. `progress.md` has no remaining work, or remaining work is explicitly transferred to a later phase.
3. `verification.md` records actual execution results and evidence links.
4. Contract changes are reflected with the implementation or documented as prerequisites.
5. The linked PR is merged and the merge commit or squash commit is recorded.
6. The completed date is recorded.

## Branch and PR Rules

- Start from an up-to-date `main`.
- Create one branch per phase or focused sub-phase.
- Keep implementation, contract updates, and verification evidence in the same PR when they affect each other.
- Do not implement future phase features early.
- Update README only when entry-point commands or major document links change.
- Before PR creation, record PR as `Pending`.
- After PR creation, update the phase progress document with the PR number and head commit in a follow-up commit.
- After merge, update the phase progress document with `COMPLETED`, merge commit or squash commit, and completed date.

## MVP Delivery Milestones

Component phases do not by themselves prove a user-facing MVP workflow is complete. A milestone is complete only when integration verification passes for the full vertical slice.

### M1. Group Setup

- Backend group and member APIs
- Frontend group setup and member MBTI input
- Membership authorization
- Integration verification

### M2. Transaction Analysis

- Transaction ingestion
- Deterministic analysis
- Result persistence
- Result visualization

### M3. AI Explanation

- AI input contract
- Report generation
- Failure fallback
- Report UI

## Verification Metadata Standard

Each `verification.md` should include:

- Verified scope or verified commit
- Verified at
- Environment
- Verifier
- Evidence file links when output is long

Long terminal output should be stored under `docs/evidence/<phase-name>/`.

For an open PR with additional review commits, avoid recording the moving branch head as a fixed value. Use `Current PR head: See PR #` and record the merge commit or squash commit after the PR is merged.

## MVP Exclusions

The following are excluded from all current MVP phases:

- Real bank account connection
- Transfer or automatic payment execution
- Credit score analysis
- Financial product recommendation
- Real personality diagnosis
- Large organization dues management
- Investment or asset management consulting
