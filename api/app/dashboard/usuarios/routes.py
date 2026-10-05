from flask import g, jsonify, request

from app.core.auth import require_perfil
from . import usuarios_bp
from . import service


@usuarios_bp.route("/", methods=["GET"])
@require_perfil("ADMIN")
def listar():
    result = service.listar()
    return jsonify(result.data), result.status_code


@usuarios_bp.route("/", methods=["POST"])
@require_perfil("ADMIN")
def criar():
    result = service.criar(request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@usuarios_bp.route("/<usuario_id>", methods=["GET"])
@require_perfil("ADMIN")
def obter(usuario_id):
    result = service.obter(usuario_id)
    return jsonify(result.data), result.status_code


@usuarios_bp.route("/<usuario_id>", methods=["PATCH"])
@require_perfil("ADMIN")
def atualizar(usuario_id):
    result = service.atualizar(usuario_id, request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@usuarios_bp.route("/<usuario_id>", methods=["DELETE"])
@require_perfil("ADMIN")
def desativar(usuario_id):
    result = service.desativar(usuario_id, g.usuario.id)
    return jsonify(result.data), result.status_code
