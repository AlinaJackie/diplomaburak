function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

async function apiFetch(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const hasBody = options.body !== undefined && options.body !== null;

  if (
    hasBody &&
    !headers.has("Content-Type") &&
    !(options.body instanceof FormData)
  ) {
    headers.set("Content-Type", "application/json");
  }

  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();

    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }

    if (
      options.body instanceof FormData &&
      csrfToken &&
      !options.body.has("csrf_token")
    ) {
      options.body.append("csrf_token", csrfToken);
    }
  }

  return fetch(url, {
    credentials: "same-origin",
    ...options,
    method,
    headers,
  });
}

function getStatusFallbackMessage(status) {
  const messages = {
    400: "Некоректний запит. Перевірте введені дані.",
    401: "Потрібно увійти в акаунт.",
    403: "У вас немає доступу до цієї дії.",
    404: "Запитаний ресурс не знайдено.",
    405: "Ця дія для запиту не підтримується.",
    413: "Файл завеликий. Максимальний розмір — 15 МБ.",
    415: "Сервер не зміг обробити формат переданих даних.",
    500: "Сталася помилка на сервері. Спробуйте ще раз.",
  };

  return messages[Number(status)] || "Сталася помилка. Спробуйте ще раз.";
}

async function readApiResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return {
        error: getStatusFallbackMessage(response.status),
        status_code: response.status,
      };
    }
  }

  try {
    const text = await response.text();

    if (!response.ok) {
      return {
        error: getStatusFallbackMessage(response.status),
        raw: text,
        status_code: response.status,
      };
    }

    return { message: text, raw: text, status_code: response.status };
  } catch {
    return {
      error: getStatusFallbackMessage(response.status),
      status_code: response.status,
    };
  }
}

function getErrorMessage(
  data,
  fallback = "Сталася помилка. Спробуйте ще раз.",
) {
  if (data && typeof data.error === "string" && data.error.trim()) {
    return data.error.trim();
  }

  if (data && typeof data.message === "string" && data.message.trim()) {
    return data.message.trim();
  }

  if (data && typeof data.details === "string" && data.details.trim()) {
    return data.details.trim();
  }

  if (data && data.status_code) {
    return getStatusFallbackMessage(data.status_code);
  }

  return fallback;
}

window.apiFetch = apiFetch;
window.readApiResponse = readApiResponse;
window.getErrorMessage = getErrorMessage;
