from app.extensions import db
from app.core.models import Conversation, Message, User
from app.core.dtos import ResultDTO, SendRequestDTO
from app.features.bot.whatsapp import send_whatsapp
from app.features.dashboard.auth.service import _decode_token


def _auth_user(token: str) -> User | None:
    payload = _decode_token(token)
    if not payload:
        return None
    return User.query.filter_by(wa_id=payload["sub"], deleted_at=None).first()


def send_message(body: dict | None, token: str) -> ResultDTO:
    user = _auth_user(token)
    if not user:
        return ResultDTO.unauthorized("Not authenticated")

    if not body:
        return ResultDTO.bad_request("Invalid JSON body")

    req = SendRequestDTO(
        wa_id=(body.get("wa_id") or "").strip(),
        message=(body.get("message") or "").strip(),
    )

    if not req.wa_id or not req.message:
        return ResultDTO.bad_request("wa_id and message are required")

    ok = send_whatsapp(req.wa_id, req.message)
    if not ok:
        return ResultDTO.bad_request("Failed to send message")

    conversation = Conversation.query.filter_by(
        wa_id=req.wa_id, status="active", deleted_at=None
    ).first()
    if not conversation:
        conversation = Conversation(wa_id=req.wa_id, status="active")
        db.session.add(conversation)
        db.session.flush()

    msg = Message(conversation_id=conversation.id, role="staff", content=req.message)
    db.session.add(msg)
    db.session.commit()

    return ResultDTO.ok({"status": "sent", "conversation_id": conversation.id})