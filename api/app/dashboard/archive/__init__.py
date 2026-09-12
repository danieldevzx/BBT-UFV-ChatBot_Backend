from flask import Blueprint

archive_bp = Blueprint("dashboard_archive", __name__)

from . import routes