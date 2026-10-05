from app.core.database.extensions import db
from app.core.models._common import utcnow


class Log(db.Model):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.String(36), db.ForeignKey("usuario.id"), nullable=True)
    acao = db.Column(db.String(100), nullable=False)
    tabela_afetada = db.Column(db.String(100))
    registro_id = db.Column(db.Integer)
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    usuario = db.relationship("Usuario", lazy="joined")
