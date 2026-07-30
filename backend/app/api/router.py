from fastapi import APIRouter

from app.core.config import settings
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import me_router
from app.modules.auth.router import router as auth_router
from app.modules.groups.router import router as groups_router
from app.modules.transactions.router import router as transactions_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(me_router)
router.include_router(admin_router)
router.include_router(groups_router)
router.include_router(transactions_router)


@router.get("/meta")
def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }
