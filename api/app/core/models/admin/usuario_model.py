from uuid import uuid7

from app.core.database.extensions import db
from app.core.models._common import utcnow


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid7()))
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    perfil_id = db.Column(db.SmallInteger, db.ForeignKey("perfil.id"), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    perfil = db.relationship("Perfil", lazy="joined")
