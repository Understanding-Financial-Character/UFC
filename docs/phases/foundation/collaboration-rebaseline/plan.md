# Collaboration Rebaseline Foundation

## Status
VERIFYING

## Goal
Preserve completed implementation while aligning phase structure, data design, analysis ownership, and local collaboration commands.

## Why
Future phases need a single source of truth for responsibilities, branch ownership, data contracts, and local verification.

## Prerequisites
- Start from latest `main`.
- Do not import PR #6 code.
- Verify PR #2 through PR #6 status.

## In Scope
- Documentation rebaseline
- Phase folder structure
- 9-table target design documentation
- Analysis, rule engine, and Qwen responsibility boundaries
- Makefile-based local development workflow
- Compose readiness improvements

## Out of Scope
- BE Phase 4 transaction API implementation
- New DB migrations or models for future tables
- Feature calculation logic
- PR #6 code duplication
- Rule Engine implementation
- Qwen3 Provider implementation
- Frontend user screens
- Admin console
- Bank integration
- Real personal data seeds

## Responsible Modules
- `docs`
- `Makefile`
- `scripts/bootstrap_env.py`
- `compose.yaml`
- `compose.dev.yaml`
- `AGENTS.md`
- `.env.example`

## Contracts
Documentation-only contract alignment.

## Data Changes
No database migration or model change.

## Security Considerations
Secrets remain local-only. Qwen prompt input excludes raw identities, transaction arrays, tokens, ciphertext, and secrets.

## Implementation Tasks
- Reconfirm implemented phases.
- Create new phase folder structure.
- Add analysis rule design docs.
- Add Makefile and bootstrap script.
- Update README and development docs.
- Verify local commands.

## Test Scenarios
- `make init`
- `make dev`
- `make ps`
- `make migrate`
- `make test`
- `make lint`
- `make verify`
- `make down`

## Completion Criteria
- Current implementation state is verified.
- Completed, in-progress, and not-started phases are separated.
- 9-table design updates are documented.
- Feature, Rule, and Qwen responsibilities are documented.
- New phase folders exist.
- `AGENTS.md` is updated.
- Makefile commands exist.
- `make dev` can run or failure is documented truthfully.
- Verification results are recorded.

## Branch
`chore/phase-rebaseline-collaboration-foundation`

## Dependencies
Completed PR #2, #3, #4, and #5. PR #6 is tracked but not imported.
