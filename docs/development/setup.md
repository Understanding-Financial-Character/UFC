# Development Setup

## Requirements

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose

## Run With Docker

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

## Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Database Migration

```bash
cd backend
alembic revision --autogenerate -m "message"
alembic upgrade head
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```
