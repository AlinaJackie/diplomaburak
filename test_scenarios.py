import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/foodgo_scenarios.db"
os.environ["MAIL_USERNAME"] = ""

from models import Notification, Restaurant, MenuItem, Order, User
from extensions import db
from app import create_app


app = create_app()
app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)


def assert_status(response, expected, label):
    if response.status_code != expected:
        raise AssertionError(
            f"{label}: expected {expected}, got {response.status_code}, body={response.get_data(as_text=True)}"
        )


with app.app_context():
    db.drop_all()
    db.create_all()

client = app.test_client()

# 1. реєстрація
register_res = client.post(
    "/auth/register",
    json={
        "email": "buyer@test.com",
        "phone": "+380501112233",
        "password": "BuyerTest1!",
        "full_name": "Тестовий Користувач",
        "city": "Івано-Франківськ",
        "street": "Шевченка",
        "house": "10",
        "extra_info": "кв. 2",
    },
)
assert_status(register_res, 201, "registration")

# partner registration
partner_reg = client.post(
    "/auth/register",
    json={
        "email": "partner@test.com",
        "phone": "+380501112244",
        "password": "PartnerTest1!",
        "full_name": "Тестовий Партнер",
        "city": "Івано-Франківськ",
        "street": "Грушевського",
        "house": "7",
        "extra_info": "",
    },
)
assert_status(partner_reg, 201, "partner registration")

# admin create direct
with app.app_context():
    from werkzeug.security import generate_password_hash

    admin = User(
        email="admin@test.com",
        phone="+380501112255",
        password_hash=generate_password_hash("AdminTest1!"),
        full_name="Admin",
        city="Івано-Франківськ",
        is_admin=True,
    )
    db.session.add(admin)
    db.session.commit()

# 2. логін партнера
login_partner = client.post(
    "/auth/login",
    json={
        "identifier": "partner@test.com",
        "password": "PartnerTest1!",
    },
)
assert_status(login_partner, 200, "partner login")

# 3. створення заявки партнера
partner_app = client.post(
    "/api/partner/applications",
    json={
        "contact_person": "Тестовий Партнер",
        "brand_name": "Test Pizza",
        "phone": "+380501112244",
        "email": "partner@test.com",
        "city": "Івано-Франківськ",
        "verification_link": "https://example.com/test-pizza",
        "planned_locations_count": 1,
        "edrpou_or_ipn": "12345678",
        "business_description": "Тестовий ресторан для сценарію.",
        "personal_data_agreement": True,
        "representation_agreement": True,
    },
)
assert_status(partner_app, 201, "partner application create")
client.post("/auth/logout")

# 4. схвалення заявки
admin_login = client.post(
    "/auth/login",
    json={
        "identifier": "admin@test.com",
        "password": "AdminTest1!",
    },
)
assert_status(admin_login, 200, "admin login")
apps_res = client.get("/admin/api/partner-applications")
assert_status(apps_res, 200, "partner applications list")
app_id = apps_res.get_json()[0]["id"]
approve_res = client.patch(
    f"/admin/api/partner-applications/{app_id}", json={"status": "approved"}
)
assert_status(approve_res, 200, "partner application approve")
client.post("/auth/logout")

# 5. створення ресторану
# Після рефакторингу партнерська панель використовує /partner/api/...,
# тоді як модерація заявок партнера й надалі лишається в /admin/api/...
client.post(
    "/auth/login", json={"identifier": "partner@test.com", "password": "PartnerTest1!"}
)
create_rest = client.post(
    "/partner/api/restaurants",
    data={
        "name": "Test Pizza",
        "city": "Івано-Франківськ",
        "address": "вул. Незалежності, 1",
        "opening_time": "09:00",
        "closing_time": "23:00",
        "description": "Піцца та напої",
        "price_level": "$$",
        "eta": "20-30 хв",
        "categories": "pizza,fastfood",
        "minimum_order_amount": "200",
        "is_active": "true",
    },
)
assert_status(create_rest, 201, "restaurant create")
restaurant_id = create_rest.get_json()["id"]

# 6. додавання страв
menu_create = client.post(
    f"/partner/api/restaurants/{restaurant_id}/menu",
    data={
        "name": "Піцца 4 сири",
        "description": "Сирна піца",
        "price": "240",
        "weight": "520 г",
        "is_available": "true",
    },
)
assert_status(menu_create, 201, "menu item create")
item_id = menu_create.get_json()["id"]
status_update = client.post("/auth/logout")

# 7. логін покупця
buyer_login = client.post(
    "/auth/login",
    json={
        "identifier": "buyer@test.com",
        "password": "BuyerTest1!",
    },
)
assert_status(buyer_login, 200, "buyer login")

preview = client.post(
    "/api/orders/preview",
    json={
        "restaurant_id": restaurant_id,
        "items": [{"id": item_id, "quantity": 1}],
        "customer_name": "Тестовий Користувач",
        "phone": "+380501112233",
        "city": "Івано-Франківськ",
        "address": "вул. Гетьмана Мазепи, 10",
        "comment": "без оливок",
        "payment_method": "cash",
        "delivery_type": "delivery",
    },
)
assert_status(preview, 200, "order preview")

# 8. оформлення замовлення
create_order = client.post(
    "/api/orders",
    json={
        "restaurant_id": restaurant_id,
        "items": [{"id": item_id, "quantity": 1}],
        "customer_name": "Тестовий Користувач",
        "phone": "+380501112233",
        "city": "Івано-Франківськ",
        "address": "вул. Гетьмана Мазепи, 10",
        "comment": "без оливок",
        "payment_method": "cash",
        "delivery_type": "delivery",
    },
)
assert_status(create_order, 201, "order create")
order_id = create_order.get_json()["order_id"]
client.post("/auth/logout")

# 9. зміна статусу партнером
client.post(
    "/auth/login", json={"identifier": "partner@test.com", "password": "PartnerTest1!"}
)
for next_status, note in [
    ("accepted", "Замовлення підтверджено"),
    ("processing", "Замовлення готується"),
    ("delivering", "Кур'єр виїхав"),
    ("completed", "Готово"),
]:
    update_status = client.patch(
        f"/partner/api/orders/{order_id}/status",
        json={"status": next_status, "note": note},
    )
    assert_status(update_status, 200, f"order status update: {next_status}")
client.post("/auth/logout")

# 10. залишення відгуку
client.post(
    "/auth/login", json={"identifier": "buyer@test.com", "password": "BuyerTest1!"}
)
review_res = client.post(
    f"/api/orders/{order_id}/review", json={"rating": 5, "comment": "Все супер"}
)
assert_status(review_res, 201, "review create")

with app.app_context():
    order = db.session.get(Order, order_id)
    restaurant = db.session.get(Restaurant, restaurant_id)
    menu_item = db.session.get(MenuItem, item_id)
    if order.status != "completed":
        raise AssertionError("Order did not stay completed")
    if restaurant.rating != 5.0:
        raise AssertionError(f"Unexpected rating: {restaurant.rating}")
    if not menu_item or menu_item.name != "Піцца 4 сири":
        raise AssertionError("Menu item missing after scenario")

    buyer = User.query.filter_by(email="buyer@test.com").first()
    notifications = Notification.query.filter_by(user_id=buyer.id).all()
    if len(notifications) < 5:
        raise AssertionError("Expected order notifications were not created")

print("All core scenarios passed successfully.")
