(() => {
  const GUEST_CART_KEY = "cart";
  const GUEST_CART_MAX_AGE_MS = 24 * 60 * 60 * 1000;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const bodyEl = document.body;
  const isAuthenticated = bodyEl?.getAttribute("data-authenticated") === "true";
  const checkoutForm = document.getElementById("checkout-form");
  const checkoutSummary = document.getElementById("ch-summary");
  const checkoutResult = document.getElementById("checkout-result");
  const deliveryTypeSelect = document.getElementById("ch-delivery-type");
  const addressRow = document.getElementById("address-row");
  const addressInput = document.getElementById("ch-address");
  const cityInput = document.getElementById("ch-city");
  const nameInput = document.getElementById("ch-name");
  const phoneInput = document.getElementById("ch-phone");
  const commentInput = document.getElementById("ch-comment");
  const paymentInput = document.getElementById("ch-payment");

  let previewRequestTimer = null;
  let previewData = null;
  let cartState = { restaurant_id: null, items: [] };

  function clearGuestCart() {
    try {
      localStorage.removeItem(GUEST_CART_KEY);
    } catch {
      // ignore storage errors
    }
  }

  function isGuestCartFresh(cartData) {
    if (!cartData || typeof cartData !== "object") return false;

    const updatedAt = Number(cartData.updated_at);
    if (!Number.isFinite(updatedAt) || updatedAt <= 0) return false;

    const age = Date.now() - updatedAt;
    if (!Number.isFinite(age) || age < 0 || age > GUEST_CART_MAX_AGE_MS) return false;

    const restaurantIdValue = Number(cartData.restaurant_id);
    if (!Number.isFinite(restaurantIdValue) || restaurantIdValue <= 0) return false;

    const items = cartData.items;
    if (!Array.isArray(items)) return false;

    for (const item of items) {
      const id = Number(item?.menu_item_id || item?.id || 0);
      const qty = Number(item?.quantity || 0);
      if (!id || !Number.isInteger(qty) || qty <= 0 || qty > 20) return false;
    }

    return true;
  }

  function getGuestCart() {
    try {
      const data = JSON.parse(localStorage.getItem(GUEST_CART_KEY) || "null");
      if (!isGuestCartFresh(data)) {
        if (data) clearGuestCart();
        return { restaurant_id: null, items: [] };
      }

      const rawItems = Array.isArray(data.items) ? data.items : [];

      // Defensive merge to prevent duplicated items from corrupting totals/preview.
      const merged = new Map();
      rawItems.forEach((item) => {
        const menuItemId = Number(item.menu_item_id || item.id || 0);
        const quantity = Number(item.quantity || 0);
        if (!menuItemId || !Number.isFinite(quantity) || quantity <= 0) return;

        const existing = merged.get(menuItemId);
        if (existing) {
          existing.quantity = Math.min(20, existing.quantity + quantity);
        } else {
          merged.set(menuItemId, {
            id: menuItemId,
            menu_item_id: menuItemId,
            name: item.name,
            price: Number(item.price || 0),
            quantity: Math.min(20, quantity),
          });
        }
      });

      const items = Array.from(merged.values());
      if (!items.length) {
        clearGuestCart();
        return { restaurant_id: null, items: [] };
      }

      return {
        restaurant_id: Number(data.restaurant_id) || null,
        items,
      };
    } catch {
      return { restaurant_id: null, items: [] };
    }
  }

  function showResult(message, isSuccess = true) {
    if (!checkoutResult) return;

    checkoutResult.innerHTML = `
      <div class="${isSuccess ? "checkout-success" : "checkout-error"}">
        ${escapeHtml(message)}
      </div>
    `;
  }

  function clearResult() {
    if (checkoutResult) {
      checkoutResult.innerHTML = "";
    }
  }

  function getLocalCart() {
    return getGuestCart();
  }

  async function loadCart() {
    if (!isAuthenticated) {
      cartState = getLocalCart();
      return;
    }

    const res = await apiFetch("/api/cart");
    const data = await readApiResponse(res);

    if (!res.ok) {
      throw new Error(getErrorMessage(data, "Не вдалося завантажити кошик."));
    }

    cartState = {
      restaurant_id: Number(data.restaurant_id) || null,
      items: Array.isArray(data.items)
        ? data.items.map((item) => ({
            id: Number(item.id || item.menu_item_id),
            menu_item_id: Number(item.menu_item_id || item.id),
            name: item.name,
            price: Number(item.price),
            quantity: Number(item.quantity),
          }))
        : [],
    };

    // If user just logged in and still has a guest cart in localStorage,
    // import it into the server cart so checkout stays intact.
    if (!cartState.items.length) {
      const localCart = getLocalCart();

      let allowImport = false;
      try {
        allowImport = sessionStorage.getItem("foodgo_guest_checkout") === "1";
      } catch {
        allowImport = false;
      }

      if (!allowImport) {
        return;
      }

      const localItems = Array.isArray(localCart.items) ? localCart.items : [];

      if (localCart.restaurant_id && localItems.length) {
        const payload = {
          restaurant_id: Number(localCart.restaurant_id),
          items: localItems
            .map((item) => ({
              menu_item_id: Number(item.menu_item_id || item.id),
              quantity: Number(item.quantity || 1),
            }))
            .filter((item) => item.menu_item_id && item.quantity > 0),
        };

        if (payload.items.length) {
          const putRes = await apiFetch("/api/cart", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          const putData = await readApiResponse(putRes);

          if (putRes.ok) {
            clearGuestCart();
            try {
              sessionStorage.removeItem("foodgo_guest_checkout");
            } catch {
              // ignore sessionStorage errors
            }
            cartState = {
              restaurant_id: Number(putData.restaurant_id) || null,
              items: Array.isArray(putData.items)
                ? putData.items.map((item) => ({
                    id: Number(item.id || item.menu_item_id),
                    menu_item_id: Number(item.menu_item_id || item.id),
                    name: item.name,
                    price: Number(item.price),
                    quantity: Number(item.quantity),
                  }))
                : [],
            };
          } else {
            console.warn("Cart import failed:", putData);
            if ([400, 404].includes(Number(putRes.status))) clearGuestCart();
          }
        }
      } else {
        // Nothing to import (stale cart, invalid format, or empty cart).
        try {
          sessionStorage.removeItem("foodgo_guest_checkout");
        } catch {
          // ignore sessionStorage errors
        }
      }
    }
  }

  async function clearCart() {
    clearGuestCart();

    if (!isAuthenticated) return;
    await apiFetch("/api/cart", { method: "DELETE" });
  }

  function toggleDeliveryFields() {
    if (!deliveryTypeSelect || !addressRow || !addressInput) return;

    const isPickup = deliveryTypeSelect.value === "pickup";
    addressRow.style.display = isPickup ? "none" : "block";
    addressInput.required = !isPickup;

    if (isPickup) {
      addressInput.value = "";
    }
  }

  function buildPayload() {
    const deliveryType = deliveryTypeSelect
      ? deliveryTypeSelect.value
      : "delivery";

    return {
      restaurant_id: Number(cartState.restaurant_id),
      items: Array.isArray(cartState.items) ? cartState.items : [],
      customer_name: nameInput ? nameInput.value.trim() : "",
      phone: phoneInput ? phoneInput.value.trim() : "",
      city: cityInput ? cityInput.value.trim() : "",
      address:
        deliveryType === "pickup"
          ? ""
          : addressInput
            ? addressInput.value.trim()
            : "",
      comment: commentInput ? commentInput.value.trim() : "",
      payment_method: paymentInput ? paymentInput.value : "cash",
      delivery_type: deliveryType,
    };
  }

  function renderEmptySummary(message = "Кошик порожній") {
    if (!checkoutSummary) return;

    checkoutSummary.innerHTML = `
      <div class="checkout-summary">
        <div class="checkout-summary__title">Ваше замовлення</div>
        <p>${escapeHtml(message)}</p>
      </div>
    `;
  }

  function renderPreviewSummary(data) {
    if (!checkoutSummary) return;

    const items = Array.isArray(data.items) ? data.items : [];
    const deliveryLabel =
      data.delivery_type === "pickup" ? "Самовивіз" : "Доставка";

    checkoutSummary.innerHTML = `
      <div class="checkout-summary">
        <div class="checkout-summary__title">Ваше замовлення</div>

        <div class="checkout-summary__list">
          ${items
            .map(
              (item) => `
                <div class="checkout-summary__row">
                  <span>${escapeHtml(item.name)} × ${item.quantity}</span>
                  <strong>${item.line_total} грн</strong>
                </div>
              `,
            )
            .join("")}
        </div>

        <div class="checkout-summary__row checkout-summary__service">
          <span>Сума страв</span>
          <strong>${data.items_total} грн</strong>
        </div>

        <div class="checkout-summary__row">
          <span>Спосіб отримання</span>
          <strong>${deliveryLabel}</strong>
        </div>

        <div class="checkout-summary__row">
          <span>Вартість доставки</span>
          <strong>${data.delivery_fee} грн</strong>
        </div>

        <div class="checkout-summary__row">
          <span>Приблизний час</span>
          <strong>${data.eta_minutes} хв</strong>
        </div>

        ${
          data.delivery_is_estimated
            ? `
              <div class="checkout-summary__row">
                <span>Тип розрахунку</span>
                <strong>Орієнтовний</strong>
              </div>
            `
            : ""
        }

        ${
          data.distance_km !== null && data.distance_km !== undefined
            ? `
              <div class="checkout-summary__row">
                <span>Відстань</span>
                <strong>${data.distance_km} км</strong>
              </div>
            `
            : ""
        }

        <div class="checkout-summary__total">
          <span>Разом</span>
          <strong>${data.total_price} грн</strong>
        </div>
      </div>
    `;
  }

  function renderPreviewError(message) {
    if (!checkoutSummary) return;

    const items = Array.isArray(cartState.items) ? cartState.items : [];
    const itemsTotal = items.reduce(
      (sum, item) => sum + Number(item.price) * Number(item.quantity),
      0,
    );

    checkoutSummary.innerHTML = `
      <div class="checkout-summary">
        <div class="checkout-summary__title">Ваше замовлення</div>

        <div class="checkout-summary__list">
          ${items
            .map(
              (item) => `
                <div class="checkout-summary__row">
                  <span>${escapeHtml(item.name)} × ${item.quantity}</span>
                  <strong>${Number(item.price) * Number(item.quantity)} грн</strong>
                </div>
              `,
            )
            .join("")}
        </div>

        <div class="checkout-summary__row checkout-summary__service">
          <span>Сума страв</span>
          <strong>${itemsTotal} грн</strong>
        </div>

        <div class="checkout-summary__row">
          <span class="text-danger-inline">${escapeHtml(message)}</span>
        </div>
      </div>
    `;
  }

  async function loadCheckoutPreview() {
    const items = Array.isArray(cartState.items) ? cartState.items : [];

    if (!items.length) {
      previewData = null;
      renderEmptySummary("Кошик порожній");
      return;
    }

    const payload = buildPayload();

    if (!payload.restaurant_id) {
      previewData = null;
      renderPreviewError("Не вибрано ресторан");
      return;
    }

    if (!payload.customer_name || !payload.phone || !payload.city) {
      previewData = null;
      renderPreviewError("Заповніть ім’я, телефон і місто");
      return;
    }

    if (payload.delivery_type === "delivery" && !payload.address) {
      previewData = null;
      renderPreviewError("Вкажіть адресу доставки");
      return;
    }

    try {
      const res = await apiFetch("/api/orders/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await readApiResponse(res);

      if (!res.ok) {
        previewData = null;
        renderPreviewError(
          getErrorMessage(data, "Не вдалося розрахувати умови доставки."),
        );
        return;
      }

      previewData = data;
      renderPreviewSummary(data);
    } catch {
      previewData = null;
      renderPreviewError("Не вдалося отримати дані доставки");
    }
  }

  function schedulePreviewUpdate() {
    clearResult();

    if (previewRequestTimer) {
      clearTimeout(previewRequestTimer);
    }

    previewRequestTimer = setTimeout(() => {
      loadCheckoutPreview();
    }, 350);
  }

  if (deliveryTypeSelect) {
    deliveryTypeSelect.addEventListener("change", () => {
      clearResult();
      toggleDeliveryFields();
      schedulePreviewUpdate();
    });
  }

  [addressInput, cityInput, nameInput, phoneInput, commentInput].forEach(
    (input) => {
      if (input) input.addEventListener("input", schedulePreviewUpdate);
    },
  );

  if (paymentInput) {
    paymentInput.addEventListener("change", schedulePreviewUpdate);
  }

  document.addEventListener("DOMContentLoaded", async () => {
    if (!checkoutForm) return;

    toggleDeliveryFields();

    try {
      await loadCart();
    } catch {
      cartState = { restaurant_id: null, items: [] };
      renderEmptySummary("Кошик порожній");
      showResult("Не вдалося завантажити кошик", false);
      return;
    }

    await loadCheckoutPreview();

    checkoutForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearResult();

      const items = Array.isArray(cartState.items) ? cartState.items : [];
      if (!items.length) {
        showResult("Кошик порожній", false);
        renderEmptySummary("Кошик порожній");
        return;
      }

      const payload = buildPayload();

      if (payload.delivery_type === "delivery" && !payload.address) {
        showResult("Вкажіть адресу доставки", false);
        renderPreviewError("Вкажіть адресу доставки");
        return;
      }

      try {
        const res = await apiFetch("/api/orders", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await readApiResponse(res);

        if (!res.ok) {
          showResult(
            getErrorMessage(data, "Не вдалося створити замовлення"),
            false,
          );
          return;
        }

        await clearCart();
        cartState = { restaurant_id: null, items: [] };
        previewData = null;

        checkoutForm.reset();

        if (nameInput) {
          nameInput.value = nameInput.defaultValue || "";
        }
        if (phoneInput) {
          phoneInput.value = phoneInput.defaultValue || "";
        }
        if (cityInput) {
          cityInput.value = cityInput.defaultValue || cityInput.value || "ivano-frankivsk";
        }
        if (addressInput) {
          addressInput.value = addressInput.defaultValue || "";
        }

        toggleDeliveryFields();
        renderEmptySummary("Кошик порожній");

        showResult("Замовлення успішно створено", true);

        setTimeout(() => {
          window.location.href = "/";
        }, 1800);
      } catch {
        showResult("Сталася помилка під час оформлення замовлення", false);
      }
    });
  });
})();
