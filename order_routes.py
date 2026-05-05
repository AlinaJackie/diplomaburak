from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user, login_required
from flask import flash

from services.order_service import (
    preview_order_service,
    create_order_service,
    get_my_orders_service,
    create_review_service,
    repeat_order_service,
)

order_bp = Blueprint("order", __name__)


@order_bp.get("/checkout")
@login_required
def checkout_page():
    return render_template("checkout.html")


@order_bp.post("/api/orders/preview")
@login_required
def preview_order():
    result, status_code = preview_order_service(
        request.get_json() or {},
        current_user,
    )
    return jsonify(result), status_code


@order_bp.post("/api/orders")
@login_required
def create_order():
    result, status_code = create_order_service(
        request.get_json() or {},
        current_user,
    )
    return jsonify(result), status_code


@order_bp.get("/api/orders/my")
@login_required
def my_orders_api():
    result = get_my_orders_service(current_user)
    return jsonify(result)


@order_bp.post("/api/orders/<int:order_id>/review")
@login_required
def create_review(order_id):
    result, status_code = create_review_service(
        order_id,
        request.get_json() or {},
        current_user,
    )
    return jsonify(result), status_code


@order_bp.route("/api/orders/<int:order_id>/repeat", methods=["GET", "POST"])
@login_required
def repeat_order(order_id):
    result, status_code = repeat_order_service(order_id, current_user)

    if status_code < 400:
        flash(result.get("message") or "Кошик оновлено", "success")

        skipped = result.get("skipped_items") or []
        if isinstance(skipped, list) and skipped:
            skipped_text = ", ".join(str(x) for x in skipped if x)
            if skipped_text:
                flash(
                    f"Деякі страви недоступні і були пропущені: {skipped_text}",
                    "warning",
                )
    return jsonify(result), status_code


@order_bp.get("/api/my-orders")
@login_required
def my_orders_legacy_api():
    result = get_my_orders_service(current_user)
    return jsonify(result)


@order_bp.get("/my-orders")
@login_required
def my_orders_page():
    return render_template("my_orders.html")
