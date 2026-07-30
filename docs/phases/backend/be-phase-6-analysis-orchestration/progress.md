# BE Phase 6 - Analysis Orchestration Progress

## Current Status
IMPLEMENTED
## Implemented
- Analysis orchestration API:
  - `POST /api/v1/groups/{groupId}/analyses`
  - `GET /api/v1/analyses/{analysisId}`
  - `GET /api/v1/groups/{groupId}/analyses/latest`
  - `POST /api/v1/analyses/{analysisId}/retry`
- Group ownership and readiness checks before analysis execution.
- Active run conflict prevention for the same group.
- Transaction lookup by requested period and conversion from DB entities to pure `AnalysisInput` DTOs.
- Synchronous MVP orchestration through preprocessing, behavior metrics, rule engine, persistence, and grounded AI report generation.
- Behavior metric, consumption MBTI, AI report, minimized analysis input snapshot, snapshot hash, and version persistence.
- LLM/report fallback isolation so deterministic rule results remain persisted.
- `INSUFFICIENT_DATA` runs skip AI report generation and preserve deterministic outputs only.
- Analysis periods use the canonical `Asia/Seoul` calendar boundary before UTC persistence/querying.
- Failed run retry is limited to `FAILED` analyses and reuses the original persisted analysis input snapshot.
- AI report-only retry is available for `PARTIALLY_COMPLETED` runs with failed report rows, without recalculating deterministic outputs.
- AI report-only retry locks the analysis run and rejects concurrent retry attempts.
- AI report-only retry uses member MBTI summary from the persisted analysis input snapshot.
- Legacy failed runs without valid snapshots return `ANALYSIS_SNAPSHOT_UNAVAILABLE` instead of leaking a server error.
- API response DTOs that do not expose SQLAlchemy entities or raw transaction arrays.
## Remaining
Frontend polling integration remains a later frontend phase.
## Contract Changes
- `api-contracts.md` documents Phase 6 analysis create/get/latest/retry endpoints.
- `api-contracts.md` documents report-only retry.
- `analysis-output-contract.md` documents Phase 6 terminal analysis statuses, input snapshot persistence, AI skip behavior for insufficient data, and report retry behavior.
- `data-model.md` documents extended `analysis_runs.status` values, `analysis_input_snapshot`, and `retried_from_analysis_id`.
## Migration Changes
`20260730_0006_analysis_orchestration.py` extends `analysis_run_status`, adds `analysis_input_snapshot` and `retried_from_analysis_id`, and updates the lifecycle check constraint.
## Linked PR
- PR: #19
- Branch: `feat/be-phase-6-analysis-orchestration`
## Commits
- Initial implementation: `d25b552`
- Review fixes verified: `a9bf962`
- Verification record: `c3afd61`
- Report retry review fix: `9fb4390`
- Report retry concurrency/snapshot fix: `b78be41`
## Blockers
None.
## Handover Notes
Qwen/report generation receives only grounded aggregate evidence. Raw transaction arrays are not included in the AI report prompt context or API response.
