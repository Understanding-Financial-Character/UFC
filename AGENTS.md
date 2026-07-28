# AGENTS

## Project Context

UFC is a FastAPI and React MVP for analyzing small-group account spending behavior against member MBTI inputs.

## Working Rules

- Keep backend domain code under `backend/app/modules`.
- Keep reusable backend infrastructure under `backend/app/core`, `backend/app/db`, and `backend/app/shared`.
- Keep deterministic analysis logic under `backend/app/analysis`.
- Keep LLM prompt/client boundaries under `backend/app/ai`.
- Store project decisions in `docs/decisions`.
- Do not commit secrets or real financial personal data.
