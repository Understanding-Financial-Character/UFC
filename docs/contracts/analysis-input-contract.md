# Analysis Input Contract

## Purpose

Defines the structured input that deterministic analysis and AI report generation may consume.

## Required Conceptual Fields

- `group_id`: Internal group identifier
- `analysis_period`: Start and end dates for the analyzed period
- `members`: Member identifiers and self-declared MBTI values
- `transactions`: Normalized transaction records
- `scenario_source`: Uploaded data or mock scenario reference

## Transaction Fields

- Internal transaction identifier
- Transaction date and time
- Amount
- Direction or transaction type
- Merchant label or normalized merchant key
- Category
- Optional memo or scenario tag
- Recurring or one-time marker when available

## Data Constraints

- Real account numbers are not accepted.
- Raw personal identifiers should be excluded unless needed for MVP behavior.
- Synthetic data must be marked as synthetic.
- Uploaded data must be validated before analysis.

## Status

This is a Phase 0 conceptual contract. Backend implementation will convert it into concrete Pydantic schemas.
