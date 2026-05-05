(() => {
  const tabAdminOverviewLink = document.getElementById(
    "tab-admin-overview-link",
  );
  const tabAdminOrdersLink = document.getElementById("tab-admin-orders-link");
  const tabAdminPartnersLink = document.getElementById(
    "tab-admin-partners-link",
  );
  const tabAdminRestaurantsLink = document.getElementById(
    "tab-admin-restaurants-link",
  );

  const tabAdminOverview = document.getElementById("tab-admin-overview");
  const tabAdminOrders = document.getElementById("tab-admin-orders");
  const tabAdminPartners = document.getElementById("tab-admin-partners");
  const tabAdminRestaurants = document.getElementById("tab-admin-restaurants");

  const adminOrdersTableBody =
    document.getElementById("admin-orders-table-body") ||
    document.querySelector("#admin-orders tbody");
  const adminPartnersTableBody =
    document.getElementById("admin-partners-table-body") ||
    document.querySelector("#admin-partners-table tbody");
  const adminRestaurantsTableBody =
    document.getElementById("admin-restaurants-table-body") ||
    document.querySelector("#admin-restaurants-table tbody");

  const adminPendingCount = document.getElementById("admin-pending-count");
  const adminRestaurantsCount = document.getElementById(
    "admin-restaurants-count",
  );
  const adminPartnersCount = document.getElementById("admin-partners-count");
  const adminApplicationsCount = document.getElementById(
    "admin-applications-count",
  );
  const adminActiveOrdersCount = document.getElementById(
    "admin-active-orders-count",
  );
  const adminCompletedOrdersCount = document.getElementById(
    "admin-completed-orders-count",
  );
  const adminTopRestaurantsList = document.getElementById(
    "admin-top-restaurants-list",
  );

  if (
    !tabAdminOverviewLink &&
    !adminPartnersTableBody &&
    !adminRestaurantsTableBody
  ) {
    return;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function safeImageUrl(value) {
    const url = String(value ?? "").trim();
    if (!url) return "";
    if (
      url.startsWith("/") ||
      url.startsWith("http://") ||
      url.startsWith("https://")
    ) {
      return url;
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

  function statusLabel(status) {
    if (status === "pending") return "Очікує";
    if (status === "approved") return "Схвалено";
    if (status === "rejected") return "Відхилено";
    return status || "—";
  }

  function orderStatusLabel(status) {
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

  function setAdminTab(active) {
    const map = {
      overview: [tabAdminOverviewLink, tabAdminOverview],
      orders: [tabAdminOrdersLink, tabAdminOrders],
      partners: [tabAdminPartnersLink, tabAdminPartners],
      restaurants: [tabAdminRestaurantsLink, tabAdminRestaurants],
    };

    Object.values(map).forEach(([link, section]) => {
      if (link) link.classList.remove("active");
      if (section) section.style.display = "none";
    });

    if (map[active]) {
      const [link, section] = map[active];
      if (link) link.classList.add("active");
      if (section) section.style.display = "grid";
    }
  }

  async function updatePartnerApplicationStatus(id, status) {
    try {
      const response = await apiFetch(`/admin/api/partner-applications/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Помилка оновлення статусу"));
      }

      await loadPartnerApplications();
      await loadAdminRestaurants();
      await loadAdminAnalytics();
    } catch (error) {
      console.error(error);
      alert(error.message || "Помилка оновлення статусу");
    }
  }

  async function loadPartnerApplications() {
    if (!adminPartnersTableBody) return;

    try {
      const response = await apiFetch("/admin/api/partner-applications");
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Не вдалося завантажити заявки партнерів."),
        );
      }

      const applications = Array.isArray(data) ? data : [];

      if (adminPendingCount) {
        adminPendingCount.textContent = applications.filter(
          (x) => x.status === "pending",
        ).length;
      }

      if (!applications.length) {
        adminPartnersTableBody.innerHTML =
          '<tr><td colspan="6">Заявок поки немає.</td></tr>';
        return;
      }

      adminPartnersTableBody.innerHTML = applications
        .map((a) => {
          const safeLink =
            safeImageUrl(a.verification_link) ||
            escapeHtml(a.verification_link || "—");
          const verificationBlock =
            safeLink && safeLink !== escapeHtml(a.verification_link || "—")
              ? `<a href="${escapeHtml(safeLink)}" target="_blank" rel="noopener noreferrer">Відкрити</a>`
              : escapeHtml(a.verification_link || "—");

          return `
          <tr>
            <td>${Number(a.id) || 0}</td>
            <td>${escapeHtml(a.brand_name || "—")}</td>
            <td>${escapeHtml(a.city || "—")}</td>
            <td><span class="status-badge status-${escapeHtml(a.status || "pending")}">${statusLabel(a.status)}</span></td>
            <td>
              ${
                a.status === "pending"
                  ? `<button class="btn btn-primary btn-sm" type="button" data-approve="${Number(a.id) || 0}">Підтвердити</button>
                     <button class="btn btn-outline btn-sm" type="button" data-reject="${Number(a.id) || 0}">Відхилити</button>`
                  : "—"
              }
            </td>
            <td><button class="btn btn-outline btn-sm" type="button" data-toggle-details="${Number(a.id) || 0}">Детальніше</button></td>
          </tr>
          <tr class="admin-details-row is-hidden-row" id="details-${Number(a.id) || 0}">
            <td colspan="6">
              <div class="admin-details-card">
                <div class="admin-details-grid">
                  <div><strong>Контактна особа:</strong> ${escapeHtml(a.contact_person || "—")}</div>
                  <div><strong>Бренд / мережа / заклад:</strong> ${escapeHtml(a.brand_name || "—")}</div>
                  <div><strong>Email:</strong> ${escapeHtml(a.email || "—")}</div>
                  <div><strong>Телефон:</strong> ${escapeHtml(a.phone || "—")}</div>
                  <div><strong>Місто:</strong> ${escapeHtml(a.city || "—")}</div>
                  <div><strong>Посилання для перевірки:</strong> ${verificationBlock}</div>
                  <div><strong>Кількість закладів:</strong> ${escapeHtml(a.planned_locations_count || "—")}</div>
                  <div><strong>ЄДРПОУ / ІПН:</strong> ${escapeHtml(a.edrpou_or_ipn || "—")}</div>
                  <div><strong>Опис бізнесу:</strong> ${escapeHtml(a.business_description || "—")}</div>
                  <div><strong>Згода на обробку даних:</strong> ${a.personal_data_agreement ? "Так" : "Ні"}</div>
                  <div><strong>Підтвердження повноважень:</strong> ${a.representation_agreement ? "Так" : "Ні"}</div>
                  <div><strong>Створено:</strong> ${escapeHtml(a.created_at || "—")}</div>
                </div>
              </div>
            </td>
          </tr>`;
        })
        .join("");

      adminPartnersTableBody
        .querySelectorAll("[data-approve]")
        .forEach((btn) => {
          btn.addEventListener("click", async () => {
            await updatePartnerApplicationStatus(
              Number(btn.dataset.approve),
              "approved",
            );
          });
        });

      adminPartnersTableBody
        .querySelectorAll("[data-reject]")
        .forEach((btn) => {
          btn.addEventListener("click", async () => {
            await updatePartnerApplicationStatus(
              Number(btn.dataset.reject),
              "rejected",
            );
          });
        });

      adminPartnersTableBody
        .querySelectorAll("[data-toggle-details]")
        .forEach((btn) => {
          btn.addEventListener("click", () => {
            const detailsRow = document.getElementById(
              `details-${btn.dataset.toggleDetails}`,
            );
            if (!detailsRow) return;
            const isHidden = detailsRow.classList.contains("is-hidden-row");
            detailsRow.classList.toggle("is-hidden-row", !isHidden);
            detailsRow.style.display = isHidden ? "table-row" : "none";
            btn.textContent = isHidden ? "Сховати" : "Детальніше";
          });
        });
    } catch (error) {
      console.error(error);
      adminPartnersTableBody.innerHTML =
        '<tr><td colspan="6">Помилка завантаження заявок.</td></tr>';
    }
  }

  async function loadAdminRestaurants() {
    if (!adminRestaurantsTableBody) return;

    try {
      const response = await apiFetch("/admin/api/restaurants");
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Не вдалося завантажити ресторани."),
        );
      }

      const restaurants = Array.isArray(data) ? data : [];

      if (adminRestaurantsCount) {
        adminRestaurantsCount.textContent = restaurants.filter(
          (restaurant) => restaurant.is_active,
        ).length;
      }

      if (!restaurants.length) {
        adminRestaurantsTableBody.innerHTML =
          '<tr><td colspan="6">Ресторанів поки немає.</td></tr>';
        return;
      }

      adminRestaurantsTableBody.innerHTML = restaurants
        .map((restaurant) => {
          const image = safeImageUrl(restaurant.image_url)
            ? `<img src="${escapeHtml(safeImageUrl(restaurant.image_url))}" alt="${escapeHtml(restaurant.name || "restaurant")}">`
            : "—";
          const nameCell = `${escapeHtml(restaurant.name || "—")}${
            restaurant.is_active
              ? ' <span class="status-badge status-approved">Активний</span>'
              : ' <span class="status-badge status-rejected">Неактивний</span>'
          }`;

          return `
          <tr>
            <td>${Number(restaurant.id) || 0}</td>
            <td>${nameCell}</td>
            <td>${escapeHtml(restaurant.city || "—")}</td>
            <td>${escapeHtml((restaurant.categories || []).map(mapCategoryName).join(", ") || "—")}</td>
            <td>${escapeHtml(restaurant.eta || "—")}</td>
            <td>${image}</td>
          </tr>
        `;
        })
        .join("");
    } catch (error) {
      console.error(error);
      adminRestaurantsTableBody.innerHTML =
        '<tr><td colspan="6">Помилка завантаження ресторанів.</td></tr>';
    }
  }

  async function loadAdminOrders() {
    if (!adminOrdersTableBody) return;

    try {
      const response = await apiFetch("/admin/api/orders");
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Не вдалося завантажити замовлення."),
        );
      }

      const orders = Array.isArray(data) ? data : [];

      if (!orders.length) {
        adminOrdersTableBody.innerHTML =
          '<tr><td colspan="7">Замовлень поки немає.</td></tr>';
        return;
      }

      adminOrdersTableBody.innerHTML = orders
        .map(
          (order) => `
        <tr>
          <td>${Number(order.id) || 0}</td>
          <td>${escapeHtml(order.customer_name || "—")}</td>
          <td>${escapeHtml(order.phone || "—")}</td>
          <td>${escapeHtml(order.restaurant_name || "—")}</td>
          <td>${Number(order.total_price) || 0} грн</td>
          <td>${escapeHtml(orderStatusLabel(order.status))}</td>
          <td>${escapeHtml(order.created_at || "—")}</td>
        </tr>
      `,
        )
        .join("");
    } catch (error) {
      console.error(error);
      adminOrdersTableBody.innerHTML =
        '<tr><td colspan="7">Помилка завантаження замовлень.</td></tr>';
    }
  }

  async function loadAdminAnalytics() {
    try {
      const response = await apiFetch("/admin/api/analytics");
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Не вдалося завантажити аналітику."),
        );
      }

      if (adminPartnersCount)
        adminPartnersCount.textContent = data.partners_count ?? 0;
      if (adminApplicationsCount)
        adminApplicationsCount.textContent = data.applications_count ?? 0;
      if (adminActiveOrdersCount)
        adminActiveOrdersCount.textContent = data.active_orders_count ?? 0;
      if (adminCompletedOrdersCount)
        adminCompletedOrdersCount.textContent =
          data.completed_orders_count ?? 0;

      if (adminTopRestaurantsList) {
        const topRestaurants = data.top_restaurants || [];
        if (!topRestaurants.length) {
          adminTopRestaurantsList.innerHTML =
            '<div class="analytics-empty">Поки що немає даних.</div>';
        } else {
          adminTopRestaurantsList.innerHTML = topRestaurants
            .map(
              (item) => `
            <div class="analytics-list-item">
              <span>${escapeHtml(item.name || "—")}</span>
              <strong>${Number(item.orders_count) || 0}</strong>
            </div>
          `,
            )
            .join("");
        }
      }
    } catch (error) {
      console.error(error);
    }
  }

  if (tabAdminOverviewLink)
    tabAdminOverviewLink.addEventListener("click", (event) => {
      event.preventDefault();
      setAdminTab("overview");
    });
  if (tabAdminOrdersLink)
    tabAdminOrdersLink.addEventListener("click", (event) => {
      event.preventDefault();
      setAdminTab("orders");
    });
  if (tabAdminPartnersLink)
    tabAdminPartnersLink.addEventListener("click", (event) => {
      event.preventDefault();
      setAdminTab("partners");
    });
  if (tabAdminRestaurantsLink)
    tabAdminRestaurantsLink.addEventListener("click", (event) => {
      event.preventDefault();
      setAdminTab("restaurants");
    });

  document.addEventListener("DOMContentLoaded", async () => {
    setAdminTab("overview");
    await loadPartnerApplications();
    await loadAdminRestaurants();
    await loadAdminOrders();
    await loadAdminAnalytics();
  });
})();
