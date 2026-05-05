from flask import render_template, redirect, url_for
from flask_login import login_required

from models import Order
from . import admin_bp
from auth.access import admin_required


@admin_bp.get("")
@admin_bp.get("/")
@login_required
def admin_page():
    if not admin_required():
        return redirect(url_for("restaurant.home_page"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin.html", orders=orders)
