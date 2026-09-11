from flask import request, jsonify

from app.core.dtos import ResultDTO
from . import conversations_bp
from . import service as conv_svc


@conversations_bp.route("/", methods=["GET"])
def list_conversations():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    result = conv_svc.list_conversations(token)
    return jsonify(result.data), result.status_code


@conversations_bp.route("/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    result = conv_svc.get_conversation(conversation_id, token)
    return jsonify(result.data), result.status_code