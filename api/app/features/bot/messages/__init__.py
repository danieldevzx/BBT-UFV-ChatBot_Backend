from flask import Blueprint

messages_bp = Blueprint("bot_messages", __name__)

from . import routes