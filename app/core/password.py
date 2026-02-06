import hashlib
import hmac
from typing import cast

try:
    from passlib.context import CryptContext
except ModuleNotFoundError:  # pragma: no cover - optional dependency in local env.
    CryptContext = None

_pwd_context = (
    CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto") if CryptContext is not None else None
)


def hash_password(password: str) -> str:
    if _pwd_context is not None:
        return cast(str, _pwd_context.hash(password))
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return f"sha256${digest}"


def verify_password(password: str, hashed_password: str) -> bool:
    if _pwd_context is not None:
        return cast(bool, _pwd_context.verify(password, hashed_password))
    if not hashed_password.startswith("sha256$"):
        return False
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(hashed_password, f"sha256${digest}")
