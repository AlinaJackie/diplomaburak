from sqlalchemy import desc, func

from constants import (
    ORDER_ACTIVE_STATUSES,
    ORDER_STATUS_COMPLETED,
    PARTNER_APPLICATION_STATUS_APPROVED,
    PARTNER_APPLICATION_STATUS_PENDING,
    PARTNER_APPLICATION_STATUS_REJECTED,
)
from extensions import db
from models import Order, PartnerApplication, Restaurant, User
from services.notification_service import create_notification, send_email_notification
from utils.formatters import format_datetime


def get_partner_applications_service():
    apps = PartnerApplication.query.order_by(PartnerApplication.created_at.desc()).all()

    result = []
    for app_obj in apps:
        result.append(
            {
                "id": app_obj.id,
                "contact_person": app_obj.contact_person,
                "brand_name": app_obj.brand_name,
                "phone": app_obj.phone,
                "email": app_obj.email,
                "city": app_obj.city,
                "verification_link": app_obj.verification_link,
                "planned_locations_count": app_obj.planned_locations_count,
                "edrpou_or_ipn": app_obj.edrpou_or_ipn,
                "business_description": app_obj.business_description,
                "personal_data_agreement": app_obj.personal_data_agreement,
                "representation_agreement": app_obj.representation_agreement,
                "status": app_obj.status,
                "created_at": format_datetime(app_obj.created_at),
            }
        )
    return result


def update_partner_application_status_service(app_id, status):
    app_obj = db.session.get(PartnerApplication, app_id)
    if not app_obj:
        return {"error": "Заявку партнера не знайдено"}, 404

    if status not in (
        PARTNER_APPLICATION_STATUS_APPROVED,
        PARTNER_APPLICATION_STATUS_REJECTED,
    ):
        return {"error": "Некоректний статус"}, 400

    current_status = (app_obj.status or "").strip().lower()
    if current_status == status:
        return {"message": "Статус заявки не змінено", "status": app_obj.status}, 200

    if current_status != PARTNER_APPLICATION_STATUS_PENDING:
        return {"error": "Можна змінювати лише заявки зі статусом 'pending'"}, 400

    app_obj.status = status

    owner = None
    if app_obj.user_id:
        owner = db.session.get(User, app_obj.user_id)

    if status == PARTNER_APPLICATION_STATUS_APPROVED:
        if not app_obj.user_id:
            return {
                "error": (
                    "Неможливо схвалити заявку без прив’язаного "
                    "користувача. Партнер повинен подати заявку "
                    "з авторизованого акаунта."
                )
            }, 400

        if not owner:
            return {"error": "Користувача заявки не знайдено"}, 404

        if app_obj.contact_person and not owner.full_name:
            owner.full_name = app_obj.contact_person

        if app_obj.city:
            owner.city = app_obj.city

    if owner:
        if status == PARTNER_APPLICATION_STATUS_APPROVED:
            create_notification(
                user_id=owner.id,
                message=(
                    "Вашу заявку партнера схвалено. "
                    "Тепер ви можете користуватися кабінетом партнера."
                ),
            )
        else:
            create_notification(
                user_id=owner.id,
                message=(
                    "Вашу заявку партнера відхилено. "
                    "Ви можете виправити дані та подати її повторно."
                ),
            )

    db.session.commit()

    if app_obj.email:
        if status == PARTNER_APPLICATION_STATUS_APPROVED:
            send_email_notification(
                subject="FoodGo — заявку схвалено",
                recipients=[app_obj.email],
                body=(
                    "Вітаємо!\n\n"
                    "Вашу заявку на співпрацю з FoodGo схвалено.\n\n"
                    f"Заклад: {app_obj.brand_name}\n\n"
                    "Тепер ви можете увійти у свій акаунт і перейти "
                    "в кабінет партнера.\n\n"
                    "З повагою,\n"
                    "Команда FoodGo"
                ),
            )
        else:
            send_email_notification(
                subject="FoodGo — заявку відхилено",
                recipients=[app_obj.email],
                body=(
                    "Вітаємо.\n\n"
                    "На жаль, вашу заявку на співпрацю з FoodGo "
                    "наразі відхилено.\n\n"
                    f"Заклад: {app_obj.brand_name}\n\n"
                    "Ви можете подати заявку повторно пізніше "
                    "або уточнити деталі у служби підтримки.\n\n"
                    "З повагою,\n"
                    "Команда FoodGo"
                ),
            )

    return {"message": "Оновлено", "status": app_obj.status}, 200


def get_admin_orders_service():
    orders = Order.query.order_by(Order.created_at.desc()).all()

    return [
        {
            "id": order.id,
            "customer_name": order.customer_name,
            "phone": order.phone,
            "restaurant_name": order.restaurant.name if order.restaurant else "—",
            "status": order.status,
            "total_price": order.total_price,
            "created_at": format_datetime(order.created_at),
            "delivery_type": order.delivery_type,
        }
        for order in orders
    ]


def get_admin_restaurants_service():
    restaurants = Restaurant.query.order_by(Restaurant.name.asc()).all()

    result = []
    for restaurant in restaurants:
        categories = []
        if restaurant.categories:
            categories = [
                category.strip()
                for category in restaurant.categories.split(",")
                if str(category).strip()
            ]

        result.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "city": restaurant.city,
                "categories": categories,
                "eta": restaurant.eta,
                "image_url": restaurant.image_url,
                "is_active": restaurant.is_active,
            }
        )

    return result


def get_admin_analytics_service():
    partners_count = (
        db.session.query(func.count(func.distinct(PartnerApplication.user_id)))
        .filter(
            PartnerApplication.status == PARTNER_APPLICATION_STATUS_APPROVED,
            PartnerApplication.user_id.isnot(None),
        )
        .scalar()
        or 0
    )

    applications_count = PartnerApplication.query.count()

    active_orders_count = Order.query.filter(
        Order.status.in_(ORDER_ACTIVE_STATUSES)
    ).count()

    completed_orders_count = Order.query.filter(
        Order.status == ORDER_STATUS_COMPLETED
    ).count()

    top_restaurants_query = (
        db.session.query(
            Restaurant.id.label("restaurant_id"),
            Restaurant.name.label("name"),
            func.count(Order.id).label("orders_count"),
        )
        .outerjoin(Order, Order.restaurant_id == Restaurant.id)
        .group_by(Restaurant.id, Restaurant.name)
        .order_by(desc("orders_count"), Restaurant.name.asc())
        .limit(5)
        .all()
    )

    top_restaurants = [
        {
            "restaurant_id": row.restaurant_id,
            "name": row.name,
            "orders_count": int(row.orders_count or 0),
        }
        for row in top_restaurants_query
    ]

    return {
        "partners_count": partners_count,
        "applications_count": applications_count,
        "active_orders_count": active_orders_count,
        "completed_orders_count": completed_orders_count,
        "top_restaurants": top_restaurants,
    }
