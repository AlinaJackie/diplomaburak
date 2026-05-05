from utils.city_utils import normalize_city_input
import re


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{10,20}$")


def _normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone or "")


def _validate_email(email: str):
    if not email:
        return "Вкажіть email"

    if not EMAIL_REGEX.match(email):
        return "Некоректний формат email"

    return None


def _validate_phone(phone: str):
    if not phone:
        return "Вкажіть номер телефону"

    if not PHONE_REGEX.match(phone):
        return "Некоректний формат телефону"

    normalized = _normalize_phone(phone)

    digits_only = re.sub(r"\D", "", normalized)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return "Некоректний формат телефону"

    return None


def _validate_password(password: str):
    if not password:
        return "Вкажіть пароль"

    if len(password) < 8:
        return "Пароль має містити щонайменше 8 символів"

    if not re.search(r"[A-ZА-ЯІЇЄҐ]", password):
        return "Пароль має містити хоча б одну велику літеру"

    if not re.search(r"[a-zа-яіїєґ]", password):
        return "Пароль має містити хоча б одну малу літеру"

    if not re.search(r"\d", password):
        return "Пароль має містити хоча б одну цифру"

    if not re.search(r"[^A-Za-zА-Яа-яІЇЄҐієїґ0-9]", password):
        return "Пароль має містити хоча б один спеціальний символ"

    return None


def validate_password_reset_request(identifier):
    identifier = (identifier or "").strip().lower()

    if not identifier:
        return None, "Вкажіть email або телефон"

    if "@" in identifier:
        email_error = _validate_email(identifier)
        if email_error:
            return None, email_error
    else:
        phone_error = _validate_phone(identifier)
        if phone_error:
            return None, phone_error

    return identifier, None


def validate_reset_password_payload(data):
    data = data or {}

    password = str(data.get("password", "")).strip()
    confirm_password = str(data.get("confirm_password", "")).strip()

    if not password or not confirm_password:
        return None, "Заповніть усі поля"

    password_error = _validate_password(password)
    if password_error:
        return None, password_error

    if password != confirm_password:
        return None, "Паролі не співпадають"

    return {
        "password": password,
        "confirm_password": confirm_password,
    }, None


def validate_register_payload(data):
    data = data or {}

    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    city = normalize_city_input(data.get("city"))
    street = (data.get("street") or "").strip()
    house = (data.get("house") or "").strip()
    extra_info = (data.get("extra_info") or "").strip()

    if not email or not phone or not password or not full_name:
        return None, "Заповніть обов’язкові поля"

    email_error = _validate_email(email)
    if email_error:
        return None, email_error

    phone_error = _validate_phone(phone)
    if phone_error:
        return None, phone_error

    password_error = _validate_password(password)
    if password_error:
        return None, password_error

    if len(full_name) < 2:
        return None, "Вкажіть коректне ім’я"

    return {
        "email": email,
        "phone": _normalize_phone(phone),
        "password": password,
        "full_name": full_name,
        "city": city,
        "street": street,
        "house": house,
        "extra_info": extra_info,
    }, None


def validate_login_payload(data):
    data = data or {}

    identifier = (data.get("identifier") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not identifier or not password:
        return None, "Введіть логін і пароль"

    return {
        "identifier": identifier,
        "password": password,
    }, None
