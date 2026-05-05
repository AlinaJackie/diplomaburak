from flask import Blueprint

partner_panel_bp = Blueprint("partner_panel", __name__, url_prefix="/partner")

import partner_panel.restaurants
import partner_panel.menu
import partner_panel.orders
import partner_panel.analytics