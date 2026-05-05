from utils.category_utils import normalize_category_key
from utils.formatters import format_datetime
from utils.restaurant_helpers import get_restaurant_open_status
from utils.city_utils import city_to_slug


def normalize_image_url(image_url):
    value = (image_url or "").strip()

    if not value:
        return ""

    if value.startswith(("http://", "https://", "/static/")):
        return value

    if value.startswith("static/"):
        return f"/{value}"

    if value.startswith("uploads/"):
        return f"/static/{value}"

    if value.startswith("/uploads/"):
        return f"/static{value}"

    filename = value.split("/")[-1].strip()
    if not filename:
        return ""

    return f"/static/uploads/{filename}"


def serialize_restaurant_list_item(restaurant, is_favorite=False):
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "description": restaurant.description,
        "city": restaurant.city,
        "city_slug": city_to_slug(restaurant.city),
        "categories": [
            normalize_category_key(category) for category in restaurant.category_list()
        ],
        "price_level": restaurant.price_level,
        "eta": restaurant.eta,
        "rating": restaurant.rating,
        "image_url": normalize_image_url(restaurant.image_url),
        "is_favorite": is_favorite,
        "opening_time": restaurant.opening_time,
        "closing_time": restaurant.closing_time,
        "is_open": get_restaurant_open_status(restaurant),
        "is_active": restaurant.is_active,
        "minimum_order_amount": restaurant.minimum_order_amount,
    }


def serialize_review(review):
    return {
        "id": review.id,
        "user_name": (
            review.user.full_name
            if review.user and review.user.full_name
            else "Користувач"
        ),
        "rating": review.rating,
        "comment": review.comment,
        "created_at": format_datetime(review.created_at),
    }


def serialize_restaurant_detail(restaurant, reviews, is_favorite=False):
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "description": restaurant.description,
        "city": restaurant.city,
        "city_slug": city_to_slug(restaurant.city),
        "categories": [
            normalize_category_key(category) for category in restaurant.category_list()
        ],
        "price_level": restaurant.price_level,
        "eta": restaurant.eta,
        "rating": restaurant.rating,
        "image_url": normalize_image_url(restaurant.image_url),
        "is_favorite": is_favorite,
        "opening_time": restaurant.opening_time,
        "closing_time": restaurant.closing_time,
        "is_open": get_restaurant_open_status(restaurant),
        "is_active": restaurant.is_active,
        "minimum_order_amount": restaurant.minimum_order_amount,
        "reviews_count": len(reviews),
        "reviews": [serialize_review(review) for review in reviews],
    }


def serialize_menu_item(item, is_favorite=False):
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "image_url": normalize_image_url(item.image_url),
        "weight": item.weight,
        "is_favorite": is_favorite,
        "is_available": item.is_available,
    }


def serialize_partner_restaurant(restaurant):
    categories = []
    if restaurant.categories:
        if isinstance(restaurant.categories, str):
            categories = [
                normalize_category_key(category)
                for category in restaurant.categories.split(",")
                if str(category).strip()
            ]
        else:
            categories = restaurant.categories

    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "city": restaurant.city,
        "city_slug": city_to_slug(restaurant.city),
        "address": restaurant.address,
        "description": restaurant.description,
        "categories": categories,
        "price_level": restaurant.price_level,
        "eta": restaurant.eta,
        "image_url": normalize_image_url(restaurant.image_url),
        "opening_time": restaurant.opening_time,
        "closing_time": restaurant.closing_time,
        "minimum_order_amount": restaurant.minimum_order_amount,
        "is_active": restaurant.is_active,
        "latitude": restaurant.latitude,
        "longitude": restaurant.longitude,
    }


def serialize_partner_menu_item(item):
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "image_url": normalize_image_url(item.image_url),
        "weight": item.weight,
        "is_available": item.is_available,
    }
