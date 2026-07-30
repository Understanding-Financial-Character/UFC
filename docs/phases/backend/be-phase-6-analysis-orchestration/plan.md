# BE Phase 6 - Analysis Orchestration

## Status
NOT_STARTED
## Goal
Coordinate transaction lookup, analysis execution, rule results, persistence, and AI report triggering.
## Why
Analysis workflow needs explicit state transitions and failure boundaries.
## Prerequisites
BE Phase 5, AN Phase 3, AI runtime/report phases.
## In Scope
Analysis run API, orchestration state transitions, retry/failure handling.

The orchestration service must connect the already implemented lower-level modules in this order:

```text
PostgreSQL group/member/transaction lookup
-> AnalysisInput adapter
-> preprocess_analysis_input()
-> calculate_behavior_metrics()
-> score_consumption_mbti()
-> analysis persistence repositories
-> GroundedReportService
-> ai_reports persistence
```

If preprocessing returns `analysis_eligible=false` with `INSUFFICIENT_DATA`, BE Phase 6 must complete the run with `result_status=INSUFFICIENT_DATA`, persist no forced `mbti_type`, and skip rule-engine and Qwen judgment.
## Out of Scope
New metric formulas, rule definitions, frontend UI.
## Responsible Modules
`backend/app/orchestration`, `backend/app/modules`, tests.
## Contracts
Analysis run API contracts:

- `POST /groups/{groupId}/analyses`
- `GET /analyses/{analysisId}`
- `GET /analyses/{analysisId}/report`

The report response must expose the AI Phase 2 `grounded-ai-report-v1` fields as documented in `docs/contracts/api-contracts.md` and `docs/contracts/analysis-output-contract.md`.
## Data Changes
No new tables beyond BE Phase 5 unless explicitly approved.
## Security Considerations
Owner checks on analysis and report resources.

Qwen3 input must be built only from deterministic analysis outputs:

- spending MBTI
- axis scores
- confidence
- top evidence
- member MBTI summary
- limitations
- result status

It must not include email, nickname, internal user id, raw transaction arrays, transaction memo text, ciphertext, tokens, or secrets.
## Implementation Tasks
Define orchestration services and tests.

- Add a DB-to-analysis DTO adapter without passing SQLAlchemy entities into `backend/app/analysis`.
- Create analysis runs with `RUNNING` or `PENDING` execution status.
- Apply owner authorization before creating or reading analysis resources.
- Run preprocessing and stop early on `INSUFFICIENT_DATA`.
- Calculate behavior metrics only from normalized eligible transactions.
- Run the rule engine only after sufficient preprocessing output exists.
- Persist behavior metrics, consumption MBTI result, and AI report under one explicit transaction boundary.
- Save fallback AI reports as `FALLBACK_COMPLETED` without invalidating deterministic results.
- Return analysis and report DTOs, never ORM entities.
## Test Scenarios
Success, insufficient data, AI failure, owner denial.

- Mock fixture `SCN-01` through `SCN-07` produce the documented golden MBTI values through the full backend path.
- Mock fixture `SCN-08` stops before rule and LLM judgment with `INSUFFICIENT_DATA`.
- Qwen timeout or invalid JSON stores a fallback report.
- Another user cannot create, list, or read analysis/report resources for an owned group.
- Repeated requests for the same group and period do not create contradictory completed runs.
## Completion Criteria
End-to-end backend analysis path verified.

- The three analysis/report endpoints are implemented and routed.
- Mock data can be applied, analyzed, persisted, and retrieved through APIs.
- Deterministic MBTI output remains available even when Qwen fails.
- API response schema matches `grounded-ai-report-v1`.
- Golden mock pipeline expectations in `docs/analysis/golden-scenarios.md` pass through backend API tests.
## Branch
`feat/be-phase-6-analysis-orchestration`
## Dependencies
BE Phase 5, AN Phase 3, AI Phase 2.
