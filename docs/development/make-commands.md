# Make Commands

| Command | Purpose |
| --- | --- |
| `make help` | Show available commands. |
| `make init` | Create `.env` if missing and generate missing local secrets. |
| `make dev` | Full local startup: init, config, build, up, migrate, health checks, status. |
| `make up` | Start `db`, `backend`, and `frontend`. |
| `make down` | Stop local services. |
| `make restart` | Stop and start local services. |
| `make build` | Build local service images. |
| `make ps` | Show Docker Compose service status. |
| `make logs` | Follow all service logs. |
| `make logs-backend` | Follow backend logs. |
| `make logs-frontend` | Follow frontend logs. |
| `make migrate` | Run `alembic upgrade head` inside backend container. |
| `make migration-check` | Show current Alembic revision. |
| `make test` | Run backend pytest. |
| `make lint` | Run backend ruff and frontend lint. |
| `make verify` | Run full local verification. |
| `make reset CONFIRM=1` | Stop containers, delete local PostgreSQL volume, restart, and migrate. |
| `make clean` | Remove stopped Compose containers and project-local build/cache artifacts. |
| `make doctor` | Check local tool availability. |
| `make ai-up` | Start optional Ollama profile. |
| `make ai-pull` | Start Ollama if needed and pull `qwen3:4b` only when missing. |
| `make ai-health` | Check optional Ollama service and required model availability. |
| `make ai-setup` | Start Ollama, ensure `qwen3:4b` exists, and run health checks. |
| `make ai-smoke` | Run a minimal Ollama generation request. |
| `make dev-ai` | Run default `make dev` plus optional AI runtime setup. |
| `make verify-ai` | Verify optional AI runtime setup and smoke generation. |

`make reset` requires `CONFIRM=1` because it deletes the local PostgreSQL volume.
