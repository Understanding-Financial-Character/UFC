.PHONY: dev backend frontend test lint migrate

dev:
	docker compose -f compose.yaml -f compose.dev.yaml up --build

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest
	cd frontend && npm test

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint

migrate:
	cd backend && alembic upgrade head
