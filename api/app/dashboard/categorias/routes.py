from flask import g, jsonify, request

from app.core.auth import login_required, require_perfil
from . import categorias_bp
from . import service


@categorias_bp.route("/", methods=["GET"])
@login_required
def listar():
    result = service.listar()
    return jsonify(result.data), result.status_code


@categorias_bp.route("/<int:categoria_id>", methods=["GET"])
@login_required
def obter(categoria_id):
    result = service.obter(categoria_id)
    return jsonify(result.data), result.status_code


@categorias_bp.route("/", methods=["POST"])
@require_perfil("ADMIN")
def criar():
    result = service.criar(request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@categorias_bp.route("/<int:categoria_id>", methods=["PATCH"])
@require_perfil("ADMIN")
def atualizar(categoria_id):
    result = service.atualizar(categoria_id, request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@categorias_bp.route("/<int:categoria_id>", methods=["DELETE"])
@require_perfil("ADMIN")
def remover(categoria_id):
    result = service.remover(categoria_id, g.usuario.id)
    return jsonify(result.data), result.status_code
