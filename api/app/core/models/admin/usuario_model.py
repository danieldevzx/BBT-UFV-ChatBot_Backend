from app.core.database.extensions import db
from app.core.models._common import IsoDateTime, utcnow


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    # No banco a coluna se chama senha_hash; o atributo Python mantém o nome antigo.
    password_hash = db.Column("senha_hash", db.Text, nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey("perfil.id"), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(IsoDateTime, nullable=False, default=utcnow)

    perfil = db.relationship("Perfil", lazy="joined")
