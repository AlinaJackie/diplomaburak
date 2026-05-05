(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const phoneRegex = /^\+380\d{9}$/;
  const urlLikeRegex = /^(https?:\/\/|www\.)/i;
  const taxIdRegex = /^[0-9A-Za-zА-Яа-яЇїІіЄєҐґ\- ]{6,20}$/;

  const partnerApplyForm = document.getElementById("partner-apply-form");
  if (!partnerApplyForm) return;

  const paResult = document.getElementById("pa-result");

  partnerApplyForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const contact_person = document.getElementById("pa-contact-person").value.trim();
    const brand_name = document.getElementById("pa-brand-name").value.trim();
    const phone = document.getElementById("pa-phone").value.trim();
    const email = document.getElementById("pa-email").value.trim();
    const city = document.getElementById("pa-city").value.trim();
    const verification_link = document.getElementById("pa-verification-link").value.trim();
    const planned_locations_count = document.getElementById("pa-planned-locations-count").value.trim();
    const edrpou_or_ipn = document.getElementById("pa-edrpou-or-ipn").value.trim();
    const business_description = document.getElementById("pa-business-description").value.trim();

    const personal_data_agreement = document.getElementById("pa-personal-data-agreement").checked;
    const representation_agreement = document.getElementById("pa-representation-agreement").checked;

    if (
      !contact_person ||
      !brand_name ||
      !phone ||
      !email ||
      !city ||
      !verification_link ||
      !planned_locations_count ||
      !edrpou_or_ipn ||
      !business_description
    ) {
      paResult.textContent = "Заповніть усі обов’язкові поля.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (!emailRegex.test(email)) {
      paResult.textContent = "Введіть коректний email.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (!phoneRegex.test(phone)) {
      paResult.textContent = "Телефон має бути у форматі +380XXXXXXXXX.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (!urlLikeRegex.test(verification_link)) {
      paResult.textContent = "Вкажіть коректне посилання на Instagram, сайт або Google Maps.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    const plannedCountNumber = Number(planned_locations_count);
    if (!Number.isInteger(plannedCountNumber) || plannedCountNumber < 1) {
      paResult.textContent = "Кількість закладів має бути цілим числом від 1.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (!taxIdRegex.test(edrpou_or_ipn)) {
      paResult.textContent = "Некоректний формат ЄДРПОУ / ІПН.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (business_description.length < 20) {
      paResult.textContent = "Короткий опис бізнесу має бути змістовнішим.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (business_description.length > 1000) {
      paResult.textContent = "Опис бізнесу занадто довгий (макс. 1000 символів).";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (!personal_data_agreement) {
      paResult.textContent = "Потрібно надати згоду на обробку персональних даних.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    if (!representation_agreement) {
      paResult.textContent = "Потрібно підтвердити право представляти бренд або заклад.";
      paResult.style.color = "#ff4d4f";
      return;
    }

    const payload = {
      contact_person,
      brand_name,
      phone,
      email,
      city,
      verification_link,
      planned_locations_count: plannedCountNumber,
      edrpou_or_ipn,
      business_description,
      personal_data_agreement,
      representation_agreement,
    };

    try {
      const res = await apiFetch("/api/partner/applications", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        paResult.textContent = data.error || "Сталася помилка під час надсилання заявки.";
        paResult.style.color = "#ff4d4f";
        return;
      }

      partnerApplyForm.reset();

      paResult.textContent =
        'Заявку надіслано. Після первинної перевірки менеджер FoodGo зв’яжеться з вами для уточнення деталей співпраці.';
      paResult.style.color = "#16a34a";

      setTimeout(() => {
        window.location.href = "/partner/status";
      }, 1400);
    } catch (err) {
      console.error(err);
      paResult.textContent = "Мережева помилка. Спробуйте пізніше.";
      paResult.style.color = "#ff4d4f";
    }
  });
})();