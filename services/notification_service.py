from extensions import db
from models import Notification
from mail_utils import send_email_safe


def create_notification(user_id, message):
    if not user_id or not message:
        return None

    notification = Notification(
        user_id=user_id,
        message=message,
    )
    db.session.add(notification)
    return notification


def send_email_notification(subject, recipients, body):
    return send_email_safe(
        subject=subject,
        recipients=recipients,
        body=body,
    )
