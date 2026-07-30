from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiException
from app.modules.groups.models import Group, GroupMember, GroupMemberStatus
from app.modules.groups.service import get_owned_group
from app.modules.transactions.models import (
    Category,
    CategoryBehaviorGroup,
    Transaction,
    TransactionSourceType,
    TransactionType,
)
from app.modules.transactions.schemas import (
    RowValidationError,
    TransactionImportResponse,
    TransactionImportRowResult,
    TransactionUpdate,
)

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
CATEGORY_SEED_PATH = FIXTURE_ROOT / "categories_seed_v2.csv"
MOCK_TRANSACTION_PATH = FIXTURE_ROOT / "transactions_mock_v2.csv"
MOCK_SCENARIOS = {
    "mock-v2": {
        "name": "Mock Transactions V2",
        "description": "Synthetic group-account transactions for BE Phase 4.",
    }
}

ALLOWED_CSV_FIELDS = {
    "id",
    "group_id",
    "member_id",
    "category_id",
    "transaction_at",
    "transaction_type",
    "amount",
    "currency_code",
    "merchant_name",
    "description",
    "is_shared_expense",
    "is_planned",
    "is_recurring",
    "is_excluded",
    "exclusion_reason",
    "category_source",
    "category_confidence",
    "source_type",
    "source_row_key",
    "created_at",
    "updated_at",
}
SENSITIVE_FIELD_HINTS = {"account", "card", "bank_auth", "access_token", "refresh_token"}


@dataclass
class ParsedTransactionRow:
    row_number: int
    source_row_key: str | None
    transaction_at: datetime
    transaction_type: TransactionType
    amount: Decimal
    category_id: str | None
    member_id: str | None
    merchant_name: str | None
    description: str | None
    is_shared_expense: bool | None
    is_planned: bool | None
    is_recurring: bool | None
    is_excluded: bool
    exclusion_reason: str | None


def ensure_seed_categories(db: Session) -> None:
    existing_ids = set(db.scalars(select(Category.id)).all())
    with CATEGORY_SEED_PATH.open(encoding="utf-8-sig", newline="") as seed_file:
        for row in csv.DictReader(seed_file):
            if row["id"] in existing_ids:
                continue
            db.add(
                Category(
                    id=row["id"],
                    code=row["code"].strip(),
                    name=row["name"].strip(),
                    behavior_group=CategoryBehaviorGroup(row["behavior_group"].strip()),
                    display_order=int(row["display_order"]),
                    is_active=parse_required_bool(row["is_active"]),
                    created_at=parse_datetime(row["created_at"]),
                    updated_at=parse_datetime(row["updated_at"]),
                )
            )
    db.commit()


def list_categories(db: Session) -> list[Category]:
    ensure_seed_categories(db)
    return list(
        db.scalars(
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.display_order, Category.name)
        ).all()
    )


def list_mock_scenarios() -> list[dict[str, object]]:
    rows = read_mock_transaction_rows()
    return [
        {
            "scenario_id": "mock-v2",
            "name": MOCK_SCENARIOS["mock-v2"]["name"],
            "description": MOCK_SCENARIOS["mock-v2"]["description"],
            "transaction_count": len(rows),
        }
    ]


def import_csv_transactions(
    db: Session, group_id: str, owner_user_id: str, csv_text: str
) -> TransactionImportResponse:
    group = get_owned_group(db, group_id, owner_user_id)
    ensure_seed_categories(db)
    parsed_rows = parse_csv_text(csv_text, group.id)
    return persist_import_rows(db, group, parsed_rows, TransactionSourceType.CSV_UPLOAD)


def apply_mock_scenario(
    db: Session, group_id: str, owner_user_id: str, scenario_id: str
) -> TransactionImportResponse:
    if scenario_id not in MOCK_SCENARIOS:
        raise ApiException(code="NOT_FOUND", message="Mock scenario was not found.", status_code=404)
    group = get_owned_group(db, group_id, owner_user_id)
    ensure_seed_categories(db)
    mock_rows = read_mock_transaction_rows()
    rows = [row for row in mock_rows if row.get("group_id") == group.id]
    if not rows:
        first_group_id = mock_rows[0]["group_id"] if mock_rows else None
        rows = [dict(row) for row in mock_rows if row.get("group_id") == first_group_id]
        member_map = build_mock_member_map(rows, group)
        for row in rows:
            row["group_id"] = group.id
            row["member_id"] = member_map.get(row.get("member_id"), "")
    parsed_rows = [parse_row(index, row, group.id) for index, row in enumerate(rows, start=2)]
    return persist_import_rows(db, group, parsed_rows, TransactionSourceType.MOCK)


