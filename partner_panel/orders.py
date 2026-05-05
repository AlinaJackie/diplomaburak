from flask import jsonify, request
from flask_login import current_user, login_required

from auth.access import partner_required
from services.partner_service import (
    get_partner_orders_service,
    update_partner_order_status_service,
)
from . import partner_panel_bp


@partner_panel_bp.get("/api/orders")
@login_required
def partner_orders_list():
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Доступ дозволено лише після схвалення заявки."
                )
            }
        ), 403

    result, status_code = get_partner_orders_service(current_user)
    return jsonify(result), status_code


@partner_panel_bp.patch("/api/orders/<int:order_id>/status")
@login_required
def partner_order_update_status(order_id):
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Доступ дозволено лише після схвалення заявки."
                )
            }
        ), 403

    data = request.get_json() or {}
    result, status_code = update_partner_order_status_service(
        order_id,
        data,
        current_user,
    )
    return jsonify(result), status_code
