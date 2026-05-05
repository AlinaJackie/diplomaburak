from datetime import datetime, timedelta
import secrets

from flask import current_app
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from mail_utils import send_email_safe
from models import Notification, PasswordResetToken, User
from validators.auth_validators import (
    validate_login_payload,
    validate_password_reset_request,
    validate_register_payload,
    validate_reset_password_payload,
)


def send_reset_email(to_email: str, reset_link: str) -> bool:
    subject = "Відновлення пароля FoodGo"
    body = (
        "Ви надіслали запит на скидання пароля для акаунта FoodGo.\n\n"
        f"Перейдіть за посиланням, щоб встановити новий пароль:\n{reset_link}\n\n"
        "Посилання діє обмежений час.\n"
        "Якщо це були не ви, просто проігноруйте цей лист."
    )

    try:
        return send_email_safe(
            subject=subject,
            recipients=[to_email],
            body=body,
        )
    except Exception as error:
        current_app.logger.error(
            "RESET EMAIL SEND ERROR to %s: %s",
            to_email,
            error,
        )
        return False


def request_password_reset(data):
    data = data or {}

    identifier, error = validate_password_reset_request(
        data.get("identifier")
    )
    if error:
        return {"error": error}, 400

    success_message = {
        "message": "Якщо акаунт існує, лист для відновлення вже надіслано."
    }

    user = User.query.filter(
        db.or_(User.email == identifier, User.phone == identifier)
    ).first()

    if not user:
        return success_message, 200

    if not user.email:
        current_app.logger.warning(
            "PASSWORD RESET SKIPPED: user_id=%s has no email",
            user.id,
        )
        return success_message, 200

    old_tokens = PasswordResetToken.query.filter_by(
        user_id=user.id,
        used=False,
    ).all()

    for token_obj in old_tokens:
        token_obj.used = True

    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(
        hours=current_app.config.get("PASSWORD_RESET_TOKEN_HOURS", 1)
    )

    token_obj = PasswordResetToken(
        user_id=user.id,
        token=raw_token,
        expires_at=expires_at,
        used=False,
    )
    db.session.add(token_obj)
    db.session.commit()

    base_url = current_app.config.get(
        "APP_BASE_URL",
        "http://127.0.0.1:5000",
    )
    reset_link = f"{base_url}/auth/reset-password/{raw_token}"

    email_sent = send_reset_email(user.email, reset_link)

    if not email_sent:
        current_app.logger.warning(
            "PASSWORD RESET EMAIL FAILED for user_id=%s email=%s",
            user.id,
            user.email,
        )

    return success_message, 200


def get_valid_reset_token(token):
    token_obj = PasswordResetToken.query.filter_by(
        token=token,
        used=False,
    ).first()

    if not token_obj:
        return None

    if token_obj.expires_at < datetime.utcnow():
        return None

    return token_obj


def reset_user_password(token, data):
    validated, error = validate_reset_password_payload(data)
    if error:
        return {"error": error}, 400

    password = validated["password"]

    token_obj = PasswordResetToken.query.filter_by(
        token=token,
        used=False,
    ).first()

    if not token_obj:
        return {"error": "Токен недійсний або вже використаний"}, 400

    if token_obj.expires_at < datetime.utcnow():
        token_obj.used = True
        db.session.commit()
        return {"error": "Термін дії посилання минув"}, 400

    user = db.session.get(User, token_obj.user_id)
    if not user:
        return {"error": "Користувача не знайдено"}, 404

    user.password_hash = generate_password_hash(password)

    PasswordResetToken.query.filter_by(
        user_id=user.id,
        used=False,
    ).update({"used": True})

    db.session.commit()
    login_user(user)

    return {
        "message": "Пароль успішно змінено",
        "redirect": "/",
    }, 200


def register_user(data):
    validated, error = validate_register_payload(data)
    if error:
        return {"error": error}, 400

    email = validated["email"]
    phone = validated["phone"]
    password = validated["password"]
    full_name = validated["full_name"]
    city = validated["city"]
    street = validated["street"]
    house = validated["house"]
    extra_info = validated["extra_info"]

    existing_user = User.query.filter(
        (User.email == email) | (User.phone == phone)
    ).first()

    if existing_user:
        return {
            "error": "Користувач з таким email або телефоном уже існує"
        }, 400

    hashed_password = generate_password_hash(password)

    user = User(
        email=email,
        phone=phone,
        password_hash=hashed_password,
        full_name=full_name,
        city=city,
        street=street,
        house=house,
        extra_info=extra_info,
    )

    db.session.add(user)
    db.session.commit()
    login_user(user)

    return {
        "message": "Реєстрація успішна",
        "redirect": "/",
    }, 201


def login_user_by_credentials(data):
    validated, error = validate_login_payload(data)
    if error:
        return {"error": error}, 400

    identifier = validated["identifier"]
    password = validated["password"]

    user = User.query.filter(
        (User.email == identifier) | (User.phone == identifier)
    ).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {"error": "Невірний логін або пароль"}, 401

    login_user(user)

    return {
        "message": "ok",
        "redirect": "/",
    }, 200


def logout_current_user():
    logout_user()
    return {"message": "logged_out"}, 200


def build_me_response(user):
    if not user.is_authenticated:
        return {"authenticated": False}, 200

    return {
        "authenticated": True,
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "full_name": user.full_name,
        "city": user.city,
    }, 200


def get_user_notifications(user_id):
    notifications = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [
        {
            "id": notification.id,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.strftime("%d.%m.%Y %H:%M")
                if notification.created_at
                else None
            ),
        }
        for notification in notifications
    ]
