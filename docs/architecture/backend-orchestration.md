# Backend Orchestration

## Responsibility

FastAPI coordinates MVP workflows across persistence, deterministic analysis, and AI report generation.

- User and group API orchestration
- Member MBTI registration
- Transaction upload, validation, classification handoff, and lookup
- Analysis input adapter handoff
- Spending MBTI result persistence
- Qwen3 report request orchestration
- API error normalization

## Boundaries

- Domain APIs live under `backend/app/modules`.
- Deterministic scoring and metric calculation live under `backend/app/analysis`.
- Qwen3 prompts, clients, validation, and fallback live under `backend/app/ai`.
- Analysis execution order and state transitions live under `backend/app/orchestration`.
- SQLAlchemy session and model foundations live under `backend/app/db`.
- Shared cross-cutting code lives under `backend/app/shared`.

## Data Ownership

PostgreSQL is the source of truth for users, groups, transactions, analysis metrics, MBTI results, and generated reports.

The backend owns write access to persisted business data. Frontend and AI integrations operate through backend contracts only.

The backend must keep API DTOs, DB entities, and analysis DTOs separate. SQLAlchemy entities must not be returned directly from API routes.

## Exclusions

The backend must not include current MVP-excluded features:

- Real bank account connection
- Transfer or automatic payment execution
- Credit score analysis
- Financial product recommendation
- Investment or asset management consulting
