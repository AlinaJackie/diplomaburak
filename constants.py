# constants.py

# ----------------------------
# Ролі
# ----------------------------
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_PARTNER = "partner"


# ----------------------------
# Статуси заявок партнерів
# ----------------------------
PARTNER_APPLICATION_STATUS_PENDING = "pending"
PARTNER_APPLICATION_STATUS_APPROVED = "approved"
PARTNER_APPLICATION_STATUS_REJECTED = "rejected"

PARTNER_APPLICATION_ALLOWED_STATUSES = {
    PARTNER_APPLICATION_STATUS_PENDING,
    PARTNER_APPLICATION_STATUS_APPROVED,
    PARTNER_APPLICATION_STATUS_REJECTED,
}


# ----------------------------
# Статуси замовлень
# ----------------------------
ORDER_STATUS_NEW = "new"
ORDER_STATUS_ACCEPTED = "accepted"
ORDER_STATUS_PROCESSING = "processing"
ORDER_STATUS_DELIVERING = "delivering"
ORDER_STATUS_COMPLETED = "completed"
ORDER_STATUS_CANCELLED = "cancelled"

ORDER_ACTIVE_STATUSES = {
    ORDER_STATUS_NEW,
    ORDER_STATUS_ACCEPTED,
    ORDER_STATUS_PROCESSING,
    ORDER_STATUS_DELIVERING,
}

ORDER_FINAL_STATUSES = {
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_CANCELLED,
}

ORDER_ALLOWED_STATUSES = ORDER_ACTIVE_STATUSES | ORDER_FINAL_STATUSES

ORDER_ALLOWED_TRANSITIONS = {
    ORDER_STATUS_NEW: [ORDER_STATUS_ACCEPTED, ORDER_STATUS_CANCELLED],
    ORDER_STATUS_ACCEPTED: [ORDER_STATUS_PROCESSING, ORDER_STATUS_CANCELLED],
    ORDER_STATUS_PROCESSING: [ORDER_STATUS_DELIVERING, ORDER_STATUS_CANCELLED],
    ORDER_STATUS_DELIVERING: [ORDER_STATUS_COMPLETED, ORDER_STATUS_CANCELLED],
    ORDER_STATUS_COMPLETED: [],
    ORDER_STATUS_CANCELLED: [],
}

ORDER_STATUS_LABELS = {
    ORDER_STATUS_NEW: "Нове",
    ORDER_STATUS_ACCEPTED: "Прийнято",
    ORDER_STATUS_PROCESSING: "Готується",
    ORDER_STATUS_DELIVERING: "Доставляється",
    ORDER_STATUS_COMPLETED: "Виконано",
    ORDER_STATUS_CANCELLED: "Скасовано",
}


# ----------------------------
# Типи доставки
# ----------------------------
DELIVERY_TYPE_DELIVERY = "delivery"
DELIVERY_TYPE_PICKUP = "pickup"

ALLOWED_DELIVERY_TYPES = {
    DELIVERY_TYPE_DELIVERY,
    DELIVERY_TYPE_PICKUP,
}


# ----------------------------
# Типи оплати
# ----------------------------
PAYMENT_METHOD_CASH = "cash"
PAYMENT_METHOD_CARD_ON_DELIVERY = "card_on_delivery"

ALLOWED_PAYMENT_METHODS = {
    PAYMENT_METHOD_CASH,
    PAYMENT_METHOD_CARD_ON_DELIVERY,
}


# ----------------------------
# Типи сповіщень
# ----------------------------
NOTIFICATION_TYPE_ORDER_CREATED = "order_created"
NOTIFICATION_TYPE_ORDER_STATUS_CHANGED = "order_status_changed"
NOTIFICATION_TYPE_PARTNER_APPLICATION_CREATED = "partner_application_created"
NOTIFICATION_TYPE_PARTNER_APPLICATION_APPROVED = "partner_application_approved"
NOTIFICATION_TYPE_PARTNER_APPLICATION_REJECTED = "partner_application_rejected"
NOTIFICATION_TYPE_PASSWORD_RESET = "password_reset"


# ----------------------------
# Дозволені розширення файлів
# ----------------------------
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


# ----------------------------
# Міста, де доступна доставка
# ----------------------------
DELIVERY_ALLOWED_CITIES = {
    "ivano-frankivsk",
    "lviv",
    "chernivtsi",
}

DELIVERY_ALLOWED_CITIES_TEXT = "Івано-Франківську, Львові та Чернівцях"
