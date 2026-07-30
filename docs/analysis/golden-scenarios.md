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

Generation baseline:

- Behavior feature schema version: `behavior-features-v1`
- Behavior feature policy version: `behavior-policy-v1`
- Category mapping version: `category-map-v2`
- Rule version: `consumption-mbti-v1`

| Scenario | Expected handling | Expected consumption MBTI | Axis scores `EI/SN/TF/JP` | Low-margin axes | Result status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `SCN-01` | Analyze | `ENFJ` | `0.7894 / 0.7746 / 0.5068 / 0.4312` | `TF` | `PROVISIONAL` | Synthetic data. |
| `SCN-02` | Analyze | `ISTJ` | `0.2880 / 0.3902 / 0.3637 / 0.3283` | None | `PROVISIONAL` | Synthetic data. |
| `SCN-03` | Analyze | `ENTJ` | `0.6458 / 0.5584 / 0.1861 / 0.3603` | None | `PROVISIONAL` | Synthetic data. |
| `SCN-04` | Analyze | `ENFJ` | `0.7056 / 0.6916 / 0.5527 / 0.4890` | `JP` | `PROVISIONAL` | Synthetic data. |
| `SCN-05` | Analyze | `ENFP` | `0.5847 / 0.5111 / 0.5442 / 0.5995` | `SN`, `TF` | `PROVISIONAL` | Synthetic data. |
| `SCN-06` | Analyze | `ISTJ` | `0.2146 / 0.3967 / 0.2090 / 0.4008` | None | `PROVISIONAL` | Synthetic data. |
| `SCN-07` | Analyze | `INTP` | `0.4898 / 0.6925 / 0.1383 / 0.6293` | `EI` | `PROVISIONAL` | Synthetic data. |
| `SCN-08` | Stop after preprocessing | `null` | Not applicable | Not applicable | `INSUFFICIENT_DATA` | Sparse sample; BE Phase 6 must not invoke rule or LLM judgment. |

These expectations are regression checks for deterministic analysis behavior. They are not user-facing labels embedded in analysis input and must not be used as rule-engine input.

The regression tests also assert the primary evidence metric set for `SCN-05`. If a golden result changes, reviewers should compare axis scores, low-margin axes, rule version, metric schema version, category mapping version, and primary evidence before deciding whether the change is a regression or an intentional rule update.

## Rules

- Golden expected MBTI is test metadata only.
- Expected MBTI must not be included in analysis input DTOs.
- Rule version changes must update golden evidence intentionally.
- If a scenario relies on unavailable signals, document the limitation rather than forcing a score.
- Sparse or ineligible scenarios stop at preprocessing. They must not force a consumption MBTI or grounded AI report.
