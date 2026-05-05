(() => {
  const root = document.getElementById("userCabinetRoot");
  if (!root) return;

  const tabLinks = document.querySelectorAll(".user-cabinet-nav-link");
  const sections = document.querySelectorAll(".user-cabinet-section");
  const goTabButtons = document.querySelectorAll("[data-go-tab]");

  let cachedOrders = [];
  let cachedNotifications = [];

  function openTab(tabName) {
    sections.forEach((section) => {
      const isActive = section.dataset.tab === tabName;

      // фікс: цей клас ховає секції через display: none !important
      section.classList.remove("is-initially-hidden");

      section.hidden = !isActive;

      if (isActive) {
        section.style.removeProperty("display");
        section.classList.add("is-active");
      } else {
        section.style.display = "none";
        section.classList.remove("is-active");
      }
    });

    tabLinks.forEach((link) => {
      link.classList.toggle("active", link.dataset.tabLink === tabName);
    });
  }

  tabLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      openTab(link.dataset.tabLink);
    });
  });

  goTabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      openTab(btn.dataset.goTab);
    });
  });

  function setMessage(elementId, text, ok = false) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = text;
    el.style.color = ok ? "#16a34a" : "#dc2626";
  }

  async function repeatOrder(orderId) {
    try {
      const response = await apiFetch(`/api/orders/${orderId}/repeat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Не вдалося повторити замовлення"),
        );
      }

      try {
        localStorage.setItem(
          "cart",
          JSON.stringify({
            restaurant_id: Number(data.restaurant_id) || null,
            items: Array.isArray(data.items) ? data.items : [],
          }),
        );
      } catch {
        // ignore localStorage sync errors
      }

      window.location.href = `/restaurant/${data.restaurant_id}`;
    } catch (error) {
      console.error("REPEAT ORDER ERROR:", error);
      window.alert(error.message || "Не вдалося повторити замовлення");
    }
  }

  async function markAllNotificationsRead() {
    try {
      const res = await apiFetch("/profile/api/notifications/read-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || "Не вдалося оновити сповіщення");
      }

      cachedNotifications = cachedNotifications.map((item) => ({
        ...item,
        is_read: true,
      }));
      renderNotifications(cachedNotifications);
    } catch (error) {
      console.error("MARK NOTIFICATIONS READ ERROR:", error);
      window.alert(
        error.message || "Не вдалося позначити сповіщення як прочитані",
      );
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getStatusLabel(status) {
    const map = {
      new: "Нове",
      accepted: "Прийнято",
      processing: "Готується",
      delivering: "Доставляється",
      completed: "Виконано",
      cancelled: "Скасовано",
    };

    return map[String(status || "").toLowerCase()] || status || "Невідомо";
  }

  function getActiveOrdersCount(orders) {
    const activeStatuses = ["new", "accepted", "processing", "delivering"];
    return orders.filter((order) =>
      activeStatuses.includes(String(order.status || "").toLowerCase()),
    ).length;
  }

  function getTotalSpent(orders) {
    return orders.reduce(
      (sum, order) => sum + Number(order.total_price || 0),
      0,
    );
  }

  function getBonusPoints(totalSpent) {
    return Math.floor(totalSpent / 20);
  }

  function updateOverviewStatsFromDashboard(dashboard) {
    const stats = dashboard?.stats || {};
    const loyalty = dashboard?.loyalty || {};

    const totalOrdersEl = document.getElementById("cabinetTotalOrders");
    const activeOrdersEl = document.getElementById("cabinetActiveOrders");
    const totalSpentEl = document.getElementById("cabinetTotalSpent");
    const bonusPointsEl = document.getElementById("cabinetBonusPoints");

    if (totalOrdersEl) {
      totalOrdersEl.textContent = Number(stats.orders_count || 0);
    }

    if (activeOrdersEl) {
      activeOrdersEl.textContent = Number(stats.active_orders_count || 0);
    }

    if (totalSpentEl) {
      const totalSpent = cachedOrders.length
        ? getTotalSpent(cachedOrders)
        : Number(loyalty.points || 0) * 20;
      totalSpentEl.textContent = `${totalSpent} грн`;
    }

    if (bonusPointsEl) {
      bonusPointsEl.textContent = Number(loyalty.points || 0);
    }
  }

  function renderReviewsFromActivity(activity) {
    const container = document.getElementById("cabinetReviewsList");
    if (!container) return;

    const reviews = Array.isArray(activity?.reviews) ? activity.reviews : [];

    if (!reviews.length) {
      container.innerHTML = `<div class="analytics-empty">У вас ще немає відгуків.</div>`;
      return;
    }

    container.innerHTML = reviews
      .map(
        (review) => `
      <div class="analytics-list-item analytics-list-item--stack">
        <span>
          <strong>${escapeHtml(review.restaurant_name || "Ресторан")}</strong><br>
          Замовлення #${review.order_id || "—"}<br>
          Оцінка: ${review.rating}/5
        </span>
        <strong>${escapeHtml(review.created_at || "")}</strong>
      </div>
      <div class="review-view-box review-view-box--outside">
        ${escapeHtml(review.comment || "Без коментаря")}
      </div>
    `,
      )
      .join("");

    const favRestaurantsEl = document.getElementById(
      "cabinetFavoriteRestaurantsCount",
    );
    const favItemsEl = document.getElementById("cabinetFavoriteItemsCount");
    const reviewsCountEl = document.getElementById("cabinetReviewsCountBig");

    if (favRestaurantsEl && Array.isArray(activity?.favorite_restaurants)) {
      favRestaurantsEl.textContent = activity.favorite_restaurants.length;
    }

    if (favItemsEl && Array.isArray(activity?.favorite_menu_items)) {
      favItemsEl.textContent = activity.favorite_menu_items.length;
    }

    if (reviewsCountEl) {
      reviewsCountEl.textContent = reviews.length;
    }
  }

  function renderFavoriteRestaurantsFromActivity(activity) {
    const container = document.getElementById("cabinetFavoriteRestaurantsList");
    if (!container) return;

    const favorites = Array.isArray(activity?.favorite_restaurants)
      ? activity.favorite_restaurants
      : [];

    if (!favorites.length) {
      container.innerHTML = `<div class="analytics-empty">У вас ще немає улюблених ресторанів.</div>`;
      return;
    }

    container.innerHTML = favorites
      .map(
        (restaurant) => `
      <div class="analytics-list-item" data-favorite-row>
        <span>
          <strong>${escapeHtml(restaurant.name || "Ресторан")}</strong><br>
          <span class="order-user-meta">${escapeHtml(restaurant.city || "")}${restaurant.rating != null ? ` · ${Number(restaurant.rating)}★` : ""}</span>
        </span>
        <span class="user-cabinet-section-header-actions">
          <a class="btn btn-outline btn-sm" href="/restaurant/${Number(restaurant.id)}">Відкрити</a>
          <a
            href="/restaurant/${Number(restaurant.id)}/favorite?next=${encodeURIComponent(window.location.pathname + window.location.search)}"
            class="favorite-btn favorite-btn--inline"
            role="button"
            data-restaurant-id="${Number(restaurant.id)}"
            aria-pressed="true"
            aria-label="Remove from favorites"
            data-remove-on-unfavorite="true"
          ></a>
        </span>
      </div>
    `,
      )
      .join("");
  }

  function syncAddressPreview() {
    const city =
      document.getElementById("addressCity")?.value.trim() || "Не вказано";
    const street =
      document.getElementById("addressStreet")?.value.trim() || "Не вказано";
    const house =
      document.getElementById("addressHouse")?.value.trim() || "Не вказано";
    const extra =
      document.getElementById("addressExtraInfo")?.value.trim() || "Немає";

    const previewCity = document.getElementById("addressPreviewCity");
    const previewStreet = document.getElementById("addressPreviewStreet");
    const previewHouse = document.getElementById("addressPreviewHouse");
    const previewExtra = document.getElementById("addressPreviewExtra");

    if (previewCity) previewCity.textContent = city;
    if (previewStreet) previewStreet.textContent = street;
    if (previewHouse) previewHouse.textContent = house;
    if (previewExtra) previewExtra.textContent = extra;
  }

  async function saveProfileData(payload, resultElementId) {
    try {
      const res = await apiFetch("/profile/api", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(
          resultElementId,
          data.error || "Не вдалося оновити дані",
          false,
        );
        return false;
      }

      setMessage(resultElementId, data.message || "Дані оновлено", true);
      return true;
    } catch (error) {
      console.error(error);
      setMessage(resultElementId, "Сталася помилка", false);
      return false;
    }
  }

  const saveProfileBtn = document.getElementById("saveProfileBtn");
  const saveAddressBtn = document.getElementById("saveAddressBtn");
  const changePasswordBtn = document.getElementById("changePasswordBtn");
  const markNotificationsReadBtn = document.getElementById(
    "markNotificationsReadBtn",
  );

  if (saveProfileBtn) {
    saveProfileBtn.addEventListener("click", async () => {
      const full_name =
        document.getElementById("profileFullName")?.value.trim() || "";
      const city = document.getElementById("profileCity")?.value.trim() || "";
      const street =
        document.getElementById("profileStreet")?.value.trim() || "";
      const house = document.getElementById("profileHouse")?.value.trim() || "";
      const extra_info =
        document.getElementById("profileExtraInfo")?.value.trim() || "";

      const ok = await saveProfileData(
        { full_name, city, street, house, extra_info },
        "profileSaveResult",
      );

      if (!ok) return;

      const addressCity = document.getElementById("addressCity");
      const addressStreet = document.getElementById("addressStreet");
      const addressHouse = document.getElementById("addressHouse");
      const addressExtraInfo = document.getElementById("addressExtraInfo");

      if (addressCity) addressCity.value = city;
      if (addressStreet) addressStreet.value = street;
      if (addressHouse) addressHouse.value = house;
      if (addressExtraInfo) addressExtraInfo.value = extra_info;

      syncAddressPreview();
    });
  }

  if (saveAddressBtn) {
    saveAddressBtn.addEventListener("click", async () => {
      const full_name =
        document.getElementById("profileFullName")?.value.trim() || "";
      const city = document.getElementById("addressCity")?.value.trim() || "";
      const street =
        document.getElementById("addressStreet")?.value.trim() || "";
      const house = document.getElementById("addressHouse")?.value.trim() || "";
      const extra_info =
        document.getElementById("addressExtraInfo")?.value.trim() || "";

      const ok = await saveProfileData(
        { full_name, city, street, house, extra_info },
        "addressSaveResult",
      );

      if (!ok) return;

      const profileCity = document.getElementById("profileCity");
      const profileStreet = document.getElementById("profileStreet");
      const profileHouse = document.getElementById("profileHouse");
      const profileExtraInfo = document.getElementById("profileExtraInfo");

      if (profileCity) profileCity.value = city;
      if (profileStreet) profileStreet.value = street;
      if (profileHouse) profileHouse.value = house;
      if (profileExtraInfo) profileExtraInfo.value = extra_info;

      syncAddressPreview();
    });
  }

  if (changePasswordBtn) {
    changePasswordBtn.addEventListener("click", async () => {
      const current_password =
        document.getElementById("currentPassword")?.value || "";
      const new_password = document.getElementById("newPassword")?.value || "";

      try {
        const res = await apiFetch("/profile/api/password", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ current_password, new_password }),
        });

        const data = await res.json();

        if (!res.ok) {
          setMessage(
            "passwordSaveResult",
            data.error || "Не вдалося змінити пароль",
            false,
          );
          return;
        }

        setMessage(
          "passwordSaveResult",
          data.message || "Пароль змінено",
          true,
        );

        const currentPasswordEl = document.getElementById("currentPassword");
        const newPasswordEl = document.getElementById("newPassword");

        if (currentPasswordEl) currentPasswordEl.value = "";
        if (newPasswordEl) newPasswordEl.value = "";
      } catch (error) {
        console.error(error);
        setMessage("passwordSaveResult", "Сталася помилка", false);
      }
    });
  }

  if (markNotificationsReadBtn) {
    markNotificationsReadBtn.addEventListener("click", async () => {
      await markAllNotificationsRead();
    });
  }

  function renderOrders(orders) {
    const container = document.getElementById("my-orders-list");
    if (!container) return;

    if (!orders.length) {
      container.innerHTML = `<div class="analytics-empty">У вас поки немає замовлень.</div>`;
      return;
    }

    container.innerHTML = orders
      .map((order) => {
        const itemsHtml = (order.items || [])
          .map(
            (item) => `
      <div class="order-user-item-row">
        <span>${escapeHtml(item.name)} × ${item.quantity}</span>
        <strong>${item.line_total} грн</strong>
      </div>
    `,
          )
          .join("");

        const historyHtml = (order.status_history || [])
          .map(
            (step) => `
      <div class="order-history-step">
        <div class="order-history-step-top">
          <strong>${escapeHtml(getStatusLabel(step.status))}</strong>
          <span>${escapeHtml(step.created_at || "")}</span>
        </div>
        ${step.note ? `<div class="order-history-step-note">${escapeHtml(step.note)}</div>` : ""}
      </div>
    `,
          )
          .join("");

        let reviewBlock = "";
        if (order.review) {
          reviewBlock = `
        <div class="order-review-box">
          <div class="order-user-section-title">Ваш відгук</div>
          <div class="review-view-box">
            <div><strong>Оцінка:</strong> ${order.review.rating}/5</div>
            <div>${escapeHtml(order.review.comment || "Без коментаря")}</div>
            <div class="order-user-meta">${escapeHtml(order.review.created_at || "")}</div>
          </div>
        </div>
      `;
        } else if (order.can_review) {
          reviewBlock = `
        <div class="order-review-box">
          <div class="order-user-section-title">Залишити відгук</div>

          <select class="review-input" data-review-rating="${order.id}">
            <option value="5">5 — Відмінно</option>
            <option value="4">4 — Добре</option>
            <option value="3">3 — Нормально</option>
            <option value="2">2 — Погано</option>
            <option value="1">1 — Дуже погано</option>
          </select>

          <textarea class="review-input" data-review-comment="${order.id}" placeholder="Ваш коментар"></textarea>

          <div class="order-user-actions">
            <button class="btn btn-outline" type="button" data-submit-review="${order.id}">
              Надіслати відгук
            </button>
          </div>

          <p class="form-result" id="reviewResult-${order.id}"></p>
        </div>
      `;
        }

        const deliveryLabel =
          order.delivery_type === "pickup" ? "Самовивіз" : "Доставка";

        const addressLabel =
          order.delivery_type === "pickup"
            ? "Самовивіз із закладу"
            : `${escapeHtml(order.city || "—")}, ${escapeHtml(order.address || "—")}`;

        return `
      <div class="order-user-card">
        <div class="order-user-top">
          <div>
            <div class="order-user-title">Замовлення #${order.id}</div>
            <div class="order-user-meta">
              ${escapeHtml(order.restaurant || "Ресторан")} • ${escapeHtml(order.created_at || "")}
            </div>
          </div>

          <span class="order-status order-status--${escapeHtml(String(order.status || "new").toLowerCase())}">
            ${escapeHtml(getStatusLabel(order.status))}
          </span>
        </div>

        <div class="order-user-info">
          <div><strong>Спосіб отримання:</strong> ${deliveryLabel}</div>
          <div><strong>Адреса / отримання:</strong> ${addressLabel}</div>
          <div><strong>ETA:</strong> ${order.eta_minutes ? `${order.eta_minutes} хв` : "—"}</div>
          <div><strong>Сума страв:</strong> ${order.items_total || 0} грн</div>
          <div><strong>Доставка:</strong> ${order.delivery_fee || 0} грн</div>
        </div>

        <div class="order-user-items">
          <div class="order-user-section-title">Склад замовлення</div>
          ${itemsHtml || `<div class="analytics-empty">Позиції відсутні.</div>`}
        </div>

        <div class="order-user-summary">
          <div class="order-user-summary-row order-user-summary-row--total">
            <span>До сплати</span>
            <strong>${order.total_price || 0} грн</strong>
          </div>
        </div>

        <div class="order-user-actions">
          <button class="btn btn-outline" type="button" data-repeat-order="${order.id}">
            Повторити замовлення
          </button>
        </div>

        <div class="order-review-box">
          <div class="order-user-section-title">Історія статусів</div>
          ${historyHtml || `<div class="analytics-empty">Історія статусів відсутня.</div>`}
        </div>

        ${reviewBlock}
      </div>
    `;
      })
      .join("");

    document.querySelectorAll("[data-repeat-order]").forEach((button) => {
      button.addEventListener("click", () => {
        repeatOrder(button.dataset.repeatOrder);
      });
    });

    bindReviewActions();
  }

  function renderRecentOrders(orders) {
    const container = document.getElementById("cabinetRecentOrders");
    if (!container) return;
    const recent = orders.slice(0, 3);
    if (!recent.length) {
      container.innerHTML =
        '<div class="analytics-empty">У вас ще немає замовлень.</div>';
      return;
    }
    container.innerHTML = recent
      .map((order) => {
        return (
          '<div class="analytics-list-item analytics-list-item--stack">' +
          "<span><strong>Замовлення #" +
          order.id +
          "</strong><br>" +
          (order.restaurant || "Ресторан") +
          "</span>" +
          "<strong>" +
          (order.total_price || 0) +
          " грн</strong></div>"
        );
      })
      .join("");
  }

  function renderReviews(orders) {
    const container = document.getElementById("cabinetReviewsList");
    if (!container) return;

    const reviews = orders
      .filter((order) => order.review)
      .map((order) => ({
        orderId: order.id,
        restaurant: order.restaurant,
        review: order.review,
      }));

    if (!reviews.length) {
      container.innerHTML = `<div class="analytics-empty">У вас ще немає відгуків.</div>`;
      return;
    }

    container.innerHTML = reviews
      .map(
        (item) => `
      <div class="analytics-list-item analytics-list-item--stack">
        <span>
          <strong>${escapeHtml(item.restaurant || "Ресторан")}</strong><br>
          Замовлення #${item.orderId}<br>
          Оцінка: ${item.review.rating}/5
        </span>
        <strong>${escapeHtml(item.review.created_at || "")}</strong>
      </div>
      <div class="review-view-box review-view-box--outside">
        ${escapeHtml(item.review.comment || "Без коментаря")}
      </div>
    `,
      )
      .join("");
  }

  function renderNotifications(notifications) {
    const container = document.getElementById("cabinetNotificationsList");
    const unreadEl = document.getElementById("cabinetUnreadNotifications");

    if (!container) return;

    const unreadCount = notifications.filter((n) => !n.is_read).length;
    if (unreadEl) unreadEl.textContent = unreadCount;

    if (!notifications.length) {
      container.innerHTML = `<div class="analytics-empty">Сповіщень поки немає.</div>`;
      return;
    }

    container.innerHTML = notifications
      .map(
        (item) => `
      <div class="analytics-list-item analytics-list-item--stack">
        <span>${escapeHtml(item.message || "")}</span>
        <strong>${escapeHtml(item.created_at || "")}</strong>
      </div>
    `,
      )
      .join("");
  }

  function updateOverviewStats(orders) {
    const totalOrders = orders.length;
    const activeOrders = getActiveOrdersCount(orders);
    const totalSpent = getTotalSpent(orders);
    const bonusPoints = getBonusPoints(totalSpent);

    const totalOrdersEl = document.getElementById("cabinetTotalOrders");
    const activeOrdersEl = document.getElementById("cabinetActiveOrders");
    const totalSpentEl = document.getElementById("cabinetTotalSpent");
    const bonusPointsEl = document.getElementById("cabinetBonusPoints");

    if (totalOrdersEl) totalOrdersEl.textContent = totalOrders;
    if (activeOrdersEl) activeOrdersEl.textContent = activeOrders;
    if (totalSpentEl) totalSpentEl.textContent = `${totalSpent} грн`;
    if (bonusPointsEl) bonusPointsEl.textContent = bonusPoints;
  }

  async function loadDashboard() {
    try {
      const res = await apiFetch("/profile/api/dashboard");
      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data?.error || "Не вдалося завантажити огляд кабінету.",
        );
      }

      updateOverviewStatsFromDashboard(data);

      if (
        Array.isArray(data?.recent_notifications) &&
        data.recent_notifications.length &&
        !cachedNotifications.length
      ) {
        cachedNotifications = data.recent_notifications;
        renderNotifications(cachedNotifications);
      }
    } catch (error) {
      console.error("LOAD DASHBOARD ERROR:", error);
      updateOverviewStats(cachedOrders);
    }
  }

  async function loadOrders() {
    try {
      const res = await apiFetch("/api/orders/my");
      const data = await res.json();
      cachedOrders = Array.isArray(data) ? data : [];

      renderRecentOrders(cachedOrders);
      renderOrders(cachedOrders);
      renderReviews(cachedOrders);
      updateOverviewStats(cachedOrders);
    } catch (error) {
      console.error("LOAD ORDERS ERROR:", error);

      const ordersContainer = document.getElementById("my-orders-list");
      const reviewsContainer = document.getElementById("cabinetReviewsList");
      const recentContainer = document.getElementById("cabinetRecentOrders");

      if (ordersContainer) {
        ordersContainer.innerHTML = `<div class="analytics-empty">Не вдалося завантажити замовлення.</div>`;
      }
      if (reviewsContainer) {
        reviewsContainer.innerHTML = `<div class="analytics-empty">Не вдалося завантажити відгуки.</div>`;
      }
      if (recentContainer) {
        recentContainer.innerHTML = `<div class="analytics-empty">Не вдалося завантажити замовлення.</div>`;
      }
    }
  }

  async function loadActivity() {
    try {
      const res = await apiFetch("/profile/api/activity");
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.error || "Не вдалося завантажити активність.");
      }

      renderFavoriteRestaurantsFromActivity(data);
      renderReviewsFromActivity(data);
    } catch (error) {
      console.error("LOAD ACTIVITY ERROR:", error);
      renderReviews(cachedOrders);
    }
  }

  async function loadNotifications() {
    try {
      const res = await apiFetch("/profile/api/notifications");
      const data = await res.json();
      cachedNotifications = Array.isArray(data) ? data : [];
      renderNotifications(cachedNotifications);
    } catch (error) {
      console.error("LOAD NOTIFICATIONS ERROR:", error);
      const container = document.getElementById("cabinetNotificationsList");
      if (container) {
        container.innerHTML = `<div class="analytics-empty">Не вдалося завантажити сповіщення.</div>`;
      }
    }
  }

  async function submitReview(orderId) {
    const ratingEl = document.querySelector(
      `[data-review-rating="${orderId}"]`,
    );
    const commentEl = document.querySelector(
      `[data-review-comment="${orderId}"]`,
    );
    const resultElId = `reviewResult-${orderId}`;

    const rating = ratingEl?.value;
    const comment = commentEl?.value.trim() || "";

    try {
      const res = await apiFetch(`/api/orders/${orderId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, comment }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(resultElId, data.error || "Не вдалося додати відгук", false);
        return;
      }

      setMessage(resultElId, data.message || "Відгук додано", true);
      await loadOrders();
    } catch (error) {
      console.error("SUBMIT REVIEW ERROR:", error);
      setMessage(resultElId, "Сталася помилка", false);
    }
  }

  function bindReviewActions() {
    document.querySelectorAll("[data-submit-review]").forEach((button) => {
      button.addEventListener("click", () => {
        submitReview(button.dataset.submitReview);
      });
    });
  }

  syncAddressPreview();
  openTab("overview");

  (async () => {
    await loadOrders();
    await loadDashboard();
    await loadActivity();
    await loadNotifications();
  })();
})();
