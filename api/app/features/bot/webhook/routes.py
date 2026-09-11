import hashlib
import hmac
import logging
from http import HTTPStatus

from flask import request, jsonify
from flask import current_app

from . import webhook_bp
from . import service as wh

logger = logging.getLogger(__name__)


@webhook_bp.route("/", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    expected = current_app.config.get("WHATSAPP_VERIFY_TOKEN", "")
    if mode == "subscribe" and token == expected and challenge:
        return challenge, 200

    return "Verification failed", HTTPStatus.FORBIDDEN


@webhook_bp.route("/", methods=["POST"])
def handle():
    signature = request.headers.get("X-Hub-Signature-256", "")
    app_secret = current_app.config.get("WHATSAPP_APP_SECRET", "")

    if app_secret and not _verify_signature(request.get_data(), signature, app_secret):
        logger.warning("Invalid webhook signature")
        return "Unauthorized", HTTPStatus.UNAUTHORIZED

    data = request.get_json(silent=True)
    if not data:
        return "Bad Request", HTTPStatus.BAD_REQUEST

    wh.process(data)
    return "OK", 200


def _verify_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)