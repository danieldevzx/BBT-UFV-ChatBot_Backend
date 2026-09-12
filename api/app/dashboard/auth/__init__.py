from flask import Blueprint

auth_bp = Blueprint("dashboard_auth", __name__)

from . import routes