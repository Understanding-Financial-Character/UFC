from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class CategoryBehaviorGroup(str, enum.Enum):
    PRACTICAL = "PRACTICAL"
    EXPERIENCE = "EXPERIENCE"
    RELATIONSHIP = "RELATIONSHIP"
    REGULAR = "REGULAR"
    SAVINGS = "SAVINGS"
    OTHER = "OTHER"


class TransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class TransactionSourceType(str, enum.Enum):
    CSV_UPLOAD = "CSV_UPLOAD"
    MOCK = "MOCK"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("code", "name", name="uq_categories_code_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    behavior_group: Mapped[CategoryBehaviorGroup] = mapped_column(
        Enum(CategoryBehaviorGroup, name="category_behavior_group"), nullable=False
    )
    display_order: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint(
            "(is_excluded = false OR exclusion_reason IS NOT NULL)",
            name="ck_transactions_exclusion_reason_required",
        ),
        CheckConstraint(
            "(source_row_key IS NULL OR length(source_row_key) > 0)",
            name="ck_transactions_source_row_key_nonblank",
        ),
        UniqueConstraint("group_id", "source_row_key", name="uq_transactions_group_source_row_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[str | None] = mapped_column(
        ForeignKey("group_members.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    transaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    merchant_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_shared_expense: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_planned: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_recurring: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_excluded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exclusion_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[TransactionSourceType] = mapped_column(
        Enum(TransactionSourceType, name="transaction_source_type"), nullable=False
    )
    source_row_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
