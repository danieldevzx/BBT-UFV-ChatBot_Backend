from flask import Blueprint

conteudos_bp = Blueprint("dashboard_conteudos", __name__)

from . import routes

__all__ = ["conteudos_bp"]
