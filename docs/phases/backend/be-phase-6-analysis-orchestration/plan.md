# BE Phase 6 - Analysis Orchestration

## Status
IMPLEMENTED
## Goal
Coordinate transaction lookup, analysis execution, rule results, persistence, and AI report triggering.
## Why
Analysis workflow needs explicit state transitions, reproducible snapshots, and failure boundaries.
## Prerequisites
BE Phase 5, AN Phase 3, AI runtime/report phases.
## In Scope
Analysis run API, orchestration state transitions, full retry/report retry, failure handling, and snapshot-backed reproducibility.

The orchestration service connects the already implemented lower-level modules in this order:

```text
PostgreSQL group/member/transaction lookup
-> AnalysisInput adapter
-> preprocess_analysis_input()
-> calculate_behavior_metrics()
-> score_consumption_mbti()
-> analysis persistence repositories
-> commit deterministic analysis
-> GroundedReportService outside DB transactions
-> ai_reports persistence
```

If preprocessing and rule output combine to `INSUFFICIENT_DATA`, BE Phase 6 completes the run with `result_status=INSUFFICIENT_DATA`, persists no forced `mbti_type`, and skips Qwen/report generation.
## Out of Scope
New metric formulas, rule definitions, frontend UI.
## Responsible Modules
`backend/app/orchestration`, `backend/app/modules`, tests.
## Contracts
Analysis run API contracts:

- `POST /groups/{groupId}/analyses`
- `GET /analyses/{analysisId}`
- `GET /groups/{groupId}/analyses/latest`
- `POST /analyses/{analysisId}/retry`
- `POST /analyses/{analysisId}/report/retry`

The report response must expose the AI Phase 2 `grounded-ai-report-v1` fields as documented in `docs/contracts/api-contracts.md` and `docs/contracts/analysis-output-contract.md`.
## Data Changes
Extends `analysis_runs` with minimized `analysis_input_snapshot` JSON and nullable `retried_from_analysis_id` for failed-run snapshot retries.
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
Implemented orchestration services, analysis APIs, state transition persistence, DB-to-analysis DTO conversion, insufficient-data AI skip, snapshot-backed full retry policy, locked report-only retry policy, and tests.

- DB entities are adapted into pure `AnalysisInput` before entering `backend/app/analysis`.
- Owner authorization is applied before creating or reading analysis resources.
- Analysis periods use the canonical `Asia/Seoul` calendar boundary before UTC persistence/querying.
- Deterministic analysis is committed before invoking Qwen/report generation.
- Qwen/report generation runs outside deterministic DB transactions.
- AI report failure does not roll back deterministic behavior metrics or MBTI results.
- Full retry is limited to `FAILED` runs and reuses the persisted input snapshot.
- Report-only retry is limited to `PARTIALLY_COMPLETED` runs with failed AI report rows.
- Report-only retry locks the analysis run, rejects concurrent retry attempts, and uses member MBTI summary from the persisted snapshot.
- API responses use DTOs, never ORM entities.
## Test Scenarios
Success, insufficient data without AI generation, KST period boundaries, full retry policy, report-only retry policy, concurrent report retry rejection, snapshot-based report retry member summary, legacy snapshot rejection, AI failure, owner denial.
## Completion Criteria
End-to-end backend analysis path verified with synchronous MVP execution.

- Analysis endpoints are implemented and routed.
- Mock/user transactions can be analyzed, persisted, and retrieved through APIs.
- Deterministic MBTI output remains available even when Qwen/report generation fails.
- API response schema matches `grounded-ai-report-v1`.
- Sparse data does not trigger AI report generation.
## Branch
`feat/be-phase-6-analysis-orchestration`
## Dependencies
BE Phase 5, AN Phase 3, AI Phase 2.
