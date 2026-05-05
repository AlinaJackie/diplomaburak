(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const phoneRegex = /^\+380\d{9}$/;
  const passwordRegex =
    /^(?=.*[A-ZА-ЯІЇЄҐ])(?=.*[a-zа-яіїєґ])(?=.*\d)(?=.*[^A-Za-zА-Яа-яІЇЄҐієїґ0-9]).{8,}$/;

  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");

  function getLocalCartState() {
    try {
      const data = JSON.parse(localStorage.getItem("cart") || "{}");
      return {
        restaurant_id: Number(data.restaurant_id) || null,
        items: Array.isArray(data.items) ? data.items : [],
      };
    } catch {
      return { restaurant_id: null, items: [] };
    }
  }

  async function syncGuestCartToServer() {
    const cart = getLocalCartState();
    const items = Array.isArray(cart.items) ? cart.items : [];

    if (!cart.restaurant_id || !items.length) return true;

    const payload = {
      restaurant_id: Number(cart.restaurant_id),
      items: items
        .map((item) => ({
          menu_item_id: Number(item.menu_item_id || item.id),
          quantity: Number(item.quantity || 1),
        }))
        .filter((item) => item.menu_item_id && item.quantity > 0),
    };

    if (!payload.items.length) return true;

    const res = await apiFetch("/api/cart", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await readApiResponse(res);

    if (!res.ok) {
      console.warn("Cart sync failed:", data);
      return false;
    }

    localStorage.removeItem("cart");
    return true;
  }

  function showHint(id, text = "") {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.style.display = text ? "block" : "none";
    el.style.color = "#ff4d4f";
  }

  function clearHints() {
    document.querySelectorAll(".field-hint").forEach((el) => {
      el.textContent = "";
      el.style.display = "none";
    });
  }

  function switchAuthTab(mode) {
    const isLogin = mode === "login";

    if (tabLogin) tabLogin.classList.toggle("active", isLogin);
    if (tabRegister) tabRegister.classList.toggle("active", !isLogin);

    if (formLogin) {
      formLogin.classList.remove("is-initially-hidden");
      formLogin.hidden = !isLogin;

      if (isLogin) {
        formLogin.style.removeProperty("display");
      } else {
        formLogin.style.display = "none";
      }
    }

    if (formRegister) {
      formRegister.classList.remove("is-initially-hidden");
      formRegister.hidden = isLogin;

      if (!isLogin) {
        formRegister.style.removeProperty("display");
      } else {
        formRegister.style.display = "none";
      }
    }

    clearHints();
  }

  if (tabLogin && tabRegister) {
    tabLogin.addEventListener("click", () => switchAuthTab("login"));
    tabRegister.addEventListener("click", () => switchAuthTab("register"));
    switchAuthTab("login");
  }

  if (formLogin) {
    formLogin.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearHints();

      const identifier = document
        .getElementById("login-identifier")
        .value.trim();
      const password = document.getElementById("login-password").value;

      const isEmail = emailRegex.test(identifier);
      const isPhone = phoneRegex.test(identifier);

      if (!isEmail && !isPhone) {
        showHint(
          "login-identifier-hint",
          "Введіть коректний email або телефон +380XXXXXXXXX",
        );
        return;
      }

      if (!password) {
        showHint("login-password-hint", "Введіть пароль");
        return;
      }

      try {
        const res = await apiFetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ identifier, password }),
        });

        const data = await readApiResponse(res);

        if (!res.ok) {
          showHint(
            "login-password-hint",
            getErrorMessage(data, "Не вдалося увійти в акаунт"),
          );
          return;
        }

        const redirectTo = data.redirect || "/";
        window.location.href = redirectTo;
      } catch (error) {
        console.error(error);
        showHint("login-password-hint", "Помилка з’єднання");
      }
    });
  }

  if (formRegister) {
    formRegister.addEventListener("submit", async (e) => {
      e.preventDefault();
      clearHints();

      const email = document
        .getElementById("reg-email")
        .value.trim()
        .toLowerCase();
      const phone = document.getElementById("reg-phone").value.trim();
      const password = document.getElementById("reg-password").value;
      const password2 = document.getElementById("reg-password2").value;
      const full_name = document.getElementById("reg-fullname").value.trim();
      const city = document.getElementById("reg-city").value;
      const street = document.getElementById("reg-street").value.trim();
      const house = document.getElementById("reg-house").value.trim();
      const extra_info = document.getElementById("reg-extra").value.trim();

      let hasErrors = false;

      if (!emailRegex.test(email)) {
        showHint("reg-email-hint", "Некоректний email");
        hasErrors = true;
      }

      if (!phoneRegex.test(phone)) {
        showHint("reg-phone-hint", "Телефон має бути у форматі +380XXXXXXXXX");
        hasErrors = true;
      }

      if (!passwordRegex.test(password)) {
        showHint(
          "reg-password-hint",
          "Мінімум 8 символів, велика і мала літера, цифра та спецсимвол",
        );
        hasErrors = true;
      }

      if (password !== password2) {
        showHint("reg-password2-hint", "Паролі не співпадають");
        hasErrors = true;
      }

      if (!full_name || full_name.length < 3) {
        showHint("reg-fullname-hint", "Введіть ім’я та прізвище");
        hasErrors = true;
      }

      if (hasErrors) return;

      try {
        const res = await apiFetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            phone,
            password,
            full_name,
            city,
            street,
            house,
            extra_info,
          }),
        });

        const data = await readApiResponse(res);

        if (!res.ok) {
          alert(getErrorMessage(data, "Не вдалося завершити реєстрацію"));
          return;
        }

        const redirectTo = data.redirect || "/";
        window.location.href = redirectTo;
      } catch (error) {
        console.error(error);
        alert("Помилка з’єднання");
      }
    });
  }
})();
