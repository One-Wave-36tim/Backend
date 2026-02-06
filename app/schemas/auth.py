from pydantic import BaseModel


class LoginRequest(BaseModel):
    id: str
    pw: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user_id: str | None = None
    access_token: str | None = None
    token_type: str | None = None