from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload

from constants import (
    ORDER_ALLOWED_STATUSES,
    ORDER_ALLOWED_TRANSITIONS,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_LABELS,
    PARTNER_APPLICATION_STATUS_APPROVED,
    PARTNER_APPLICATION_STATUS_PENDING,
)
from extensions import db
from models import (
    MenuItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    PartnerApplication,
    Restaurant,
)
from serializers.order_serializers import serialize_partner_order
from serializers.restaurant_serializers import (
    serialize_partner_menu_item,
    serialize_partner_restaurant,
)
from services.file_service import save_uploaded_image
from services.notification_service import create_notification, send_email_notification
from utils.order_helpers import geocode_restaurant_location
from validators.partner_validators import validate_partner_application_payload
from validators.restaurant_validators import (
    validate_menu_item_form,
    validate_restaurant_form,
)


def _is_admin(user):
    return bool(getattr(user, "is_admin", False))


def _forbidden():
    return {"error": "Доступ заборонено"}, 403


def _get_owned_restaurant_or_error(rest_id, current_user):
    restaurant = db.session.get(Restaurant, rest_id)
    if not restaurant:
        return None, ({"error": "Ресторан не знайдено"}, 404)

    if restaurant.owner_id != current_user.id and not _is_admin(current_user):
        return None, _forbidden()

    return restaurant, None


def _get_owned_menu_item_or_error(item_id, current_user):
    item = db.session.get(MenuItem, item_id)
    if not item:
        return None, None, ({"error": "Страву не знайдено"}, 404)

    restaurant = db.session.get(Restaurant, item.restaurant_id)
    if not restaurant:
        return None, None, ({"error": "Ресторан не знайдено"}, 404)

    if restaurant.owner_id != current_user.id and not _is_admin(current_user):
        return None, None, _forbidden()

    return item, restaurant, None


def _try_set_restaurant_coordinates(restaurant, city, address):
    try:
        location = geocode_restaurant_location(city, address)
        restaurant.latitude = location["lat"]
        restaurant.longitude = location["lng"]
    except ValueError as error:
        current_app.logger.warning(
            "GEOCODING WARNING for restaurant '%s': %s",
            restaurant.name,
            error,
        )
        restaurant.latitude = None
        restaurant.longitude = None
    except Exception:
        current_app.logger.exception(
            "GEOCODING ERROR for restaurant '%s'",
            restaurant.name,
        )
        restaurant.latitude = None
        restaurant.longitude = None


def _resolve_partner_customer_name(order):
    explicit_customer_name = (getattr(order, "customer_name", "") or "").strip()
    if explicit_customer_name:
        return explicit_customer_name

    customer = getattr(order, "user", None)
    profile_name = (getattr(customer, "full_name", "") or "").strip()
    if profile_name:
        return profile_name

    return "Користувач"


def _get_allowed_next_order_statuses(status):
    normalized_status = (status or "").strip().lower()
    return ORDER_ALLOWED_TRANSITIONS.get(normalized_status, [])


def _is_order_status_transition_allowed(current_status, next_status):
    normalized_current = (current_status or "").strip().lower()
    normalized_next = (next_status or "").strip().lower()

    if normalized_current == normalized_next:
        return True

    return normalized_next in _get_allowed_next_order_statuses(normalized_current)


def _get_order_status_label(status):
    normalized_status = (status or "").strip().lower()
    return ORDER_STATUS_LABELS.get(normalized_status, normalized_status or "Невідомо")


def get_latest_partner_application(user_id):
    if not user_id:
        return None

    return (
        PartnerApplication.query.filter_by(user_id=user_id)
        .order_by(PartnerApplication.created_at.desc())
        .first()
    )


def can_access_partner_dashboard(current_user):
    if not current_user.is_authenticated:
        return False

    approved_app = (
        PartnerApplication.query.filter_by(
            user_id=current_user.id,
            status=PARTNER_APPLICATION_STATUS_APPROVED,
        )
        .order_by(PartnerApplication.created_at.desc())
        .first()
    )
    return approved_app is not None


def get_partner_restaurants(user_id):
    if not user_id:
        return []

    return Restaurant.query.filter_by(owner_id=user_id).all()


