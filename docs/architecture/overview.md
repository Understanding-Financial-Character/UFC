# UFC MVP Architecture

## Components

- React Web: 모임 관리, 거래 확인, MBTI 결과, 그래프 화면을 제공한다.
- FastAPI: 사용자·모임 관리, 거래 등록·조회, 소비 행동 지표 계산, 소비 MBTI 산출, LLM 리포트 생성을 담당한다.
- PostgreSQL: 사용자, 모임, 거래, 분석 지표, MBTI 결과, AI 리포트를 저장한다.
- Mock Data Generator: MVP 검증용 사용자·모임·거래 시나리오를 생성하고 PostgreSQL seed 데이터로 적재한다.
- LLM API: 계산된 분석 지표를 근거로 설명, 요약 리포트, 질문 문구를 생성한다.

## Backend Boundaries

- `app/modules`: API 라우터와 도메인별 서비스
- `app/analysis`: 소비 행동 지표와 소비 MBTI 계산
- `app/ai`: LLM 요청, 응답 파싱, 프롬프트 관리
- `app/db`: SQLAlchemy Base, 세션, 모델 공통 기반
- `migrations`: Alembic 스키마 변경 이력

## Data Flow

1. 사용자가 모임과 구성원 MBTI를 등록한다.
2. 사용자가 거래 내역을 업로드하거나 Mock 시나리오를 선택한다.
3. FastAPI가 거래 데이터를 PostgreSQL에 저장한다.
4. 분석 엔진이 시간대, 요일, 카테고리, 반복성, 계획성, 변동성 지표를 계산한다.
5. 소비 MBTI 엔진이 네 축의 점수와 최종 유형을 산출한다.
6. LLM API가 수치 근거 기반 리포트를 생성한다.
7. React Web이 결과, 비교 내용, 관계형 그래프를 표시한다.
