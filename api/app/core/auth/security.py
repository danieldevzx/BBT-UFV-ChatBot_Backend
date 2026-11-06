from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from flask import current_app


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def encode_token(usuario_id: int) -> str:
    payload = {
        "sub": str(usuario_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token, current_app.config["JWT_SECRET"], algorithms=["HS256"]
        )
        return int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        return None
