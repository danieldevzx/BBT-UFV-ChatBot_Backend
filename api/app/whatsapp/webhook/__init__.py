from flask import Blueprint

webhook_bp = Blueprint("whatsapp_webhook", __name__)

from . import routes