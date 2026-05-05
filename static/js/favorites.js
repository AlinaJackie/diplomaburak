(function () {
  const bodyEl = document.body;
  const isAuthenticated = bodyEl?.getAttribute("data-authenticated") === "true";

  function buildGuestLoginUrl(restaurantId) {
    const nextUrl = `${window.location.pathname}${window.location.search}`;
    const encodedNext = encodeURIComponent(nextUrl);
    return `/restaurant/${Number(restaurantId)}/favorite?next=${encodedNext}`;
  }

  function updateButtons(restaurantId, isFavorite) {
    document
      .querySelectorAll(
        `.favorite-btn[data-restaurant-id="${Number(restaurantId)}"]`,
      )
      .forEach((btn) => {
        const pressed = String(Boolean(isFavorite));
        btn.setAttribute("aria-pressed", pressed);
        btn.setAttribute(
          "aria-label",
          isFavorite ? "Remove from favorites" : "Add to favorites",
        );
      });
  }

  async function toggleFavorite(restaurantId) {
    const res = await apiFetch(`/api/restaurants/${Number(restaurantId)}/favorite`, {
      method: "POST",
    });
    const data = await readApiResponse(res);

    if (!res.ok) {
      throw new Error(getErrorMessage(data, "Не вдалося змінити обране"));
    }

    return Boolean(data?.is_favorite);
  }

  document.addEventListener("click", async (event) => {
    const target = event.target;
    const btn = target?.closest?.(".favorite-btn[data-restaurant-id]");
    if (!btn) return;

    event.preventDefault();

    const restaurantId = Number(btn.getAttribute("data-restaurant-id") || 0);
    if (!restaurantId) return;

    if (!isAuthenticated) {
      window.location.href = buildGuestLoginUrl(restaurantId);
      return;
    }

    const isDisabled =
      btn.getAttribute("aria-disabled") === "true" || btn.hasAttribute("disabled");
    if (isDisabled) return;

    btn.setAttribute("aria-disabled", "true");
    if (btn.tagName === "BUTTON") {
      btn.setAttribute("disabled", "disabled");
    }

    try {
      const isFavorite = await toggleFavorite(restaurantId);
      updateButtons(restaurantId, isFavorite);

      if (!isFavorite && btn.getAttribute("data-remove-on-unfavorite") === "true") {
        btn.closest?.("[data-favorite-row]")?.remove?.();
        const countEl = document.getElementById("cabinetFavoriteRestaurantsCount");
        if (countEl) {
          countEl.textContent = String(
            document.querySelectorAll("[data-favorite-row]").length,
          );
        }
      }
    } catch (error) {
      console.error(error);
      alert(error?.message || "Не вдалося змінити обране");
    } finally {
      btn.removeAttribute("aria-disabled");
      if (btn.tagName === "BUTTON") {
        btn.removeAttribute("disabled");
      }
    }
  });
})();
