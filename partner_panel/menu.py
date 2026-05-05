from flask import jsonify, request
from flask_login import current_user, login_required

from auth.access import partner_required
from services.partner_service import (
    create_partner_menu_item_service,
    delete_partner_menu_item_service,
    get_partner_restaurant_menu_service,
    update_partner_menu_item_service,
)
from . import partner_panel_bp


@partner_panel_bp.get("/api/restaurants/<int:rest_id>/menu")
@login_required
def partner_restaurant_menu(rest_id):
    if not partner_required():
        return jsonify({
            "error": "Доступ дозволено лише після схвалення заявки."
        }), 403

    result, status_code = get_partner_restaurant_menu_service(
        rest_id,
        current_user,
    )
    return jsonify(result), status_code


@partner_panel_bp.post("/api/restaurants/<int:rest_id>/menu")
@login_required
def partner_restaurant_menu_add(rest_id):
    if not partner_required():
        return jsonify({
            "error": "Доступ дозволено лише після схвалення заявки."
        }), 403

    result, status_code = create_partner_menu_item_service(
        rest_id,
        request.form,
        request.files,
        current_user,
    )
    return jsonify(result), status_code


@partner_panel_bp.patch("/api/menu-items/<int:item_id>")
@login_required
def partner_menu_item_update(item_id):
    if not partner_required():
        return jsonify({
            "error": "Редагування доступне лише після схвалення заявки."
        }), 403

    result, status_code = update_partner_menu_item_service(
        item_id,
        request.form,
        request.files,
        current_user,
    )
    return jsonify(result), status_code


@partner_panel_bp.delete("/api/menu-items/<int:item_id>")
@login_required
def partner_menu_item_delete(item_id):
    if not partner_required():
        return jsonify({
            "error": "Видалення доступне лише після схвалення заявки."
        }), 403

    result, status_code = delete_partner_menu_item_service(
        item_id,
        current_user,
    )
    return jsonify(result), status_code