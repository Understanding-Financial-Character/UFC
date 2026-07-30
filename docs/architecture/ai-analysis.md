# AI Analysis Architecture

## Responsibility

The AI layer turns backend-calculated evidence into readable summaries through Ollama-backed Qwen3 4B.

- Explain the spending MBTI result using provided metrics
- Summarize member MBTI and account spending MBTI similarities and differences
- Generate discussion questions for members
- Produce report text for result and sharing surfaces

## Runtime Boundary

AI Phase 1 provides a provider boundary under `backend/app/ai`:

- `ReportGenerator` protocol
- `OllamaQwenReportGenerator` for local Ollama `qwen3:4b`
- `FakeReportGenerator` for deterministic tests
- `TemplateReportGenerator` for fallback-style deterministic text

The provider receives only aggregate, grounded report input. It does not query SQLAlchemy models, access FastAPI routers, run orchestration, or load raw transactions.

## Ollama Runtime Settings

- `LLM_PROVIDER=ollama`
- `LLM_BASE_URL=http://ollama:11434`
- `LLM_MODEL=qwen3:4b`
- `LLM_THINKING_ENABLED=false`
- `LLM_TEMPERATURE=0.2`
- `LLM_TIMEOUT_SECONDS=30`

The Ollama provider checks `/api/tags` before generation and fails when the configured model is missing. Generation uses non-streaming responses, non-thinking mode by default, and conservative options.

## Deterministic Before Generative

Qwen3 4B must not be the source of truth for scores, categories, or final spending MBTI type.

The backend analysis module calculates metrics and the versioned rule engine determines type candidates first. The AI layer receives those values as input and explains them.

## Uncertainty Constraint

Spending MBTI results are behavioral interpretations of a specific transaction period. They are not personality diagnoses.

When input data is sparse, incomplete, synthetic, or below the minimum analysis threshold, AI output must preserve that uncertainty and avoid definitive language.

## Required Evidence

AI report prompts should include only structured analysis evidence such as:

- Analysis period
- Transaction count
- Category distribution
- Weekend and time-of-day ratios
- Recurring and new merchant ratios
- Planned and irregular spending ratios
- Volatility or average payment metrics
- Axis scores and confidence level
- Result status and limitations

## Prohibited AI Input

Prompts must not include:

- User email
- User name or nickname
- Internal user id
- Full transaction arrays
- Raw transaction memo text
- Tokens
- Ciphertext or encrypted fields
- Secrets

## Prohibited AI Behavior

- Inferring real personality traits from spending data
- Inventing transactions, members, categories, or scores
- Recommending financial products in the MVP
- Claiming bank-grade account integration exists
- Deciding the consumption MBTI independently from rule-engine output
