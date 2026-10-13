"""SmartPack AI - Flask backend. Also serves the frontend, so one command runs everything."""
from config.settings import Config, FRONTEND_DIR  # noqa: F401  (also adds project root to sys.path)

from flask import Flask, send_from_directory
try:
    from flask_cors import CORS   # only needed if the frontend is served from another port
except ImportError:
    CORS = None

from models import database
from routes.api import api


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    if CORS:
        CORS(app)
    database.init_db()
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:path>")
    def static_files(path):
        return send_from_directory(FRONTEND_DIR, path)

    return app


if __name__ == "__main__":
    print(f"\n  SmartPack AI running at  http://localhost:{Config.PORT}\n")
    create_app().run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
