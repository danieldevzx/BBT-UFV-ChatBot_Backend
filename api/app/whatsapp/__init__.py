from flask import Blueprint

whatsapp_bp = Blueprint("whatsapp", __name__)

from .webhook import webhook_bp

whatsapp_bp.register_blueprint(webhook_bp, url_prefix="/webhook")