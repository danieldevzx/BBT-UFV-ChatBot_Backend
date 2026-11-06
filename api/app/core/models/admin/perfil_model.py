from app.core.database.extensions import db


class Perfil(db.Model):
    __tablename__ = "perfil"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, unique=True, nullable=False)

    __table_args__ = (db.CheckConstraint("nome in ('ADMIN','ATENDENTE')"),)
