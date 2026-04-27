import os

from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = "postgresql://" + raw_db_url[len("postgres://") :]
    if raw_db_url.startswith("postgresql://") and "+psycopg" not in raw_db_url:
        raw_db_url = "postgresql+psycopg://" + raw_db_url[len("postgresql://") :]

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from . import models  # noqa: F401
    from .auth import auth_bp
    from .routes import site_bp

    app.register_blueprint(site_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    return app

