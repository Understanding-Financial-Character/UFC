# Troubleshooting

## Database connection failed

- `.env`의 `DATABASE_URL`과 Docker Compose의 `POSTGRES_*` 값이 같은지 확인한다.
- 로컬에서 backend를 직접 실행할 때는 host를 `localhost`로 둔다.
- Docker Compose 내부에서는 host를 `db`로 둔다.

## Alembic cannot import app

- `backend` 디렉터리에서 Alembic 명령을 실행한다.
- `backend/alembic.ini`의 `prepend_sys_path = .` 설정을 유지한다.

## Frontend cannot call API

- `VITE_API_BASE_URL`이 FastAPI 주소와 일치하는지 확인한다.
- 로컬 기본값은 `http://localhost:8000`이다.

## Backend test warnings

- [Backend TestClient httpx Deprecation Warning](backend-testclient-httpx-warning.md)
