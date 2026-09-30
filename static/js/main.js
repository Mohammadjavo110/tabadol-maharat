/* Liquid Glass: بازتاب نقطه‌ای و تعویض پوسته */

(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const THEME_KEY = "webdan-theme";

  /* ---------- تعویض روشن/تیره ---------- */

  const applyTheme = (theme) => {
    if (theme === "light" || theme === "dark") {
      document.documentElement.dataset.theme = theme;
    } else {
      delete document.documentElement.dataset.theme;
    }
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const isDark = isDarkMode();
      button.textContent = isDark ? "☀" : "☾";
      button.setAttribute("aria-label", isDark ? "حالت روشن" : "حالت تیره");
    });
  };

  const isDarkMode = () => {
    const explicit = document.documentElement.dataset.theme;
    if (explicit) return explicit === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  };

  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored) applyTheme(stored);
    else applyTheme(null);
  } catch {
    applyTheme(null);
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-theme-toggle]");
    if (!button) return;
    const next = isDarkMode() ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* حالت خصوصی مرورگر */
    }
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (!document.documentElement.dataset.theme) applyTheme(null);
  });

  /* ---------- بازتاب specular روی اشاره‌گر ---------- */

  const track = (element) => {
    element.addEventListener(
      "pointermove",
      (event) => {
        if (reduceMotion.matches || !finePointer.matches) return;
        const box = element.getBoundingClientRect();
        element.style.setProperty("--mx", `${event.clientX - box.left}px`);
        element.style.setProperty("--my", `${event.clientY - box.top}px`);
      },
      { passive: true }
    );
  };

  const init = () => {
    document
      .querySelectorAll(".glass, .glass-lift, .btn, .hero-glass, .nav-pills .nav-link")
      .forEach(track);
  };

  init();
  document.addEventListener("DOMContentLoaded", init);

  /* ---------- بستن هشدارها ---------- */

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".alert[data-autodismiss]").forEach((element) => {
      window.setTimeout(() => bootstrap.Alert.getOrCreateInstance(element).close(), 6000);
    });
  });
})();