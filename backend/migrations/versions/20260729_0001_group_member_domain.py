"""add user group member domain

Revision ID: 20260729_0001
Revises:
Create Date: 2026-07-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260729_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


relationship_type = sa.Enum("COUPLE", "FRIENDS", "FAMILY", "OTHER", name="relationship_type")
group_status = sa.Enum(
    "DRAFT",
    "READY_FOR_ANALYSIS",
    name="group_status",
)
mbti_type = sa.Enum(
    "ISTJ",
    "ISFJ",
    "INFJ",
    "INTJ",
    "ISTP",
    "ISFP",
    "INFP",
    "INTP",
    "ESTP",
    "ESFP",
    "ENFP",
    "ENTP",
    "ESTJ",
    "ESFJ",
    "ENFJ",
    "ENTJ",
    name="mbti_type",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("relationship_type", relationship_type, nullable=False),
        sa.Column("status", group_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_groups_owner_user_id"), "groups", ["owner_user_id"], unique=False)
    op.create_table(
        "group_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "display_name", name="uq_group_member_name"),
    )
    op.create_index(op.f("ix_group_members_group_id"), "group_members", ["group_id"], unique=False)
    op.create_table(
        "member_personalities",
        sa.Column("member_id", sa.String(length=36), nullable=False),
        sa.Column("mbti", mbti_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["group_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("member_id"),
    )


def downgrade() -> None:
    op.drop_table("member_personalities")
    op.drop_index(op.f("ix_group_members_group_id"), table_name="group_members")
    op.drop_table("group_members")
    op.drop_index(op.f("ix_groups_owner_user_id"), table_name="groups")
    op.drop_table("groups")
    op.drop_table("users")

    bind = op.get_bind()
    mbti_type.drop(bind, checkfirst=True)
    group_status.drop(bind, checkfirst=True)
    relationship_type.drop(bind, checkfirst=True)
