from app.core.database.extensions import db


class ConfigBot(db.Model):
    __tablename__ = "config_bot"

    chave = db.Column(db.String(50), primary_key=True)
    valor = db.Column(db.Text, nullable=False)
