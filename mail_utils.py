import logging

from flask import current_app
from flask_mail import Message

from extensions import mail

logger = logging.getLogger(__name__)


def send_email_safe(subject: str, recipients: list[str], body: str) -> bool:
    try:
        if not recipients:
            logger.warning("Список отримувачів порожній. Лист не надіслано.")
            return False

        if not current_app.config.get("MAIL_USERNAME"):
            logger.warning("MAIL_USERNAME не задано. Лист не надіслано.")
            return False

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
        )
        mail.send(msg)
        return True

    except Exception as e:
        logger.exception("Помилка надсилання листа: %s", e)
        return False
