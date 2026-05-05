from flask_login import current_user

from constants import PARTNER_APPLICATION_STATUS_APPROVED
from models import PartnerApplication


def admin_required() -> bool:
    return current_user.is_authenticated and getattr(
        current_user,
        'is_admin',
        False,
    )


def partner_required() -> bool:
    if not current_user.is_authenticated:
        return False

    app_obj = (
        PartnerApplication.query
        .filter_by(
            user_id=current_user.id,
            status=PARTNER_APPLICATION_STATUS_APPROVED,
        )
        .order_by(PartnerApplication.created_at.desc())
        .first()
    )
    return app_obj is not None
