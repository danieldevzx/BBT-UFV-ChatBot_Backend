from app.core.database.extensions import db


class NoFluxo(db.Model):
    __tablename__ = "no_fluxo"

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("no_fluxo.id"), nullable=True)
    titulo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.Text, nullable=False)
    conteudo_id = db.Column(db.Integer, db.ForeignKey("conteudo.id"), nullable=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    parent = db.relationship("NoFluxo", remote_side="NoFluxo.id", backref="filhos")
    conteudo = db.relationship("Conteudo", lazy="joined")

    __table_args__ = (
        db.CheckConstraint("length(titulo) <= 24"),
        db.CheckConstraint("tipo in ('MENU','RESPOSTA','ATENDENTE')"),
        db.CheckConstraint("(tipo = 'RESPOSTA') = (conteudo_id is not null)"),
        db.Index("no_fluxo_parent_idx", "parent_id", "ordem"),
    )
