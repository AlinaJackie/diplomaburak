from flask import jsonify
from flask_login import login_required

from . import admin_bp
from auth.access import admin_required
from services.admin_service import get_admin_analytics_service


@admin_bp.get("/api/analytics")
@login_required
def admin_analytics():
    if not admin_required():
        return jsonify({"error": "Доступ заборонено"}), 403

    result = get_admin_analytics_service()
    return jsonify(result)
