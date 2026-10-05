from flask import Blueprint

logs_bp = Blueprint("dashboard_logs", __name__)

from . import routes

__all__ = ["logs_bp"]
