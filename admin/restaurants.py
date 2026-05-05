from flask import jsonify
from flask_login import login_required

from . import admin_bp
from auth.access import admin_required
from services.admin_service import get_admin_restaurants_service


@admin_bp.get("/api/restaurants")
@login_required
def admin_restaurants():
    if not admin_required():
        return jsonify({"error": "Доступ заборонено"}), 403

    return jsonify(get_admin_restaurants_service())
