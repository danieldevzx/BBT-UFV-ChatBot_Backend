from flask import request, jsonify

from app.core.dtos import RegisterRequestDTO, LoginRequestDTO, ResultDTO
from . import auth_bp
from . import service as auth_svc


def _parse_json():
    data = request.get_json(silent=True)
    if not data:
        return None, (jsonify(ResultDTO.bad_request("Invalid JSON body").data), 400)
    return data, None


@auth_bp.route("/register", methods=["POST"])
def register():
    body, err = _parse_json()
    if err:
        return err

    req = RegisterRequestDTO(
        wa_id=(body.get("wa_id") or "").strip(),
        password=(body.get("password") or "").strip(),
        name=(body.get("name") or "").strip() or None,
    )

    result = auth_svc.register(req)
    return jsonify(result.data), result.status_code


@auth_bp.route("/login", methods=["POST"])
def login():
    body, err = _parse_json()
    if err:
        return err

    req = LoginRequestDTO(
        wa_id=(body.get("wa_id") or "").strip(),
        password=(body.get("password") or "").strip(),
    )

    result = auth_svc.login(req)
    return jsonify(result.data), result.status_code


@auth_bp.route("/me", methods=["GET"])
def me():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    result = auth_svc.me(token)
    return jsonify(result.data), result.status_code