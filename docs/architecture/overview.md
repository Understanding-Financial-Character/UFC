# UFC MVP Architecture

## Components

- React Web: 모임 관리, 거래 확인, MBTI 결과, 그래프 화면을 제공한다.
- FastAPI: 사용자·모임 관리, 거래 등록·조회, 분석 실행 오케스트레이션, 결과 저장과 API 응답을 담당한다.
- Python Analysis Layer: 전처리, 데이터 품질, 소비 행동 지표 계산, 규칙 기반 소비 MBTI 산출을 담당한다.
- PostgreSQL: 사용자, 모임, 거래, 분석 지표, MBTI 결과, AI 리포트를 저장한다.
- Mock Data Generator: MVP 검증용 사용자·모임·거래 시나리오를 생성하고 PostgreSQL seed 데이터로 적재한다.
- Ollama / Qwen3 4B: 계산된 분석 지표와 규칙 기반 결과만 근거로 설명, 요약 리포트, 질문 문구를 생성한다.

## Backend Boundaries

- `app/modules`: API 라우터와 도메인별 서비스
- `app/analysis`: 전처리, Feature 계산, Rule Engine
- `app/ai`: Qwen3 Provider, Prompt, 검증, Fallback
- `app/orchestration`: 분석 실행 순서와 상태 전이
- `app/db`: SQLAlchemy Base, 세션, 모델 공통 기반
- `migrations`: Alembic 스키마 변경 이력

## Data Flow

1. 사용자가 모임과 구성원 MBTI를 등록한다.
2. 사용자가 거래 내역을 업로드하거나 Mock 시나리오를 선택한다.
3. FastAPI가 거래 데이터를 PostgreSQL에 저장한다.
4. Analysis Input Adapter가 원천 데이터를 분석 입력 DTO로 변환한다.
5. 전처리와 데이터 품질 정책이 분석 가능 범위와 limitations를 계산한다.
6. Behavior Metric Engine이 행동 지표를 계산한다.
7. Versioned Rule Engine이 네 축 점수와 소비 MBTI를 산출한다.
8. FastAPI가 결과를 저장한다.
9. Qwen3 4B Report Generator가 제한된 근거만 받아 리포트를 생성한다.
10. FastAPI가 AI 리포트를 저장하고 React Web이 결과, 비교 내용, 그래프를 표시한다.

상세 흐름은 `docs/architecture/data-flow.md`, 테이블 기준은 `docs/architecture/data-model.md`를 따른다.
