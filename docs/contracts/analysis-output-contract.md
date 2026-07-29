# Analysis Output Contract

## Purpose

Defines the conceptual result produced by the deterministic analysis layer and consumed by frontend and AI report generation.

## Required Conceptual Fields

- `analysis_id`
- `group_id`
- `analysis_period`
- `transaction_count`
- `spending_mbti`
- `axis_scores`
- `confidence_level`
- `evidence_metrics`
- `member_comparison_summary`
- `graph_nodes`
- `graph_edges`
- `limitations`

## Uncertainty Rules

Analysis output must explicitly mark results as provisional when:

- Transaction count is below the minimum threshold.
- Analysis period is too short.
- Required category or merchant data is missing.
- Data is synthetic or scenario-based.
- Axis scores are too close to call.

## AI Report Dependency

AI reports must be generated from this output and must not introduce unsupported claims.

## Status

This is a Phase 0 conceptual contract. Concrete JSON schema will be finalized during backend and AI phases.
