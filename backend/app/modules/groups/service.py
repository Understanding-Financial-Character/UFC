from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ApiException
from app.modules.groups.models import Group, GroupMember, GroupStatus, MemberPersonality
from app.modules.groups.schemas import GroupCreate, GroupUpdate, MemberCreate, MemberUpdate
from app.modules.users.models import User

MIN_MEMBERS = 2
MAX_MEMBERS = 4


def calculate_analysis_readiness(group: Group) -> GroupStatus:
    member_count = len(group.members)
    has_complete_personalities = all(member.personality is not None for member in group.members)
    if MIN_MEMBERS <= member_count <= MAX_MEMBERS and has_complete_personalities:
        return GroupStatus.READY_FOR_ANALYSIS
    return GroupStatus.DRAFT


def group_can_analyze(group: Group) -> bool:
    return group.status == GroupStatus.READY_FOR_ANALYSIS


def get_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ApiException(code="NOT_FOUND", message="User was not found.", status_code=404)
    return user


def get_owned_group(db: Session, group_id: str, owner_user_id: str) -> Group:
    statement = (
        select(Group)
        .options(selectinload(Group.members).selectinload(GroupMember.personality))
        .where(Group.id == group_id, Group.owner_user_id == owner_user_id)
    )
    group = db.scalar(statement)
    if group is None:
        raise ApiException(code="NOT_FOUND", message="Group was not found.", status_code=404)
    return group


def get_owned_group_for_update(db: Session, group_id: str, owner_user_id: str) -> Group:
    statement = (
        select(Group)
        .options(selectinload(Group.members).selectinload(GroupMember.personality))
        .where(Group.id == group_id, Group.owner_user_id == owner_user_id)
        .with_for_update()
    )
    group = db.scalar(statement)
    if group is None:
        raise ApiException(code="NOT_FOUND", message="Group was not found.", status_code=404)
    return group


def list_groups(db: Session, owner_user_id: str) -> list[Group]:
    get_user(db, owner_user_id)
    statement = (
        select(Group)
        .options(selectinload(Group.members).selectinload(GroupMember.personality))
        .where(Group.owner_user_id == owner_user_id)
        .order_by(Group.created_at)
    )
    return list(db.scalars(statement).all())


def create_group(db: Session, owner_user_id: str, payload: GroupCreate) -> Group:
    get_user(db, owner_user_id)
    group = Group(
        owner_user_id=owner_user_id,
        name=payload.name,
        relationship_type=payload.relationship_type,
        status=GroupStatus.DRAFT,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    group.members = []
    return group


def update_group(db: Session, group: Group, payload: GroupUpdate) -> Group:
    if payload.name is not None:
        group.name = payload.name
    if payload.relationship_type is not None:
        group.relationship_type = payload.relationship_type
    db.commit()
    db.refresh(group)
    return get_owned_group(db, group.id, group.owner_user_id)


def add_member(db: Session, group: Group, payload: MemberCreate) -> GroupMember:
    if len(group.members) >= MAX_MEMBERS:
        raise ApiException(
            code="CONFLICT",
            message="Group member count must not exceed 4.",
            status_code=409,
            details={"member_count": len(group.members), "max_members": MAX_MEMBERS},
        )
    ensure_display_name_is_available(group, payload.display_name)

    member = GroupMember(group_id=group.id, display_name=payload.display_name)
    member.personality = MemberPersonality(mbti=payload.mbti)
    group.members.append(member)
    group.status = calculate_analysis_readiness(group)
    db.add(member)
    commit_member_change(db)
    db.refresh(member)
    return member


def update_member(db: Session, group: Group, member_id: str, payload: MemberUpdate) -> GroupMember:
    member = find_member(group, member_id)
    if payload.display_name is not None:
        ensure_display_name_is_available(group, payload.display_name, existing_member_id=member_id)
        member.display_name = payload.display_name
    if payload.mbti is not None:
        if member.personality is None:
            member.personality = MemberPersonality(mbti=payload.mbti)
        else:
            member.personality.mbti = payload.mbti
    group.status = calculate_analysis_readiness(group)
    commit_member_change(db)
    db.refresh(member)
    return member


def delete_member(db: Session, group: Group, member_id: str) -> None:
    member = find_member(group, member_id)
    db.delete(member)
    db.flush()
    group.members = [existing for existing in group.members if existing.id != member_id]
    group.status = calculate_analysis_readiness(group)
    db.commit()


def find_member(group: Group, member_id: str) -> GroupMember:
    for member in group.members:
        if member.id == member_id:
            return member
    raise ApiException(code="NOT_FOUND", message="Group member was not found.", status_code=404)


def ensure_display_name_is_available(
    group: Group, display_name: str, existing_member_id: str | None = None
) -> None:
    for member in group.members:
        if member.id != existing_member_id and member.display_name == display_name:
            raise ApiException(
                code="CONFLICT",
                message="Group member display name already exists.",
                status_code=409,
                details={"field": "display_name"},
            )


def commit_member_change(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiException(
            code="CONFLICT",
            message="Group member display name already exists.",
            status_code=409,
            details={"field": "display_name"},
        ) from exc
