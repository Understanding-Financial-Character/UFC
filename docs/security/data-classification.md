# Data Classification

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
