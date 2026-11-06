from app.core.database.extensions import db
from app.core.models._common import IsoDateTime, utcnow


class Conteudo(db.Model):
    __tablename__ = "conteudo"

    id = db.Column(db.Integer, primary_key=True)
    # Opcional no banco; a API continua exigindo categoria ao criar.
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=True)
    titulo = db.Column(db.Text, unique=True, nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fonte = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    created_at = db.Column(IsoDateTime, nullable=False, default=utcnow)
    updated_at = db.Column(IsoDateTime, nullable=False, default=utcnow, onupdate=utcnow)

    categoria = db.relationship("Categoria", lazy="joined")
    autor = db.relationship("Usuario", lazy="joined")
