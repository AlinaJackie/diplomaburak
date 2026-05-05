document.addEventListener("DOMContentLoaded", () => {
  const resetFormEl = document.getElementById("resetPasswordForm");
  if (!resetFormEl) return;

  const resultEl = document.getElementById("resetPasswordResult");

  resetFormEl.addEventListener("submit", async (e) => {
    e.preventDefault();

    const token = resetFormEl.dataset.token;
    const password = document.getElementById("resetPassword1")?.value.trim() || "";
    const confirm_password = document.getElementById("resetPassword2")?.value.trim() || "";

    resultEl.textContent = "";
    resultEl.style.color = "";

    if (!password || !confirm_password) {
      resultEl.textContent = "Заповніть обидва поля.";
      resultEl.style.color = "#dc2626";
      return;
    }

    if (password !== confirm_password) {
      resultEl.textContent = "Паролі не співпадають.";
      resultEl.style.color = "#dc2626";
      return;
    }

    try {
      const res = await apiFetch(`/auth/reset-password/${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          password,
          confirm_password
        })
      });

      const data = await res.json();

      if (!res.ok) {
        resultEl.textContent = data.error || "Не вдалося змінити пароль";
        resultEl.style.color = "#dc2626";
        return;
      }

      resultEl.textContent = data.message || "Пароль успішно змінено";
      resultEl.style.color = "#16a34a";

      setTimeout(() => {
        window.location.href = data.redirect || "/";
      }, 1200);
    } catch (error) {
      console.error("RESET PASSWORD ERROR:", error);
      resultEl.textContent = "Сталася помилка";
      resultEl.style.color = "#dc2626";
    }
  });
});