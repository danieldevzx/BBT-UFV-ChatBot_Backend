from app.core.database.extensions import db
from app.core.models._common import IsoDateTime, utcnow


class Atendimento(db.Model):
    __tablename__ = "atendimento"

    id = db.Column(db.Integer, primary_key=True)
    telefone_solicitante = db.Column(db.Text, nullable=False)
    usuario_atendente_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    status = db.Column(db.Text, nullable=False, default="ABERTO")
    canal = db.Column(db.Text, nullable=False, default="WHATSAPP")
    created_at = db.Column(IsoDateTime, nullable=False, default=utcnow)
    closed_at = db.Column(IsoDateTime, nullable=True)

    atendente = db.relationship("Usuario", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("status in ('ABERTO','EM_ATENDIMENTO','FECHADO')"),
    )
