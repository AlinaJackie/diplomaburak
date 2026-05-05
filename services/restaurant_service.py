from flask import abort
from sqlalchemy import or_

from extensions import db
from models import (
    FavoriteMenuItem,
    FavoriteRestaurant,
    MenuItem,
    Restaurant,
    Review,
)
from serializers.restaurant_serializers import (
    serialize_menu_item,
    serialize_restaurant_detail,
    serialize_restaurant_list_item,
)
from utils.category_utils import get_category_terms, normalize_category_key
from utils.city_utils import normalize_city_input
from utils.restaurant_helpers import get_restaurant_open_status


def _parse_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sort_restaurants(restaurants, sort_key):
    if sort_key == "rating_desc":
        return sorted(
            restaurants,
            key=lambda x: (
                x.get("rating") is None,
                -(x.get("rating") or 0),
                x.get("name") or "",
            ),
        )
    if sort_key == "eta_asc":
        return sorted(
            restaurants,
            key=lambda x: (
                x.get("eta") is None,
                _parse_float(x.get("eta")) or 10**9,
                x.get("name") or "",
            ),
        )
    if sort_key == "min_order_asc":
        return sorted(
            restaurants,
            key=lambda x: (
                x.get("minimum_order_amount") is None,
                x.get("minimum_order_amount") or 0,
                x.get("name") or "",
            ),
        )
    if sort_key == "name_desc":
        return sorted(
            restaurants, key=lambda x: (x.get("name") or "").lower(), reverse=True
        )
    return sorted(restaurants, key=lambda x: (x.get("name") or "").lower())


def _get_active_restaurant_or_404(restaurant_id):
    restaurant = Restaurant.query.filter_by(
        id=restaurant_id,
        is_active=True,
    ).first()

    if restaurant is None:
        abort(404, description="Ресторан не знайдено або він недоступний")

    return restaurant


def get_restaurant_page_data(restaurant_id):
    restaurant = _get_active_restaurant_or_404(restaurant_id)
    items = MenuItem.query.filter_by(
        restaurant_id=restaurant_id,
        is_available=True,
    ).all()
    return restaurant, items


def get_restaurants_list_service(args, current_user):
    city = args.get("city")
    category = args.get("category")
    search = args.get("q", "").strip().lower()
    sort = (args.get("sort") or "name_asc").strip().lower()
    open_now = (args.get("open_now") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    max_min_order = _parse_float(args.get("max_min_order"))

    query = Restaurant.query.filter_by(is_active=True)

    if city:
        normalized_city = normalize_city_input(city)
        query = query.filter_by(city=normalized_city)

    if category and category != "all":
        category_terms = get_category_terms(category) or {
            normalize_category_key(category)
        }
        category_filters = [
            Restaurant.categories.ilike(f"%{term}%") for term in category_terms if term
        ]
        if category_filters:
            query = query.filter(or_(*category_filters))

    if search:
        search_terms = {search}
        canonical_search = normalize_category_key(search)
        if canonical_search:
            search_terms.update(get_category_terms(canonical_search))
        search_terms = {term for term in search_terms if term}

        category_search_filters = [
            Restaurant.categories.ilike(f"%{term}%") for term in search_terms
        ]

        query = query.filter(
            or_(
                Restaurant.name.ilike(f"%{search}%"),
                Restaurant.description.ilike(f"%{search}%"),
                *category_search_filters,
                Restaurant.menu_items.any(MenuItem.name.ilike(f"%{search}%")),
            )
        )

    if max_min_order is not None:
        query = query.filter(Restaurant.minimum_order_amount <= int(max_min_order))

    favorite_restaurant_ids = set()
    if current_user.is_authenticated:
        favorite_restaurant_ids = {
            favorite.restaurant_id
            for favorite in FavoriteRestaurant.query.filter_by(
                user_id=current_user.id,
            ).all()
        }

    restaurants = [
        serialize_restaurant_list_item(
            restaurant,
            is_favorite=restaurant.id in favorite_restaurant_ids,
        )
        for restaurant in query.all()
    ]

    if open_now:
        restaurants = [
            restaurant for restaurant in restaurants if restaurant.get("is_open")
        ]

    return _sort_restaurants(restaurants, sort)


def get_restaurant_detail_service(restaurant_id, current_user):
    restaurant = _get_active_restaurant_or_404(restaurant_id)
    reviews = (
        Review.query.filter_by(restaurant_id=restaurant.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = (
            FavoriteRestaurant.query.filter_by(
                user_id=current_user.id,
                restaurant_id=restaurant.id,
            ).first()
            is not None
        )

    return serialize_restaurant_detail(
        restaurant,
        reviews,
        is_favorite=is_favorite,
    )


def get_restaurant_menu_service(restaurant_id, current_user):
    restaurant = _get_active_restaurant_or_404(restaurant_id)
    items = MenuItem.query.filter_by(
        restaurant_id=restaurant.id, is_available=True
    ).all()

    favorite_item_ids = set()
    if current_user.is_authenticated:
        favorite_item_ids = {
            favorite.menu_item_id
            for favorite in FavoriteMenuItem.query.filter_by(
                user_id=current_user.id,
            ).all()
        }

    return [
        serialize_menu_item(
            item,
            is_favorite=item.id in favorite_item_ids,
        )
        for item in items
    ]


def toggle_favorite_restaurant_service(restaurant_id, current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    restaurant = _get_active_restaurant_or_404(restaurant_id)
    existing = FavoriteRestaurant.query.filter_by(
        user_id=current_user.id,
        restaurant_id=restaurant.id,
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {
            "message": "Ресторан видалено з обраного",
            "is_favorite": False,
        }, 200

    favorite = FavoriteRestaurant(
        user_id=current_user.id,
        restaurant_id=restaurant.id,
    )
    db.session.add(favorite)
    db.session.commit()

    return {
        "message": "Ресторан додано в обране",
        "is_favorite": True,
    }, 201


def toggle_favorite_menu_item_service(item_id, current_user):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт"}, 401

    item = db.session.get(MenuItem, item_id)
    if not item:
        return {"error": "Страву не знайдено"}, 404

    restaurant = db.session.get(Restaurant, item.restaurant_id)
    if not restaurant or not restaurant.is_active:
        return {"error": "Ресторан недоступний"}, 404

    existing = FavoriteMenuItem.query.filter_by(
        user_id=current_user.id,
        menu_item_id=item.id,
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {
            "message": "Страву видалено з обраного",
            "is_favorite": False,
        }, 200

    favorite = FavoriteMenuItem(
        user_id=current_user.id,
        menu_item_id=item.id,
    )
    db.session.add(favorite)
    db.session.commit()

    return {
        "message": "Страву додано в обране",
        "is_favorite": True,
    }, 201
