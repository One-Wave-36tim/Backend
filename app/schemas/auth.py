from pydantic import BaseModel, constr, field_validator

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "SignupRequest",
    "SignupResponse",
]


class LoginRequest(BaseModel):
    id: str
    pw: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user_id: str | None = None


class SignupRequest(BaseModel):
    id: constr(min_length=3, max_length=50)
    pw: constr(
        min_length=8,
        max_length=128,
    )

    @field_validator("pw")
    @classmethod
    def validate_password(cls, value: str) -> str:
        has_letter = any(ch.isalpha() for ch in value)
        has_digit = any(ch.isdigit() for ch in value)
        has_symbol = any(ch in "!@#$%^&*" for ch in value)
        if not (has_letter and has_digit and has_symbol):
            raise ValueError("비밀번호는 영문, 숫자, 특수문자(!@#$%^&*)를 포함해야 합니다.")
        return value


class SignupResponse(BaseModel):
    success: bool
    message: str
    user_id: str | None = None