def list_transactions(db: Session, group_id: str, owner_user_id: str) -> list[Transaction]:
    group = get_owned_group(db, group_id, owner_user_id)
    return list(
        db.scalars(
            select(Transaction)
            .where(Transaction.group_id == group.id)
            .order_by(Transaction.transaction_at, Transaction.created_at)
        ).all()
    )


def update_transaction(
    db: Session,
    group_id: str,
    owner_user_id: str,
    transaction_id: str,
    payload: TransactionUpdate,
) -> Transaction:
    group = get_owned_group(db, group_id, owner_user_id)
    transaction = get_group_transaction(db, group.id, transaction_id)
    fields = payload.model_fields_set

    if "member_id" in fields:
        ensure_active_member_belongs_to_group(db, group.id, payload.member_id)
        transaction.member_id = payload.member_id
    if "category_id" in fields:
        ensure_category_exists(db, payload.category_id)
        transaction.category_id = payload.category_id
    if "transaction_at" in fields and payload.transaction_at is not None:
        transaction.transaction_at = payload.transaction_at
    if "transaction_type" in fields and payload.transaction_type is not None:
        transaction.transaction_type = payload.transaction_type
    if "amount" in fields and payload.amount is not None:
        transaction.amount = payload.amount
    if "merchant_name" in fields:
        transaction.merchant_name = payload.merchant_name
    if "description" in fields:
        transaction.description = payload.description
    if "is_shared_expense" in fields:
        transaction.is_shared_expense = payload.is_shared_expense
    if "is_planned" in fields:
        transaction.is_planned = payload.is_planned
    if "is_recurring" in fields:
        transaction.is_recurring = payload.is_recurring
    if "is_excluded" in fields and payload.is_excluded is not None:
        transaction.is_excluded = payload.is_excluded
    if "exclusion_reason" in fields:
        transaction.exclusion_reason = payload.exclusion_reason

    if transaction.is_excluded and transaction.exclusion_reason is None:
        raise ApiException(
            code="VALIDATION_ERROR",
            message="exclusion_reason is required for excluded transactions.",
            status_code=400,
            details={"field": "exclusion_reason"},
        )
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, group_id: str, owner_user_id: str, transaction_id: str) -> None:
    group = get_owned_group(db, group_id, owner_user_id)
    transaction = get_group_transaction(db, group.id, transaction_id)
    db.delete(transaction)
    db.commit()


def parse_csv_text(
    csv_text: str, expected_group_id: str
) -> list[ParsedTransactionRow | TransactionImportRowResult]:
    reader = csv.DictReader(StringIO(csv_text))
    if reader.fieldnames is None:
        return [rejected_row(1, None, "csv_text", "CSV_EMPTY", "CSV header is required.")]
    fields = {field.strip() for field in reader.fieldnames}
    sensitive_fields = [
        field
        for field in fields
        if any(sensitive_hint in field.lower() for sensitive_hint in SENSITIVE_FIELD_HINTS)
    ]
    if sensitive_fields:
        return [
            rejected_row(
                1,
                None,
                "header",
                "SENSITIVE_FIELD_NOT_ALLOWED",
                "CSV must not include account, card, bank auth, or token fields.",
            )
        ]
    unknown_fields = fields - ALLOWED_CSV_FIELDS
    if unknown_fields:
        return [
            rejected_row(
                1,
                None,
                "header",
                "CSV_UNKNOWN_FIELD",
                f"Unsupported CSV fields: {', '.join(sorted(unknown_fields))}.",
            )
        ]

    return [parse_row(row_number, row, expected_group_id) for row_number, row in enumerate(reader, start=2)]


