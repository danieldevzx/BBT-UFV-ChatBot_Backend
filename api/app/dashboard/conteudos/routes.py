from flask import g, jsonify, request

from app.core.auth import login_required, require_perfil
from . import conteudos_bp
from . import service


def _parse_bool(value):
    if value is None:
        return None
    return value.lower() in ("1", "true", "yes")


@conteudos_bp.route("/", methods=["GET"])
@login_required
def listar():
    categoria_id = request.args.get("categoria_id", type=int)
    ativo = _parse_bool(request.args.get("ativo"))
    result = service.listar(categoria_id=categoria_id, ativo=ativo)
    return jsonify(result.data), result.status_code


@conteudos_bp.route("/<int:conteudo_id>", methods=["GET"])
@login_required
def obter(conteudo_id):
    result = service.obter(conteudo_id)
    return jsonify(result.data), result.status_code


@conteudos_bp.route("/", methods=["POST"])
@require_perfil("ADMIN")
def criar():
    result = service.criar(request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@conteudos_bp.route("/<int:conteudo_id>", methods=["PATCH"])
@require_perfil("ADMIN")
def atualizar(conteudo_id):
    result = service.atualizar(conteudo_id, request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@conteudos_bp.route("/<int:conteudo_id>", methods=["DELETE"])
@require_perfil("ADMIN")
def desativar(conteudo_id):
    result = service.desativar(conteudo_id, g.usuario.id)
    return jsonify(result.data), result.status_code
