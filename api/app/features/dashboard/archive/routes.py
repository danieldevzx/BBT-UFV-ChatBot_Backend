from flask import jsonify
from . import archive_bp
from app.core.dtos import ResultDTO


@archive_bp.route("/", methods=["GET"])
def list_files():
    return jsonify(ResultDTO.ok([]).data)

# TODO: POST /upload, DELETE /<id>, GET /<id>