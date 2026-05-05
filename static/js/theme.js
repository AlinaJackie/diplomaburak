(function () {
  const STORAGE_KEY = "foodgo_theme";
  const root = document.documentElement;
  const toggle = document.getElementById("themeToggle");

  function getStoredTheme() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      if (value === "light" || value === "dark") return value;
      return null;
    } catch {
      return null;
    }
  }

  function getSystemTheme() {
    try {
      return window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    } catch {
      return "light";
    }
  }

  function applyTheme(theme) {
    const nextTheme = theme === "dark" ? "dark" : "light";
    root.dataset.theme = nextTheme;

    if (toggle) {
      toggle.setAttribute("aria-pressed", String(nextTheme === "dark"));
      toggle.setAttribute(
        "aria-label",
        nextTheme === "dark" ? "Switch to light theme" : "Switch to dark theme",
      );
      toggle.title =
        nextTheme === "dark" ? "Switch to light theme" : "Switch to dark theme";
    }
  }

  function setTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Ignore storage errors (private mode / blocked storage).
    }
    applyTheme(theme);
  }

  // Ensure state is consistent with the early inline theme application (if any).
  applyTheme(getStoredTheme() || root.dataset.theme || getSystemTheme());

  if (!toggle) return;

  toggle.addEventListener("click", () => {
    const current = root.dataset.theme === "dark" ? "dark" : "light";
    setTheme(current === "dark" ? "light" : "dark");
  });
})();

