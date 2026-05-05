from urllib.parse import urlsplit

from flask import Blueprint, request, jsonify, render_template, current_app, redirect, url_for, session
from flask_login import login_required, current_user

from extensions import db
from models import FavoriteRestaurant, Restaurant

from services.auth_service import (
    request_password_reset,
    get_valid_reset_token,
    reset_user_password,
    register_user,
    login_user_by_credentials,
    logout_current_user,
    build_me_response,
    get_user_notifications,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _coerce_next_url(target):
    if not target:
        return None

    target = str(target).strip()
    if not target or target.startswith("//"):
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


def _consume_next_url():
    next_url = _coerce_next_url(request.args.get("next"))
    if not next_url:
        next_url = _coerce_next_url(session.get("next_url"))

    session.pop("next_url", None)
    return next_url


def _apply_pending_favorite_restaurant(user):
    if not getattr(user, "is_authenticated", False):
        return

    restaurant_id = session.pop("pending_favorite_restaurant_id", None)
    if not restaurant_id:
        return

    try:
        restaurant_id = int(restaurant_id)
    except (TypeError, ValueError):
        return

    restaurant = db.session.get(Restaurant, restaurant_id)
    if not restaurant or not getattr(restaurant, "is_active", False):
        return

    existing = FavoriteRestaurant.query.filter_by(
        user_id=user.id,
        restaurant_id=restaurant_id,
    ).first()

    if existing:
        return

    db.session.add(
        FavoriteRestaurant(
            user_id=user.id,
            restaurant_id=restaurant_id,
        )
    )
    db.session.commit()


@auth_bp.get("/")
def login_page():
    next_url = _coerce_next_url(request.args.get("next"))
    if next_url:
        session["next_url"] = next_url
    return render_template("auth.html")


@auth_bp.get("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@auth_bp.post("/forgot-password")
def forgot_password():
    try:
        result, status_code = request_password_reset(
            request.get_json(silent=True) or request.form
        )
        return jsonify(result), status_code
    except Exception:
        current_app.logger.exception("FORGOT PASSWORD ERROR")
        return jsonify({"error": "Внутрішня помилка сервера"}), 500


@auth_bp.get("/reset-password/<token>")
def reset_password_page(token):
    token_obj = get_valid_reset_token(token)

    if not token_obj:
        return render_template("reset_password_invalid.html"), 400

    return render_template("reset_password.html", token=token)


@auth_bp.post("/reset-password/<token>")
def reset_password(token):
    result, status_code = reset_user_password(
        token,
        request.get_json(silent=True) or request.form
    )
    return jsonify(result), status_code


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        result, status_code = register_user(
            request.get_json(silent=True) or request.form
        )
        if status_code < 400:
            _apply_pending_favorite_restaurant(current_user)
            next_url = _consume_next_url()
            result["redirect"] = next_url or result.get("redirect") or "/"
        return jsonify(result), status_code
    except Exception:
        current_app.logger.exception("REGISTER ERROR")
        return jsonify({"error": "Внутрішня помилка сервера"}), 500


@auth_bp.post("/login")
def login():
    result, status_code = login_user_by_credentials(
        request.get_json(silent=True) or request.form
    )

    if status_code < 400:
        _apply_pending_favorite_restaurant(current_user)
        next_url = _consume_next_url()
        result["redirect"] = next_url or result.get("redirect") or "/"

    return jsonify(result), status_code


@auth_bp.post("/logout")
@login_required
def logout():
    result, status_code = logout_current_user()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify(result), status_code

    return redirect(url_for("restaurant.home_page"))


@auth_bp.get("/me")
def me():
    result, status_code = build_me_response(current_user)
    return jsonify(result), status_code


@auth_bp.get("/api/notifications")
@login_required
def get_notifications():
    result = get_user_notifications(current_user.id)
    return jsonify(result)
