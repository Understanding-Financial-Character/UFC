from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.dependencies import DatabaseSession
from app.api.router import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    ApiException,
    api_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.trace import trace_id_middleware
from app.db.health import check_database


def create_app() -> FastAPI:
    configure_logging(settings)
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.middleware("http")(trace_id_middleware)
    app.add_exception_handler(ApiException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    @app.get("/health")
    def root_health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def root_readiness_check(db: DatabaseSession) -> dict[str, str]:
        check_database(db)
        return {"status": "ready"}

    return app


app = create_app()
