from datetime import datetime

from flask import current_app

from extensions import db
from models import (
    Cart,
    CartItem,
    MenuItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    Restaurant,
    Review,
)
from constants import (
    DELIVERY_TYPE_DELIVERY,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_NEW,
)
from serializers.order_serializers import (
    serialize_order_review,
    serialize_user_order,
)
from services.notification_service import create_notification
from utils.order_helpers import (
    calculate_delivery_fee,
    calculate_eta_minutes,
    calculate_route_info,
)
from utils.restaurant_helpers import get_restaurant_open_status
from validators.order_validators import (
    validate_checkout_payload,
    validate_review_payload,
)


def normalize_order_items(items_data, restaurant_id):
    normalized_items = []
    items_total = 0
    seen_item_ids = set()

    for item_data in items_data:
        menu_item_id = item_data.get("id") or item_data.get("menu_item_id")
        quantity_raw = item_data.get("quantity", 1)

        try:
            menu_item_id = int(menu_item_id)
        except (TypeError, ValueError):
            return None, None, "Некоректний id страви"

        try:
            qty = int(quantity_raw)
        except (TypeError, ValueError):
            return None, None, "Кількість страви має бути цілим числом"

        if qty <= 0:
            return (
                None,
                None,
                "Кількість кожної страви має бути більшою за 0",
            )

        if qty > 20:
            return (
                None,
                None,
                "Кількість однієї позиції не може перевищувати 20",
            )

        if menu_item_id in seen_item_ids:
            return None, None, "Одна і та сама страва дублюється в кошику"
        menu_item = db.session.get(MenuItem, menu_item_id)
        if not menu_item:
            return None, None, f"Страву з id={menu_item_id} не знайдено"

        if not menu_item.is_available:
            return None, None, f"Страва '{menu_item.name}' зараз недоступна"

        if menu_item.restaurant_id != restaurant_id:
            return None, None, "У кошику є страви з іншого ресторану"

        line_price = int(menu_item.price) * qty
        items_total += line_price
        seen_item_ids.add(menu_item_id)

        normalized_items.append(
            {
                "menu_item_id": menu_item.id,
                "quantity": qty,
                "price": int(menu_item.price),
                "name": menu_item.name,
                "line_total": line_price,
            }
        )

    if not normalized_items:
        return None, None, "Не вдалося сформувати замовлення"

    return normalized_items, items_total, None


def recalculate_restaurant_rating(restaurant_id):
    reviews = Review.query.filter_by(restaurant_id=restaurant_id).all()
    restaurant = db.session.get(Restaurant, restaurant_id)

    if not restaurant:
        return

    if not reviews:
        restaurant.rating = None
    else:
        avg = sum(review.rating for review in reviews) / len(reviews)
        restaurant.rating = round(avg, 1)


def build_order_preview(validated):
    restaurant = db.session.get(Restaurant, validated["restaurant_id"])
    if not restaurant:
        return None, None, None, None, {"error": "Ресторан не знайдено"}, 404

    if not restaurant.is_active:
        return (
            None,
            None,
            None,
            None,
            {"error": "Цей ресторан тимчасово недоступний для замовлень"},
            400,
        )

    if not get_restaurant_open_status(restaurant):
        return (
            None,
            None,
            None,
            None,
            {
                "error": (
                    "Ресторан зараз зачинений. "
                    f"Години роботи: {restaurant.opening_time}–"
                    f"{restaurant.closing_time}"
                )
            },
            400,
        )

    normalized_items, items_total, items_error = normalize_order_items(
        validated["items_data"],
        restaurant.id,
    )
    if items_error:
        return None, None, None, None, {"error": items_error}, 400

    minimum_order_amount = restaurant.minimum_order_amount or 0

    if (
        validated["delivery_type"] == DELIVERY_TYPE_DELIVERY
        and items_total < minimum_order_amount
    ):
        return (
            None,
            None,
            None,
            None,
            {
                "error": (
                    "Мінімальна сума для доставки в цьому ресторані — "
                    f"{minimum_order_amount} грн"
                )
            },
            400,
        )

    distance_km = None
    delivery_is_estimated = False
    delivery_source = None

    try:
        if validated["delivery_type"] == DELIVERY_TYPE_DELIVERY:
            route_info = calculate_route_info(
                restaurant,
                validated["city"],
                validated["address"],
            )
            distance_km = route_info["distance_km"]
            eta_minutes = route_info["eta_minutes"]
            delivery_is_estimated = bool(route_info.get("is_estimated", False))
            delivery_source = route_info.get("source")
        else:
            eta_minutes = calculate_eta_minutes(
                validated["delivery_type"],
                restaurant,
                validated["city"],
                validated["address"],
            )
    except ValueError as error:
        return None, None, None, None, {"error": str(error)}, 400
    except Exception:
        current_app.logger.exception(
            "ORDER PREVIEW ROUTE ERROR for restaurant_id=%s",
            restaurant.id,
        )
        return (
            None,
            None,
            None,
            None,
            {"error": "Не вдалося розрахувати маршрут доставки"},
            400,
        )

    delivery_fee = calculate_delivery_fee(
        validated["delivery_type"],
        items_total,
        distance_km=distance_km,
    )

    total_price = items_total + delivery_fee

    preview = {
        "items_total": items_total,
        "delivery_fee": delivery_fee,
        "eta_minutes": eta_minutes,
        "distance_km": distance_km,
        "total_price": total_price,
        "delivery_type": validated["delivery_type"],
        "delivery_is_estimated": delivery_is_estimated,
        "delivery_source": delivery_source,
    }

    return restaurant, normalized_items, items_total, preview, None, 200


