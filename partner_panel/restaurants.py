from flask import jsonify, request
from flask_login import current_user, login_required

from auth.access import partner_required
from services.partner_service import (
    create_partner_restaurant_service,
    delete_partner_restaurant_service,
    get_partner_restaurants_service,
    update_partner_restaurant_service,
)
from . import partner_panel_bp


@partner_panel_bp.get("/api/restaurants")
@login_required
def partner_restaurants_list():
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Доступ дозволено лише після схвалення заявки."
                )
            }
        ), 403

    result = get_partner_restaurants_service(current_user)
    return jsonify(result)


@partner_panel_bp.post("/api/restaurants")
@login_required
def partner_restaurants_create():
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Створення доступне лише після схвалення заявки."
                )
            }
        ), 403

    result, status_code = create_partner_restaurant_service(
        request.form,
        request.files,
        current_user,
    )
    return jsonify(result), status_code


@partner_panel_bp.patch("/api/restaurants/<int:rest_id>")
@login_required
def partner_restaurants_update(rest_id):
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Редагування доступне лише після схвалення заявки."
                )
            }
        ), 403

    result, status_code = update_partner_restaurant_service(
        rest_id,
        request.form,
        request.files,
        current_user,
    )
    return jsonify(result), status_code


@partner_panel_bp.delete("/api/restaurants/<int:rest_id>")
@login_required
def partner_restaurants_delete(rest_id):
    if not partner_required():
        return jsonify(
            {
                "error": (
                    "Видалення доступне лише після схвалення заявки."
                )
            }
        ), 403

    result, status_code = delete_partner_restaurant_service(
        rest_id,
        current_user,
    )
    return jsonify(result), status_code
