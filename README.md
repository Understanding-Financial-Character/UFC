# UFC

UFC, Understand Financial Character,는 2~4인 모임의 공동 소비 데이터를 개인 MBTI와 함께 해석해 서비스용 소비 MBTI, 계산 근거, 시각화 가능한 결과, Qwen3 4B 기반 요약 리포트로 보여주는 MVP입니다.

Second test branch push check.

## Problem

모임통장이나 공동 지출 서비스는 보통 "얼마를 썼는지"와 "누가 냈는지"를 보여주는 데 집중합니다. 하지만 실제 모임에서 더 궁금한 것은 이 모임이 어떤 소비 성향을 가지고 있는지, 지출 패턴이 계획적인지 즉흥적인지, 관계 중심인지 실용 중심인지, 반복 소비가 많은지 경험 소비가 많은지에 대한 해석입니다.

UFC는 단순 정산이 아니라 모임의 소비 캐릭터를 이해하는 문제를 다룹니다.

## Value

UFC는 거래 내역을 그대로 AI에게 넘겨 판단하게 하지 않습니다. 먼저 백엔드와 분석 계층에서 데이터를 정규화하고, 행동 지표를 계산한 뒤, 버전이 관리되는 규칙 엔진이 소비 MBTI를 결정합니다. Qwen3 4B는 결정된 결과와 근거를 사용자가 이해하기 쉬운 설명으로 바꾸는 역할만 담당합니다.

이 구조를 통해 프로젝트는 다음 가치를 지향합니다.

- 작은 모임의 소비 패턴을 직관적인 소비 MBTI로 설명합니다.
- 결과가 왜 나왔는지 계산 근거와 함께 확인할 수 있게 합니다.
- LLM이 민감한 원천 거래 데이터나 개인정보를 직접 판단하지 않도록 책임 경계를 분리합니다.
- 실제 성격 진단, 금융 진단, 은행 연동, 금융상품 추천이 아닌 MVP 범위를 명확히 유지합니다.

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
