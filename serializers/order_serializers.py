from utils.formatters import format_datetime


def serialize_order_status_history(history):
    return {
        "status": history.status,
        "note": history.note,
        "created_at": format_datetime(history.created_at),
    }


def serialize_order_review(review):
    if not review:
        return None

    return {
        "id": review.id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": format_datetime(review.created_at),
    }


def serialize_order_item(item):
    return {
        "menu_item_id": item.menu_item_id,
        "name": item.menu_item.name if item.menu_item else "Страва",
        "quantity": item.quantity,
        "price": item.price,
        "line_total": item.price * item.quantity,
    }


def serialize_user_order(order, can_review=False):
    items = [serialize_order_item(item) for item in order.items]
    items_total = sum(item["line_total"] for item in items)

    return {
        "id": order.id,
        "restaurant_id": order.restaurant_id,
        "restaurant": order.restaurant.name if order.restaurant else None,
        "items_total": items_total,
        "total_price": order.total_price,
        "delivery_fee": order.delivery_fee,
        "eta_minutes": order.eta_minutes,
        "delivery_type": order.delivery_type,
        "payment_method": order.payment_method,
        "city": order.city,
        "address": order.address,
        "status": order.status,
        "created_at": format_datetime(order.created_at),
        "can_review": can_review,
        "review": serialize_order_review(order.review),
        "status_history": [
            serialize_order_status_history(history) for history in order.status_history
        ],
        "items": items,
    }


def serialize_partner_order(
    order,
    restaurant_name="—",
    customer_name="Користувач",
    allowed_next_statuses=None,
):
    return {
        "id": order.id,
        "restaurant_name": restaurant_name,
        "customer_name": customer_name,
        "phone": getattr(order, "phone", ""),
        "delivery_type": getattr(order, "delivery_type", ""),
        "payment_method": getattr(order, "payment_method", ""),
        "city": getattr(order, "city", ""),
        "address": getattr(order, "address", ""),
        "comment": getattr(order, "comment", ""),
        "total_price": getattr(order, "total_price", 0),
        "status": getattr(order, "status", "new"),
        "allowed_next_statuses": list(allowed_next_statuses or []),
        "created_at": format_datetime(order.created_at),
        "items": [serialize_order_item(item) for item in getattr(order, "items", [])],
        "status_history": [
            serialize_order_status_history(history)
            for history in getattr(order, "status_history", [])
        ],
    }
