"""extend analysis run statuses for orchestration

Revision ID: 20260730_0006
Revises: 20260730_0005
Create Date: 2026-07-30 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260730_0006"
down_revision: str | None = "20260730_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            for value in (
                "READY",
                "ANALYZING",
                "REPORT_GENERATING",
                "PARTIALLY_COMPLETED",
                "COMPLETED_WITH_FALLBACK",
            ):
                op.execute(f"ALTER TYPE analysis_run_status ADD VALUE IF NOT EXISTS '{value}'")

    op.drop_constraint(
        "ck_analysis_runs_result_status_lifecycle",
        "analysis_runs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_analysis_runs_result_status_lifecycle",
        "analysis_runs",
        "((status IN ('COMPLETED', 'PARTIALLY_COMPLETED', 'COMPLETED_WITH_FALLBACK') "
        "AND result_status IS NOT NULL) "
        "OR (status IN ('READY', 'ANALYZING', 'REPORT_GENERATING', "
        "'PENDING', 'RUNNING', 'FAILED') AND result_status IS NULL))",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_analysis_runs_result_status_lifecycle",
        "analysis_runs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_analysis_runs_result_status_lifecycle",
        "analysis_runs",
        "((status = 'COMPLETED' AND result_status IS NOT NULL) "
        "OR (status IN ('PENDING', 'RUNNING', 'FAILED') AND result_status IS NULL))",
    )
