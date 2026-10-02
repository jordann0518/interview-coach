"""interview-coach: AI-powered technical interview practice."""
from flask import Flask
from . import db
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "interview-coach-dev-key"  # dev only; flash messages
    db.init_db()
    app.register_blueprint(bp)
    return app
