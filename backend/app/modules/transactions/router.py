from fastapi import APIRouter, Response, status

from app.api.dependencies import DatabaseSession
from app.modules.auth.dependencies import AuthenticatedPrincipal
from app.modules.transactions import service
from app.modules.transactions.models import Category, Transaction
from app.modules.transactions.schemas import (
    CategoryResponse,
    CsvImportRequest,
    MockScenarioResponse,
    TransactionImportResponse,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(tags=["transactions"])


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: DatabaseSession) -> list[CategoryResponse]:
    return [build_category_response(category) for category in service.list_categories(db)]


@router.get("/mock-scenarios", response_model=list[MockScenarioResponse])
def list_mock_scenarios() -> list[MockScenarioResponse]:
    return [MockScenarioResponse(**scenario) for scenario in service.list_mock_scenarios()]


@router.post(
    "/groups/{group_id}/mock-scenarios/{scenario_id}/apply",
    response_model=TransactionImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_mock_scenario(
    group_id: str,
    scenario_id: str,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> TransactionImportResponse:
    return service.apply_mock_scenario(db, group_id, principal.user_id, scenario_id)


@router.post(
    "/groups/{group_id}/transactions/import",
    response_model=TransactionImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_transactions(
    group_id: str,
    payload: CsvImportRequest,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> TransactionImportResponse:
    return service.import_csv_transactions(db, group_id, principal.user_id, payload.csv_text)


@router.get("/groups/{group_id}/transactions", response_model=list[TransactionResponse])
def list_transactions(
    group_id: str, db: DatabaseSession, principal: AuthenticatedPrincipal
) -> list[TransactionResponse]:
    return [
        build_transaction_response(transaction)
        for transaction in service.list_transactions(db, group_id, principal.user_id)
    ]


@router.patch("/groups/{group_id}/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    group_id: str,
    transaction_id: str,
    payload: TransactionUpdate,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> TransactionResponse:
    transaction = service.update_transaction(
        db, group_id, principal.user_id, transaction_id, payload
    )
    return build_transaction_response(transaction)


@router.delete(
    "/groups/{group_id}/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_transaction(
    group_id: str,
    transaction_id: str,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> Response:
    service.delete_transaction(db, group_id, principal.user_id, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def build_category_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        category_id=category.id,
        code=category.code,
        name=category.name,
        behavior_group=category.behavior_group,
        display_order=category.display_order,
        is_active=category.is_active,
    )


def build_transaction_response(transaction: Transaction) -> TransactionResponse:
    return TransactionResponse(
        transaction_id=transaction.id,
        group_id=transaction.group_id,
        member_id=transaction.member_id,
        category_id=transaction.category_id,
        transaction_at=transaction.transaction_at,
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        merchant_name=transaction.merchant_name,
        description=transaction.description,
        is_shared_expense=transaction.is_shared_expense,
        is_planned=transaction.is_planned,
        is_recurring=transaction.is_recurring,
        is_excluded=transaction.is_excluded,
        exclusion_reason=transaction.exclusion_reason,
        source_type=transaction.source_type,
        source_row_key=transaction.source_row_key,
        created_at=transaction.created_at,
    )
