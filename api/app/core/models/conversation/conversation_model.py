from uuid import uuid7
from datetime import datetime, timezone
from app.extensions import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    wa_id = db.Column(db.String(20), nullable=False, index=True)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    messages = db.relationship("Message", back_populates="conversation", lazy="dynamic", order_by="Message.created_at")