"""add analysis persistence tables

Revision ID: 20260730_0005
Revises: 20260730_0004
Create Date: 2026-07-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260730_0005"
down_revision: str | None = "20260730_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


analysis_run_status = sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", name="analysis_run_status")
analysis_result_status = sa.Enum(
    "STANDARD", "PROVISIONAL", "INSUFFICIENT_DATA", name="analysis_result_status"
)
analysis_source_type = sa.Enum(
    "CSV_UPLOAD", "MOCK", "MANUAL_ENTRY", "INTERNAL_TEST", name="analysis_source_type"
)
consumption_mbti_type = sa.Enum(
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
    name="consumption_mbti_type",
)
ai_report_status = sa.Enum("COMPLETED", "FALLBACK_COMPLETED", "FAILED", name="ai_report_status")

analysis_run_status_column = postgresql.ENUM(
    "PENDING", "RUNNING", "COMPLETED", "FAILED", name="analysis_run_status", create_type=False
)
analysis_result_status_column = postgresql.ENUM(
    "STANDARD",
    "PROVISIONAL",
    "INSUFFICIENT_DATA",
    name="analysis_result_status",
    create_type=False,
)
analysis_source_type_column = postgresql.ENUM(
    "CSV_UPLOAD",
    "MOCK",
    "MANUAL_ENTRY",
    "INTERNAL_TEST",
    name="analysis_source_type",
    create_type=False,
)
consumption_mbti_type_column = postgresql.ENUM(
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
    name="consumption_mbti_type",
    create_type=False,
)
ai_report_status_column = postgresql.ENUM(
    "COMPLETED",
    "FALLBACK_COMPLETED",
    "FAILED",
    name="ai_report_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    analysis_run_status.create(bind, checkfirst=True)
    analysis_result_status.create(bind, checkfirst=True)
    analysis_source_type.create(bind, checkfirst=True)
    consumption_mbti_type.create(bind, checkfirst=True)
    ai_report_status.create(bind, checkfirst=True)

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("status", analysis_run_status_column, nullable=False),
        sa.Column("result_status", analysis_result_status_column, nullable=False),
        sa.Column("provisional_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("analysis_period_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("analysis_period_ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", analysis_source_type_column, nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        sa.Column("input_schema_version", sa.String(length=40), nullable=False),
        sa.Column("analysis_version", sa.String(length=40), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=128), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "analysis_period_started_at <= analysis_period_ended_at",
            name="ck_analysis_runs_period_order",
        ),
        sa.CheckConstraint("length(snapshot_hash) > 0", name="ck_analysis_runs_snapshot_hash_nonblank"),
        sa.CheckConstraint(
            "length(analysis_version) > 0",
            name="ck_analysis_runs_analysis_version_nonblank",
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_runs_group_id"), "analysis_runs", ["group_id"], unique=False)

    op.create_table(
        "behavior_metrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("metric_code", sa.String(length=80), nullable=False),
        sa.Column("metric_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("unavailable_reason", sa.String(length=120), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metric_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("calculation_version", sa.String(length=40), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(is_available = false OR metric_value IS NOT NULL)",
            name="ck_behavior_metrics_available_value_required",
        ),
        sa.CheckConstraint(
            "length(snapshot_hash) > 0",
            name="ck_behavior_metrics_snapshot_hash_nonblank",
        ),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_run_id", "metric_code", name="uq_behavior_metrics_run_metric"),
    )
    op.create_index(
        op.f("ix_behavior_metrics_analysis_run_id"),
        "behavior_metrics",
        ["analysis_run_id"],
        unique=False,
    )
    op.create_index(op.f("ix_behavior_metrics_metric_code"), "behavior_metrics", ["metric_code"], unique=False)

    op.create_table(
        "consumption_mbti_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("mbti_type", consumption_mbti_type_column, nullable=True),
        sa.Column("ei_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("sn_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("tf_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("jp_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("confidence_level", sa.String(length=20), nullable=True),
        sa.Column("confidence_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("coverage", sa.Numeric(6, 4), nullable=True),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("axis_score_directions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("rule_version", sa.String(length=40), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ei_score IS NULL OR (ei_score >= 0 AND ei_score <= 1)", name="ck_mbti_ei_score_range"),
        sa.CheckConstraint("sn_score IS NULL OR (sn_score >= 0 AND sn_score <= 1)", name="ck_mbti_sn_score_range"),
        sa.CheckConstraint("tf_score IS NULL OR (tf_score >= 0 AND tf_score <= 1)", name="ck_mbti_tf_score_range"),
        sa.CheckConstraint("jp_score IS NULL OR (jp_score >= 0 AND jp_score <= 1)", name="ck_mbti_jp_score_range"),
        sa.CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_mbti_confidence_score_range",
        ),
        sa.CheckConstraint("coverage IS NULL OR (coverage >= 0 AND coverage <= 1)", name="ck_mbti_coverage_range"),
        sa.CheckConstraint(
            "length(snapshot_hash) > 0",
            name="ck_consumption_mbti_results_snapshot_hash_nonblank",
        ),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_run_id", name="uq_consumption_mbti_results_run"),
    )
    op.create_index(
        op.f("ix_consumption_mbti_results_analysis_run_id"),
        "consumption_mbti_results",
        ["analysis_run_id"],
        unique=False,
    )

    op.create_table(
        "ai_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("status", ai_report_status_column, nullable=False),
        sa.Column("report_content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_name", sa.String(length=80), nullable=True),
        sa.Column("prompt_version", sa.String(length=80), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False),
        sa.Column("fallback_reason", sa.String(length=120), nullable=True),
        sa.Column("validation_result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "((status IN ('COMPLETED', 'FALLBACK_COMPLETED') AND report_content IS NOT NULL) "
            "OR (status = 'FAILED' AND failure_reason IS NOT NULL))",
            name="ck_ai_reports_status_payload",
        ),
        sa.CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_ai_reports_latency_nonnegative"),
        sa.CheckConstraint("length(snapshot_hash) > 0", name="ck_ai_reports_snapshot_hash_nonblank"),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_run_id", name="uq_ai_reports_run"),
    )
    op.create_index(op.f("ix_ai_reports_analysis_run_id"), "ai_reports", ["analysis_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_reports_analysis_run_id"), table_name="ai_reports")
    op.drop_table("ai_reports")
    op.drop_index(
        op.f("ix_consumption_mbti_results_analysis_run_id"),
        table_name="consumption_mbti_results",
    )
    op.drop_table("consumption_mbti_results")
    op.drop_index(op.f("ix_behavior_metrics_metric_code"), table_name="behavior_metrics")
    op.drop_index(op.f("ix_behavior_metrics_analysis_run_id"), table_name="behavior_metrics")
    op.drop_table("behavior_metrics")
    op.drop_index(op.f("ix_analysis_runs_group_id"), table_name="analysis_runs")
    op.drop_table("analysis_runs")

    bind = op.get_bind()
    ai_report_status.drop(bind, checkfirst=True)
    consumption_mbti_type.drop(bind, checkfirst=True)
    analysis_source_type.drop(bind, checkfirst=True)
    analysis_result_status.drop(bind, checkfirst=True)
    analysis_run_status.drop(bind, checkfirst=True)
