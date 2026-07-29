# Consumption MBTI Rule Catalog

## Axis Definitions

| Axis | Low pole | High pole | Meaning |
| --- | --- | --- | --- |
| EI | I | E | 생활 and repeat spending vs shared and external activity spending |
| SN | S | N | concrete, practical, concentrated spending vs diverse, culture, experience spending |
| TF | T | F | purpose and efficiency spending vs relationship, anniversary, shared experience spending |
| JP | J | P | planned, recurring, stable spending vs spontaneous, new, volatile spending |

Score direction:

- EI score: higher means E
- SN score: higher means N
- TF score: higher means F
- JP score: higher means P

The same direction contract is recorded in `backend/app/analysis/constants.py`.

## Rule Engine Principles

- Use only calculable features.
- Exclude impossible MVP signals such as living-area distance, restaurant quality, discounts, and payback.
- Treat unavailable features as unavailable, not as zero.
- Renormalize remaining weights over available features.
- Calculate coverage for each axis.
- Defer axis judgment when coverage is too low.
- Produce final MBTI only when all four axes are available.
- Mark mock-data results as `PROVISIONAL`.

## Output Rules

`consumption_mbti_results.mbti_type` is nullable. When data is insufficient, preserve axis scores and limitations instead of forcing a type.

## Versioning

Rule sets must have a version. Future changes to feature weights, thresholds, or pole mapping require a new rule version and verification against golden scenarios.
