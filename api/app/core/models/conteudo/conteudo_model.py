from app.core.database.extensions import db
from app.core.models._common import utcnow


class Conteudo(db.Model):
    __tablename__ = "conteudo"

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)
    titulo = db.Column(db.String(200), unique=True, nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fonte = db.Column(db.String(200))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.String(36), db.ForeignKey("usuario.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    categoria = db.relationship("Categoria", lazy="joined")
    autor = db.relationship("Usuario", lazy="joined")