def create_partner_application(current_user, data):
    if not current_user.is_authenticated:
        return {"error": "Потрібно увійти в акаунт."}, 401

    validated, error = validate_partner_application_payload(data)
    if error:
        return {"error": error}, 400

    existing_pending = PartnerApplication.query.filter_by(
        user_id=current_user.id,
        status=PARTNER_APPLICATION_STATUS_PENDING,
    ).first()
    if existing_pending:
        return {"error": "У вас вже є заявка, яка очікує на розгляд."}, 400

    partner_application = PartnerApplication(
        contact_person=validated["contact_person"],
        brand_name=validated["brand_name"],
        phone=validated["phone"],
        email=validated["email"],
        city=validated["city"],
        verification_link=validated["verification_link"],
        planned_locations_count=validated["planned_locations_count"],
        edrpou_or_ipn=validated["edrpou_or_ipn"],
        business_description=validated["business_description"],
        personal_data_agreement=validated["personal_data_agreement"],
        representation_agreement=validated["representation_agreement"],
        status=PARTNER_APPLICATION_STATUS_PENDING,
        user_id=current_user.id,
    )

    db.session.add(partner_application)
    db.session.commit()

    try:
        send_email_notification(
            subject="FoodGo — заявку отримано",
            recipients=[validated["email"]],
            body=(
                "Вітаємо!\n\n"
                "Ми отримали вашу заявку на співпрацю з FoodGo.\n\n"
                f"Контактна особа: {validated['contact_person']}\n"
                f"Бренд / мережа / заклад: {validated['brand_name']}\n"
                f"Місто: {validated['city']}\n"
                f"Кількість закладів: {validated['planned_locations_count']}\n\n"
                "Після первинної перевірки менеджер FoodGo зв’яжеться "
                "з вами для уточнення деталей співпраці.\n\n"
                "З повагою,\n"
                "Команда FoodGo"
            ),
        )
    except Exception:
        current_app.logger.exception(
            "PARTNER APPLICATION EMAIL ERROR for %s",
            validated["email"],
        )

    return {
        "message": "Заявку успішно подано",
        "application_id": partner_application.id,
        "status": partner_application.status,
    }, 201


def get_partner_restaurants_service(current_user):
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
    return [serialize_partner_restaurant(restaurant) for restaurant in restaurants]


def create_partner_restaurant_service(form, files, current_user):
    validated, error = validate_restaurant_form(form)
    if error:
        return {"error": error}, 400

    image_url = ""
    image_file = files.get("image_file")

    try:
        if image_file and image_file.filename:
            image_url = save_uploaded_image(
                image_file,
                "restaurants",
            )
    except ValueError as error:
        return {"error": str(error)}, 400

    restaurant = Restaurant(
        name=validated["name"],
        description=validated["description"],
        city=validated["city"],
        address=validated["address"],
        price_level=validated["price_level"] or None,
        eta=validated["eta"] or None,
        rating=None,
        categories=validated["categories"],
        image_url=image_url,
        owner_id=current_user.id,
        opening_time=validated["opening_time"],
        closing_time=validated["closing_time"],
        minimum_order_amount=validated["minimum_order_amount"],
        is_active=validated["is_active"],
    )

    _try_set_restaurant_coordinates(
        restaurant,
        validated["city"],
        validated["address"],
    )

    db.session.add(restaurant)
    db.session.commit()

    return {"id": restaurant.id, "message": "Ресторан створено"}, 201


def update_partner_restaurant_service(rest_id, form, files, current_user):
    restaurant, error_response = _get_owned_restaurant_or_error(
        rest_id,
        current_user,
    )
    if error_response:
        return error_response

    validated, error = validate_restaurant_form(form)
    if error:
        return {"error": error}, 400

    image_file = files.get("image_file")
    try:
        if image_file and image_file.filename:
            restaurant.image_url = save_uploaded_image(
                image_file,
                "restaurants",
            )
    except ValueError as error:
        return {"error": str(error)}, 400

    restaurant.name = validated["name"]
    restaurant.city = validated["city"]
    restaurant.address = validated["address"]
    restaurant.description = validated["description"]
    restaurant.price_level = validated["price_level"] or None
    restaurant.eta = validated["eta"] or None
    restaurant.categories = validated["categories"]
    restaurant.minimum_order_amount = validated["minimum_order_amount"]
    restaurant.is_active = validated["is_active"]
    restaurant.opening_time = validated["opening_time"]
    restaurant.closing_time = validated["closing_time"]

    _try_set_restaurant_coordinates(
        restaurant,
        validated["city"],
        validated["address"],
    )

    db.session.commit()
    return {"message": "Ресторан оновлено"}, 200


