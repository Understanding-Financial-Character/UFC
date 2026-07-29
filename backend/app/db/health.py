from fastapi import status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ApiException


def check_database(db: Session) -> None:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApiException(
            code="DATABASE_UNAVAILABLE",
            message="Database is not ready.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
