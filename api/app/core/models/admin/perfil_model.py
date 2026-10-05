from app.core.database.extensions import db


class Perfil(db.Model):
    __tablename__ = "perfil"

    id = db.Column(db.SmallInteger, primary_key=True)
    nome = db.Column(db.String(20), unique=True, nullable=False)

    __table_args__ = (
        db.CheckConstraint("nome IN ('ADMIN', 'ATENDENTE')", name="ck_perfil_nome"),
    )
