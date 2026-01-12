import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager


# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///hospital.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# --- Serverless function size check (helpful for Vercel deployments) ---
# This check runs automatically when the app is started on Vercel (VERCEL env var)
# or when FAIL_ON_LARGE_FUNCTION=1 is set. It logs a clear error and raises
# a RuntimeError with a direct link if the project uncompressed size exceeds
# the typical Vercel serverless limit (250 MB).

def _get_dir_size_bytes(path, exclude=None):
    exclude = set(exclude or [".git", "node_modules", "venv", ".venv", "__pycache__"])
    total = 0
    for root, dirs, files in os.walk(path, topdown=True):
        # remove excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                continue
    return total

try:
    run_size_check = bool(os.environ.get("VERCEL")) or os.environ.get("FAIL_ON_LARGE_FUNCTION") == "1"
    if run_size_check:
        threshold_mb = float(os.environ.get("FUNCTION_SIZE_THRESHOLD_MB", "250"))
        _bytes = _get_dir_size_bytes(os.getcwd())
        detected_mb = _bytes / (1024.0 * 1024.0)
        if detected_mb > threshold_mb:
            msg = (
                f"ERROR: Unzipped serverless function size ({detected_mb:.1f} MB) "
                f"exceeds the configured threshold ({threshold_mb:.1f} MB)."
                "\nVercel has a hard unzipped serverless function limit of 250 MB."
                " See: https://vercel.link/serverless-function-size"
            )
            logging.error(msg)
            raise RuntimeError(msg)
except RuntimeError:
    # Re-raise so app startup fails with a clear message
    raise
except Exception:
    # Log but don't prevent app start if size check itself fails unexpectedly
    logging.exception("Failed to perform serverless function size check")

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    
    # During development, we'll drop all tables and recreate them
    # This should be removed in production
    # db.drop_all()
    # db.create_all()
