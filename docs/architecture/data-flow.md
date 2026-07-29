# UFC Data Flow

## End-to-End Flow

User -> React -> FastAPI -> PostgreSQL source data lookup -> Analysis Input Adapter -> Preprocessing / Data Quality -> Behavior Metric Engine -> Consumption MBTI Rule Engine -> Result storage -> Qwen3 4B Report Generator -> AI Report storage -> React Result View

## Data Shape Flow

Raw Transaction -> Normalized Transaction -> Behavior Metrics -> Axis Scores -> Consumption MBTI -> Grounded AI Report

## Responsibility Split

- FastAPI Backend stores transactions and serves APIs.
- Python Analysis Layer preprocesses normalized transactions and calculates behavior metrics.
- Versioned Rule Engine determines E/I, S/N, T/F, and J/P.
- Ollama-backed Qwen3 4B turns calculated evidence into user-friendly text.

Consumption MBTI is never decided by the LLM.

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
