# Score Normalization

## Metric Normalization

All rule-engine input metrics must be normalized to `0.0` through `1.0`.

Ratios already in `0.0` through `1.0` keep their value after validation. AN Phase 2 volatility records raw CV separately and caps only `normalized_score` at `1.0`.

## Rounding

AN Phase 3 rule-engine values use four-decimal rounding for axis scores, coverage, normalized weights, and contributions.

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

AN Phase 3 thresholds:

- `coverage >= 0.70`: standard
- `0.50 <= coverage < 0.70`: provisional
- `coverage < 0.50`: deferred

Axis margin is measured in points from the midpoint:

```text
margin = abs(axis_score - 0.5) * 100
```

Exact midpoint ties at `0.50` defer the axis with `AXIS_SCORE_TIE`. Non-zero margins below `5.0` points keep the axis decision but add `LOW_AXIS_SCORE_MARGIN`.
