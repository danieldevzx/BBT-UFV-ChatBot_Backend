import logging

import requests
from flask import current_app

from app.core.utils.wa_utils import normalize_wa_id

logger = logging.getLogger(__name__)

MAX_BUTTONS = 3
MAX_ROWS = 10
MAX_BUTTON_TITLE = 20
MAX_ROW_TITLE = 24
GRAPH_URL = "https://graph.facebook.com/v25.0/{phone_id}/messages"


def _post(payload: dict) -> bool:
    phone_id = current_app.config.get("WHATSAPP_PHONE_NUMBER_ID", "")
    token = current_app.config.get("WHATSAPP_TOKEN", "")
    if not phone_id or not token:
        logger.warning("WhatsApp not configured")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            GRAPH_URL.format(phone_id=phone_id), headers=headers, json=payload, timeout=15
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("WhatsApp send error: %s", e)
        return False


def _base(wa_id: str) -> dict:
    return {"messaging_product": "whatsapp", "to": normalize_wa_id(wa_id)}


def send_text(wa_id: str, text: str) -> bool:
    return _post({**_base(wa_id), "type": "text", "text": {"body": text}})


def send_buttons(wa_id: str, body: str, buttons: list[tuple]) -> bool:
    action = {
        "buttons": [
            {
                "type": "reply",
                "reply": {"id": str(bid), "title": title[:MAX_BUTTON_TITLE]},
            }
            for bid, title in buttons[:MAX_BUTTONS]
        ]
    }
    payload = {
        **_base(wa_id),
        "type": "interactive",
        "interactive": {"type": "button", "body": {"text": body}, "action": action},
    }
    return _post(payload)


def send_list(wa_id: str, body: str, button_text: str, rows: list[tuple]) -> bool:
    action = {
        "button": button_text[:MAX_BUTTON_TITLE],
        "sections": [
            {
                "title": button_text[:MAX_BUTTON_TITLE],
                "rows": [
                    {"id": str(rid), "title": title[:MAX_ROW_TITLE]}
                    for rid, title in rows[:MAX_ROWS]
                ],
            }
        ],
    }
    payload = {
        **_base(wa_id),
        "type": "interactive",
        "interactive": {"type": "list", "body": {"text": body}, "action": action},
    }
    return _post(payload)
