# Architecture

UFC uses a React web client, a FastAPI backend, PostgreSQL for relational persistence, and an LLM API for natural-language report generation.

The backend owns user, group, transaction, analysis metric, consumption MBTI, and report workflows. SQLAlchemy is the ORM layer, Alembic manages schema migrations, and Pydantic validates API request and response contracts.

Detailed architecture notes live in [docs/architecture/overview.md](docs/architecture/overview.md).
