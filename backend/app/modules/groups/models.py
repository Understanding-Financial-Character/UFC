from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class RelationshipType(str, enum.Enum):
    COUPLE = "COUPLE"
    FRIENDS = "FRIENDS"
    FAMILY = "FAMILY"
    OTHER = "OTHER"


class GroupStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"


class MBTIType(str, enum.Enum):
    ISTJ = "ISTJ"
    ISFJ = "ISFJ"
    INFJ = "INFJ"
    INTJ = "INTJ"
    ISTP = "ISTP"
    ISFP = "ISFP"
    INFP = "INFP"
    INTP = "INTP"
    ESTP = "ESTP"
    ESFP = "ESFP"
    ENFP = "ENFP"
    ENTP = "ENTP"
    ESTJ = "ESTJ"
    ESFJ = "ESFJ"
    ENFJ = "ENFJ"
    ENTJ = "ENTJ"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type"), nullable=False
    )
    status: Mapped[GroupStatus] = mapped_column(
        Enum(GroupStatus, name="group_status"), nullable=False, default=GroupStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    members: Mapped[list[GroupMember]] = relationship(
        back_populates="group", cascade="all, delete-orphan", order_by="GroupMember.created_at"
    )


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "display_name", name="uq_group_member_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    group: Mapped[Group] = relationship(back_populates="members")
    personality: Mapped[MemberPersonality | None] = relationship(
        back_populates="member", cascade="all, delete-orphan", uselist=False
    )


class MemberPersonality(Base):
    __tablename__ = "member_personalities"

    member_id: Mapped[str] = mapped_column(
        ForeignKey("group_members.id", ondelete="CASCADE"), primary_key=True
    )
    mbti: Mapped[MBTIType] = mapped_column(Enum(MBTIType, name="mbti_type"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    member: Mapped[GroupMember] = relationship(back_populates="personality")
