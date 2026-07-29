"""add security baseline auth fields

Revision ID: 20260729_0002
Revises: 20260729_0001
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260729_0002"
down_revision: str | None = "20260729_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role = sa.Enum("USER", "ADMIN", name="user_role")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_role.create(bind, checkfirst=True)

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "email_ciphertext" not in user_columns:
        op.add_column("users", sa.Column("email_ciphertext", sa.String(length=512), nullable=True))
    if "email_lookup_hmac" not in user_columns:
        op.add_column("users", sa.Column("email_lookup_hmac", sa.String(length=64), nullable=True))
    if "email_key_version" not in user_columns:
        op.add_column("users", sa.Column("email_key_version", sa.String(length=40), nullable=True))
    if "password_hash" not in user_columns:
        op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))
    if "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column("role", user_role, nullable=False, server_default="USER"),
        )
    if "failed_login_count" not in user_columns:
        op.add_column(
            "users",
            sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if "locked_until" not in user_columns:
        op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    if "last_login_at" not in user_columns:
        op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    user_unique_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("users")
    }
    if "uq_users_email_lookup_hmac" not in user_unique_constraints:
        op.create_unique_constraint("uq_users_email_lookup_hmac", "users", ["email_lookup_hmac"])

    if "refresh_tokens" not in inspector.get_table_names():
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        )
        inspector = sa.inspect(bind)
    refresh_indexes = {index["name"] for index in inspector.get_indexes("refresh_tokens")}
    if op.f("ix_refresh_tokens_user_id") not in refresh_indexes:
        op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_constraint("uq_users_email_lookup_hmac", "users", type_="unique")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email_key_version")
    op.drop_column("users", "email_lookup_hmac")
    op.drop_column("users", "email_ciphertext")

    bind = op.get_bind()
    user_role.drop(bind, checkfirst=True)
