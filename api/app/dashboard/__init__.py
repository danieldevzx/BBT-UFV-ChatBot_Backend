from flask import Blueprint

dashboard_bp = Blueprint("dashboard", __name__)

from .auth import auth_bp
from .usuarios import usuarios_bp
from .categorias import categorias_bp
from .conteudos import conteudos_bp
from .fluxo import fluxo_bp
from .config import config_bp
from .atendimentos import atendimentos_bp
from .feedback import feedback_bp
from .logs import logs_bp

dashboard_bp.register_blueprint(auth_bp, url_prefix="/auth")
dashboard_bp.register_blueprint(usuarios_bp, url_prefix="/usuarios")
dashboard_bp.register_blueprint(categorias_bp, url_prefix="/categorias")
dashboard_bp.register_blueprint(conteudos_bp, url_prefix="/conteudos")
dashboard_bp.register_blueprint(fluxo_bp, url_prefix="/fluxo")
dashboard_bp.register_blueprint(config_bp, url_prefix="/config")
dashboard_bp.register_blueprint(atendimentos_bp, url_prefix="/atendimentos")
dashboard_bp.register_blueprint(feedback_bp, url_prefix="/feedback")
dashboard_bp.register_blueprint(logs_bp, url_prefix="/logs")
