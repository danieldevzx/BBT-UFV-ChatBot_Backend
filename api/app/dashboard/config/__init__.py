from flask import Blueprint

config_bp = Blueprint("dashboard_config", __name__)

from . import routes

__all__ = ["config_bp"]