def delete_partner_restaurant_service(rest_id, current_user):
    restaurant, error_response = _get_owned_restaurant_or_error(rest_id, current_user)
    if error_response:
        return error_response

    has_orders = (
        db.session.query(Order.id).filter_by(restaurant_id=restaurant.id).first()
        is not None
    )

    if has_orders:
        restaurant.is_active = False

        for item in restaurant.menu_items:
            item.is_available = False

        db.session.commit()
        return {
            "message": (
                "Ресторан має історію замовлень, тому його деактивовано "
                "замість повного видалення"
            )
        }, 200

    db.session.delete(restaurant)
    db.session.commit()
    return {"message": "Ресторан видалено"}, 200


def get_partner_restaurant_menu_service(rest_id, current_user):
    restaurant, error_response = _get_owned_restaurant_or_error(rest_id, current_user)
    if error_response:
        return error_response

    items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    return [serialize_partner_menu_item(item) for item in items], 200


def create_partner_menu_item_service(rest_id, form, files, current_user):
    restaurant, error_response = _get_owned_restaurant_or_error(rest_id, current_user)
    if error_response:
        return error_response

    validated, error = validate_menu_item_form(
        form,
        default_is_available="true",
    )
    if error:
        return {"error": error}, 400

    image_url = ""
    image_file = files.get("image_file")

    try:
        if image_file and image_file.filename:
            image_url = save_uploaded_image(image_file, "menu")
    except ValueError as error:
        return {"error": str(error)}, 400

    item = MenuItem(
        restaurant_id=restaurant.id,
        name=validated["name"],
        description=validated["description"] or None,
        price=validated["price"],
        image_url=image_url,
        weight=validated["weight"] or None,
        is_available=validated["is_available"],
    )

    try:
        db.session.add(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return {"error": "Не вдалося додати страву. Перевірте введені дані."}, 500

    return {
        "id": item.id,
        "message": "Страву додано",
    }, 201


def update_partner_menu_item_service(item_id, form, files, current_user):
    item, _, error_response = _get_owned_menu_item_or_error(item_id, current_user)
    if error_response:
        return error_response

    validated, error = validate_menu_item_form(
        form,
        default_is_available=str(item.is_available),
    )
    if error:
        return {"error": error}, 400

    image_file = files.get("image_file")
    try:
        if image_file and image_file.filename:
            item.image_url = save_uploaded_image(image_file, "menu")
    except ValueError as error:
        return {"error": str(error)}, 400

    item.name = validated["name"]
    item.description = validated["description"] or None
    item.price = validated["price"]
    item.weight = validated["weight"] or None
    item.is_available = validated["is_available"]

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return {"error": "Не вдалося оновити страву. Перевірте введені дані."}, 500

    return {"message": "Страву оновлено"}, 200


def delete_partner_menu_item_service(item_id, current_user):
    item, _, error_response = _get_owned_menu_item_or_error(item_id, current_user)
    if error_response:
        return error_response

    has_order_history = (
        db.session.query(OrderItem.id).filter_by(menu_item_id=item.id).first()
        is not None
    )

    if has_order_history:
        item.is_available = False
        db.session.commit()
        return {
            "message": (
                "Страва вже є в історії замовлень, тому її приховано з меню "
                "замість повного видалення"
            )
        }, 200

    db.session.delete(item)
    db.session.commit()
    return {"message": "Страву видалено"}, 200


def get_partner_orders_service(current_user):
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
    restaurant_ids = [restaurant.id for restaurant in restaurants]

    if not restaurant_ids:
        return [], 200

    restaurant_map = {restaurant.id: restaurant.name for restaurant in restaurants}

    orders = (
        Order.query.filter(Order.restaurant_id.in_(restaurant_ids))
        .options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.menu_item),
            joinedload(Order.status_history),
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    result = []
    for order in orders:
        result.append(
            serialize_partner_order(
                order,
                restaurant_name=restaurant_map.get(order.restaurant_id, "—"),
                customer_name=_resolve_partner_customer_name(order),
                allowed_next_statuses=_get_allowed_next_order_statuses(order.status),
            )
        )

    return result, 200


def update_partner_order_status_service(order_id, data, current_user):
    order = db.session.get(Order, order_id)
    if not order:
        return {"error": "Замовлення не знайдено"}, 404

    restaurant = db.session.get(Restaurant, order.restaurant_id)

    if not restaurant or restaurant.owner_id != current_user.id:
        return _forbidden()

    status = (data.get("status") or "").strip().lower()
    note = (data.get("note") or "").strip()

    if status not in ORDER_ALLOWED_STATUSES:
        return {"error": "Некоректний статус"}, 400

    previous_status = (order.status or "").strip().lower()
    if previous_status == status:
        return {"message": "Статус не змінено", "status": order.status}, 200

    if not _is_order_status_transition_allowed(previous_status, status):
        allowed_statuses = _get_allowed_next_order_statuses(previous_status)
        if allowed_statuses:
            allowed_labels = ", ".join(
                _get_order_status_label(item) for item in allowed_statuses
            )
            return {
                "error": (
                    "Некоректний перехід статусу. "
                    f"Із статусу '{_get_order_status_label(previous_status)}' "
                    f"можна перейти лише в: {allowed_labels}."
                )
            }, 400

        return {
            "error": "Замовлення вже має фінальний статус і не може бути змінене"
        }, 400

    order.status = status

    history_item = OrderStatusHistory(
        order_id=order.id,
        status=status,
        note=(
            note
            or (
                f"Статус змінено з '{_get_order_status_label(previous_status)}' "
                f"на '{_get_order_status_label(status)}'"
            )
        ),
    )
    db.session.add(history_item)

    if getattr(order, "user_id", None):
        create_notification(
            user_id=order.user_id,
            message=(
                f"Статус вашого замовлення №{order.id} змінено на "
                f"«{_get_order_status_label(status)}»."
            ),
        )

    db.session.commit()

    return {
        "message": "Статус оновлено",
        "status": order.status,
        "allowed_next_statuses": _get_allowed_next_order_statuses(order.status),
    }, 200


def get_partner_analytics_service(current_user):
    restaurants = Restaurant.query.filter_by(owner_id=current_user.id).all()
    restaurant_ids = [restaurant.id for restaurant in restaurants]

    if not restaurant_ids:
        return {
            "orders_today": 0,
            "orders_week": 0,
            "total_revenue": 0,
            "average_check": 0,
            "top_dishes": [],
        }, 200

    now = datetime.utcnow()
    start_today = datetime(now.year, now.month, now.day)
    start_week = now - timedelta(days=7)

    orders_today = Order.query.filter(
        Order.restaurant_id.in_(restaurant_ids),
        Order.created_at >= start_today,
    ).count()

    orders_week = Order.query.filter(
        Order.restaurant_id.in_(restaurant_ids),
        Order.created_at >= start_week,
    ).count()

    total_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_price), 0))
        .filter(
            Order.restaurant_id.in_(restaurant_ids),
            Order.status == ORDER_STATUS_COMPLETED,
        )
        .scalar()
    )

    average_check = (
        db.session.query(func.coalesce(func.avg(Order.total_price), 0))
        .filter(
            Order.restaurant_id.in_(restaurant_ids),
            Order.status == ORDER_STATUS_COMPLETED,
        )
        .scalar()
    )

    top_dishes_query = (
        db.session.query(
            MenuItem.id.label("menu_item_id"),
            MenuItem.name.label("name"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_qty"),
        )
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.restaurant_id.in_(restaurant_ids),
            Order.status == ORDER_STATUS_COMPLETED,
        )
        .group_by(MenuItem.id, MenuItem.name)
        .order_by(desc("total_qty"), MenuItem.name.asc())
        .limit(5)
        .all()
    )

    top_dishes = [
        {
            "menu_item_id": row.menu_item_id,
            "name": row.name,
            "total_qty": int(row.total_qty or 0),
        }
        for row in top_dishes_query
    ]

    return {
        "orders_today": orders_today,
        "orders_week": orders_week,
        "total_revenue": int(total_revenue or 0),
        "average_check": round(float(average_check or 0), 2),
        "top_dishes": top_dishes,
    }, 200
