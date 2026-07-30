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

## Input Ownership

The backend provides `analysis-input-v1` with source-level transaction facts. The analysis layer owns:

- transaction-type filtering
- category-to-behavior-group mapping
- synthetic data and source-type quality handling
- analysis-period sufficiency checks
- feature availability decisions

AN Phase 2 adds the deterministic behavior feature engine. It consumes preprocessed `NormalizedTransaction` rows and emits `behavior-features-v1` without applying axis weights, MBTI rules, persistence, API routing, or Qwen3 calls.

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
