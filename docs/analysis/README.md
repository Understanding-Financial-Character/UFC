# Analysis Layer

## Purpose

The analysis layer converts normalized transaction data into deterministic behavior evidence and rule-based consumption MBTI results.

It does not call Qwen3, shape final UI copy, persist database rows directly, or diagnose real personality.

## Pipeline

1. Analysis Input Adapter
2. Preprocessing and Data Quality
3. Behavior Metric Engine
4. Score Normalization
5. Consumption MBTI Rule Engine
6. Result DTO for backend persistence and AI report generation

## Entry Documents

- [Feature Catalog](feature-catalog.md)
- [Rule Catalog](rule-catalog.md)
- [Score Normalization](score-normalization.md)
- [Data Quality Policy](data-quality-policy.md)
- [Uncertainty Policy](uncertainty-policy.md)
- [Mock Scenario Policy](mock-scenario-policy.md)
- [Golden Scenarios](golden-scenarios.md)

## Non-Goals

- LLM-based score calculation
- Real financial diagnosis
- Real personality diagnosis
- Bank-grade transaction categorization
- Feature inference from unavailable signals