def preview_order_service(data, current_user):
    validated, error = validate_checkout_payload(data)
    if error:
        return {"error": error}, 400

    restaurant, normalized_items, _, preview, error_response, status_code = (
        build_order_preview(validated)
    )
    if error_response:
        return error_response, status_code

    return {
        **preview,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "items": normalized_items,
    }, 200


def create_order_service(data, current_user):
    validated, error = validate_checkout_payload(data)
    if error:
        return {"error": error}, 400

    restaurant, normalized_items, _, preview, error_response, status_code = (
        build_order_preview(validated)
    )
    if error_response:
        return error_response, status_code

    order = Order(
        user_id=current_user.id if current_user.is_authenticated else None,
        restaurant_id=restaurant.id,
        customer_name=validated["customer_name"],
        phone=validated["phone"],
        city=validated["city"],
        address=(
            validated["address"]
            if validated["delivery_type"] == DELIVERY_TYPE_DELIVERY
            else None
        ),
        comment=validated["comment"],
        payment_method=validated["payment_method"],
        delivery_type=validated["delivery_type"],
        delivery_fee=preview["delivery_fee"],
        eta_minutes=preview["eta_minutes"],
        total_price=preview["total_price"],
        status=ORDER_STATUS_NEW,
        created_at=datetime.utcnow(),
    )

    db.session.add(order)
    db.session.flush()

    initial_history = OrderStatusHistory(
        order_id=order.id,
        status=ORDER_STATUS_NEW,
        note="Замовлення створено",
    )
    db.session.add(initial_history)

    for item in normalized_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item["menu_item_id"],
            quantity=item["quantity"],
            price=item["price"],
        )
        db.session.add(order_item)

    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if cart:
            cart.restaurant_id = None
            for cart_item in list(cart.items):
                db.session.delete(cart_item)

        create_notification(
            user_id=current_user.id,
            message=(f"Ваше замовлення №{order.id} " "успішно створено."),
        )

    db.session.commit()

    return {
        "message": "Замовлення створено",
        "order_id": order.id,
        "items_total": preview["items_total"],
        "delivery_fee": preview["delivery_fee"],
        "eta_minutes": preview["eta_minutes"],
        "distance_km": preview["distance_km"],
        "total_price": preview["total_price"],
        "status": order.status,
        "delivery_type": validated["delivery_type"],
        "items": normalized_items,
    }, 201


def get_my_orders_service(current_user):
    if not current_user.is_authenticated:
        return []

    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []

    for order in orders:
        result.append(
            serialize_user_order(
                order,
                can_review=(
                    order.status == ORDER_STATUS_COMPLETED and order.review is None
                ),
            )
        )

    return result


def create_review_service(order_id, data, current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    order = db.session.get(Order, order_id)
    if not order:
        return {"error": "Замовлення не знайдено"}, 404

    if order.user_id != current_user.id:
        return {"error": "Ви не можете залишити відгук до цього замовлення"}, 403

    if order.status != ORDER_STATUS_COMPLETED:
        return {"error": "Відгук можна залишити лише після виконаного замовлення"}, 400

    if order.review is not None:
        return {"error": "Відгук до цього замовлення вже існує"}, 400

    validated, error = validate_review_payload(data)
    if error:
        return {"error": error}, 400

    rating = validated["rating"]
    comment = validated["comment"]

    review = Review(
        user_id=current_user.id,
        restaurant_id=order.restaurant_id,
        order_id=order.id,
        rating=rating,
        comment=comment,
    )

    db.session.add(review)
    recalculate_restaurant_rating(order.restaurant_id)
    db.session.commit()

    return {
        "message": "Відгук успішно додано",
        "review": serialize_order_review(review),
    }, 201


def repeat_order_service(order_id, current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    order = db.session.get(Order, order_id)
    if not order:
        return {"error": "Замовлення не знайдено"}, 404
    if order.user_id != current_user.id:
        return {"error": "Немає доступу до цього замовлення"}, 403

    restaurant = db.session.get(Restaurant, order.restaurant_id)
    if not restaurant or not restaurant.is_active:
        return {
            "error": "Цей ресторан зараз недоступний, тому повторити замовлення неможливо"
        }, 400

    repeat_items = []
    unavailable_items = []

    for item in order.items:
        menu_item = item.menu_item
        if not menu_item or not menu_item.is_available:
            unavailable_items.append(
                menu_item.name if menu_item else f"Страва #{item.menu_item_id}"
            )
            continue

        if menu_item.restaurant_id != order.restaurant_id:
            unavailable_items.append(menu_item.name)
            continue

        quantity = int(item.quantity or 0)
        if quantity <= 0:
            continue

        repeat_items.append(
            {
                "id": menu_item.id,
                "menu_item_id": menu_item.id,
                "quantity": quantity,
                "price": int(menu_item.price or item.price or 0),
                "name": menu_item.name,
            }
        )

    if False and unavailable_items:
        unavailable_text = ", ".join(unavailable_items)
        return {
            "error": (
                "Не вдалося повністю повторити замовлення. "
                f"Недоступні позиції: {unavailable_text}"
            )
        }, 400

    if not repeat_items:
        return {"error": "У цьому замовленні немає доступних страв для повторення"}, 400

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart is None:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.flush()

    cart.restaurant_id = restaurant.id
    for cart_item in list(cart.items):
        db.session.delete(cart_item)
    db.session.flush()

    for item in repeat_items:
        db.session.add(
            CartItem(
                cart=cart,
                menu_item_id=item["menu_item_id"],
                quantity=item["quantity"],
            )
        )

    db.session.commit()

    return {
        "message": "Замовлення додано в кошик",
        "restaurant_id": order.restaurant_id,
        "items": repeat_items,
        "skipped_items": unavailable_items,
    }, 200
