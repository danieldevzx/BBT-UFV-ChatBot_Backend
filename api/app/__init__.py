import logging

from flask import Flask
from .config import Config
from .core.database.extensions import db, migrate

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .core import models
    from .core.utils.health import health_bp
    from .dashboard import dashboard_bp
    from .whatsapp import whatsapp_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(whatsapp_bp, url_prefix="/api/whatsapp")

    return app