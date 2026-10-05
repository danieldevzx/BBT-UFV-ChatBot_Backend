from flask import g, jsonify, request

from app.core.auth import login_required
from . import atendimentos_bp
from . import service


@atendimentos_bp.route("/", methods=["GET"])
@login_required
def listar():
    result = service.listar(g.usuario)
    return jsonify(result.data), result.status_code


@atendimentos_bp.route("/<int:atendimento_id>", methods=["GET"])
@login_required
def obter(atendimento_id):
    result = service.obter(atendimento_id, g.usuario)
    return jsonify(result.data), result.status_code


@atendimentos_bp.route("/<int:atendimento_id>", methods=["PATCH"])
@login_required
def atualizar(atendimento_id):
    result = service.atualizar(
        atendimento_id, request.get_json(silent=True) or {}, g.usuario
    )
    return jsonify(result.data), result.status_code


@atendimentos_bp.route("/<int:atendimento_id>/mensagens", methods=["GET"])
@login_required
def listar_mensagens(atendimento_id):
    result = service.listar_mensagens(atendimento_id, g.usuario)
    return jsonify(result.data), result.status_code


@atendimentos_bp.route("/<int:atendimento_id>/mensagens", methods=["POST"])
@login_required
def criar_mensagem(atendimento_id):
    result = service.criar_mensagem(
        atendimento_id, request.get_json(silent=True) or {}, g.usuario
    )
    return jsonify(result.data), result.status_code
