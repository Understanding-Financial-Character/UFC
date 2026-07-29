# Mock Scenario Policy

## Source of Truth

Scenario definitions are managed as YAML or Python configuration, not hand-edited CSV tables.

Pipeline:

```text
Scenario Definition -> Mock Generator -> Generated CSV -> PostgreSQL Seed -> Golden Test
```

Generated CSV files are treated as source transaction data after generation.

## Test Expectations

Scenario expected MBTI values are for golden tests only. They must not be passed into the rule engine as inputs.

## Result Status

Mock scenario analysis results are marked `PROVISIONAL` because they are synthetic.

## Repository Rules

- Scenario definitions live in `mock-data/scenarios`.
- Generated CSV artifacts live in `mock-data/generated`.
- Do not commit real personal or financial data.
