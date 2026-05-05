from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

import admin.pages
import admin.partner_applications
import admin.analytics
import admin.orders
import admin.restaurants
