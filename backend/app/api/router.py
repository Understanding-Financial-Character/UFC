from fastapi import APIRouter

from app.core.config import settings
from app.modules.groups.router import router as groups_router
from app.modules.users.router import router as users_router

router = APIRouter()
router.include_router(users_router)
router.include_router(groups_router)


@router.get("/meta")
def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }
