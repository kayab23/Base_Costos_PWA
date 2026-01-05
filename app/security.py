"""Herramientas compartidas para hashing de contraseñas."""
from __future__ import annotations

from passlib.context import CryptContext

try:  # pragma: no cover - parche para cambios en bcrypt 4+
    import bcrypt as _bcrypt  # type: ignore

    if not hasattr(_bcrypt, "__about__"):
        class _About:
            __version__ = getattr(_bcrypt, "__version__", "unknown")

        _bcrypt.__about__ = _About()  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    pass

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(password, password_hash)
    except ValueError:
        return False
