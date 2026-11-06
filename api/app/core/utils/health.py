from flask import Blueprint, jsonify
from sqlalchemy import text

from app.core.database.extensions import SCHEMA_VERSION, db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    try:
        versao = db.session.execute(text("PRAGMA user_version")).scalar()
    except Exception:
        return jsonify({"status": "erro", "db": "indisponível"}), 503
    status = "ok" if versao == SCHEMA_VERSION else "schema_desatualizado"
    return jsonify({"status": status, "schema_version": versao, "schema_esperado": SCHEMA_VERSION}), (
        200 if status == "ok" else 503
    )
