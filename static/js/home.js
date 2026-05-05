(() => {
  const restaurantsContainer = document.getElementById("restaurants");
  const emptyState = document.getElementById("restaurants-empty");

  const citySelect = document.getElementById("city-filter");
  const sortSelect = document.getElementById("sort-filter");
  const maxMinOrderSelect = document.getElementById("min-order-filter");
  const openNowCheckbox = document.getElementById("open-now-filter");
  const categoryButtons = document.querySelectorAll(".categories .category-card");
  const searchInput = document.getElementById("search-input");
  const searchBtn = document.getElementById("search-btn");

  function mapCategoryName(key) {
    switch (key) {
      case "fastfood": return "Фаст-фуд";
      case "burgers": return "Бургери";
      case "ukrainian": return "Українська";
      case "breakfast": return "Сніданок";
      case "pizza": return "Піца";
      case "sushi": return "Суші";
      case "shawarma": return "Шаурма";
      case "healthy": return "Корисна їжа";
      case "grill": return "Гриль";
      case "homemade": return "По-домашньому";
      default: return key || "";
    }
  }

  function getActiveCategory() {
    const activeBtn = document.querySelector(".category-card.active");
    return activeBtn ? activeBtn.dataset.category : "";
  }

  function clearElement(element) {
    while (element.firstChild) {
      element.removeChild(element.firstChild);
    }
  }

  function showEmptyState(show, message = "Нічого не знайдено.") {
    if (!emptyState) return;

    emptyState.classList.toggle("hidden", !show);

    const title = emptyState.querySelector("h3");
    if (title) {
      title.textContent = message;
    }
  }

  function setMessage(message) {
    if (!restaurantsContainer) return;

    clearElement(restaurantsContainer);
    showEmptyState(false);

    const box = document.createElement("div");
    box.className = "empty-state";

    const icon = document.createElement("div");
    icon.className = "empty-state__icon";
    icon.textContent = "⚠️";

    const title = document.createElement("h3");
    title.textContent = message;

    box.appendChild(icon);
    box.appendChild(title);
    restaurantsContainer.appendChild(box);
  }

  function createMetaText(categories, openingTime, closingTime, minOrder) {
    const parts = [];

    if (Array.isArray(categories) && categories.length) {
      parts.push(categories.map(mapCategoryName).join(" · "));
    }

    if (openingTime && closingTime) {
      parts.push(`${openingTime}–${closingTime}`);
    }

    if (minOrder) {
      parts.push(`від ${minOrder} грн`);
    }

    return parts.join(" · ");
  }

  function createRestaurantCard(r) {
    const article = document.createElement("article");
    article.className = "restaurant-card";

    const favBtn = document.createElement("a");
    favBtn.href = `/restaurant/${Number(r.id)}/favorite`;
    favBtn.className = "favorite-btn";
    favBtn.setAttribute("role", "button");
    favBtn.setAttribute("data-restaurant-id", String(r.id || ""));
    favBtn.setAttribute("aria-pressed", String(Boolean(r.is_favorite)));
    favBtn.setAttribute(
      "aria-label",
      r.is_favorite ? "Remove from favorites" : "Add to favorites",
    );
    article.appendChild(favBtn);

    const img = document.createElement("img");
    img.src = r.image_url || "https://placehold.co/600x400?text=Restaurant";
    img.alt = r.name || "Restaurant image";
    img.onerror = function () {
      this.src = "https://placehold.co/600x400?text=Restaurant";
    };
    article.appendChild(img);

    const content = document.createElement("div");
    content.className = "restaurant-content";

    const header = document.createElement("div");
    header.className = "restaurant-card__header";

    const leftBox = document.createElement("div");
    leftBox.className = "restaurant-card__title-wrap";

    const name = document.createElement("h3");
    name.className = "restaurant-name";
    name.title = r.name || "";
    name.textContent = r.name || "";

    leftBox.appendChild(name);

    const rightBox = document.createElement("div");
    rightBox.className = "restaurant-tags";

    const status = document.createElement("span");
    status.className = `restaurant-status ${r.is_open ? "open" : "closed"}`;
    status.textContent = r.is_open ? "Відчинено" : "Зачинено";
    rightBox.appendChild(status);

    if (r.rating != null) {
      const ratingTag = document.createElement("span");
      ratingTag.className = "tag";
      ratingTag.textContent = `${r.rating}★`;
      rightBox.appendChild(ratingTag);
    }

    if (r.eta) {
      const etaTag = document.createElement("span");
      etaTag.className = "tag";
      etaTag.textContent = r.eta;
      rightBox.appendChild(etaTag);
    }

    header.appendChild(leftBox);
    header.appendChild(rightBox);

    const description = document.createElement("p");
    description.className = "restaurant-description";
    description.textContent =
      r.description || "Смачна їжа та зручне замовлення онлайн.";

    const fullMeta = document.createElement("div");
    fullMeta.className = "restaurant-meta";
    fullMeta.textContent = createMetaText(
      Array.isArray(r.categories) ? r.categories : [],
      r.opening_time,
      r.closing_time,
      r.minimum_order_amount
    );

    const actions = document.createElement("div");
    actions.className = "restaurant-actions";

    const link = document.createElement("a");
    link.href = `/restaurant/${r.id}`;
    link.className = "btn btn-primary";
    link.textContent = "Перейти в меню";

    actions.appendChild(link);

    content.appendChild(header);
    content.appendChild(description);
    content.appendChild(fullMeta);
    content.appendChild(actions);

    article.appendChild(content);

    return article;
  }

  function renderRestaurants(list) {
    if (!restaurantsContainer) return;

    clearElement(restaurantsContainer);

    if (!Array.isArray(list) || !list.length) {
      showEmptyState(true, "Ресторанів не знайдено.");
      return;
    }

    showEmptyState(false);

    list.forEach((restaurant) => {
      restaurantsContainer.appendChild(createRestaurantCard(restaurant));
    });
  }

  function fillCities(restaurants) {
    if (!citySelect) return;

    const currentValue = citySelect.value || "";

    const cities = [
      ...new Set(
        (Array.isArray(restaurants) ? restaurants : [])
          .map((r) => String(r.city || "").trim())
          .filter(Boolean)
      ),
    ].sort((a, b) => a.localeCompare(b, "uk"));

    citySelect.innerHTML = "";

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Усі міста";
    citySelect.appendChild(defaultOption);

    cities.forEach((city) => {
      const option = document.createElement("option");
      option.value = city;
      option.textContent = city;
      citySelect.appendChild(option);
    });

    if (cities.includes(currentValue)) {
      citySelect.value = currentValue;
    }
  }

  async function loadCities() {
    if (!citySelect) return;

    try {
      const response = await apiFetch("/api/restaurants?sort=name_asc");
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Не вдалося завантажити міста"));
      }

      fillCities(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Помилка завантаження міст:", error);
      citySelect.innerHTML = `<option value="">Усі міста</option>`;
    }
  }

  async function loadRestaurants() {
    if (!restaurantsContainer) return;

    const params = new URLSearchParams();
    const city = citySelect ? citySelect.value : "";
    const category = getActiveCategory();
    const q = searchInput ? searchInput.value.trim() : "";
    const sort = sortSelect ? sortSelect.value : "name_asc";
    const maxMinOrder = maxMinOrderSelect ? maxMinOrderSelect.value : "";
    const openNow = openNowCheckbox ? openNowCheckbox.checked : false;

    if (city) params.set("city", city);
    if (category && category !== "all") params.set("category", category);
    if (q) params.set("q", q);
    if (sort) params.set("sort", sort);
    if (maxMinOrder) params.set("max_min_order", maxMinOrder);
    if (openNow) params.set("open_now", "true");

    try {
      const queryString = params.toString();
      const url = queryString ? `/api/restaurants?${queryString}` : "/api/restaurants";

      const response = await apiFetch(url);
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(getErrorMessage(data, "Сталася помилка при завантаженні ресторанів."));
      }

      renderRestaurants(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setMessage(err.message || "Сталася помилка при завантаженні ресторанів.");
    }
  }

  if (categoryButtons.length) {
    categoryButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        categoryButtons.forEach((button) => button.classList.remove("active"));
        btn.classList.add("active");
        loadRestaurants();
      });
    });
  }

  [citySelect, sortSelect, maxMinOrderSelect, openNowCheckbox].forEach((control) => {
    if (!control) return;
    control.addEventListener("change", loadRestaurants);
  });

  if (searchBtn) {
    searchBtn.addEventListener("click", loadRestaurants);
  }

  if (searchInput) {
    searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        loadRestaurants();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await loadCities();
    await loadRestaurants();
  });
})();
