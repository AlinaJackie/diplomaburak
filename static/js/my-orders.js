(() => {
  const myOrdersList = document.getElementById("my-orders-list");
  if (!myOrdersList) return;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function statusText(status) {
    const map = {
      pending: "Очікує підтвердження",
      new: "Нове",
      accepted: "Прийнято",
      processing: "Готується",
      delivering: "Доставляється",
      completed: "Завершено",
      cancelled: "Скасовано",
      rejected: "Відхилено",
    };
    return map[status] || status || "—";
  }

  function paymentMethodText(method) {
    const map = {
      cash: "Готівка",
      card_on_delivery: "Карткою при отриманні",
    };
    return map[method] || method || "—";
  }

  function deliveryTypeText(type) {
    const map = {
      delivery: "Доставка",
      pickup: "Самовивіз",
    };
    return map[type] || type || "—";
  }

  function formatOrderAddress(order) {
    if (!order || order.delivery_type === "pickup") {
      return "Самовивіз із закладу";
    }

    const parts = [order.city, order.address].filter(Boolean);
    return parts.length ? parts.join(", ") : "—";
  }

  function canRepeat(status) {
    const activeStatuses = new Set([
      "new",
      "accepted",
      "processing",
      "delivering",
    ]);
    return status && !activeStatuses.has(String(status));
  }

  async function isCartNotEmpty() {
    try {
      const res = await apiFetch("/api/cart");
      const data = await readApiResponse(res);
      if (!res.ok) return false;
      const items = Array.isArray(data?.items) ? data.items : [];
      return items.length > 0;
    } catch {
      return false;
    }
  }

  async function repeatOrder(orderId) {
    const cartNotEmpty = await isCartNotEmpty();
    if (cartNotEmpty) {
      const ok = confirm(
        "Ваш кошик не порожній. Очистити його та додати страви з цього замовлення?",
      );
      if (!ok) return;
    }

    const response = await apiFetch(`/api/orders/${orderId}/repeat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await readApiResponse(response);

    if (!response.ok) {
      alert(getErrorMessage(data, "Не вдалося повторити замовлення"));
      return;
    }

    try {
      localStorage.removeItem("cart");
    } catch {
      // ignore localStorage sync errors
    }

    window.location.href = "/checkout";
  }

  async function submitReview(orderId) {
    const ratingEl = document.getElementById(`review-rating-${orderId}`);
    const commentEl = document.getElementById(`review-comment-${orderId}`);

    const response = await apiFetch(`/api/orders/${orderId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rating: ratingEl?.value,
        comment: commentEl?.value || "",
      }),
    });

    const data = await readApiResponse(response);

    if (!response.ok) {
      alert(getErrorMessage(data, "Не вдалося зберегти відгук"));
      return;
    }

    await loadMyOrders();
  }

  async function loadMyOrders() {
    try {
      const response = await apiFetch("/api/orders/my");
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Не вдалося завантажити замовлення"),
        );
      }

      const orders = Array.isArray(data) ? data : [];

      if (!orders.length) {
        myOrdersList.innerHTML =
          '<div class="empty-state"><h3>У вас ще немає замовлень.</h3></div>';
        return;
      }

      myOrdersList.innerHTML = orders
        .map(
          (order) => `
        <article class="order-user-card">
          <div class="order-user-top">
            <div>
              <div class="order-user-title">Замовлення #${Number(order.id) || 0}</div>
              <div class="order-user-meta">${escapeHtml(order.created_at || "—")}</div>
            </div>
            <span class="status-badge order-status order-status--${escapeHtml(order.status || "pending")}">
              ${escapeHtml(statusText(order.status))}
            </span>
          </div>

          <div class="order-user-info">
            <div><strong>Ресторан:</strong> ${escapeHtml(order.restaurant || "—")}</div>
            <div><strong>Тип:</strong> ${escapeHtml(deliveryTypeText(order.delivery_type))}</div>
            <div><strong>Адреса:</strong> ${escapeHtml(formatOrderAddress(order))}</div>
            <div><strong>Оплата:</strong> ${escapeHtml(paymentMethodText(order.payment_method))}</div>
          </div>

          <div class="order-user-items">
            <div class="order-user-section-title">Склад замовлення</div>
            ${(order.items || [])
              .map(
                (item) => `
              <div class="order-user-item-row">
                <span>${escapeHtml(item.name || "—")} × ${Number(item.quantity) || 0}</span>
                <strong>${Number(item.line_total) || 0} грн</strong>
              </div>
            `,
              )
              .join("")}
          </div>

          <div class="order-user-summary">
            <div class="order-user-summary-row">
              <span>Сума страв</span>
              <strong>${order.items_total ?? 0} грн</strong>
            </div>
            <div class="order-user-summary-row">
              <span>Вартість доставки</span>
              <strong>${order.delivery_fee ?? 0} грн</strong>
            </div>
            <div class="order-user-summary-row order-user-summary-row--total">
              <span>Разом до сплати</span>
              <strong>${order.total_price ?? 0} грн</strong>
            </div>
          </div>

          <div class="order-user-actions" style="${canRepeat(order.status) ? "" : "display:none;"}">
            <button class="btn btn-outline" onclick="repeatOrder(${order.id})">
              Повторити замовлення
            </button>
          </div>

          ${
            order.review
              ? `
                <div class="order-review-box">
                  <div class="order-user-section-title">Ваш відгук</div>
                  <div><strong>Оцінка:</strong> ${order.review.rating}/5</div>
                  <div><strong>Коментар:</strong> ${escapeHtml(order.review.comment || "—")}</div>
                </div>
              `
              : order.can_review
                ? `
                  <div class="order-review-box">
                    <div class="order-user-section-title">Залишити відгук</div>
                    <select id="review-rating-${order.id}" class="review-input">
                      <option value="">Оберіть оцінку</option>
                      <option value="5">5</option>
                      <option value="4">4</option>
                      <option value="3">3</option>
                      <option value="2">2</option>
                      <option value="1">1</option>
                    </select>
                    <textarea id="review-comment-${order.id}" class="review-input" placeholder="Напишіть короткий відгук"></textarea>
                    <button class="btn btn-primary" onclick="submitReview(${order.id})">
                      Надіслати відгук
                    </button>
                  </div>
                `
                : ""
          }
        </article>
      `,
        )
        .join("");
    } catch (error) {
      console.error(error);
      myOrdersList.innerHTML =
        "<p>Сталася помилка при завантаженні замовлень.</p>";
    }
  }

  window.repeatOrder = repeatOrder;
  window.submitReview = submitReview;

  document.addEventListener("DOMContentLoaded", loadMyOrders);
})();
