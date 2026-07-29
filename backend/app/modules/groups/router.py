from fastapi import APIRouter, Response, status

from app.api.dependencies import DatabaseSession
from app.modules.auth.dependencies import AuthenticatedPrincipal
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


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate, db: DatabaseSession, principal: AuthenticatedPrincipal
) -> GroupResponse:
    group = service.create_group(db, principal.user_id, payload)
    return build_group_response(group)


@router.get("", response_model=list[GroupResponse])
def list_groups(db: DatabaseSession, principal: AuthenticatedPrincipal) -> list[GroupResponse]:
    groups = service.list_groups(db, principal.user_id)
    return [build_group_response(group) for group in groups]


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: str, db: DatabaseSession, principal: AuthenticatedPrincipal
) -> GroupResponse:
    group = service.get_owned_group(db, group_id, principal.user_id)
    return build_group_response(group)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: str, payload: GroupUpdate, db: DatabaseSession, principal: AuthenticatedPrincipal
) -> GroupResponse:
    group = service.get_owned_group(db, group_id, principal.user_id)
    updated_group = service.update_group(db, group, payload)
    return build_group_response(updated_group)


@router.post("/{group_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: str, payload: MemberCreate, db: DatabaseSession, principal: AuthenticatedPrincipal
) -> MemberResponse:
    group = service.get_owned_group_for_update(db, group_id, principal.user_id)
    member = service.add_member(db, group, payload)
    return build_member_response(member)


@router.patch("/{group_id}/members/{member_id}", response_model=MemberResponse)
def update_member(
    group_id: str,
    member_id: str,
    payload: MemberUpdate,
    db: DatabaseSession,
    principal: AuthenticatedPrincipal,
) -> MemberResponse:
    group = service.get_owned_group(db, group_id, principal.user_id)
    member = service.update_member(db, group, member_id, payload)
    return build_member_response(member)


@router.delete("/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    group_id: str, member_id: str, db: DatabaseSession, principal: AuthenticatedPrincipal
) -> Response:
    group = service.get_owned_group(db, group_id, principal.user_id)
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
