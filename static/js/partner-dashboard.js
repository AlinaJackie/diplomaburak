(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const restaurantsGrid = document.getElementById("restaurantsGrid");
    if (!restaurantsGrid) return;

    const restaurantsEmpty = document.getElementById("restaurantsEmpty");
    const menuRestaurantSelect = document.getElementById(
      "menuRestaurantSelect",
    );
    const menuList = document.getElementById("menuList");
    const menuEmpty = document.getElementById("menuEmpty");
    const ordersTableBody = document.getElementById("ordersTableBody");
    const ordersEmpty = document.getElementById("ordersEmpty");

    const restaurantForm = document.getElementById("restaurantForm");
    const dishForm = document.getElementById("dishForm");

    const restaurantModal = document.getElementById("restaurantModal");
    const dishModal = document.getElementById("dishModal");

    const openRestaurantModalBtn = document.getElementById(
      "openRestaurantModalBtn",
    );
    const openDishModalBtn = document.getElementById("openDishModalBtn");
    const openRestaurantModalBtnSecondary = document.getElementById(
      "openRestaurantModalBtnSecondary",
    );

    const restaurantsCount = document.getElementById("restaurantsCount");
    const menuItemsCount = document.getElementById("menuItemsCount");
    const activeOrdersCount = document.getElementById("activeOrdersCount");
    const completedOrdersCount = document.getElementById(
      "completedOrdersCount",
    );

    const ordersTodayCount = document.getElementById("ordersTodayCount");
    const ordersWeekCount = document.getElementById("ordersWeekCount");
    const totalRevenueCount = document.getElementById("totalRevenueCount");
    const averageCheckCount = document.getElementById("averageCheckCount");
    const topDishesList = document.getElementById("topDishesList");

    let restaurants = [];
    let orders = [];
    let selectedRestaurantId = "";
    let currentMenuItems = [];

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }
    function sanitizeUrl(value) {
      const raw = String(value ?? "").trim();

      if (!raw) {
        return "";
      }

      if (
        raw.startsWith("/") ||
        raw.startsWith("./") ||
        raw.startsWith("../")
      ) {
        return raw;
      }

      try {
        const url = new URL(raw, window.location.origin);
        if (url.protocol === "http:" || url.protocol === "https:") {
          return url.toString();
        }
      } catch {
        return "";
      }

      return "";
    }
    function mapCategoryName(category) {
      const map = {
        fastfood: "Фаст-фуд",
        burgers: "Бургери",
        ukrainian: "Українська",
        breakfast: "Сніданки",
        pizza: "Піца",
        sushi: "Суші",
        shawarma: "Шаурма",
        healthy: "Корисна їжа",
        grill: "Гриль",
        homemade: "По-домашньому",
      };
      return map[category] || category || "—";
    }

    function parseCategories(categories) {
      if (!categories) return [];
      if (Array.isArray(categories)) return categories;
      return String(categories)
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    }

    function mapDeliveryType(type) {
      const map = {
        delivery: "Доставка",
        pickup: "Самовивіз",
      };
      return map[type] || type || "—";
    }

    function mapPaymentMethod(method) {
      const map = {
        cash: "Готівка",
        card_on_delivery: "Карткою при отриманні",
      };
      return map[method] || method || "—";
    }

    function mapOrderStatus(status) {
      const map = {
        new: "Нове",
        accepted: "Прийнято",
        processing: "Готується",
        delivering: "Доставляється",
        completed: "Виконано",
        cancelled: "Скасовано",
      };
      return map[String(status || "").toLowerCase()] || status || "—";
    }

    function formatOrderAddress(order) {
      if (!order || order.delivery_type === "pickup") {
        return "Самовивіз із закладу";
      }

      const parts = [order.city, order.address].filter(Boolean);
      return parts.length ? parts.join(", ") : "—";
    }

    async function apiFetch(url, options = {}) {
      const response = await window.apiFetch(url, options);
      const data = await window.readApiResponse(response);

      if (!response.ok) {
        throw new Error(window.getErrorMessage(data));
      }

      return data;
    }

    function openModal(modal) {
      if (modal) modal.classList.remove("hidden");
    }

    function closeModal(modal) {
      if (modal) modal.classList.add("hidden");
    }

    function switchPartnerTab(tabName) {
      document.querySelectorAll(".partner-side-link").forEach((tab) => {
        tab.classList.toggle("active", tab.dataset.partnerTab === tabName);
      });

      document.querySelectorAll(".partner-panel").forEach((content) => {
        content.classList.remove("active");
      });

      const target = document.getElementById(`partner-tab-${tabName}`);
      if (target) {
        target.classList.add("active");
      }
    }

    function updateStats() {
      if (restaurantsCount) {
        restaurantsCount.textContent = restaurants.length;
      }

      const active = orders.filter((order) =>
        ["new", "accepted", "processing", "delivering"].includes(order.status),
      ).length;

      const completed = orders.filter(
        (order) => order.status === "completed",
      ).length;

      if (activeOrdersCount) {
        activeOrdersCount.textContent = active;
      }

      if (completedOrdersCount) {
        completedOrdersCount.textContent = completed;
      }
    }

    async function calculateMenuStats() {
      try {
        const responses = await Promise.all(
          restaurants.map((restaurant) =>
            apiFetch(`/partner/api/restaurants/${restaurant.id}/menu`).catch(
              () => [],
            ),
          ),
        );

        const total = responses.reduce(
          (sum, items) => sum + (Array.isArray(items) ? items.length : 0),
          0,
        );

        if (menuItemsCount) {
          menuItemsCount.textContent = total;
        }
      } catch {
        if (menuItemsCount) {
          menuItemsCount.textContent = "0";
        }
      }
    }

    async function loadPartnerAnalytics() {
      if (
        !ordersTodayCount &&
        !ordersWeekCount &&
        !totalRevenueCount &&
        !averageCheckCount &&
        !topDishesList
      ) {
        return;
      }

      try {
        const data = await apiFetch("/partner/api/analytics");

        if (ordersTodayCount) {
          ordersTodayCount.textContent = data.orders_today ?? 0;
        }

        if (ordersWeekCount) {
          ordersWeekCount.textContent = data.orders_week ?? 0;
        }

        if (totalRevenueCount) {
          totalRevenueCount.textContent = `${data.total_revenue ?? 0} грн`;
        }

        if (averageCheckCount) {
          averageCheckCount.textContent = `${Math.round(data.average_check ?? 0)} грн`;
        }

        if (topDishesList) {
          if (!data.top_dishes || !data.top_dishes.length) {
            topDishesList.innerHTML =
              '<div class="partner-empty">Поки що немає даних по стравах.</div>';
          } else {
            topDishesList.innerHTML = data.top_dishes
              .map(
                (dish, index) => `
                  <div class="analytics-list-item">
                    <span>${index + 1}. ${escapeHtml(dish.name)}</span>
                    <strong>${dish.total_qty} шт.</strong>
                  </div>
                `,
              )
              .join("");
          }
        }
      } catch (error) {
        console.error(error);

        if (topDishesList) {
          topDishesList.innerHTML =
            '<div class="partner-empty">Не вдалося завантажити аналітику.</div>';
        }
      }
    }

    function fillRestaurantSelect() {
      if (!menuRestaurantSelect) return;

      const previousValue = String(
        selectedRestaurantId || menuRestaurantSelect.value || "",
      );

      menuRestaurantSelect.innerHTML =
        '<option value="">Оберіть ресторан</option>';

      restaurants.forEach((restaurant) => {
        const option = document.createElement("option");
        option.value = String(restaurant.id);
        option.textContent = restaurant.name;
        menuRestaurantSelect.appendChild(option);
      });

      let nextSelected = "";

      if (
        previousValue &&
        restaurants.some(
          (restaurant) => String(restaurant.id) === previousValue,
        )
      ) {
        nextSelected = previousValue;
      } else if (restaurants.length) {
        nextSelected = String(restaurants[0].id);
      }

      selectedRestaurantId = nextSelected;
      menuRestaurantSelect.value = nextSelected;

      if (openDishModalBtn) {
        openDishModalBtn.disabled = !nextSelected;
      }
    }

    function renderRestaurants() {
      if (!restaurantsGrid) return;

      if (!restaurants.length) {
        restaurantsGrid.innerHTML = "";
        if (restaurantsEmpty) restaurantsEmpty.style.display = "block";
        return;
      }

      if (restaurantsEmpty) restaurantsEmpty.style.display = "none";

      restaurantsGrid.innerHTML = restaurants
        .map(
          (restaurant) => `
            <div class="partner-card">
              <div class="partner-card__top">
                <div>
                  <h3>${escapeHtml(restaurant.name || "Без назви")}</h3>
                  <div class="partner-card__meta">
                    ${escapeHtml(restaurant.city || "—")} ·
                    ${
                      Array.isArray(restaurant.categories)
                        ? restaurant.categories.map(mapCategoryName).join(", ")
                        : "—"
                    }
                  </div>
                </div>
                <div class="partner-card__badges">
                  <span class="partner-badge ${
                    restaurant.is_active
                      ? "partner-badge--ok"
                      : "partner-badge--muted"
                  }">
                    ${restaurant.is_active ? "Активний" : "Неактивний"}
                  </span>
                  <span class="partner-badge">
                    Мін. замовлення: ${restaurant.minimum_order_amount ?? 0} грн
                  </span>
                </div>
              </div>

              ${
                sanitizeUrl(restaurant.image_url)
                  ? `<img class="partner-card__image" src="${sanitizeUrl(restaurant.image_url)}" alt="${escapeHtml(restaurant.name || "Restaurant")}">`
                  : ""
              }

              <div class="partner-card__meta partner-card__schedule">
                Години роботи: ${escapeHtml(restaurant.opening_time || "09:00")}–${escapeHtml(restaurant.closing_time || "22:00")}
              </div>

              <div class="partner-card__description">
                ${escapeHtml(restaurant.description || "Опис відсутній")}
              </div>

              <div class="partner-card__actions">
                <button type="button" class="btn btn-outline" onclick="editRestaurant(${restaurant.id})">
                  Редагувати
                </button>
                <button type="button" class="btn btn-outline" onclick="deleteRestaurant(${restaurant.id})">
                  Видалити
                </button>
              </div>
            </div>
          `,
        )
        .join("");
    }

    function renderMenu(items) {
      currentMenuItems = Array.isArray(items) ? items : [];

      if (!menuList) return;

      if (!currentMenuItems.length) {
        menuList.innerHTML = "";
        if (menuEmpty) menuEmpty.style.display = "block";
        return;
      }

      if (menuEmpty) menuEmpty.style.display = "none";

      menuList.innerHTML = currentMenuItems
        .map(
          (item) => `
            <div class="partner-card">
              <div class="partner-card__top">
                <div>
                  <h3>${escapeHtml(item.name || "Без назви")}</h3>
                  <div class="partner-card__meta">
                    ${escapeHtml(item.weight || "—")} · ${item.price ?? 0} грн
                  </div>
                </div>
                <div class="partner-card__badges">
                  <span class="partner-badge ${
                    item.is_available
                      ? "partner-badge--ok"
                      : "partner-badge--muted"
                  }">
                    ${item.is_available ? "Доступна" : "Недоступна"}
                  </span>
                </div>
              </div>

              ${
                sanitizeUrl(item.image_url)
                  ? `<img class="partner-card__image" src="${sanitizeUrl(item.image_url)}" alt="${escapeHtml(item.name || "Dish")}">`
                  : ""
              }

              <div class="partner-card__description">
                ${escapeHtml(item.description || "Опис відсутній")}
              </div>

              <div class="partner-card__actions">
                <button type="button" class="btn btn-outline" onclick="editDish(${item.id})">
                  Редагувати
                </button>
                <button type="button" class="btn btn-outline" onclick="deleteMenuItem(${item.id})">
                  Видалити
                </button>
              </div>
            </div>
          `,
        )
        .join("");
    }

    function buildOrderStatusOptions(order) {
      const statusSequence = [
        ["new", "Нове"],
        ["accepted", "Прийнято"],
        ["processing", "Готується"],
        ["delivering", "Доставляється"],
        ["completed", "Виконано"],
        ["cancelled", "Скасовано"],
      ];
      const currentStatus = String(order.status || "new").toLowerCase();
      const allowedNextStatuses = Array.isArray(order.allowed_next_statuses)
        ? order.allowed_next_statuses.map((item) =>
            String(item || "").toLowerCase(),
          )
        : [];

      return statusSequence
        .map(([value, label]) => {
          const isCurrent = value === currentStatus;
          const isAllowed = allowedNextStatuses.includes(value);
          const isEnabled = isCurrent || isAllowed;

          return `<option value="${value}" ${isCurrent ? "selected" : ""} ${isEnabled ? "" : "disabled"}>${label}</option>`;
        })
        .join("");
    }

    function renderOrders() {
      if (!ordersTableBody) return;

      if (!orders.length) {
        ordersTableBody.innerHTML = "";
        if (ordersEmpty) ordersEmpty.style.display = "block";
        return;
      }

      if (ordersEmpty) ordersEmpty.style.display = "none";
      ordersTableBody.innerHTML = "";

      orders.forEach((order) => {
        const row = document.createElement("tr");

        row.innerHTML = `
          <td>#${order.id}</td>
          <td>${escapeHtml(order.restaurant_name || "—")}</td>
          <td>
            <div><strong>${escapeHtml(order.customer_name || "Користувач")}</strong></div>
            <div class="partner-order-meta">${escapeHtml(order.phone || "—")}</div>
            <div class="partner-order-meta">${escapeHtml(mapDeliveryType(order.delivery_type))}</div>
            <div class="partner-order-meta">${escapeHtml(formatOrderAddress(order))}</div>
            <div class="partner-order-meta">${escapeHtml(mapPaymentMethod(order.payment_method))}</div>
            ${order.comment ? `<div class="partner-order-meta">Коментар: ${escapeHtml(order.comment)}</div>` : ""}
          </td>
          <td>
            <div><strong>${order.total_price ?? 0} грн</strong></div>
            ${
              order.items?.length
                ? `
                  <div class="partner-order-history">
                    ${order.items
                      .map(
                        (item) => `
                          <div>${escapeHtml(item.name || "Страва")} × ${Number(item.quantity) || 0} — ${Number(item.line_total) || 0} грн</div>
                        `,
                      )
                      .join("")}
                  </div>
                `
                : ""
            }
          </td>
          <td>${escapeHtml(order.created_at || "—")}</td>
          <td>
            <select data-order-id="${order.id}" data-current-status="${escapeHtml(order.status || "new")}">
              ${buildOrderStatusOptions(order)}
            </select>
            ${
              order.status_history?.length
                ? `
                  <div class="partner-order-history">
                    ${order.status_history
                      .map(
                        (item) => `
                          <div>
                            <strong>${escapeHtml(mapOrderStatus(item.status))}</strong>
                            ${item.created_at ? ` · ${escapeHtml(item.created_at)}` : ""}
                            ${item.note ? ` — ${escapeHtml(item.note)}` : ""}
                          </div>
                        `,
                      )
                      .join("")}
                  </div>
                `
                : ""
            }
          </td>
        `;

        ordersTableBody.appendChild(row);
      });

      ordersTableBody
        .querySelectorAll("select[data-order-id]")
        .forEach((select) => {
          select.addEventListener("change", async () => {
            const orderId = select.getAttribute("data-order-id");
            const status = select.value;
            const previousStatus =
              select.getAttribute("data-current-status") || "new";
            const note = window.prompt(
              "Коментар до зміни статусу (необов’язково)",
              "",
            );

            if (note === null) {
              select.value = previousStatus;
              return;
            }

            try {
              await apiFetch(`/partner/api/orders/${orderId}/status`, {
                method: "PATCH",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({ status, note: note.trim() }),
              });

              select.setAttribute("data-current-status", status);
              await loadOrders();
            } catch (error) {
              select.value = previousStatus;
              alert(error.message || "Не вдалося оновити статус замовлення");
            }
          });
        });
    }

    async function loadRestaurants() {
      try {
        restaurants = await apiFetch("/partner/api/restaurants");

        renderRestaurants();
        fillRestaurantSelect();
        updateStats();
        await calculateMenuStats();

        if (selectedRestaurantId) {
          await loadMenu(selectedRestaurantId);
        } else {
          renderMenu([]);
          if (menuEmpty) {
            menuEmpty.style.display = "block";
          }
        }
      } catch (error) {
        if (restaurantsGrid) {
          restaurantsGrid.innerHTML = `<div class="partner-empty">${escapeHtml(error.message)}</div>`;
        }

        if (menuList) {
          menuList.innerHTML = "";
        }

        if (menuEmpty) {
          menuEmpty.style.display = "block";
          menuEmpty.textContent = "Не вдалося завантажити ресторани.";
        }

        if (openDishModalBtn) {
          openDishModalBtn.disabled = true;
        }
      }
    }

    async function loadMenu(restaurantId) {
      const normalizedRestaurantId = String(restaurantId || "").trim();

      if (!normalizedRestaurantId) {
        selectedRestaurantId = "";
        if (menuRestaurantSelect) {
          menuRestaurantSelect.value = "";
        }
        if (openDishModalBtn) {
          openDishModalBtn.disabled = true;
        }
        renderMenu([]);
        if (menuEmpty) {
          menuEmpty.style.display = "block";
          menuEmpty.textContent = "Оберіть ресторан, щоб переглянути меню.";
        }
        return;
      }

      selectedRestaurantId = normalizedRestaurantId;

      if (menuRestaurantSelect) {
        menuRestaurantSelect.value = normalizedRestaurantId;
      }

      if (openDishModalBtn) {
        openDishModalBtn.disabled = false;
      }

      try {
        const items = await apiFetch(
          `/partner/api/restaurants/${normalizedRestaurantId}/menu`,
        );

        renderMenu(items);

        if (menuEmpty && Array.isArray(items) && items.length) {
          menuEmpty.style.display = "none";
        } else if (menuEmpty) {
          menuEmpty.style.display = "block";
          menuEmpty.textContent = "У цьому ресторані ще немає страв.";
        }
      } catch (error) {
        if (menuList) {
          menuList.innerHTML = `<div class="partner-empty">${escapeHtml(error.message)}</div>`;
        }
        if (menuEmpty) {
          menuEmpty.style.display = "none";
        }
      }
    }

    async function loadOrders() {
      try {
        orders = await apiFetch("/partner/api/orders");
        renderOrders();
        updateStats();
      } catch (error) {
        if (ordersTableBody) {
          ordersTableBody.innerHTML = `<tr><td colspan="7">${escapeHtml(error.message)}</td></tr>`;
        }
      }
    }

    window.editRestaurant = function editRestaurant(restaurantId) {
      const restaurant = restaurants.find(
        (r) => Number(r.id) === Number(restaurantId),
      );
      if (!restaurant || !restaurantForm || !restaurantModal) return;

      restaurantForm.dataset.editId = restaurant.id;

      const modalTitle = restaurantModal.querySelector("h3");
      if (modalTitle) modalTitle.textContent = "Редагувати ресторан";

      const nameEl = document.getElementById("restaurantName");
      const cityEl = document.getElementById("restaurantCity");
      const addressEl = document.getElementById("restaurantAddress");
      const categoriesEl = document.getElementById("restaurantCategories");
      const descriptionEl = document.getElementById("restaurantDescription");
      const openingEl = document.getElementById("restaurantOpeningTime");
      const closingEl = document.getElementById("restaurantClosingTime");
      const minimumOrderEl = document.getElementById(
        "restaurantMinimumOrderAmount",
      );
      const isActiveEl = document.getElementById("restaurantIsActive");

      if (nameEl) nameEl.value = restaurant.name || "";
      if (cityEl) cityEl.value = restaurant.city_slug || "";
      if (addressEl) addressEl.value = restaurant.address || "";
      if (categoriesEl)
        if (categoriesEl) {
          categoriesEl.value = Array.isArray(restaurant.categories)
            ? restaurant.categories.join(",")
            : "";
        }
      if (descriptionEl) descriptionEl.value = restaurant.description || "";
      if (openingEl) openingEl.value = restaurant.opening_time || "09:00";
      if (closingEl) closingEl.value = restaurant.closing_time || "22:00";
      if (minimumOrderEl) {
        minimumOrderEl.value = restaurant.minimum_order_amount ?? 200;
      }
      if (isActiveEl) isActiveEl.checked = Boolean(restaurant.is_active);

      openModal(restaurantModal);
    };

    window.editDish = function editDish(itemId) {
      const item = currentMenuItems.find(
        (x) => Number(x.id) === Number(itemId),
      );
      if (!item || !dishForm || !dishModal) return;

      dishForm.dataset.editId = item.id;

      const modalTitle = dishModal.querySelector("h3");
      if (modalTitle) modalTitle.textContent = "Редагувати страву";

      const nameEl = document.getElementById("dishName");
      const descriptionEl = document.getElementById("dishDescription");
      const priceEl = document.getElementById("dishPrice");
      const weightEl = document.getElementById("dishWeight");
      const isAvailableEl = document.getElementById("dishIsAvailable");

      if (nameEl) nameEl.value = item.name || "";
      if (descriptionEl) descriptionEl.value = item.description || "";
      if (priceEl) priceEl.value = item.price ?? "";
      if (weightEl) weightEl.value = item.weight || "";
      if (isAvailableEl) isAvailableEl.checked = Boolean(item.is_available);

      openModal(dishModal);
    };

    window.deleteRestaurant = async function deleteRestaurant(restaurantId) {
      if (!confirm("Видалити ресторан?")) return;

      try {
        await apiFetch(`/partner/api/restaurants/${restaurantId}`, {
          method: "DELETE",
        });

        await loadRestaurants();

        if (String(selectedRestaurantId) === String(restaurantId)) {
          selectedRestaurantId = "";
          renderMenu([]);
          fillRestaurantSelect();
        }
      } catch (error) {
        alert(error.message);
      }
    };

    window.deleteMenuItem = async function deleteMenuItem(itemId) {
      if (!confirm("Видалити страву?")) return;

      try {
        await apiFetch(`/partner/api/menu-items/${itemId}`, {
          method: "DELETE",
        });

        if (selectedRestaurantId) {
          await loadMenu(selectedRestaurantId);
          await calculateMenuStats();
        }
      } catch (error) {
        alert(error.message);
      }
    };

    document.querySelectorAll(".partner-side-link").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabName = btn.dataset.partnerTab;
        if (!tabName) return;
        switchPartnerTab(tabName);
      });
    });

    document.querySelectorAll(".partner-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        switchPartnerTab(tab.dataset.partnerTab);
      });
    });

    document.querySelectorAll("[data-partner-tab-target]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetTab = btn.dataset.partnerTabTarget;
        if (!targetTab) return;
        switchPartnerTab(targetTab);
      });
    });

    document.querySelectorAll("[data-close-modal]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const modalId = btn.getAttribute("data-close-modal");
        const modal = document.getElementById(modalId);
        if (modal) closeModal(modal);
      });
    });

    document.querySelectorAll("[data-menu-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-menu-id");
        selectedRestaurantId = id;
        if (menuRestaurantSelect) {
          menuRestaurantSelect.value = id;
        }
        switchPartnerTab("menu");
        loadMenu(id);
      });
    });

    document.querySelectorAll("[data-edit-restaurant-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const restaurantId = Number(
          btn.getAttribute("data-edit-restaurant-id"),
        );
        window.editRestaurant(restaurantId);
      });
    });

    if (openRestaurantModalBtn) {
      openRestaurantModalBtn.addEventListener("click", () => {
        if (!restaurantForm || !restaurantModal) return;

        restaurantForm.reset();
        delete restaurantForm.dataset.editId;

        const imageEl = document.getElementById("restaurantImage");
        const openingEl = document.getElementById("restaurantOpeningTime");
        const closingEl = document.getElementById("restaurantClosingTime");
        const minimumOrderEl = document.getElementById(
          "restaurantMinimumOrderAmount",
        );
        const isActiveEl = document.getElementById("restaurantIsActive");

        if (imageEl) imageEl.value = "";
        if (openingEl) openingEl.value = "09:00";
        if (closingEl) closingEl.value = "22:00";
        if (minimumOrderEl) minimumOrderEl.value = "200";
        if (isActiveEl) isActiveEl.checked = true;

        const modalTitle = restaurantModal.querySelector("h3");
        if (modalTitle) modalTitle.textContent = "Додати ресторан";

        openModal(restaurantModal);
      });
    }

    if (openRestaurantModalBtnSecondary) {
      openRestaurantModalBtnSecondary.addEventListener("click", () => {
        if (openRestaurantModalBtn) {
          openRestaurantModalBtn.click();
        }
      });
    }

    if (openDishModalBtn) {
      openDishModalBtn.addEventListener("click", () => {
        if (!selectedRestaurantId) {
          alert("Спочатку оберіть ресторан");
          return;
        }

        if (!dishForm || !dishModal) return;

        dishForm.reset();
        delete dishForm.dataset.editId;

        const dishImageEl = document.getElementById("dishImage");
        const dishIsAvailableEl = document.getElementById("dishIsAvailable");

        if (dishImageEl) dishImageEl.value = "";
        if (dishIsAvailableEl) dishIsAvailableEl.checked = true;

        const modalTitle = dishModal.querySelector("h3");
        if (modalTitle) {
          modalTitle.textContent = "Додати страву";
        }

        openModal(dishModal);
      });
    }

    if (menuRestaurantSelect) {
      menuRestaurantSelect.addEventListener("change", async () => {
        const value = String(menuRestaurantSelect.value || "").trim();
        await loadMenu(value);
      });
    }

    if (restaurantForm) {
      restaurantForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formData = new FormData(restaurantForm);
        const editId = restaurantForm.dataset.editId;

        const categoriesValue = String(formData.get("categories") || "")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
          .join(",");

        formData.set("categories", categoriesValue);

        const minimumOrderEl = document.getElementById(
          "restaurantMinimumOrderAmount",
        );
        const isActiveEl = document.getElementById("restaurantIsActive");

        formData.set(
          "minimum_order_amount",
          minimumOrderEl ? String(minimumOrderEl.value || "200").trim() : "200",
        );

        formData.set(
          "is_active",
          isActiveEl && isActiveEl.checked ? "true" : "false",
        );

        try {
          const response = await apiFetch(
            editId
              ? `/partner/api/restaurants/${editId}`
              : "/partner/api/restaurants",
            {
              method: editId ? "PATCH" : "POST",
              body: formData,
            },
          );

          restaurantForm.reset();
          delete restaurantForm.dataset.editId;
          closeModal(restaurantModal);

          if (!editId && response && response.id) {
            selectedRestaurantId = String(response.id);
          }

          await loadRestaurants();
          await calculateMenuStats();
          switchPartnerTab("menu");

          if (selectedRestaurantId) {
            await loadMenu(selectedRestaurantId);
          }
        } catch (error) {
          alert(error.message || "Не вдалося зберегти ресторан");
        }
      });
    }

    if (dishForm) {
      dishForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!selectedRestaurantId && !dishForm.dataset.editId) {
          alert("Спочатку оберіть ресторан");
          return;
        }

        const formData = new FormData(dishForm);
        const editId = dishForm.dataset.editId;

        const priceInput = document.getElementById("dishPrice");
        const weightInput = document.getElementById("dishWeight");
        const dishNameInput = document.getElementById("dishName");

        if (dishNameInput) {
          formData.set("name", String(dishNameInput.value || "").trim());
        }

        if (priceInput) {
          formData.set("price", String(priceInput.value || "").trim());
        }

        if (weightInput) {
          formData.set("weight", String(weightInput.value || "").trim());
        }

        formData.set(
          "is_available",
          document.getElementById("dishIsAvailable")?.checked
            ? "true"
            : "false",
        );

        try {
          await apiFetch(
            editId
              ? `/partner/api/menu-items/${editId}`
              : `/partner/api/restaurants/${selectedRestaurantId}/menu`,
            {
              method: editId ? "PATCH" : "POST",
              body: formData,
            },
          );

          dishForm.reset();
          delete dishForm.dataset.editId;
          closeModal(dishModal);

          if (selectedRestaurantId) {
            await loadMenu(selectedRestaurantId);
          }

          await calculateMenuStats();
        } catch (error) {
          alert(error.message || "Не вдалося зберегти страву");
        }
      });
    }

    (async function initPartnerDashboard() {
      switchPartnerTab("overview");
      await loadRestaurants();
      await loadOrders();
      await loadPartnerAnalytics();
    })();
  });
})();
