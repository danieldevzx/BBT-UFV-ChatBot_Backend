from app.core.database.extensions import db
from app.core.models._common import IsoDateTime, utcnow


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    no_fluxo_id = db.Column(db.Integer, db.ForeignKey("no_fluxo.id"), nullable=False)
    util = db.Column(db.Boolean, nullable=False)
    comentario = db.Column(db.Text)
    criado_em = db.Column(IsoDateTime, nullable=False, default=utcnow)

    no_fluxo = db.relationship("NoFluxo", lazy="joined")

    __table_args__ = (db.CheckConstraint("util in (0,1)"),)
