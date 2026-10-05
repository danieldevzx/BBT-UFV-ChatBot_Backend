from flask import g, jsonify, request

from app.core.auth import login_required, require_perfil
from . import fluxo_bp
from . import service


def _parse_bool(value):
    if value is None:
        return None
    return value.lower() in ("1", "true", "yes")


@fluxo_bp.route("/", methods=["GET"])
@login_required
def listar():
    result = service.listar(
        parent_id=request.args.get("parent_id", type=int),
        raiz=_parse_bool(request.args.get("raiz")) or False,
        ativo=_parse_bool(request.args.get("ativo")),
    )
    return jsonify(result.data), result.status_code


@fluxo_bp.route("/<int:no_id>", methods=["GET"])
@login_required
def obter(no_id):
    result = service.obter(no_id)
    return jsonify(result.data), result.status_code


@fluxo_bp.route("/", methods=["POST"])
@require_perfil("ADMIN")
def criar():
    result = service.criar(request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@fluxo_bp.route("/<int:no_id>", methods=["PATCH"])
@require_perfil("ADMIN")
def atualizar(no_id):
    result = service.atualizar(no_id, request.get_json(silent=True) or {}, g.usuario.id)
    return jsonify(result.data), result.status_code


@fluxo_bp.route("/<int:no_id>", methods=["DELETE"])
@require_perfil("ADMIN")
def desativar(no_id):
    result = service.desativar(no_id, g.usuario.id)
    return jsonify(result.data), result.status_code
