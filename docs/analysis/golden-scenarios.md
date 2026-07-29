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

## Rules

- Golden expected MBTI is test metadata only.
- Expected MBTI must not be included in analysis input DTOs.
- Rule version changes must update golden evidence intentionally.
- If a scenario relies on unavailable signals, document the limitation rather than forcing a score.
