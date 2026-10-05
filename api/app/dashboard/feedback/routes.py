from flask import jsonify, request

from app.core.auth import login_required, require_perfil
from . import feedback_bp
from . import service


@feedback_bp.route("/", methods=["GET"])
@require_perfil("ADMIN")
def listar():
    no_fluxo_id = request.args.get("no_fluxo_id", type=int)
    result = service.listar(no_fluxo_id=no_fluxo_id)
    return jsonify(result.data), result.status_code


@feedback_bp.route("/", methods=["POST"])
@login_required
def criar():
    result = service.criar(request.get_json(silent=True) or {})
    return jsonify(result.data), result.status_code
