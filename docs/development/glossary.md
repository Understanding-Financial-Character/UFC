# Glossary

This glossary keeps Korean planning terms and contract field names aligned.

| Korean term | Contract term | Meaning |
| --- | --- | --- |
| 분석 결과 상태 | `result_status` | Whether the completed analysis result is final or provisional. |
| 잠정 결과 | `PROVISIONAL` | Result can be shown, but limitations must be displayed. |
| 표준 근거 결과 | `STANDARD` | Result satisfies MVP data sufficiency rules, but is still a behavioral interpretation. |
| 거래 내역 | `transaction` | Normalized spending or deposit record used for MVP analysis. |
| 소비 MBTI | `spending_mbti` | MBTI-format label derived from spending behavior, not personality diagnosis. |
| 분석 신뢰도 | `confidence` | Confidence level and score for the analysis result. |
| 제한사항 | `limitations` | User-facing caveats that explain data or scoring constraints. |
| 결과 부족 | `INSUFFICIENT_DATA` | Data is too sparse to force a consumption MBTI. |
| 행동 지표 | `behavior_metrics` | Deterministic metrics calculated from normalized transactions. |
| 규칙 엔진 | `rule_engine` | Versioned deterministic logic that maps metrics to axis scores and consumption MBTI. |
| 삼상 Boolean | `tri_state_boolean` | `TRUE`, `FALSE`, and `NULL` retain separate meanings; `NULL` means unknown. |
| Qwen 리포트 | `ai_report` | User-friendly grounded text generated from deterministic evidence. |
| 축별 기여 | `axis_contributions` | Per-axis contribution details used to explain rule-engine scoring. |
