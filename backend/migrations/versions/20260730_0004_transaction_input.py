"""add transaction input tables

Revision ID: 20260730_0004
Revises: 20260729_0003
Create Date: 2026-07-30 00:00:00.000000
"""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260730_0004"
down_revision: str | None = "20260729_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


group_member_status = sa.Enum("ACTIVE", "INACTIVE", name="group_member_status")
category_behavior_group = sa.Enum(
    "PRACTICAL",
    "EXPERIENCE",
    "RELATIONSHIP",
    "REGULAR",
    "SAVINGS",
    "OTHER",
    name="category_behavior_group",
)
transaction_type = sa.Enum("DEPOSIT", "WITHDRAWAL", name="transaction_type")
transaction_source_type = sa.Enum("CSV_UPLOAD", "MOCK", "MANUAL_ENTRY", name="transaction_source_type")
group_member_status_column = postgresql.ENUM(
    "ACTIVE", "INACTIVE", name="group_member_status", create_type=False
)
category_behavior_group_column = postgresql.ENUM(
    "PRACTICAL",
    "EXPERIENCE",
    "RELATIONSHIP",
    "REGULAR",
    "SAVINGS",
    "OTHER",
    name="category_behavior_group",
    create_type=False,
)
transaction_type_column = postgresql.ENUM(
    "DEPOSIT", "WITHDRAWAL", name="transaction_type", create_type=False
)
transaction_source_type_column = postgresql.ENUM(
    "CSV_UPLOAD", "MOCK", "MANUAL_ENTRY", name="transaction_source_type", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    group_member_status.create(bind, checkfirst=True)
    category_behavior_group.create(bind, checkfirst=True)
    transaction_type.create(bind, checkfirst=True)
    transaction_source_type.create(bind, checkfirst=True)

    op.add_column(
        "group_members",
        sa.Column("status", group_member_status_column, nullable=False, server_default="ACTIVE"),
    )
    op.alter_column("group_members", "status", server_default=None)

    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("behavior_group", category_behavior_group_column, nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", "name", name="uq_categories_code_name"),
    )
    op.create_index(op.f("ix_categories_code"), "categories", ["code"], unique=False)
    seed_categories()

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("member_id", sa.String(length=36), nullable=True),
        sa.Column("category_id", sa.String(length=36), nullable=True),
        sa.Column("transaction_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transaction_type", transaction_type_column, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("merchant_name", sa.String(length=120), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_shared_expense", sa.Boolean(), nullable=True),
        sa.Column("is_planned", sa.Boolean(), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=True),
        sa.Column("is_excluded", sa.Boolean(), nullable=False),
        sa.Column("exclusion_reason", sa.String(length=255), nullable=True),
        sa.Column("source_type", transaction_source_type_column, nullable=False),
        sa.Column("source_row_key", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        sa.CheckConstraint(
            "(is_excluded = false OR exclusion_reason IS NOT NULL)",
            name="ck_transactions_exclusion_reason_required",
        ),
        sa.CheckConstraint(
            "(source_row_key IS NULL OR length(source_row_key) > 0)",
            name="ck_transactions_source_row_key_nonblank",
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["group_members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "source_row_key", name="uq_transactions_group_source_row_key"),
    )
    op.create_index(op.f("ix_transactions_category_id"), "transactions", ["category_id"], unique=False)
    op.create_index(op.f("ix_transactions_group_id"), "transactions", ["group_id"], unique=False)
    op.create_index(op.f("ix_transactions_member_id"), "transactions", ["member_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_member_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_group_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_categories_code"), table_name="categories")
    op.drop_table("categories")
    op.drop_column("group_members", "status")

    bind = op.get_bind()
    transaction_source_type.drop(bind, checkfirst=True)
    transaction_type.drop(bind, checkfirst=True)
    category_behavior_group.drop(bind, checkfirst=True)
    group_member_status.drop(bind, checkfirst=True)


def seed_categories() -> None:
    import csv

    seed_path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "data"
        / "20260730_0004_categories.csv"
    )
    categories_table = sa.table(
        "categories",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("behavior_group", category_behavior_group_column),
        sa.column("display_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    with seed_path.open(encoding="utf-8-sig", newline="") as seed_file:
        op.bulk_insert(
            categories_table,
            [
                {
                    "id": row["id"],
                    "code": row["code"],
                    "name": row["name"],
                    "behavior_group": row["behavior_group"],
                    "display_order": int(row["display_order"]),
                    "is_active": row["is_active"].strip().upper() == "TRUE",
                    "created_at": datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                    "updated_at": datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
                }
                for row in csv.DictReader(seed_file)
            ],
        )