def parse_row(
    row_number: int, row: dict[str, Any], expected_group_id: str
) -> ParsedTransactionRow | TransactionImportRowResult:
    errors: list[RowValidationError] = []
    source_row_key = normalize_text(row.get("source_row_key"), 120)
    row_group_id = normalize_text(row.get("group_id"), 36)
    if row_group_id is not None and row_group_id != expected_group_id:
        errors.append(
            RowValidationError(
                field="group_id",
                code="GROUP_MISMATCH",
                message="CSV row group_id must match the target group.",
            )
        )
    transaction_at = parse_datetime_field(row.get("transaction_at"), "transaction_at", errors)
    transaction_type = parse_enum_field(
        row.get("transaction_type"), TransactionType, "transaction_type", errors
    )
    amount = parse_amount(row.get("amount"), errors)
    category_id = normalize_text(row.get("category_id"), 36)
    member_id = normalize_text(row.get("member_id"), 36)
    merchant_name = normalize_text(row.get("merchant_name"), 120)
    description = normalize_text(row.get("description"), 255)
    is_shared_expense = parse_nullable_bool(row.get("is_shared_expense"), "is_shared_expense", errors)
    is_planned = parse_nullable_bool(row.get("is_planned"), "is_planned", errors)
    is_recurring = parse_nullable_bool(row.get("is_recurring"), "is_recurring", errors)
    is_excluded = parse_bool_default(row.get("is_excluded"), "is_excluded", False, errors)
    exclusion_reason = normalize_text(row.get("exclusion_reason"), 255)

    if is_excluded and exclusion_reason is None:
        errors.append(
            RowValidationError(
                field="exclusion_reason",
                code="REQUIRED_FOR_EXCLUDED",
                message="exclusion_reason is required when is_excluded is true.",
            )
        )
    if errors or transaction_at is None or transaction_type is None or amount is None:
        return TransactionImportRowResult(
            row_number=row_number,
            source_row_key=source_row_key,
            status="REJECTED",
            errors=errors,
        )
    return ParsedTransactionRow(
        row_number=row_number,
        source_row_key=source_row_key,
        transaction_at=transaction_at,
        transaction_type=transaction_type,
        amount=amount,
        category_id=category_id,
        member_id=member_id,
        merchant_name=merchant_name,
        description=description,
        is_shared_expense=is_shared_expense,
        is_planned=is_planned,
        is_recurring=is_recurring,
        is_excluded=is_excluded,
        exclusion_reason=exclusion_reason,
    )


def persist_import_rows(
    db: Session,
    group: Group,
    rows: list[ParsedTransactionRow | TransactionImportRowResult],
    source_type: TransactionSourceType,
) -> TransactionImportResponse:
    existing_keys = set(
        db.scalars(
            select(Transaction.source_row_key).where(
                Transaction.group_id == group.id, Transaction.source_row_key.is_not(None)
            )
        ).all()
    )
    batch_keys: set[str] = set()
    results: list[TransactionImportRowResult] = []
    for row in rows:
        if isinstance(row, TransactionImportRowResult):
            results.append(row)
            continue
        errors: list[RowValidationError] = []
        validate_category_id(db, row.category_id, errors)
        validate_active_member_id(db, group.id, row.member_id, errors)
        if row.source_row_key is not None:
            if row.source_row_key in existing_keys or row.source_row_key in batch_keys:
                errors.append(
                    RowValidationError(
                        field="source_row_key",
                        code="DUPLICATE_SOURCE_ROW_KEY",
                        message="source_row_key already exists for this group.",
                    )
                )
            batch_keys.add(row.source_row_key)
        if errors:
            results.append(
                TransactionImportRowResult(
                    row_number=row.row_number,
                    source_row_key=row.source_row_key,
                    status="REJECTED",
                    errors=errors,
                )
            )
            continue

        transaction = Transaction(
            group_id=group.id,
            member_id=row.member_id,
            category_id=row.category_id,
            transaction_at=row.transaction_at,
            transaction_type=row.transaction_type,
            amount=row.amount,
            merchant_name=row.merchant_name,
            description=row.description,
            is_shared_expense=row.is_shared_expense,
            is_planned=row.is_planned,
            is_recurring=row.is_recurring,
            is_excluded=row.is_excluded,
            exclusion_reason=row.exclusion_reason,
            source_type=source_type,
            source_row_key=row.source_row_key,
        )
        db.add(transaction)
        db.flush()
        results.append(
            TransactionImportRowResult(
                row_number=row.row_number,
                source_row_key=row.source_row_key,
                status="ACCEPTED",
                transaction_id=transaction.id,
            )
        )
    db.commit()
    accepted_count = sum(1 for row in results if row.status == "ACCEPTED")
    rejected_count = len(results) - accepted_count
    status = "FAILED"
    if accepted_count and rejected_count:
        status = "PARTIALLY_COMPLETED"
    elif accepted_count:
        status = "COMPLETED"
    return TransactionImportResponse(
        group_id=group.id,
        source_type=source_type,
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        status=status,
        rows=results,
    )


def get_group_transaction(db: Session, group_id: str, transaction_id: str) -> Transaction:
    transaction = db.scalar(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.group_id == group_id)
    )
    if transaction is None:
        raise ApiException(code="NOT_FOUND", message="Transaction was not found.", status_code=404)
    return transaction


def validate_category_id(
    db: Session, category_id: str | None, errors: list[RowValidationError]
) -> None:
    if category_id is None:
        return
    category = db.get(Category, category_id)
    if category is None or not category.is_active:
        errors.append(
            RowValidationError(
                field="category_id",
                code="CATEGORY_NOT_FOUND",
                message="Category was not found.",
            )
        )


