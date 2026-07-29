from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.health import check_database

router = APIRouter()
DB_DEPENDENCY = Depends(get_db)


@router.get("/meta")
def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check(db: Session = DB_DEPENDENCY) -> dict[str, str]:
    check_database(db)
    return {"status": "ready"}
