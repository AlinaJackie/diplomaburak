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

  function sanitizeUrl(value) {
    const raw = String(value ?? "").trim();

    if (!raw) return "";

    if (raw.startsWith("/") || raw.startsWith("./") || raw.startsWith("../")) {
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

  const bodyEl = document.body;
  const restaurantId = Number(bodyEl?.getAttribute("data-restaurant-id") || 0);
  const isAuthenticated = bodyEl?.getAttribute("data-authenticated") === "true";
  const menuContainer = document.getElementById("menu-items");
  const cartEl = document.getElementById("cart");

  let cart = [];
  let menuItemsCache = [];

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

    // Items must be parseable and within bounds.
    for (const item of items) {
      const id = Number(item?.menu_item_id || item?.id || 0);
      const qty = Number(item?.quantity || 0);
      if (!id || !Number.isInteger(qty) || qty <= 0 || qty > 20) return false;
    }

    return true;
  }

  function getGuestCartRaw() {
    try {
      const data = JSON.parse(localStorage.getItem(GUEST_CART_KEY) || "null");
      return data && typeof data === "object" ? data : null;
    } catch {
      return null;
    }
  }

  function normalizeCartItem(item) {
    return {
      id: Number(item.id || item.menu_item_id),
      menu_item_id: Number(item.menu_item_id || item.id),
      name: String(item.name || ""),
      price: Number(item.price || 0),
      quantity: Number(item.quantity || 1),
      line_total: Number(item.line_total || 0),
      is_available: item.is_available !== false,
    };
  }

  function mergeCartItems(items) {
    const merged = new Map();

    (Array.isArray(items) ? items : []).forEach((raw) => {
      const item = normalizeCartItem(raw);
      if (!Number.isFinite(item.id) || item.id <= 0) return;

      const qty = Number(item.quantity || 0);
      if (!Number.isFinite(qty) || qty <= 0) return;

      const existing = merged.get(item.id);
      if (existing) {
        existing.quantity = Math.min(20, existing.quantity + qty);
      } else {
        merged.set(item.id, { ...item, quantity: Math.min(20, qty) });
      }
    });

    return Array.from(merged.values());
  }

  function getGuestCartForRestaurant() {
    const raw = getGuestCartRaw();

    // If format is missing/outdated/stale -> drop it.
    if (!isGuestCartFresh(raw)) {
      if (raw) clearGuestCart();
      return [];
    }

    const storedRestaurantId = Number(raw.restaurant_id);

    // If cart belongs to a different restaurant -> remove it.
    if (storedRestaurantId !== restaurantId) {
      clearGuestCart();
      return [];
    }

    const merged = mergeCartItems(raw.items);
    if (!merged.length) {
      clearGuestCart();
      return [];
    }

    return merged;
  }

  function saveGuestCart() {
    if (!cart.length) {
      clearGuestCart();
      return;
    }

    try {
      localStorage.setItem(
        GUEST_CART_KEY,
        JSON.stringify({
          restaurant_id: restaurantId,
          items: cart,
          updated_at: Date.now(),
        }),
      );
    } catch {
      // ignore storage errors
    }
  }

  async function fetchMenuItems(url) {
    const response = await apiFetch(url);
    const data = await readApiResponse(response);

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "Помилка завантаження меню"));
    }

    return Array.isArray(data) ? data : [];
  }

  async function loadMenu() {
    if (!restaurantId || !menuContainer) return [];

    try {
      const items = await fetchMenuItems(
        `/api/restaurants/${restaurantId}/menu`,
      );
      menuItemsCache = Array.isArray(items) ? items : [];

      if (!items.length) {
        menuContainer.innerHTML = "<p>Меню поки що порожнє.</p>";
        return [];
      }

      menuContainer.innerHTML = items
        .map((item) => {
          const safeImage =
            sanitizeUrl(item.image_url) ||
            "https://placehold.co/600x400?text=Dish";

          return `
            <div class="menu-card">
              <img
                src="${safeImage}"
                alt="${escapeHtml(item.name)}"
                class="menu-card__image"
                onerror="this.src='https://placehold.co/600x400?text=Dish'"
              >
              <div class="menu-card__content">
                <h3 class="menu-card__title">${escapeHtml(item.name)}</h3>
                <p class="menu-card__desc">${escapeHtml(item.description || "")}</p>

                <div class="menu-card__meta">
                  <span class="menu-card__weight">${escapeHtml(item.weight || "")}</span>
                  <span class="menu-card__price">${Number(item.price || 0)} грн</span>
                </div>

                <div class="menu-card__actions">
                  ${
                    item.is_available
                      ? `<button class="add-to-cart-btn" data-id="${Number(item.id)}" type="button">Додати в кошик</button>`
                      : `<button class="add-to-cart-btn" type="button" disabled>Недоступно</button>`
                  }
                </div>
              </div>
            </div>
          `;
        })
        .join("");

      menuContainer
        .querySelectorAll(".add-to-cart-btn[data-id]")
        .forEach((btn) => {
          btn.addEventListener("click", () => {
            const id = Number(btn.dataset.id);
            const item = items.find((x) => Number(x.id) === id);
            if (item) addToCart(item);
          });
        });
    } catch (error) {
      console.error(error);
      menuContainer.innerHTML = `<p>${escapeHtml(error.message || "Сталася помилка при завантаженні меню.")}</p>`;
      return [];
    }

    return menuItemsCache;
  }

  function getLocalCart() {
    return getGuestCartForRestaurant();
  }

  function saveLocalCart() {
    saveGuestCart();
  }

  function reconcileCartWithMenu(items) {
    if (!Array.isArray(items) || !items.length) return false;

    const menuById = new Map(items.map((item) => [Number(item.id), item]));
    let changed = false;

    const merged = new Map();

    cart.forEach((raw) => {
      const current = normalizeCartItem(raw);
      const menuItem = menuById.get(Number(current.id));

      // Drop stale/unavailable items.
      if (!menuItem || menuItem.is_available === false) {
        changed = true;
        return;
      }

      const next = {
        ...current,
        name: String(menuItem.name || current.name || ""),
        price: Number(menuItem.price || 0),
        is_available: true,
      };

      if (!Number.isFinite(next.quantity) || next.quantity <= 0) {
        changed = true;
        return;
      }

      if (next.quantity > 20) {
        next.quantity = 20;
        changed = true;
      }

      const existing = merged.get(next.id);
      if (existing) {
        existing.quantity += next.quantity;
        changed = true;
      } else {
        merged.set(next.id, next);
      }
    });

    const nextCart = Array.from(merged.values()).sort((a, b) => a.id - b.id);
    if (nextCart.length !== cart.length) changed = true;

    cart = nextCart;
    return changed;
  }

  async function loadServerCart() {
    const response = await apiFetch("/api/cart");
    const data = await readApiResponse(response);

    if (!response.ok) {
      throw new Error(getErrorMessage(data, "Не вдалося завантажити кошик"));
    }

    if (Number(data.restaurant_id) === restaurantId) {
      cart = Array.isArray(data.items) ? data.items.map(normalizeCartItem) : [];
    } else {
      cart = [];
    }
  }

  async function persistCart() {
    if (!isAuthenticated) {
      saveLocalCart();
      return true;
    }

    const response = await apiFetch("/api/cart", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        restaurant_id: restaurantId,
        items: cart.map((item) => ({
          menu_item_id: item.id,
          quantity: item.quantity,
        })),
      }),
    });

    const data = await readApiResponse(response);

    if (!response.ok) {
      alert(getErrorMessage(data, "Не вдалося зберегти кошик"));
      return false;
    }

    cart = Array.isArray(data.items) ? data.items.map(normalizeCartItem) : [];
    return true;
  }

  async function addToCart(item) {
    const existing = cart.find((product) => product.id === Number(item.id));

    if (existing) {
      if (existing.quantity >= 20) return;
      existing.quantity += 1;
    } else {
      cart.push({
        id: Number(item.id),
        menu_item_id: Number(item.id),
        name: item.name,
        price: Number(item.price || 0),
        quantity: 1,
      });
    }

    const saved = await persistCart();

    if (!saved) {
      if (existing) {
        existing.quantity -= 1;
        if (existing.quantity <= 0) {
          cart = cart.filter((x) => x.id !== Number(item.id));
        }
      } else {
        cart = cart.filter((x) => x.id !== Number(item.id));
      }
      return;
    }

    renderCart();
  }

  async function changeQty(id, delta) {
    const product = cart.find((item) => item.id === id);
    if (!product) return;

    const oldQty = product.quantity;
    product.quantity += delta;
    if (product.quantity > 20) product.quantity = 20;

    if (product.quantity <= 0) {
      cart = cart.filter((item) => item.id !== id);
    }

    const saved = await persistCart();
    if (!saved) {
      const existing = cart.find((item) => item.id === id);
      if (existing) {
        existing.quantity = oldQty;
      } else {
        product.quantity = oldQty;
        cart.push(product);
      }
    }

    renderCart();
  }

  function renderCart() {
    if (!cartEl) return;

    if (!cart.length) {
      cartEl.innerHTML = `
        <div class="cart-title">Кошик</div>
        <p class="restaurant-meta">Кошик порожній</p>
      `;
      return;
    }

    const total = cart.reduce(
      (sum, item) => sum + Number(item.price || 0) * Number(item.quantity || 0),
      0,
    );

    cartEl.innerHTML = `
      <div class="cart-title">Кошик</div>
      ${cart
        .map(
          (item) => `
            <div class="cart-item">
              <span>${escapeHtml(item.name)} × ${Number(item.quantity || 0)}</span>
              <span>${Number(item.price || 0) * Number(item.quantity || 0)} грн</span>
            </div>
            <div class="cart-item cart-item--controls">
              <button class="btn btn-outline btn-sm qty-btn" type="button" data-dec="${Number(item.id)}" aria-label="Зменшити кількість">-</button>
              <button class="btn btn-outline btn-sm qty-btn" type="button" data-inc="${Number(item.id)}" aria-label="Збільшити кількість">+</button>
            </div>
          `,
        )
        .join("")}
      <div class="cart-footer">
        <div class="cart-total-row">
          <span>Разом:</span>
          <span><strong>${total}</strong> грн</span>
        </div>
        <button class="btn btn-primary btn-block" id="checkout-btn" type="button">Оформити</button>
      </div>
    `;

    cartEl.querySelectorAll("[data-inc]").forEach((btn) => {
      btn.addEventListener("click", () =>
        changeQty(Number(btn.dataset.inc), 1),
      );
    });

    cartEl.querySelectorAll("[data-dec]").forEach((btn) => {
      btn.addEventListener("click", () =>
        changeQty(Number(btn.dataset.dec), -1),
      );
    });

    document.getElementById("checkout-btn")?.addEventListener("click", () => {
      if (!isAuthenticated) {
        saveLocalCart();
        try {
          sessionStorage.setItem("foodgo_guest_checkout", "1");
        } catch {
          // ignore sessionStorage errors
        }
      }
      window.location.href = "/checkout";
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    const menuItems = await loadMenu();

    if (isAuthenticated) {
      try {
        await loadServerCart();
      } catch (error) {
        console.error(error);
        cart = [];
      }
    } else {
      cart = getLocalCart();
      cart = mergeCartItems(cart);

      if (reconcileCartWithMenu(menuItems)) {
        saveLocalCart();
      }
    }

    renderCart();
  });
})();
