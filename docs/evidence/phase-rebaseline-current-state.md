# Phase Rebaseline Current Implementation State

Verified from `main` on 2026-07-30 before creating `chore/phase-rebaseline-collaboration-foundation`.

## Implemented On main

- FastAPI application factory
- `/health`, `/ready`, `/api/v1/meta`, `/api/v1/openapi.json`
- SQLAlchemy session foundation and Alembic migrations
- Normalized error response and trace id middleware
- User, group, group member, and member personality domain
- Bearer-token auth with signup, login, refresh, logout, `/me`
- USER and ADMIN roles
- Admin masked user summary API
- AES-256-GCM email encryption with lookup HMAC and key version
- Refresh token hash storage, family rotation metadata, and reuse detection

## Implemented Tables

- `users`
- `groups`
- `group_members`
- `member_personalities`
- `refresh_tokens`

## Not Implemented On main

- `categories`
- `transactions`
- `analysis_runs`
- `behavior_metrics`
- `consumption_mbti_results`
- `ai_reports`
- Qwen3 provider
- Rule engine
- Frontend user workflows beyond the starter Vite app

## Important Difference

PR #6 contains behavior metrics code, but it is not merged into `main`. This branch intentionally does not import it.
