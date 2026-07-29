# UFC

UFC(Understand Financial Character)는 개인 MBTI와 모임통장 소비 패턴을 함께 분석해, 소규모 모임의 공동 소비 성향을 MBTI 형식과 그래프, AI 요약 리포트로 보여주는 MVP 프로젝트입니다.

## 핵심 범위

- 2~4인 모임 생성 및 구성원 MBTI 등록
- 거래 내역 업로드 또는 Mock 데이터 선택
- 소비 행동 지표 계산 및 모임통장 소비 MBTI 산출
- 개인 MBTI와 통장 소비 MBTI 비교
- LLM 기반 요약 리포트와 소비 패턴 그래프 제공

## 기술 스택

- Backend: Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- Frontend: React, TypeScript, Vite
- Infra: Docker Compose, Nginx

## 문서

- [아키텍처](docs/architecture/overview.md)
- [API 계약](docs/contracts/api-contracts.md)
- [개발 Phase](docs/phases/README.md)
- [보안 기준](docs/security/data-classification.md)
- [개발 가이드](docs/development/setup.md)
- [PRD 요약](docs/evidence/prd-summary.md)
- [트러블슈팅](docs/troubleshooting/README.md)

## 로컬 개발

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.dev.yaml up --build
```
