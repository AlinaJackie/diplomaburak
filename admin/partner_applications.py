from flask import jsonify, request
from flask_login import login_required

from . import admin_bp
from auth.access import admin_required
from services.admin_service import (
    get_partner_applications_service,
    update_partner_application_status_service,
)


@admin_bp.get("/api/partner-applications")
@login_required
def admin_list_partner_applications():
    if not admin_required():
        return jsonify({"error": "Доступ заборонено"}), 403

    result = get_partner_applications_service()
    return jsonify(result)


@admin_bp.patch("/api/partner-applications/<int:app_id>")
@login_required
def admin_update_partner_application(app_id):
    if not admin_required():
        return jsonify({"error": "Доступ заборонено"}), 403

    data = request.get_json() or {}
    result, status_code = update_partner_application_status_service(
        app_id, data.get("status"))

    return jsonify(result), status_code
