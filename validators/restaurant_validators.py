from utils.category_utils import normalize_restaurant_categories
from utils.city_utils import normalize_city_input
from utils.restaurant_helpers import parse_time_to_minutes


def validate_restaurant_form(data):
    name = (data.get("name") or "").strip()
    city = normalize_city_input(data.get("city"))
    address = (data.get("address") or "").strip()
    opening_time = (data.get("opening_time") or "09:00").strip()
    closing_time = (data.get("closing_time") or "22:00").strip()
    description = (data.get("description") or "").strip()
    price_level = (data.get("price_level") or "").strip()
    eta = (data.get("eta") or "").strip()
    categories_raw = data.get("categories") or ""
    minimum_order_amount_raw = (data.get("minimum_order_amount") or "200").strip()
    is_active_raw = (data.get("is_active") or "true").strip().lower()

    if not name or not city or not address:
        return None, "Назва, місто та адреса ресторану обов’язкові"

    if parse_time_to_minutes(opening_time) is None:
        return None, "Час відкриття має бути у форматі ГГ:ХХ"

    if parse_time_to_minutes(closing_time) is None:
        return None, "Час закриття має бути у форматі ГГ:ХХ"

    try:
        minimum_order_amount = int(
            float(str(minimum_order_amount_raw).replace(",", "."))
        )
    except (TypeError, ValueError):
        return None, "Мінімальна сума замовлення має бути числом"

    if minimum_order_amount < 0:
        return None, "Мінімальна сума замовлення не може бути від’ємною"

    categories_str = normalize_restaurant_categories(categories_raw)
    is_active = is_active_raw in {"true", "1", "yes", "on"}

    return {
        "name": name,
        "city": city,
        "address": address,
        "opening_time": opening_time,
        "closing_time": closing_time,
        "description": description,
        "price_level": price_level,
        "eta": eta,
        "categories": categories_str,
        "minimum_order_amount": minimum_order_amount,
        "is_active": is_active,
    }, None


def validate_menu_item_form(data, default_is_available="true"):
    name = (data.get("name") or "").strip()
    price_raw = (data.get("price") or "").strip()
    description = (data.get("description") or "").strip()
    weight = (data.get("weight") or "").strip()

    is_available_raw = (
        (data.get("is_available") or default_is_available).strip().lower()
    )
    is_available = is_available_raw in {"true", "1", "yes", "on"}

    if not name:
        return None, "Назва страви обов’язкова"

    if not price_raw:
        return None, "Ціна обов’язкова"

    try:
        price = int(float(str(price_raw).replace(",", ".")))
    except (TypeError, ValueError):
        return None, "Ціна має бути числом"

    if price < 0:
        return None, "Ціна не може бути від’ємною"

    return {
        "name": name,
        "price": price,
        "description": description,
        "weight": weight,
        "is_available": is_available,
    }, None
