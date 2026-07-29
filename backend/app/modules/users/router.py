from fastapi import APIRouter, status

from app.api.dependencies import DatabaseSession
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DatabaseSession) -> UserResponse:
    user = User(display_name=payload.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(user_id=user.id, display_name=user.display_name, created_at=user.created_at)
