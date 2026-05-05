from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import current_user, login_required

from services.partner_service import (
    create_partner_application,
    get_latest_partner_application,
    get_partner_restaurants,
    can_access_partner_dashboard,
)


partner_bp = Blueprint("partner", __name__)


@partner_bp.get("/partner")
def partner_apply_page():
    return render_template("partner_apply.html")


@partner_bp.post("/api/partner/applications")
@login_required
def partner_apply_api():
    result, status_code = create_partner_application(
        current_user,
        request.get_json() or {}
    )
    return jsonify(result), status_code


@partner_bp.get("/partner/status")
@login_required
def partner_status_page():
    app_obj = get_latest_partner_application(current_user.id)
    return render_template("partner_status.html", app_obj=app_obj)


@partner_bp.get("/partner/dashboard")
@login_required
def partner_dashboard():
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("admin.admin_page"))

    if not can_access_partner_dashboard(current_user):
        return redirect(url_for("partner.partner_status_page"))

    restaurants = get_partner_restaurants(current_user.id)
    return render_template("partner_dashboard.html", restaurants=restaurants)
