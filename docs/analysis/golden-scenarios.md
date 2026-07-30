# Golden Scenarios

## Purpose

Golden scenarios verify that preprocessing, behavior metrics, and rule-engine versions remain stable as the project evolves.

## Required Scenario Types

- Balanced normal spending
- Shared social spending
- Practical concentrated spending
- Diverse experience spending
- Planned recurring spending
- Spontaneous volatile spending
- Sparse insufficient data
- Synthetic mock scenario

## Current Mock Fixture Expectations

`backend/app/modules/transactions/fixtures/transactions_mock_v2.csv` is the current generated mock transaction fixture used before BE Phase 6 orchestration is implemented. The fixture is grouped by the `SCN-xx` prefix in `source_row_key`.

| Scenario | Expected handling | Expected consumption MBTI | Result status | Notes |
| --- | --- | --- | --- | --- |
| `SCN-01` | Analyze | `ENFJ` | `PROVISIONAL` | Synthetic data; TF axis is near the low-margin threshold. |
| `SCN-02` | Analyze | `ISTJ` | `PROVISIONAL` | Synthetic data. |
| `SCN-03` | Analyze | `ENTJ` | `PROVISIONAL` | Synthetic data. |
| `SCN-04` | Analyze | `ENFJ` | `PROVISIONAL` | Synthetic data; JP axis is near the low-margin threshold. |
| `SCN-05` | Analyze | `ENFP` | `PROVISIONAL` | Synthetic data; SN and TF axes are near the low-margin threshold. |
| `SCN-06` | Analyze | `ISTJ` | `PROVISIONAL` | Synthetic data. |
| `SCN-07` | Analyze | `INTP` | `PROVISIONAL` | Synthetic data; EI axis is near the low-margin threshold. |
| `SCN-08` | Stop after preprocessing | `null` | `INSUFFICIENT_DATA` | Sparse sample; BE Phase 6 must not invoke rule or LLM judgment. |

These expectations are regression checks for deterministic analysis behavior. They are not user-facing labels embedded in analysis input and must not be used as rule-engine input.

## Rules

- Golden expected MBTI is test metadata only.
- Expected MBTI must not be included in analysis input DTOs.
- Rule version changes must update golden evidence intentionally.
- If a scenario relies on unavailable signals, document the limitation rather than forcing a score.
- Sparse or ineligible scenarios stop at preprocessing. They must not force a consumption MBTI or grounded AI report.
