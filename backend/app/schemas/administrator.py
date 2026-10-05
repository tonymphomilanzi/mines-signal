from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# CREATE ADMINISTRATOR
# ============================================================

class CreateAdministratorRequest(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    role: str = "ADMINISTRATOR"

    status: str = "ACTIVE"

    password: str = Field(
        min_length=8,
    )

    confirm_password: str = Field(
        min_length=8,
    )


# ============================================================
# ADMINISTRATOR RESPONSE
# ============================================================

class AdministratorResponse(BaseModel):
    id: UUID

    first_name: str

    last_name: str

    email: str

    role: str

    status: str

    is_active: bool

    last_login_at: datetime | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# ADMINISTRATOR LIST RESPONSE
# ============================================================

class AdministratorListResponse(BaseModel):
    items: list[AdministratorResponse]

    total: int