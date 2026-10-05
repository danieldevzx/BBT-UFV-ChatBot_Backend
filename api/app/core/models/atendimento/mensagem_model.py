from app.core.database.extensions import db
from app.core.models._common import utcnow


class Mensagem(db.Model):
    __tablename__ = "mensagem"

    id = db.Column(db.Integer, primary_key=True)
    atendimento_id = db.Column(db.Integer, db.ForeignKey("atendimento.id"), nullable=False)
    remetente = db.Column(db.String(12), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    enviado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    atendimento = db.relationship("Atendimento", backref="mensagens")

    __table_args__ = (
        db.CheckConstraint(
            "remetente IN ('USUARIO', 'BOT', 'ATENDENTE')", name="ck_mensagem_remetente"
        ),
    )
