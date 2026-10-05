from flask import Blueprint

usuarios_bp = Blueprint("dashboard_usuarios", __name__)

from . import routes

__all__ = ["usuarios_bp"]
