from flask import Blueprint

bot_bp = Blueprint("bot", __name__)

from .webhook import webhook_bp
from .messages import messages_bp
from .conversations import conversations_bp

bot_bp.register_blueprint(webhook_bp, url_prefix="/webhook")
bot_bp.register_blueprint(messages_bp, url_prefix="")
bot_bp.register_blueprint(conversations_bp, url_prefix="/conversations")