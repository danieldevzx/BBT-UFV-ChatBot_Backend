from flask import Blueprint

conversations_bp = Blueprint("bot_conversations", __name__)

from . import routes