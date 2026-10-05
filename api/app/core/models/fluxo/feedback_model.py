from app.core.database.extensions import db
from app.core.models._common import utcnow


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    no_fluxo_id = db.Column(db.Integer, db.ForeignKey("no_fluxo.id"), nullable=False)
    util = db.Column(db.Boolean)
    comentario = db.Column(db.Text)
    criado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    no_fluxo = db.relationship("NoFluxo", lazy="joined")
