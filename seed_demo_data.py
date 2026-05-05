from constants import (
    ORDER_STATUS_ACCEPTED,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_DELIVERING,
    ORDER_STATUS_NEW,
    PARTNER_APPLICATION_STATUS_APPROVED,
    PARTNER_APPLICATION_STATUS_PENDING,
)
from models import (
    MenuItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    PartnerApplication,
    Restaurant,
    Review,
    User,
)
from extensions import db
from app import create_app
import os
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

os.environ.setdefault("PYTHONUTF8", "1")


app = create_app()


def make_user(email, phone, password, full_name, city, is_admin=False):
    user = User(
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        city=city,
        street="Головна",
        house="1",
        extra_info="",
        is_admin=is_admin,
    )
    db.session.add(user)
    db.session.flush()
    return user


with app.app_context():
    db.drop_all()
    db.create_all()

    admin = make_user(
        "admin@foodgo.test",
        "+380500000001",
        "AdminTest1",
        "Адміністратор FoodGo",
        "Івано-Франківськ",
        is_admin=True,
    )
    partner = make_user(
        "partner@foodgo.test",
        "+380500000002",
        "PartnerTest1",
        "Марія Партнер",
        "Івано-Франківськ",
    )
    second_partner = make_user(
        "friend@foodgo.test",
        "+380500000003",
        "PartnerTest2",
        "Василь Партнер",
        "Івано-Франківськ",
    )
    customer = make_user(
        "customer@foodgo.test",
        "+380500000004",
        "CustomerTest1",
        "Іван Петренко",
        "Івано-Франківськ",
    )
    second_customer = make_user(
        "guest@foodgo.test",
        "+380500000005",
        "GuestTest1",
        "Олена Коваль",
        "Львів",
    )

    db.session.add(PartnerApplication(
        contact_person="Марія Партнер",
        brand_name="Pizza Corner",
        phone=partner.phone,
        email=partner.email,
        city="Івано-Франківськ",
        verification_link="https://example.com/partner-docs",
        planned_locations_count=2,
        edrpou_or_ipn="12345678",
        business_description="Локальна мережа піцерій з доставкою.",
        personal_data_agreement=True,
        representation_agreement=True,
        status=PARTNER_APPLICATION_STATUS_APPROVED,
        user_id=partner.id,
    ))

    db.session.add(PartnerApplication(
        contact_person="Василь Партнер",
        brand_name="Green Bowl",
        phone=second_partner.phone,
        email=second_partner.email,
        city="Івано-Франківськ",
        verification_link="https://example.com/partner-docs",
        planned_locations_count=2,
        edrpou_or_ipn="1213428",
        business_description="Смачні Боули та салати",
        personal_data_agreement=True,
        representation_agreement=True,
        status=PARTNER_APPLICATION_STATUS_APPROVED,
        user_id=second_partner.id,
    ))

    db.session.add(PartnerApplication(
        contact_person="Олена Коваль",
        brand_name="Green Bowl",
        phone=second_customer.phone,
        email=second_customer.email,
        city="Львів",
        verification_link="https://example.com/green-bowl",
        planned_locations_count=1,
        edrpou_or_ipn="87654321",
        business_description="Здорова їжа та боули.",
        personal_data_agreement=True,
        representation_agreement=True,
        status=PARTNER_APPLICATION_STATUS_PENDING,
        user_id=second_customer.id,
    ))
    db.session.flush()

    restaurants = [
        Restaurant(
            name="Pizza Corner Центр",
            description="Піца, паста та швидка доставка по місту.",
            city="Івано-Франківськ",
            address="вул. Незалежності, 12",
            latitude=48.9226,
            longitude=24.7111,
            price_level="$$",
            eta="25-35 хв",
            rating=4.8,
            categories="pizza,fastfood",
            image_url="https://placehold.co/600x400?text=Pizza+Corner",
            opening_time="00:00",
            closing_time="23:59",
            is_active=True,
            minimum_order_amount=250,
            owner_id=partner.id,
        ),
        Restaurant(
            name="Burger Lab",
            description="Бургери, картопля та комбо-набори.",
            city="Івано-Франківськ",
            address="вул. Січових Стрільців, 20",
            latitude=48.9207,
            longitude=24.7094,
            price_level="$$",
            eta="20-30 хв",
            rating=4.6,
            categories="burgers,fastfood,grill",
            image_url="https://placehold.co/600x400?text=Burger+Lab",
            opening_time="00:00",
            closing_time="23:59",
            is_active=True,
            minimum_order_amount=220,
            owner_id=partner.id,
        ),
        Restaurant(
            name="Green Bowl",
            description="Боул, салати та корисна їжа.",
            city="Львів",
            address="пл. Ринок, 5",
            latitude=49.8419,
            longitude=24.0315,
            price_level="$$$",
            eta="30-40 хв",
            rating=4.9,
            categories="healthy,breakfast,homemade",
            image_url="https://placehold.co/600x400?text=Green+Bowl",
            opening_time="00:00",
            closing_time="23:59",
            is_active=True,
            minimum_order_amount=300,
            owner_id=second_partner.id,
        ),
    ]
    db.session.add_all(restaurants)
    db.session.flush()

    menu_items = [
        MenuItem(restaurant_id=restaurants[0].id, name="Маргарита", description="Класична піца з моцарелою",
                 price=210, weight="520 г", image_url="https://placehold.co/600x400?text=Маргарита", is_available=True),
        MenuItem(restaurant_id=restaurants[0].id, name="Пепероні", description="Піца з пепероні та сиром",
                 price=245, weight="540 г", image_url="https://placehold.co/600x400?text=Пепероні", is_available=True),
        MenuItem(restaurant_id=restaurants[1].id, name="Cheese Burger", description="Соковитий бургер з яловичиною",
                 price=185, weight="320 г", image_url="https://placehold.co/600x400?text=Cheese+Burger", is_available=True),
        MenuItem(restaurant_id=restaurants[1].id, name="Картопля фрі", description="Хрустка картопля",
                 price=89, weight="150 г", image_url="https://placehold.co/600x400?text=Fries", is_available=True),
        MenuItem(restaurant_id=restaurants[2].id, name="Боул з куркою", description="Боул з кіноа та овочами",
                 price=260, weight="400 г", image_url="https://placehold.co/600x400?text=Bowl", is_available=True),
        MenuItem(restaurant_id=restaurants[2].id, name="Салат Цезар", description="Салат з куркою та пармезаном",
                 price=230, weight="300 г", image_url="https://placehold.co/600x400?text=Caesar", is_available=True),
    ]
    db.session.add_all(menu_items)
    db.session.flush()

    now = datetime.utcnow()
    order1 = Order(
        user_id=customer.id,
        restaurant_id=restaurants[0].id,
        customer_name=customer.full_name,
        phone=customer.phone,
        city="Івано-Франківськ",
        address="вул. Галицька, 10",
        comment="Подзвонити перед доставкою",
        payment_method="cash",
        delivery_type="delivery",
        delivery_fee=70,
        eta_minutes=35,
        total_price=525,
        status=ORDER_STATUS_COMPLETED,
        created_at=now - timedelta(days=1),
    )
    order2 = Order(
        user_id=customer.id,
        restaurant_id=restaurants[1].id,
        customer_name=customer.full_name,
        phone=customer.phone,
        city="Івано-Франківськ",
        address="вул. Дністровська, 5",
        comment="Без цибулі",
        payment_method="card_on_delivery",
        delivery_type="delivery",
        delivery_fee=60,
        eta_minutes=28,
        total_price=334,
        status=ORDER_STATUS_DELIVERING,
        created_at=now - timedelta(hours=3),
    )
    order3 = Order(
        user_id=second_customer.id,
        restaurant_id=restaurants[2].id,
        customer_name=second_customer.full_name,
        phone=second_customer.phone,
        city="Львів",
        address="вул. Дорошенка, 8",
        comment="",
        payment_method="cash",
        delivery_type="pickup",
        delivery_fee=0,
        eta_minutes=15,
        total_price=260,
        status=ORDER_STATUS_ACCEPTED,
        created_at=now - timedelta(hours=1),
    )
    db.session.add_all([order1, order2, order3])
    db.session.flush()

    db.session.add_all([
        OrderItem(order_id=order1.id,
                  menu_item_id=menu_items[0].id, quantity=1, price=210),
        OrderItem(order_id=order1.id,
                  menu_item_id=menu_items[1].id, quantity=1, price=245),
        OrderItem(order_id=order2.id,
                  menu_item_id=menu_items[2].id, quantity=1, price=185),
        OrderItem(order_id=order2.id,
                  menu_item_id=menu_items[3].id, quantity=1, price=89),
        OrderItem(order_id=order3.id,
                  menu_item_id=menu_items[4].id, quantity=1, price=260),
    ])

    for order, status, note in [
        (order1, ORDER_STATUS_NEW, "Замовлення створено"),
        (order1, ORDER_STATUS_COMPLETED, "Доставлено клієнту"),
        (order2, ORDER_STATUS_NEW, "Замовлення створено"),
        (order2, ORDER_STATUS_DELIVERING, "Кур'єр уже в дорозі"),
        (order3, ORDER_STATUS_NEW, "Замовлення створено"),
        (order3, ORDER_STATUS_ACCEPTED, "Замовлення прийняте рестораном"),
    ]:
        db.session.add(OrderStatusHistory(
            order_id=order.id, status=status, note=note))

    db.session.add(Review(
        user_id=customer.id,
        restaurant_id=restaurants[0].id,
        order_id=order1.id,
        rating=5,
        comment="Дуже смачна піца і швидка доставка.",
    ))

    db.session.commit()
    print("Demo database seeded successfully.")
