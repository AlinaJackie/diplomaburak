from constants import (
    ALLOWED_DELIVERY_TYPES,
    ALLOWED_PAYMENT_METHODS,
    DELIVERY_ALLOWED_CITIES_TEXT,
    DELIVERY_TYPE_DELIVERY,
)
from utils.city_utils import normalize_city_input
from utils.order_helpers import (
    normalize_text,
    normalize_phone,
    is_valid_phone,
    is_delivery_city_supported,
)


def validate_checkout_payload(data):
    data = data or {}

    restaurant_id = data.get("restaurant_id")
    items_data = data.get("items", [])

    customer_name = normalize_text(data.get("customer_name"))
    phone = normalize_text(data.get("phone"))
    city = normalize_city_input(data.get("city"))
    address = normalize_text(data.get("address"))
    comment = normalize_text(data.get("comment"))
    payment_method = normalize_text(data.get("payment_method")).lower()
    delivery_type = normalize_text(
        data.get("delivery_type") or DELIVERY_TYPE_DELIVERY
    ).lower()

    if not restaurant_id:
        return None, "Не вказано ресторан"

    if not isinstance(items_data, list) or not items_data:
        return None, "Кошик порожній"

    if not customer_name or not phone or not city:
        return None, "Заповніть обов’язкові поля"

    if len(customer_name) < 2:
        return None, "Вкажіть коректне ім’я"

    if not is_valid_phone(phone):
        return None, "Вкажіть коректний номер телефону"

    if delivery_type not in ALLOWED_DELIVERY_TYPES:
        return None, "Оберіть спосіб отримання"

    if payment_method not in ALLOWED_PAYMENT_METHODS:
        return None, "Оберіть спосіб оплати"

    if delivery_type == DELIVERY_TYPE_DELIVERY:
        if not address:
            return None, "Вкажіть адресу доставки"

        if not is_delivery_city_supported(city):
            return None, (
                "Доставка наразі доступна лише в " f"{DELIVERY_ALLOWED_CITIES_TEXT}"
            )

    try:
        restaurant_id = int(restaurant_id)
    except (TypeError, ValueError):
        return None, "Некоректний ресторан"

    return {
        "restaurant_id": restaurant_id,
        "items_data": items_data,
        "customer_name": customer_name,
        "phone": normalize_phone(phone),
        "city": city,
        "address": address,
        "comment": comment,
        "payment_method": payment_method,
        "delivery_type": delivery_type,
    }, None


def validate_review_payload(data):
    data = data or {}

    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return None, "Оцінка має бути від 1 до 5"

    if rating < 1 or rating > 5:
        return None, "Оцінка має бути від 1 до 5"

    return {
        "rating": rating,
        "comment": comment,
    }, None
