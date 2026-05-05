from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user

from services.profile_service import (
    update_profile_service,
    update_password_service,
    get_profile_dashboard_service,
    get_profile_notifications_service,
    mark_notifications_read_service,
    get_profile_activity_service,
)

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.get("/")
@login_required
def profile_page():
    if getattr(current_user, "is_admin", False):
        return redirect(url_for("admin.admin_page"))
    return render_template("profile.html")


@profile_bp.patch("/api")
@login_required
def update_profile():
    result, status_code = update_profile_service(
        current_user,
        request.get_json() or {},
    )
    return jsonify(result), status_code


@profile_bp.patch("/api/password")
@login_required
def update_password():
    result, status_code = update_password_service(
        current_user,
        request.get_json() or {},
    )
    return jsonify(result), status_code


@profile_bp.get("/api/dashboard")
@login_required
def profile_dashboard():
    result, status_code = get_profile_dashboard_service(current_user)
    return jsonify(result), status_code


@profile_bp.get("/api/notifications")
@login_required
def profile_notifications():
    result, status_code = get_profile_notifications_service(current_user)
    return jsonify(result), status_code


@profile_bp.post("/api/notifications/read-all")
@login_required
def mark_notifications_read():
    result, status_code = mark_notifications_read_service(current_user)
    return jsonify(result), status_code


@profile_bp.get("/api/activity")
@login_required
def profile_activity():
    result, status_code = get_profile_activity_service(current_user)
    return jsonify(result), status_code