def validate_active_member_id(
    db: Session, group_id: str, member_id: str | None, errors: list[RowValidationError]
) -> None:
    if member_id is None:
        return
    member = db.get(GroupMember, member_id)
    if member is None or member.group_id != group_id or member.status != GroupMemberStatus.ACTIVE:
        errors.append(
            RowValidationError(
                field="member_id",
                code="MEMBER_NOT_IN_GROUP",
                message="Member must be ACTIVE and belong to the target group.",
            )
        )


def ensure_active_member_belongs_to_group(
    db: Session, group_id: str, member_id: str | None
) -> None:
    errors: list[RowValidationError] = []
    validate_active_member_id(db, group_id, member_id, errors)
    if errors:
        raise ApiException(
            code="NOT_FOUND",
            message="Group member was not found.",
            status_code=404,
            details={"field": "member_id"},
        )


def ensure_category_exists(db: Session, category_id: str | None) -> None:
    errors: list[RowValidationError] = []
    validate_category_id(db, category_id, errors)
    if errors:
        raise ApiException(
            code="NOT_FOUND",
            message="Category was not found.",
            status_code=404,
            details={"field": "category_id"},
        )


def read_mock_transaction_rows() -> list[dict[str, str]]:
    with MOCK_TRANSACTION_PATH.open(encoding="utf-8-sig", newline="") as mock_file:
        return list(csv.DictReader(mock_file))


def build_mock_member_map(rows: list[dict[str, str]], group: Group) -> dict[str | None, str]:
    active_member_ids = [
        member.id for member in group.members if member.status == GroupMemberStatus.ACTIVE
    ]
    if not active_member_ids:
        return {}
    unique_source_members = sorted({row.get("member_id") for row in rows if row.get("member_id")})
    return {
        source_member_id: active_member_ids[index % len(active_member_ids)]
        for index, source_member_id in enumerate(unique_source_members)
    }


def rejected_row(
    row_number: int, source_row_key: str | None, field: str, code: str, message: str
) -> TransactionImportRowResult:
    return TransactionImportRowResult(
        row_number=row_number,
        source_row_key=source_row_key,
        status="REJECTED",
        errors=[RowValidationError(field=field, code=code, message=message)],
    )


def parse_required_bool(raw_value: object) -> bool:
    value = str(raw_value).strip().lower()
    return value in {"true", "1", "yes", "y"}


def parse_datetime(raw_value: object) -> datetime:
    return datetime.fromisoformat(str(raw_value).strip())


def parse_datetime_field(
    raw_value: object, field: str, errors: list[RowValidationError]
) -> datetime | None:
    value = normalize_text(raw_value, 80)
    if value is None:
        errors.append(RowValidationError(field=field, code="REQUIRED", message=f"{field} is required."))
        return None
    try:
        return parse_datetime(value)
    except ValueError:
        errors.append(
            RowValidationError(
                field=field,
                code="INVALID_DATETIME",
                message=f"{field} must be an ISO 8601 datetime.",
            )
        )
        return None


def parse_enum_field(
    raw_value: object,
    enum_type: type[TransactionType],
    field: str,
    errors: list[RowValidationError],
) -> TransactionType | None:
    value = normalize_text(raw_value, 40)
    if value is None:
        errors.append(RowValidationError(field=field, code="REQUIRED", message=f"{field} is required."))
        return None
    try:
        return enum_type(value)
    except ValueError:
        errors.append(
            RowValidationError(
                field=field,
                code="INVALID_ENUM",
                message=f"{field} has an unsupported value.",
            )
        )
        return None


def parse_amount(raw_value: object, errors: list[RowValidationError]) -> Decimal | None:
    value = normalize_text(raw_value, 40)
    if value is None:
        errors.append(RowValidationError(field="amount", code="REQUIRED", message="amount is required."))
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation:
        errors.append(
            RowValidationError(
                field="amount",
                code="INVALID_AMOUNT",
                message="amount must be a positive decimal.",
            )
        )
        return None
    if amount <= 0:
        errors.append(
            RowValidationError(
                field="amount",
                code="AMOUNT_NOT_POSITIVE",
                message="amount must be positive.",
            )
        )
        return None
    return amount.quantize(Decimal("0.01"))


def parse_nullable_bool(
    raw_value: object, field: str, errors: list[RowValidationError]
) -> bool | None:
    value = normalize_text(raw_value, 20)
    if value is None:
        return None
    lowered = value.lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    if lowered in {"null", "none"}:
        return None
    errors.append(
        RowValidationError(
            field=field,
            code="INVALID_BOOLEAN",
            message=f"{field} must be true, false, or blank.",
        )
    )
    return None


def parse_bool_default(
    raw_value: object, field: str, default: bool, errors: list[RowValidationError]
) -> bool:
    parsed = parse_nullable_bool(raw_value, field, errors)
    return default if parsed is None else parsed


def normalize_text(raw_value: object, max_length: int) -> str | None:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    return value[:max_length]
