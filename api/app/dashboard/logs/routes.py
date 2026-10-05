from flask import jsonify

from app.core.auth import require_perfil
from . import logs_bp
from . import service


@logs_bp.route("/", methods=["GET"])
@require_perfil("ADMIN")
def listar():
    result = service.listar()
    return jsonify(result.data), result.status_code
