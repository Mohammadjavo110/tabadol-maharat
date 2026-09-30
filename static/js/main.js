document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-bs-toggle='tooltip']").forEach((element) => {
    new bootstrap.Tooltip(element);
  });

  document.querySelectorAll(".alert[data-autodismiss]").forEach((element) => {
    window.setTimeout(() => {
      const instance = bootstrap.Alert.getOrCreateInstance(element);
      instance.close();
    }, 6000);
  });
});
