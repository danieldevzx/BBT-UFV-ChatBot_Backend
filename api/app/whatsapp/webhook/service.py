import logging

from app.core.database.extensions import db
from app.core.models import Conversation, Message
from app.core.utils.wa_utils import normalize_wa_id
from app.whatsapp.whatsapp import send_whatsapp
from app.bot.responder import gerar_resposta

logger = logging.getLogger(__name__)


def process(data: dict):
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                wa_id = normalize_wa_id(msg.get("from", ""))
                msg_type = msg.get("type", "")

                logger.warning("Incoming | wa_id=%s type=%s", wa_id, msg_type)

                if msg_type != "text":
                    continue

                text = (msg.get("text", {}) or {}).get("body", "")
                if not wa_id or not text:
                    continue

                _handle_incoming(wa_id, text)


def _handle_incoming(wa_id: str, text: str):
    conversation = Conversation.query.filter_by(
        wa_id=wa_id, status="active", deleted_at=None
    ).first()
    if not conversation:
        conversation = Conversation(wa_id=wa_id, status="active")
        db.session.add(conversation)
        db.session.flush()

    msg_in = Message(conversation_id=conversation.id, role="user", content=text)
    db.session.add(msg_in)
    db.session.commit()

    reply = gerar_resposta(text)
    ok = send_whatsapp(wa_id, reply)
    logger.warning("send_whatsapp to %s -> %s", wa_id, ok)

    msg_out = Message(conversation_id=conversation.id, role="bot", content=reply)
    db.session.add(msg_out)
    db.session.commit()