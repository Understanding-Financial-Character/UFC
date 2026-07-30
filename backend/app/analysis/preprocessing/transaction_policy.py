from __future__ import annotations

from app.analysis.contracts import AnalysisTransactionInput, AnalysisTransactionType

EXCLUDED_NON_SPENDING_REASONS = {
    AnalysisTransactionType.DEPOSIT: "DEPOSIT_EXCLUDED_FROM_SPENDING_ANALYSIS",
    AnalysisTransactionType.REFUND: "REFUND_EXCLUDED_FROM_SPENDING_ANALYSIS",
    AnalysisTransactionType.TRANSFER: "TRANSFER_EXCLUDED_FROM_SPENDING_ANALYSIS",
    AnalysisTransactionType.ADJUSTMENT: "ADJUSTMENT_EXCLUDED_FROM_SPENDING_ANALYSIS",
}


def exclusion_reason_for(transaction: AnalysisTransactionInput) -> str | None:
    if transaction.is_excluded:
        return "SOURCE_TRANSACTION_EXCLUDED"
    if transaction.transaction_type == AnalysisTransactionType.WITHDRAWAL:
        return None
    return EXCLUDED_NON_SPENDING_REASONS[transaction.transaction_type]
