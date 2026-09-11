from flask import Blueprint

webhook_bp = Blueprint("bot_webhook", __name__)

from . import routes