from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginAdministratorResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    role: str
    status: str
    is_active: bool
    last_login_at: datetime | None

    model_config = {
        "from_attributes": True,
    }


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    administrator: LoginAdministratorResponse