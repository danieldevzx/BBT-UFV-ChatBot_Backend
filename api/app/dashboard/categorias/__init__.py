from flask import Blueprint

categorias_bp = Blueprint("dashboard_categorias", __name__)

from . import routes

__all__ = ["categorias_bp"]
