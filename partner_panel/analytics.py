from flask import jsonify
from flask_login import current_user, login_required

from auth.access import partner_required
from services.partner_service import get_partner_analytics_service
from . import partner_panel_bp


@partner_panel_bp.get("/api/analytics")
@login_required
def partner_analytics():
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Доступ дозволено лише після схвалення заявки."
                )
            }
        ), 403

    result, status_code = get_partner_analytics_service(current_user)
    return jsonify(result), status_code
