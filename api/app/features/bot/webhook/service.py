from app.extensions import db
from app.core.models import Conversation, Message
from app.features.bot.whatsapp import send_whatsapp
from app.features.bot.responder import get_reply


def process(data: dict):
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                wa_id = msg.get("from", "")
                msg_type = msg.get("type", "")

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

    reply = get_reply(text)
    send_whatsapp(wa_id, reply)

    msg_out = Message(conversation_id=conversation.id, role="bot", content=reply)
    db.session.add(msg_out)
    db.session.commit()