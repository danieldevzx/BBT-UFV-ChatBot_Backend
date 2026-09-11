from flask import Flask
from .config import Config
from .extensions import db, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from .core import models
    from .core.health import health_bp
    from .features.dashboard import dashboard_bp
    from .features.bot import bot_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(bot_bp, url_prefix="/api/bot")

    return app