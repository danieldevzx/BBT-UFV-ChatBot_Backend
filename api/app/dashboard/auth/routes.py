from flask import g, jsonify, request

from app.core.dtos import LoginRequestDTO, RegisterRequestDTO
from app.core.auth import login_required
from . import auth_bp
from . import service as auth_svc


def _parse_json():
    data = request.get_json(silent=True)
    if not data:
        return None, (jsonify({"error": "Invalid JSON body"}), 400)
    return data, None


@auth_bp.route("/register", methods=["POST"])
def register():
    body, err = _parse_json()
    if err:
        return err

    req = RegisterRequestDTO(
        email=(body.get("email") or "").strip().lower(),
        password=(body.get("password") or "").strip(),
        name=(body.get("name") or "").strip() or None,
        perfil=(body.get("perfil") or "").strip().upper() or None,
    )
    result = auth_svc.register(req)
    return jsonify(result.data), result.status_code


@auth_bp.route("/login", methods=["POST"])
def login():
    body, err = _parse_json()
    if err:
        return err

    req = LoginRequestDTO(
        email=(body.get("email") or "").strip().lower(),
        password=(body.get("password") or "").strip(),
    )
    result = auth_svc.login(req)
    return jsonify(result.data), result.status_code


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    result = auth_svc.me(g.usuario)
    return jsonify(result.data), result.status_code
