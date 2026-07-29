# Score Normalization

## Metric Normalization

All rule-engine input metrics must be normalized to `0.0` through `1.0`.

Ratios already in `0.0` through `1.0` keep their value after validation. Volatility metrics are capped at `1.0` unless a later rule version documents another transform.

## Rounding

Stored and API-facing metric values use fixed two-decimal half-up rounding unless a phase contract states a more precise storage format.

## Axis Score Direction

- EI score: higher means E
- SN score: higher means N
- TF score: higher means F
- JP score: higher means P

## Weight Renormalization

If a feature is unavailable, remove it from the axis calculation and renormalize the remaining weights:

```text
effective_weight = configured_weight / sum(configured_weight of available features)
```

Do not assign unavailable features a score of zero.

## Coverage

Coverage is calculated per axis:

```text
coverage = sum(configured_weight of available features)
```

The rule engine may defer an axis when coverage is below the configured threshold.
