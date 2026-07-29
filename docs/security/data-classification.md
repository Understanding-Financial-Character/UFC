# Data Classification

## BE Phase 3 Classification

| Classification | UFC Data |
| --- | --- |
| Public | Service descriptions, MBTI explanation copy |
| Internal | Analysis rules, prompt versions, model settings |
| Personal Data | Email, username, personal MBTI |
| Sensitive Financial Data | Transaction rows, spending patterns, financial reports |
| Authentication Data | Passwords, refresh tokens |

## Public

Information safe to publish in the repository.

- Product description
- Architecture documents
- Synthetic examples without real personal or financial data
- Development commands

## Internal

Project data that should remain in the team workflow.

- Branch and PR tracking
- Non-sensitive implementation notes
- Test evidence without real personal data

## Sensitive

Data requiring minimization and controlled access.

- Uploaded transaction rows
- Merchant and category behavior data
- Member MBTI inputs
- Group membership data
- Analysis metrics and AI reports
- Share card metadata before explicit user sharing
- Email and personal MBTI values are treated as personal data within this sensitive-control boundary.

## Authentication Data

Data that must never be stored or logged in plaintext.

- Passwords
- Refresh tokens
- Access tokens

Passwords are stored only as Argon2id hashes. Refresh tokens are stored only as SHA-256 hashes.

## Restricted

Data not allowed in the MVP repository or mock fixtures.

- Real account numbers
- Bank authentication credentials
- Transfer credentials
- Credit score data
- Government identifiers
- Raw production financial exports
- API keys and secrets

## MVP Rule

MVP development may use synthetic or manually uploaded transaction-like data only. Any example committed to the repository must be synthetic and clearly marked.

## Control Matrix

| Classification | Storage | Logging | External transfer | Test data | Access |
| --- | --- | --- | --- | --- | --- |
| Public | Allowed in repository and public docs | Allowed | Allowed | Allowed | No restriction |
| Internal | Internal repository and project tools only | Minimized | Prohibited by default | Synthetic data only | Project members |
| Sensitive | Application database only; encryption required before production-like use | Raw values prohibited | Allowed only after field minimization | Synthetic or de-identified data only | Resource owner and group members |
| Restricted | Not allowed in MVP storage | Prohibited | Prohibited | Prohibited | Not applicable |
| Authentication Data | Application database hashes only | Prohibited | Prohibited | Synthetic test credentials only | Owning user for token lifecycle; backend verification only |

## LLM Transfer Rules

- Member MBTI values are Sensitive.
- The AI layer may receive member MBTI values only when needed for comparison text.
- The AI layer must receive display labels or internal member references instead of real names when possible.
- Raw transaction rows should not be sent to the LLM API.
- Analysis metrics, aggregate category ratios, axis scores, and limitation flags are preferred over raw financial details.
