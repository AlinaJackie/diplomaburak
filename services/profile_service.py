from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import Notification, FavoriteRestaurant, FavoriteMenuItem
from constants import (
    ORDER_ACTIVE_STATUSES,
    ORDER_STATUS_COMPLETED,
)
from serializers.profile_serializers import (
    serialize_notification,
    serialize_favorite_restaurant,
    serialize_favorite_menu_item,
    serialize_profile_review,
)
from validators.profile_validators import (
    validate_profile_update_payload,
    validate_profile_password_payload,
)


def build_loyalty_data(orders):
    completed_orders = [
        order for order in orders
        if (order.status or "").lower() == ORDER_STATUS_COMPLETED
    ]
    points = sum(int(order.total_price or 0)
                 for order in completed_orders) // 20

    if points >= 1500:
        level = "Platinum"
        next_level = None
        points_to_next = 0
    elif points >= 800:
        level = "Gold"
        next_level = "Platinum"
        points_to_next = 1500 - points
    elif points >= 300:
        level = "Silver"
        next_level = "Gold"
        points_to_next = 800 - points
    else:
        level = "Bronze"
        next_level = "Silver"
        points_to_next = 300 - points

    return {
        "points": points,
        "level": level,
        "next_level": next_level,
        "points_to_next": max(points_to_next, 0),
        "completed_orders_count": len(completed_orders),
    }


def update_profile_service(current_user, data):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    validated, error = validate_profile_update_payload(data)
    if error:
        return {"error": error}, 400

    current_user.full_name = validated["full_name"]
    current_user.city = validated["city"]
    current_user.street = validated["street"]
    current_user.house = validated["house"]
    current_user.extra_info = validated["extra_info"]

    db.session.commit()

    return {"message": "Профіль оновлено"}, 200


def update_password_service(current_user, data):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    validated, error = validate_profile_password_payload(data)
    if error:
        return {"error": error}, 400

    current_password = validated["current_password"]
    new_password = validated["new_password"]

    if not check_password_hash(current_user.password_hash, current_password):
        return {"error": "Поточний пароль неправильний"}, 400

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return {"message": "Пароль успішно змінено"}, 200


def get_profile_dashboard_service(current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    orders = list(current_user.orders or [])
    active_orders = [
        order for order in orders
        if (order.status or "").lower() in ORDER_ACTIVE_STATUSES
    ]
    completed_orders = [
        order for order in orders
        if (order.status or "").lower() == ORDER_STATUS_COMPLETED
    ]

    loyalty = build_loyalty_data(orders)

    recent_notifications = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "phone": current_user.phone,
            "full_name": current_user.full_name,
            "city": current_user.city,
            "street": current_user.street,
            "house": current_user.house,
            "extra_info": current_user.extra_info,
        },
        "stats": {
            "orders_count": len(orders),
            "active_orders_count": len(active_orders),
            "completed_orders_count": len(completed_orders),
        },
        "loyalty": loyalty,
        "recent_notifications": [
            serialize_notification(notification)
            for notification in recent_notifications
        ],
    }, 200


def get_profile_notifications_service(current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    notifications = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        serialize_notification(notification)
        for notification in notifications
    ], 200


def mark_notifications_read_service(current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({"is_read": True})

    db.session.commit()

    return {"message": "Сповіщення позначено як прочитані"}, 200


def get_profile_activity_service(current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    favorite_restaurants = [
        serialize_favorite_restaurant(favorite)
        for favorite in current_user.favorite_restaurants
        if favorite.restaurant is not None
    ]

    favorite_menu_items = [
        serialize_favorite_menu_item(favorite)
        for favorite in current_user.favorite_menu_items
        if favorite.menu_item is not None
    ]

    reviews = sorted(
        current_user.reviews or [],
        key=lambda review: review.created_at or 0,
        reverse=True,
    )

    review_list = [
        serialize_profile_review(review)
        for review in reviews
    ]

    return {
        "favorite_restaurants": favorite_restaurants,
        "favorite_menu_items": favorite_menu_items,
        "reviews": review_list,
    }, 200
