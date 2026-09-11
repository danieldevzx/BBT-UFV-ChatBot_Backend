from flask import jsonify
from . import users_bp
from app.core.dtos import ResultDTO


@users_bp.route("/", methods=["GET"])
def list_users():
    return jsonify(ResultDTO.ok([]).data)

# TODO: GET /<id>, DELETE /<id>, PATCH /<id>