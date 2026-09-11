from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from flask import current_app

from app.extensions import db
from app.core.models import User
from app.core.dtos import RegisterRequestDTO, LoginRequestDTO, AuthResponseDTO, UserResponseDTO, ResultDTO


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _encode_token(wa_id: str) -> str:
    payload = {
        "sub": wa_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def _decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _active_user_by_wa_id(wa_id: str) -> User | None:
    return User.query.filter_by(wa_id=wa_id, deleted_at=None).first()


def register(req: RegisterRequestDTO) -> ResultDTO:
    if not req.wa_id or not req.password:
        return ResultDTO.bad_request("wa_id and password are required")

    if _active_user_by_wa_id(req.wa_id):
        return ResultDTO.conflict("wa_id already registered")

    name = req.name or req.wa_id
    user = User(wa_id=req.wa_id, name=name, password_hash=_hash_password(req.password))
    db.session.add(user)
    db.session.commit()

    return ResultDTO.created(AuthResponseDTO(message="User created", wa_id=req.wa_id, name=name).__dict__)


def login(req: LoginRequestDTO) -> ResultDTO:
    if not req.wa_id or not req.password:
        return ResultDTO.bad_request("wa_id and password are required")

    user = _active_user_by_wa_id(req.wa_id)
    if not user or not _check_password(req.password, user.password_hash):
        return ResultDTO.unauthorized("Invalid credentials")

    token = _encode_token(req.wa_id)
    return ResultDTO.ok(AuthResponseDTO(token=token, wa_id=req.wa_id, name=user.name).__dict__)


def me(token: str) -> ResultDTO:
    payload = _decode_token(token)
    if not payload:
        return ResultDTO.unauthorized("Not authenticated")

    user = _active_user_by_wa_id(payload["sub"])
    if not user:
        return ResultDTO.unauthorized("Not authenticated")

    return ResultDTO.ok(
        UserResponseDTO(
            wa_id=user.wa_id,
            name=user.name,
            created_at=user.created_at.isoformat(),
        ).__dict__
    )