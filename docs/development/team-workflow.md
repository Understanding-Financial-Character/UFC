# Team Workflow

## Standard Flow

1. Update `main`.
2. Create one branch for the phase.
3. Set the phase `plan.md` or `progress.md` status to `IN_PROGRESS`.
4. Change implementation, contracts, tests, and docs in the same PR when they depend on each other.
5. Record verification commands and results in `verification.md`.
6. Push the branch.
7. Create a PR.
8. Address review comments.
9. After merge, record `COMPLETED`, merge commit, and completion date.

## Shared Files

Check active PRs or the current owner before changing:

- `backend/app/main.py`
- `backend/app/api/router.py`
- DB model modules
- Alembic migrations
- `compose.yaml`
- `compose.dev.yaml`
- `Makefile`
- `docs/contracts`

## PR #6 Note

PR #6 is tracked as Analysis / AN Phase 2 behavior metrics work. It is not merged into `main` and must not be treated as completed implementation in other branches.
