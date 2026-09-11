from flask import Blueprint

users_bp = Blueprint("dashboard_users", __name__)

from . import routes