document.addEventListener("DOMContentLoaded", () => {
  const forgotPasswordForm = document.getElementById("forgotPasswordForm");
  if (!forgotPasswordForm) return;

  const identifierInput = document.getElementById("forgotIdentifier");
  const resultEl = document.getElementById("forgotPasswordResult");

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const phoneRegex = /^\+380\d{9}$/;

  forgotPasswordForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const identifier = identifierInput?.value.trim() || "";

    resultEl.textContent = "";
    resultEl.style.color = "";

    if (!identifier) {
      resultEl.textContent = "Вкажіть email або телефон.";
      resultEl.style.color = "#dc2626";
      return;
    }

    const isEmail = emailRegex.test(identifier);
    const isPhone = phoneRegex.test(identifier);

    if (!isEmail && !isPhone) {
      resultEl.textContent = "Введіть коректний email або телефон у форматі +380XXXXXXXXX.";
      resultEl.style.color = "#dc2626";
      return;
    }

    try {
      const res = await apiFetch("/auth/forgot-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ identifier }),
      });

      const data = await res.json();

      if (!res.ok) {
        resultEl.textContent = data.error || "Не вдалося надіслати посилання.";
        resultEl.style.color = "#dc2626";
        return;
      }

      resultEl.textContent =
        data.message || "Якщо акаунт існує, лист для відновлення вже надіслано.";
      resultEl.style.color = "#16a34a";
      forgotPasswordForm.reset();
    } catch (error) {
      console.error("FORGOT PASSWORD ERROR:", error);
      resultEl.textContent = "Сталася помилка. Спробуйте пізніше.";
      resultEl.style.color = "#dc2626";
    }
  });
});