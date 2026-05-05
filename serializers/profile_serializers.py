from utils.formatters import format_datetime


def serialize_notification(notification):
    return {
        "id": notification.id,
        "message": notification.message,
        "is_read": notification.is_read,
        "created_at": format_datetime(notification.created_at),
    }


def serialize_favorite_restaurant(favorite):
    return {
        "id": favorite.restaurant.id,
        "name": favorite.restaurant.name,
        "city": favorite.restaurant.city,
        "rating": favorite.restaurant.rating,
        "created_at": format_datetime(favorite.created_at),
    }


def serialize_favorite_menu_item(favorite):
    return {
        "id": favorite.menu_item.id,
        "name": favorite.menu_item.name,
        "price": favorite.menu_item.price,
        "restaurant_name": (
            favorite.menu_item.restaurant.name
            if favorite.menu_item.restaurant else None
        ),
        "created_at": format_datetime(favorite.created_at),
    }


def serialize_profile_review(review):
    return {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "restaurant_name": (
            review.restaurant.name if review.restaurant else None
        ),
        "created_at": format_datetime(review.created_at),
        "order_id": review.order_id,
    }
