from flask import request, jsonify

from app.core.dtos import ResultDTO
from . import messages_bp
from . import service as msg_svc


@messages_bp.route("/send", methods=["POST"])
def send():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    result = msg_svc.send_message(request.get_json(silent=True), token)
    return jsonify(result.data), result.status_code