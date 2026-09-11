from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__)

from .auth import auth_bp
from .archive import archive_bp
from .users import users_bp

dashboard_bp.register_blueprint(auth_bp, url_prefix="/auth")
dashboard_bp.register_blueprint(archive_bp, url_prefix="/archive")
dashboard_bp.register_blueprint(users_bp, url_prefix="/users")