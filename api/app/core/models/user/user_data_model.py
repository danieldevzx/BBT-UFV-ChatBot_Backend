from uuid import uuid7
from datetime import datetime, timezone
from app.core.database.extensions import db
from app.core.utils.crypto import EncryptedText


class UserData(db.Model):
    __tablename__ = "users_data"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), unique=True, nullable=False)
    email = db.Column(EncryptedText, nullable=True)
    phone = db.Column(EncryptedText, nullable=True)
    bio = db.Column(EncryptedText, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="data", lazy="joined")