from flask import g, jsonify, request

from app.core.auth import login_required, require_perfil
from . import config_bp
from . import service


@config_bp.route("/", methods=["GET"])
@login_required
def listar():
    result = service.listar()
    return jsonify(result.data), result.status_code


@config_bp.route("/<chave>", methods=["GET"])
@login_required
def obter(chave):
    result = service.obter(chave)
    return jsonify(result.data), result.status_code


@config_bp.route("/<chave>", methods=["PUT"])
@require_perfil("ADMIN")
def upsert(chave):
    result = service.upsert(chave, request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@config_bp.route("/<chave>", methods=["DELETE"])
@require_perfil("ADMIN")
def remover(chave):
    result = service.remover(chave, g.usuario.id)
    return jsonify(result.data), result.status_code
