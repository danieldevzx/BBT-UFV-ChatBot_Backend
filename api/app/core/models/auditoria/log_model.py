from app.core.database.extensions import db
from app.core.models._common import IsoDateTime, utcnow


class Log(db.Model):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    acao = db.Column(db.Text, nullable=False)
    tabela_afetada = db.Column(db.Text)
    registro_id = db.Column(db.Integer)
    criado_em = db.Column(IsoDateTime, nullable=False, default=utcnow)

    usuario = db.relationship("Usuario", lazy="joined")
