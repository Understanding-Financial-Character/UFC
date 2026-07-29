# UFC Data Flow

## End-to-End Flow

User -> React -> FastAPI -> PostgreSQL source data lookup -> Analysis Input Adapter -> Analysis Preprocessing / Data Quality -> Behavior Metric Engine -> Consumption MBTI Rule Engine -> Result storage -> Qwen3 4B Report Generator -> AI Report storage -> React Result View

## Data Shape Flow

Raw Transaction -> AnalysisInput Transaction -> Preprocessed Spending Transaction -> Behavior Metrics -> Axis Scores -> Consumption MBTI -> Grounded AI Report

## Responsibility Split

- FastAPI Backend stores transactions, validates ownership, and builds `analysis-input-v1` without sensitive identity fields.
- Python Analysis Layer preprocesses analysis input transactions, filters non-spending transaction types, derives behavior groups, scores data quality, and calculates behavior metrics.
- Versioned Rule Engine determines E/I, S/N, T/F, and J/P.
- Ollama-backed Qwen3 4B turns calculated evidence into user-friendly text.

Consumption MBTI is never decided by the LLM.

## Analysis Input Boundary

The backend passes source-level analysis fields such as `groupPurposeType`, `analysisPeriod`, `sourceType`, `isSynthetic`, `transactionId`, nullable `memberId`, `transactionType`, and `categoryCode`.

AN Phase 1 owns preprocessing decisions:

- `DEPOSIT`, `REFUND`, `ADJUSTMENT`, and `TRANSFER` rows are not treated as ordinary spending.
- `categoryCode -> behaviorGroup` mapping is versioned in the analysis layer.
- Unknown behavior groups make dependent features unavailable instead of zero.
- Synthetic/mock runs are carried into uncertainty and result-status policy.

## Qwen3 4B Allowed Input

- Consumption MBTI
- Axis scores
- Confidence
- Top evidence
- Member MBTI summary
- Limitations
- Result status

## Qwen3 4B Prohibited Input

- User email
- User name or nickname
- Internal user id
- Full transaction array
- Raw transaction memo text
- Token
- Ciphertext or encrypted storage fields
- Secret

## MVP Exclusions

UFC does not connect to real bank accounts, execute transfers, run credit-score analysis, recommend financial products, or diagnose real personality traits.
