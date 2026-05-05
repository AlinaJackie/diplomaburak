from urllib.parse import urlsplit

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import current_user

from services.restaurant_service import (
    get_restaurant_page_data,
    get_restaurants_list_service,
    get_restaurant_detail_service,
    get_restaurant_menu_service,
    toggle_favorite_restaurant_service,
    toggle_favorite_menu_item_service,
)
from models import FavoriteRestaurant

restaurant_bp = Blueprint("restaurant", __name__)


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


@restaurant_bp.get("/")
def home_page():
    return render_template("index.html")


@restaurant_bp.get("/restaurant/<int:restaurant_id>")
def restaurant_page(restaurant_id):
    restaurant, items = get_restaurant_page_data(restaurant_id)

    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = (
            FavoriteRestaurant.query.filter_by(
                user_id=current_user.id,
                restaurant_id=restaurant.id,
            ).first()
            is not None
        )

    return render_template(
        "restaurant.html",
        restaurant=restaurant,
        items=items,
        is_favorite=is_favorite,
    )


@restaurant_bp.get("/api/restaurants")
def api_restaurants():
    result = get_restaurants_list_service(request.args, current_user)
    return jsonify(result)


@restaurant_bp.get("/api/restaurants/<int:restaurant_id>")
def api_restaurant_detail(restaurant_id):
    result = get_restaurant_detail_service(restaurant_id, current_user)
    return jsonify(result)


@restaurant_bp.get("/api/restaurants/<int:restaurant_id>/menu")
def get_restaurant_menu(restaurant_id):
    result = get_restaurant_menu_service(restaurant_id, current_user)
    return jsonify(result)


@restaurant_bp.post("/api/restaurants/<int:restaurant_id>/favorite")
def toggle_favorite_restaurant(restaurant_id):
    result, status_code = toggle_favorite_restaurant_service(
        restaurant_id,
        current_user,
    )
    return jsonify(result), status_code


@restaurant_bp.get("/restaurant/<int:restaurant_id>/favorite")
def toggle_favorite_restaurant_fallback(restaurant_id):
    # Non-JS / guest-friendly entrypoint:
    # - guests: flash and redirect to login, then apply pending favorite after auth
    # - logged-in: toggle and redirect back
    next_url = (
        _coerce_next_url(request.args.get("next"))
        or _coerce_next_url(request.referrer)
        or url_for("restaurant.restaurant_page", restaurant_id=restaurant_id)
    )

    if not current_user.is_authenticated:
        session["next_url"] = next_url
        session["pending_favorite_restaurant_id"] = int(restaurant_id)
        flash(
            "Щоб додати ресторан в обране, увійдіть або зареєструйтесь",
            "info",
        )
        return redirect(url_for("auth.login_page", next=next_url))

    result, status_code = toggle_favorite_restaurant_service(
        restaurant_id,
        current_user,
    )

    if status_code < 400:
        flash(result.get("message") or "Зміни збережено", "success")
    else:
        flash(result.get("error") or "Не вдалося змінити обране", "danger")

    return redirect(next_url)


@restaurant_bp.post("/api/menu-items/<int:item_id>/favorite")
def toggle_favorite_menu_item(item_id):
    result, status_code = toggle_favorite_menu_item_service(
        item_id,
        current_user,
    )
    return jsonify(result), status_code
