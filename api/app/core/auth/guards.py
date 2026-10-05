from functools import wraps

from flask import g, jsonify, request

from app.core.models import Usuario
from .security import decode_token


def current_usuario() -> Usuario | None:
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return None
    usuario_id = decode_token(token)
    if not usuario_id:
        return None
    return Usuario.query.filter_by(id=usuario_id, ativo=True).first()


def require_perfil(*perfis: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            usuario = current_usuario()
            if not usuario:
                return jsonify({"error": "Not authenticated"}), 401
            if perfis and usuario.perfil.nome not in perfis:
                return jsonify({"error": "Forbidden"}), 403
            g.usuario = usuario
            return fn(*args, **kwargs)

        return wrapper

    return decorator


login_required = require_perfil()
