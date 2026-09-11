import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def send_whatsapp(wa_id: str, text: str) -> bool:
    phone_id = current_app.config.get("WHATSAPP_PHONE_NUMBER_ID", "")
    token = current_app.config.get("WHATSAPP_TOKEN", "")
    if not phone_id or not token:
        logger.warning("WhatsApp not configured")
        return False

    url = f"https://graph.facebook.com/v22.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("WhatsApp send error: %s", e)
        return False