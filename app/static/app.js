document.querySelectorAll("[data-preview]").forEach((zone) => {
  const input = zone.querySelector("input[type=file]");
  const preview = zone.querySelector("img");
  input.addEventListener("change", () => {
    const [file] = input.files;
    if (!file) return;
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    zone.classList.add("has-image");
  });
});

document.querySelectorAll("#upload-form, form[data-processing]").forEach((form) => {
  form.addEventListener("submit", () => {
    form.querySelector("button[type=submit]").disabled = true;
    form.querySelector(".processing").hidden = false;
  });
});

document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});
