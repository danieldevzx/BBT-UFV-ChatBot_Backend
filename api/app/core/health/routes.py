from flask import jsonify
from . import health_bp


@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})