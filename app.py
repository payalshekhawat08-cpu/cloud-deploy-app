"""Cloud-deployed Flask web app.

Demonstrates: environment-based config/secrets, managed database,
application logging, health check endpoint for monitoring.
"""
import logging
import os
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine, text

# ---------- Configuration (all from environment variables) ----------
APP_ENV = os.environ.get("APP_ENV", "development")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")

# Render/Heroku style URLs start with postgres://, SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("cloud-app")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
START_TIME = time.time()


def init_db():
    """Create the table if it does not exist (works on SQLite and PostgreSQL)."""
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name VARCHAR(80) NOT NULL, "
            "body VARCHAR(500) NOT NULL, "
            "created_at VARCHAR(40) NOT NULL)"
            if engine.dialect.name == "sqlite" else
            "CREATE TABLE IF NOT EXISTS messages ("
            "id SERIAL PRIMARY KEY, "
            "name VARCHAR(80) NOT NULL, "
            "body VARCHAR(500) NOT NULL, "
            "created_at VARCHAR(40) NOT NULL)"
        ))
    log.info("Database ready (dialect=%s)", engine.dialect.name)


init_db()


@app.route("/", methods=["GET"])
def index():
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT name, body, created_at FROM messages ORDER BY id DESC LIMIT 50"
        )).fetchall()
    log.info("GET / -> %d messages", len(rows))
    return render_template("index.html", messages=rows, env=APP_ENV,
                           db=engine.dialect.name)


@app.route("/add", methods=["POST"])
def add():
    name = (request.form.get("name") or "").strip()[:80]
    body = (request.form.get("body") or "").strip()[:500]
    if not name or not body:
        log.warning("Rejected empty submission")
        return redirect(url_for("index"))
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO messages (name, body, created_at) "
                 "VALUES (:n, :b, :t)"),
            {"n": name, "b": body,
             "t": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")},
        )
    log.info("New message saved from '%s'", name)
    return redirect(url_for("index"))


@app.route("/health")
def health():
    """Used by the cloud platform (and you) to monitor the app."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        log.error("Health check DB failure: %s", exc)
        db_ok = False
    status = 200 if db_ok else 503
    return jsonify(
        status="ok" if db_ok else "degraded",
        database="up" if db_ok else "down",
        environment=APP_ENV,
        uptime_seconds=int(time.time() - START_TIME),
    ), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
