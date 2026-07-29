# UFC

UFC, Understand Financial Character, is an MVP that analyzes personal MBTI with 2-4 member group-account spending data and presents a service-specific consumption MBTI with evidence, graph-ready results, and a grounded Qwen3 4B report.

## Current Status

- Phase 0: completed
- BE Phase 1: FastAPI foundation completed
- BE Phase 2: user, group, and member domain completed
- BE Phase 3: authentication, authorization, and data protection completed
- BE Phase 4 and later backend work: not started
- Analysis, AI, frontend, and integration phases: not started on `main`
- PR #6 is tracked as Analysis / AN Phase 2 behavior metrics work and is not part of `main`

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- Frontend: React, TypeScript, Vite
- AI runtime target: Ollama with Qwen3 4B
- Infra: Docker Compose and Makefile

## Local Development

```bash
make dev
```

Stop services:

```bash
make down
```

Run full local verification:

```bash
make verify
```

## Common Commands

- `make help`: list commands
- `make init`: create `.env` if missing and generate local secrets
- `make ps`: show service status
- `make logs`: follow logs
- `make migrate`: run Alembic migrations
- `make test`: run backend tests
- `make lint`: run backend and frontend lint

## Documentation Entry Points

- [Architecture](docs/architecture/overview.md)
- [Data Flow](docs/architecture/data-flow.md)
- [Data Model](docs/architecture/data-model.md)
- [Analysis Rules](docs/analysis/README.md)
- [API Contracts](docs/contracts/api-contracts.md)
- [Development Phases](docs/phases/README.md)
- [Development Setup](docs/development/setup.md)
- [Team Workflow](docs/development/team-workflow.md)
- [Security Baseline](docs/security/data-classification.md)
- [Troubleshooting](docs/troubleshooting/README.md)

## MVP Exclusions

UFC does not provide real personality diagnosis, real financial diagnosis, bank account integration, transfers, automatic payments, credit score analysis, or financial product recommendations.
