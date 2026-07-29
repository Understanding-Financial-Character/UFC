# AI Analysis Architecture

## Responsibility

The AI layer turns backend-calculated evidence into readable summaries through Ollama-backed Qwen3 4B.

- Explain the spending MBTI result using provided metrics
- Summarize member MBTI and account spending MBTI similarities and differences
- Generate discussion questions for members
- Produce report text for result and sharing surfaces

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
