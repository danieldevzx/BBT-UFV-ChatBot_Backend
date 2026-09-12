from uuid import uuid7
from datetime import datetime, timezone
from app.core.database.extensions import db


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime, nullable=True)

    conversation = db.relationship("Conversation", back_populates="messages", lazy="joined")