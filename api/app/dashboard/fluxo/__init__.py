from flask import Blueprint

fluxo_bp = Blueprint("dashboard_fluxo", __name__)

from . import routes

__all__ = ["fluxo_bp"]
