from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from extensions import db
from models import Cart, CartItem, MenuItem, Restaurant

cart_bp = Blueprint("cart", __name__)


def _get_or_create_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.flush()
    return cart


def _cleanup_cart(cart):
    """
    Self-heal legacy cart rows so the UI and totals don't break:
    - remove orphaned cart_items (deleted menu items)
    - remove unavailable items
    - normalize restaurant_id to match the remaining items
    """

    changed = False
    restaurant_ids = set()

    for cart_item in list(cart.items):
        menu_item = cart_item.menu_item
        quantity = int(cart_item.quantity or 0)

        if quantity <= 0 or menu_item is None or not bool(getattr(menu_item, "is_available", True)):
            db.session.delete(cart_item)
            changed = True
            continue

        restaurant_ids.add(int(menu_item.restaurant_id or 0))

    if changed:
        db.session.flush()

    restaurant_ids = {rid for rid in restaurant_ids if rid}

    if len(restaurant_ids) > 1:
        for cart_item in list(cart.items):
            db.session.delete(cart_item)
        cart.restaurant_id = None
        db.session.flush()
        return True

    if restaurant_ids:
        inferred_restaurant_id = next(iter(restaurant_ids))
        if cart.restaurant_id != inferred_restaurant_id:
            cart.restaurant_id = inferred_restaurant_id
            db.session.flush()
            changed = True
    else:
        if cart.restaurant_id is not None:
            cart.restaurant_id = None
            db.session.flush()
            changed = True

    return changed


def _serialize_cart(cart):
    items = []

    for cart_item in cart.items:
        menu_item = cart_item.menu_item
        if menu_item is None:
            continue

        price = int(menu_item.price or 0)
        quantity = int(cart_item.quantity or 0)

        items.append(
            {
                "id": menu_item.id,
                "menu_item_id": menu_item.id,
                "name": menu_item.name,
                "price": price,
                "quantity": quantity,
                "line_total": price * quantity,
                "is_available": bool(menu_item.is_available),
            }
        )

    return {
        "restaurant_id": cart.restaurant_id,
        "items": items,
    }


def _clear_cart(cart):
    cart.restaurant_id = None
    cart.items.clear()
    db.session.flush()


def _replace_cart(cart, restaurant_id, items_data):
    if not isinstance(items_data, list):
        return None, (jsonify({"error": "Некоректний формат кошика"}), 400)

    if not restaurant_id:
        _clear_cart(cart)
        return {"restaurant_id": None, "items": []}, None

    try:
        restaurant_id = int(restaurant_id)
    except (TypeError, ValueError):
        return None, (jsonify({"error": "Некоректний ресторан"}), 400)

    restaurant = db.session.get(Restaurant, restaurant_id)
    if not restaurant:
        return None, (jsonify({"error": "Ресторан не знайдено"}), 404)

    merged_quantities = {}

    for item_data in items_data:
        menu_item_id = item_data.get("id") or item_data.get("menu_item_id")
        quantity = item_data.get("quantity", 1)

        try:
            menu_item_id = int(menu_item_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            return None, (jsonify({"error": "Некоректні дані кошика"}), 400)

        if quantity <= 0:
            continue

        if quantity > 20:
            return None, (
                jsonify({"error": "Кількість однієї позиції не може перевищувати 20"}),
                400,
            )

        menu_item = db.session.get(MenuItem, menu_item_id)
        if not menu_item:
            return None, (
                jsonify({"error": f"Страву з id={menu_item_id} не знайдено"}),
                404,
            )

        if not bool(menu_item.is_available):
            return None, (
                jsonify({"error": f"Страва '{menu_item.name}' зараз недоступна"}),
                400,
            )

        if menu_item.restaurant_id != restaurant_id:
            return None, (
                jsonify({"error": "У кошику можуть бути лише страви одного ресторану"}),
                400,
            )

        merged_quantities[menu_item_id] = (
            merged_quantities.get(menu_item_id, 0) + quantity
        )

    _clear_cart(cart)
    cart.restaurant_id = restaurant_id if merged_quantities else None

    for menu_item_id, quantity in merged_quantities.items():
        db.session.add(
            CartItem(
                cart=cart,
                menu_item_id=menu_item_id,
                quantity=quantity,
            )
        )

    db.session.flush()
    return _serialize_cart(cart), None


@cart_bp.get("/api/cart")
@login_required
def get_cart():
    cart = _get_or_create_cart(current_user.id)
    changed = _cleanup_cart(cart)

    if changed:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify(_serialize_cart(cart))


@cart_bp.put("/api/cart")
@login_required
def replace_cart():
    payload = request.get_json(silent=True) or {}
    restaurant_id = payload.get("restaurant_id")
    items_data = payload.get("items") or []

    cart = _get_or_create_cart(current_user.id)
    data, error_response = _replace_cart(cart, restaurant_id, items_data)

    if error_response:
        db.session.rollback()
        return error_response

    try:
        db.session.commit()
        return jsonify(data)
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Не вдалося оновити кошик. Спробуйте ще раз."}), 500


@cart_bp.delete("/api/cart")
@login_required
def clear_cart():
    cart = _get_or_create_cart(current_user.id)
    _clear_cart(cart)

    try:
        db.session.commit()
        return jsonify(
            {
                "message": "Кошик очищено",
                "restaurant_id": None,
                "items": [],
            }
        )
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Не вдалося очистити кошик"}), 500
