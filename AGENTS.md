# AGENTS

## Project Purpose

UFC, Understand Financial Character, is an MVP that analyzes personal MBTI values together with 2-4 member group-account spending data, expresses the group's shared spending tendency as a service-specific consumption MBTI, and presents calculation evidence, graph-ready data, and a Qwen3 4B summary report.

UFC is not a real personality diagnosis, real financial diagnosis, bank account integration, transfer service, credit score analysis, or financial product recommendation service.

## MVP Scope

Included:

- 2-4 member group setup
- Member MBTI registration
- Synthetic or uploaded transaction-like data
- Transaction normalization and data quality checks
- Behavior metric calculation
- Versioned rule-based consumption MBTI
- Grounded AI report text from calculated evidence

Excluded:

- Real bank account connection
- Transfers, automatic payments, or settlement execution
- Credit score analysis
- Financial product recommendation
- Real personal or financial seed data

## Responsibility Boundaries

- `backend/app/modules`: user, group, transaction, and admin domain APIs.
- `backend/app/core`: settings, exceptions, logging, security, and cross-cutting backend runtime concerns.
- `backend/app/db`: SQLAlchemy base, sessions, and common DB foundations.
- `backend/app/analysis`: preprocessing, feature calculation, data quality, score normalization, and versioned rule engine.
- `backend/app/ai`: Qwen3 provider, prompt construction, report validation, and fallback handling.
- `backend/app/orchestration`: analysis execution order, state transitions, and handoff between persistence, analysis, and AI.
- `frontend/src/features`: frontend user-feature modules.
- `mock-data/scenarios`: source scenario definitions.
- `mock-data/generated`: generated CSV seed artifacts.
- `docs`: contracts, phase plans, decisions, verification evidence, and troubleshooting.
- `infra`: optional delivery and deployment infrastructure.

Frontend does not calculate authoritative scores or call the LLM directly. Backend APIs do not return SQLAlchemy entities directly; API request and response DTOs must remain separate from DB models. Analysis DTOs must remain separate from DB persistence models.

## Data Ownership

The canonical MVP table plan has 9 application tables:

- Source data: `users`, `groups`, `group_members`, `categories`, `transactions`
- Analysis results: `analysis_runs`, `behavior_metrics`, `consumption_mbti_results`, `ai_reports`

Current implementation owns only the tables introduced through completed backend phases. Future tables must be added only in their own phase with Alembic migrations and updated docs.

## Security and Privacy

- Do not commit secrets, real financial personal data, real account identifiers, access tokens, refresh tokens, or production exports.
- `.env` is local-only. `.env.example` may list keys and safe placeholders only.
- Email is stored encrypted plus lookup HMAC in BE Phase 3; do not reintroduce plaintext email uniqueness.
- Transaction boolean signals such as `is_planned`, `is_recurring`, and `is_shared_expense` are tri-state. `NULL` means unknown and must not be interpreted as `FALSE`.

## Analysis and AI Rules

- The rule engine, not Qwen3, determines E/I, S/N, T/F, J/P axis outcomes and final consumption MBTI.
- Qwen3 receives only grounded aggregate evidence and produces user-friendly explanation.
- Unavailable features are excluded from score calculation, not treated as zero.
- Axis weights are renormalized over available features.
- Coverage must be calculated. Low coverage may defer axis or final MBTI output.
- Final `mbti_type` is nullable when data is insufficient.

Axis score direction is fixed:

- EI score: higher means E
- SN score: higher means N
- TF score: higher means F
- JP score: higher means P

## Branch and Phase Rules

- Start each phase from an up-to-date `main`.
- Use one branch and one PR per phase or focused sub-phase.
- Do not commit directly to `main`.
- Do not copy code from unmerged PRs into another branch unless the user explicitly asks for that integration.
- Keep implementation, contracts, tests, and phase verification in the same PR when they affect each other.
- Do not implement future phase features early.

## Documentation Rules

- Update docs in the same PR as behavior, contract, schema, or workflow changes.
- Store project decisions in `docs/decisions`.
- Store reusable troubleshooting notes in `docs/troubleshooting`.
- Preserve completed phase evidence; do not delete historical verification outputs.
- README should stay minimal and link to detailed docs instead of duplicating them.

## Migration Rules

- Every DB schema change requires an Alembic migration in the same PR.
- Do not create migrations for future tables in documentation-only or foundation work.
- Do not use `Base.metadata.create_all()` as a replacement for PostgreSQL migrations.
- Coordinate changes to shared DB models and migration heads before opening overlapping PRs.

## Test Rules

- Run the phase-relevant tests before finishing.
- Backend changes require `ruff check app tests` and `pytest` unless explicitly documented as not executable.
- Frontend changes require at least typecheck/build or documented non-execution.
- `make verify` is the default full local verification path.

## Shared-File Caution

Coordinate before editing high-conflict files:

- `backend/app/main.py`
- `backend/app/api/router.py`
- DB model modules
- Alembic migrations
- `compose.yaml`
- `compose.dev.yaml`
- `Makefile`
- `docs/contracts`
