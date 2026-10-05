from app.core.database.extensions import db


class NoFluxo(db.Model):
    __tablename__ = "no_fluxo"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("no_fluxo.id"), nullable=True)
    titulo = db.Column(db.String(24), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    conteudo_id = db.Column(db.Integer, db.ForeignKey("conteudo.id"), nullable=True)
    ordem = db.Column(db.SmallInteger, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    parent = db.relationship("NoFluxo", remote_side="NoFluxo.id", backref="filhos")
    conteudo = db.relationship("Conteudo", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("tipo IN ('MENU', 'RESPOSTA', 'ATENDENTE')", name="ck_no_fluxo_tipo"),
        db.CheckConstraint("length(titulo) <= 24", name="ck_no_fluxo_titulo"),
        db.CheckConstraint(
            "(tipo = 'RESPOSTA' AND conteudo_id IS NOT NULL) OR (tipo <> 'RESPOSTA')",
            name="ck_no_fluxo_conteudo",
        ),
    )
