import os
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

from flask import Flask, jsonify, redirect, request, url_for, flash, session
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate

from config import Config
from extensions import db, login_manager, mail, csrf
from models import User
from auth_routes import auth_bp
from restaurant_routes import restaurant_bp
from order_routes import order_bp
from admin import admin_bp
from partner_panel import partner_panel_bp
from partner_routes import partner_bp
from profile_routes import profile_bp
from cart_routes import cart_bp


JSON_ERROR_PATH_PREFIXES = (
    "/api/",
    "/admin/api/",
    "/partner/api/",
    "/profile/api",
    "/api/partner/",
    "/auth/api/",
)

JSON_ERROR_EXACT_PATHS = {
    "/auth/login",
    "/auth/register",
    "/auth/forgot-password",
    "/auth/me",
}

HTTP_ERROR_MESSAGES = {
    400: "Некоректний запит",
    401: "Потрібно увійти в акаунт",
    403: "Доступ заборонено",
    404: "Ресурс не знайдено",
    405: "Метод запиту не підтримується",
    413: "Файл завеликий. Максимальний розмір — 15 МБ",
    415: "Непідтримуваний формат даних",
    422: "Не вдалося обробити запит",
    429: "Забагато запитів. Спробуйте трохи пізніше",
    500: "Внутрішня помилка сервера",
}


def _wants_json_error_response():
    path = request.path or ""

    if path in JSON_ERROR_EXACT_PATHS:
        return True

    if path.startswith(JSON_ERROR_PATH_PREFIXES):
        return True

    if path.startswith("/auth/reset-password/") and request.method.upper() == "POST":
        return True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return True

    accept_mimetypes = request.accept_mimetypes
    return (
        accept_mimetypes["application/json"]
        >= accept_mimetypes["text/html"]
    )


def _json_error_response(status_code, message=None, details=None):
    payload = {
        "error": message or HTTP_ERROR_MESSAGES.get(status_code, "Сталася помилка"),
        "status_code": status_code,
    }

    if details:
        payload["details"] = details

    return jsonify(payload), status_code


def _coerce_next_url(target):
    if not target:
        return None

    target = str(target).strip()
    if not target:
        return None

    if target.startswith("//"):
        return None

    parts = urlsplit(target)

    if parts.scheme and parts.netloc:
        if parts.netloc != request.host:
            return None

        path = parts.path or "/"
        if parts.query:
            path = f"{path}?{parts.query}"
        return path

    if target.startswith("/"):
        return target

    return None


def create_admin():
    from werkzeug.security import generate_password_hash

    email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD")
    phone = (os.getenv("ADMIN_PHONE") or "+380000000000").strip()

    if not email or not password:
        return False, "ADMIN_EMAIL or ADMIN_PASSWORD is not set."

    existing = User.query.filter_by(email=email).first()

    if not existing:
        admin = User(
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            full_name="Admin",
            city="ivano-frankivsk",
            street="",
            house="",
            extra_info="",
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
        return True, "Admin created successfully."

    existing.password_hash = generate_password_hash(password)
    existing.is_admin = True

    if not getattr(existing, "phone", None):
        existing.phone = phone

    db.session.commit()
    return True, "Admin updated successfully."


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024
    app.config["WTF_CSRF_TIME_LIMIT"] = 7200

    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "restaurants"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "menu"), exist_ok=True)

    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if _wants_json_error_response():
            return _json_error_response(401)

        next_url = _coerce_next_url(request.url) or "/"
        session["next_url"] = next_url

        return redirect(url_for(login_manager.login_view, next=next_url))

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        if _wants_json_error_response():
            return _json_error_response(400)
        return ("CSRF error", 400)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if _wants_json_error_response():
            return _json_error_response(error.code or 500)
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        if _wants_json_error_response():
            app.logger.exception("ERROR")
            return _json_error_response(500)

        app.logger.exception("ERROR")
        return ("Internal error", 500)

    app.cli.command("create-admin")(create_admin)

    app.register_blueprint(auth_bp)
    app.register_blueprint(restaurant_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(partner_panel_bp)
    app.register_blueprint(partner_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(cart_bp)

    # 💥 FIX ДЛЯ RENDER / SQLITE
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.getenv("FLASK_DEBUG", "false").strip().lower() == "true"
    app.run(debug=debug_mode)