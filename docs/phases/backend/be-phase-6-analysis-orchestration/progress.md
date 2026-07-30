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
- Behavior metric, consumption MBTI, AI report, snapshot hash, and version persistence.
- LLM/report fallback isolation so deterministic rule results remain persisted.
- API response DTOs that do not expose SQLAlchemy entities or raw transaction arrays.
## Remaining
Frontend polling integration remains a later frontend phase.
## Contract Changes
- `api-contracts.md` documents Phase 6 analysis create/get/latest/retry endpoints.
- `analysis-output-contract.md` documents Phase 6 terminal analysis statuses.
- `data-model.md` documents extended `analysis_runs.status` values.
## Migration Changes
`20260730_0006_analysis_orchestration.py` extends `analysis_run_status` and updates the lifecycle check constraint.
## Linked PR
Not assigned.
## Commits
Pending final commit.
## Blockers
None.
## Handover Notes
Qwen/report generation receives only grounded aggregate evidence. Raw transaction arrays are not included in the AI report prompt context or API response.
