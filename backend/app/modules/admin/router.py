from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import DatabaseSession
from app.modules.admin.schemas import AdminUserSummary
from app.modules.auth import service as auth_service
from app.modules.auth.dependencies import AdminPrincipal
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserSummary])
def list_users(_principal: AdminPrincipal, db: DatabaseSession) -> list[AdminUserSummary]:
    users = list(db.scalars(select(User).order_by(User.created_at)).all())
    return [
        AdminUserSummary(
            user_id=user.id,
            display_name=user.display_name,
            masked_email=auth_service.masked_email_for_user(user),
            role=user.role,
            failed_login_count=user.failed_login_count,
            created_at=user.created_at,
        )
        for user in users
    ]
