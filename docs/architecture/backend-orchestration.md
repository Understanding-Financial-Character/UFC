# Backend Orchestration

## Responsibility

FastAPI coordinates MVP workflows across persistence, deterministic analysis, and AI report generation.

- User and group API orchestration
- Member MBTI registration
- Transaction upload, validation, classification handoff, and lookup
- Consumption behavior metric calculation handoff
- Spending MBTI result persistence
- LLM report request orchestration
- API error normalization

## Boundaries

- Domain APIs live under `backend/app/modules`.
- Deterministic scoring and metric calculation live under `backend/app/analysis`.
- LLM prompts, clients, and response parsing live under `backend/app/ai`.
- SQLAlchemy session and model foundations live under `backend/app/db`.
- Shared cross-cutting code lives under `backend/app/shared`.

## Data Ownership

PostgreSQL is the source of truth for users, groups, transactions, analysis metrics, MBTI results, and generated reports.

The backend owns write access to persisted business data. Frontend and AI integrations operate through backend contracts only.

## Exclusions

The backend must not include current MVP-excluded features:

- Real bank account connection
- Transfer or automatic payment execution
- Credit score analysis
- Financial product recommendation
- Investment or asset management consulting
