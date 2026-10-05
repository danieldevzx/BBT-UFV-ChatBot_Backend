from app.core.database.extensions import db
from app.core.models._common import utcnow


class Atendimento(db.Model):
    __tablename__ = "atendimento"

    id = db.Column(db.Integer, primary_key=True)
    telefone_solicitante = db.Column(db.String(20), nullable=False)
    usuario_atendente_id = db.Column(db.String(36), db.ForeignKey("usuario.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ABERTO")
    canal = db.Column(db.String(20), nullable=False, default="WHATSAPP")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    atendente = db.relationship("Usuario", lazy="joined")

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ABERTO', 'EM_ATENDIMENTO', 'FECHADO')",
            name="ck_atendimento_status",
        ),
    )
