from datetime import datetime

from pydantic import BaseModel

from app.modules.users.models import UserRole

SCHEMA_VERSION = "1.0"


class AdminUserSummary(BaseModel):
    schema_version: str = SCHEMA_VERSION
    user_id: str
    display_name: str
    masked_email: str | None
    role: UserRole
    failed_login_count: int
    created_at: datetime
