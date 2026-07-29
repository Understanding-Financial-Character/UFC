"""harden refresh token rotation metadata

Revision ID: 20260729_0003
Revises: 20260729_0002
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260729_0003"
down_revision: str | None = "20260729_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "refresh_tokens" not in inspector.get_table_names():
        return

    refresh_columns = {column["name"] for column in inspector.get_columns("refresh_tokens")}
    if "family_id" not in refresh_columns:
        op.add_column(
            "refresh_tokens",
            sa.Column("family_id", sa.String(length=36), nullable=True),
        )
        op.execute("UPDATE refresh_tokens SET family_id = id WHERE family_id IS NULL")
        op.alter_column("refresh_tokens", "family_id", nullable=False)
    if "replaced_by_token_id" not in refresh_columns:
        op.add_column(
            "refresh_tokens",
            sa.Column("replaced_by_token_id", sa.String(length=36), nullable=True),
        )
    if "revocation_reason" not in refresh_columns:
        op.add_column(
            "refresh_tokens",
            sa.Column("revocation_reason", sa.String(length=40), nullable=True),
        )

    refresh_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("refresh_tokens")}
    if op.f("ix_refresh_tokens_family_id") not in refresh_indexes:
        op.create_index(
            op.f("ix_refresh_tokens_family_id"), "refresh_tokens", ["family_id"], unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "refresh_tokens" not in inspector.get_table_names():
        return

    refresh_indexes = {index["name"] for index in inspector.get_indexes("refresh_tokens")}
    if op.f("ix_refresh_tokens_family_id") in refresh_indexes:
        op.drop_index(op.f("ix_refresh_tokens_family_id"), table_name="refresh_tokens")

    refresh_columns = {column["name"] for column in sa.inspect(bind).get_columns("refresh_tokens")}
    for column_name in ("revocation_reason", "replaced_by_token_id", "family_id"):
        if column_name in refresh_columns:
            op.drop_column("refresh_tokens", column_name)
