from flask import Blueprint

atendimentos_bp = Blueprint("dashboard_atendimentos", __name__)

from . import routes

__all__ = ["atendimentos_bp"]
