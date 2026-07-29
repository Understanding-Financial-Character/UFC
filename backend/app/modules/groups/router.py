from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.api.dependencies import DatabaseSession
from app.modules.groups import service
from app.modules.groups.models import Group, GroupMember
from app.modules.groups.schemas import (
    GroupCreate,
    GroupResponse,
    GroupUpdate,
    MemberCreate,
    MemberResponse,
    MemberUpdate,
)

router = APIRouter(prefix="/groups", tags=["groups"])

# Temporary BE Phase 2 identity only.
# This header is not an authentication boundary.
CurrentUserId = Annotated[str, Header(alias="X-UFC-User-Id", min_length=1)]


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, db: DatabaseSession, current_user_id: CurrentUserId) -> GroupResponse:
    group = service.create_group(db, current_user_id, payload)
    return build_group_response(group)


@router.get("", response_model=list[GroupResponse])
def list_groups(db: DatabaseSession, current_user_id: CurrentUserId) -> list[GroupResponse]:
    groups = service.list_groups(db, current_user_id)
    return [build_group_response(group) for group in groups]


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: str, db: DatabaseSession, current_user_id: CurrentUserId) -> GroupResponse:
    group = service.get_owned_group(db, group_id, current_user_id)
    return build_group_response(group)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: str, payload: GroupUpdate, db: DatabaseSession, current_user_id: CurrentUserId
) -> GroupResponse:
    group = service.get_owned_group(db, group_id, current_user_id)
    updated_group = service.update_group(db, group, payload)
    return build_group_response(updated_group)


@router.post("/{group_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: str, payload: MemberCreate, db: DatabaseSession, current_user_id: CurrentUserId
) -> MemberResponse:
    group = service.get_owned_group_for_update(db, group_id, current_user_id)
    member = service.add_member(db, group, payload)
    return build_member_response(member)


@router.patch("/{group_id}/members/{member_id}", response_model=MemberResponse)
def update_member(
    group_id: str,
    member_id: str,
    payload: MemberUpdate,
    db: DatabaseSession,
    current_user_id: CurrentUserId,
) -> MemberResponse:
    group = service.get_owned_group(db, group_id, current_user_id)
    member = service.update_member(db, group, member_id, payload)
    return build_member_response(member)


@router.delete("/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    group_id: str, member_id: str, db: DatabaseSession, current_user_id: CurrentUserId
) -> Response:
    group = service.get_owned_group(db, group_id, current_user_id)
    service.delete_member(db, group, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def build_group_response(group: Group) -> GroupResponse:
    return GroupResponse(
        group_id=group.id,
        name=group.name,
        relationship_type=group.relationship_type,
        status=group.status,
        member_count=len(group.members),
        can_analyze=service.group_can_analyze(group),
        created_at=group.created_at,
        members=[build_member_response(member) for member in group.members],
    )


def build_member_response(member: GroupMember) -> MemberResponse:
    return MemberResponse(
        group_id=member.group_id,
        member_id=member.id,
        display_name=member.display_name,
        mbti=member.personality.mbti if member.personality else None,
        created_at=member.created_at,
    )
