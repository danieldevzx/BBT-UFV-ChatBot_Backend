from app.core.models import Conversation, User
from app.core.dtos import ResultDTO, ConversationResponseDTO, MessageResponseDTO
from app.features.dashboard.auth.service import _decode_token


def _auth_user(token: str) -> User | None:
    payload = _decode_token(token)
    if not payload:
        return None
    return User.query.filter_by(wa_id=payload["sub"], deleted_at=None).first()


def list_conversations(token: str) -> ResultDTO:
    user = _auth_user(token)
    if not user:
        return ResultDTO.unauthorized("Not authenticated")

    conversations = Conversation.query.filter_by(deleted_at=None).order_by(
        Conversation.updated_at.desc()
    ).all()
    data = [
        ConversationResponseDTO(
            id=c.id,
            wa_id=c.wa_id,
            status=c.status,
            message_count=c.messages.filter_by(deleted_at=None).count(),
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        ).__dict__
        for c in conversations
    ]
    return ResultDTO.ok(data)


def get_conversation(conversation_id: str, token: str) -> ResultDTO:
    user = _auth_user(token)
    if not user:
        return ResultDTO.unauthorized("Not authenticated")

    conversation = Conversation.query.filter_by(id=conversation_id, deleted_at=None).first()
    if not conversation:
        return ResultDTO.bad_request("Conversation not found")

    messages = [
        MessageResponseDTO(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        ).__dict__
        for m in conversation.messages.filter_by(deleted_at=None).all()
    ]

    return ResultDTO.ok({
        "conversation": ConversationResponseDTO(
            id=conversation.id,
            wa_id=conversation.wa_id,
            status=conversation.status,
            message_count=len(messages),
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
        ).__dict__,
        "messages": messages,
    })