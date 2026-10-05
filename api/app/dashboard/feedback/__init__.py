from flask import Blueprint

feedback_bp = Blueprint("dashboard_feedback", __name__)

from . import routes

__all__ = ["feedback_bp"]
