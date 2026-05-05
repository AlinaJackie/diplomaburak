from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    full_name = db.Column(db.String(120))
    city = db.Column(db.String(80))
    street = db.Column(db.String(120))
    house = db.Column(db.String(50))
    extra_info = db.Column(db.String(255))

    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", back_populates="user")
    cart = db.relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    partner_applications = db.relationship(
        "PartnerApplication",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="PartnerApplication.created_at.desc()",
    )
    reviews = db.relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )
    favorite_restaurants = db.relationship(
        "FavoriteRestaurant", back_populates="user", cascade="all, delete-orphan"
    )
    favorite_menu_items = db.relationship(
        "FavoriteMenuItem", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens = db.relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    city = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    price_level = db.Column(db.String(20))
    eta = db.Column(db.String(50))
    rating = db.Column(db.Float)
    categories = db.Column(db.String(255))
    image_url = db.Column(db.String(255))
    opening_time = db.Column(db.String(5), default="09:00")
    closing_time = db.Column(db.String(5), default="22:00")

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    minimum_order_amount = db.Column(db.Integer, default=200, nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    menu_items = db.relationship(
        "MenuItem", back_populates="restaurant", cascade="all, delete-orphan"
    )
    orders = db.relationship(
        "Order", back_populates="restaurant", cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "Review", back_populates="restaurant", cascade="all, delete-orphan"
    )
    favorited_by = db.relationship(
        "FavoriteRestaurant", back_populates="restaurant", cascade="all, delete-orphan"
    )

    def category_list(self):
        return (
            [c.strip() for c in self.categories.split(
                ",")] if self.categories else []
        )

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255))
    weight = db.Column(db.String(50))
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    restaurant = db.relationship("Restaurant", back_populates="menu_items")
    favorited_by = db.relationship(
        "FavoriteMenuItem", back_populates="menu_item", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<MenuItem {self.name} {self.price}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )

    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    comment = db.Column(db.String(255), nullable=True)

    payment_method = db.Column(db.String(50), nullable=True)
    delivery_type = db.Column(db.String(50), nullable=True)
    delivery_fee = db.Column(db.Integer, default=0)
    eta_minutes = db.Column(db.Integer, default=0)

    total_price = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="new")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders")
    restaurant = db.relationship("Restaurant", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    review = db.relationship(
        "Review", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    status_history = db.relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at.asc()",
    )

    def __repr__(self):
        return f"<Order {self.id} {self.total_price}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(
        "orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey(
        "menu_items.id"), nullable=False)

    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    menu_item = db.relationship("MenuItem")

    def __repr__(self):
        return f"<OrderItem {self.menu_item_id} x{self.quantity}>"


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(
        "orders.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False)

    order = db.relationship("Order", back_populates="status_history")

    def __repr__(self):
        return f"<OrderStatusHistory order={self.order_id} status={self.status}>"


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="cart")
    restaurant = db.relationship("Restaurant")
    items = db.relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        order_by="CartItem.id.asc()",
    )

    def __repr__(self):
        return f"<Cart user={self.user_id} restaurant={self.restaurant_id}>"


class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (
        db.UniqueConstraint("cart_id", "menu_item_id", name="uq_cart_menu_item"),
    )

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    cart = db.relationship("Cart", back_populates="items")
    menu_item = db.relationship("MenuItem")

    def __repr__(self):
        return f"<CartItem cart={self.cart_id} item={self.menu_item_id} qty={self.quantity}>"


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, unique=True
    )

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="reviews")
    restaurant = db.relationship("Restaurant", back_populates="reviews")
    order = db.relationship("Order", back_populates="review")

    def __repr__(self):
        return f"<Review {self.id} rating={self.rating}>"


class FavoriteRestaurant(db.Model):
    __tablename__ = "favorite_restaurants"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "restaurant_id", name="uq_user_restaurant_favorite"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id = db.Column(
        db.Integer, db.ForeignKey("restaurants.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favorite_restaurants")
    restaurant = db.relationship("Restaurant", back_populates="favorited_by")

    def __repr__(self):
        return (
            f"<FavoriteRestaurant user={self.user_id} restaurant={self.restaurant_id}>"
        )


class FavoriteMenuItem(db.Model):
    __tablename__ = "favorite_menu_items"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "menu_item_id", name="uq_user_menu_item_favorite"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey(
        "menu_items.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favorite_menu_items")
    menu_item = db.relationship("MenuItem", back_populates="favorited_by")

    def __repr__(self):
        return f"<FavoriteMenuItem user={self.user_id} item={self.menu_item_id}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id}>"


class PartnerApplication(db.Model):
    __tablename__ = "partner_application"

    id = db.Column(db.Integer, primary_key=True)

    contact_person = db.Column(db.String(120), nullable=False)
    brand_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    verification_link = db.Column(db.String(255), nullable=False)
    planned_locations_count = db.Column(db.Integer, nullable=False, default=1)
    edrpou_or_ipn = db.Column(db.String(50), nullable=False)
    business_description = db.Column(db.String(1000), nullable=False)

    personal_data_agreement = db.Column(
        db.Boolean, default=False, nullable=False)
    representation_agreement = db.Column(
        db.Boolean, default=False, nullable=False)

    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", back_populates="partner_applications")


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="password_reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken user={self.user_id} used={self.used}>"
