import logging
import sqlite3

from flask import Flask

from .config import Config
from .core.database.extensions import SCHEMA_VERSION, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _conferir_banco(app: Flask) -> None:
    """Avisa no log se o arquivo não existe ou está numa versão diferente."""
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    caminho = uri.removeprefix("sqlite:///")
    if not uri.startswith("sqlite:///") or caminho == ":memory:":
        return
    try:
        conn = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
        versao = conn.execute("PRAGMA user_version").fetchone()[0]
        conn.close()
    except sqlite3.Error:
        logger.error("Banco não encontrado em %s. Rode 'flask db init'.", caminho)
        return
    if versao != SCHEMA_VERSION:
        logger.error(
            "Schema do banco em v%s, o código espera v%s. Rode 'flask db upgrade'.",
            versao, SCHEMA_VERSION,
        )


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Config)

    db.init_app(app)
    _conferir_banco(app)

    from .core import models  # noqa: F401
    from .core.database.cli import db_cli
    from .core.utils.health import health_bp
    from .dashboard import dashboard_bp
    from .painel import painel_bp
    from .whatsapp import whatsapp_bp

    app.cli.add_command(db_cli)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")
    app.register_blueprint(painel_bp)

    return app
