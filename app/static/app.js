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

document.querySelectorAll("input[name=mode]").forEach((radio) => {
  radio.addEventListener("change", () => {
    document.querySelectorAll("[data-mode]").forEach((group) => {
      const active = group.dataset.mode === radio.value;
      group.hidden = !active;
      group.querySelectorAll("input[type=file]").forEach((input) => {
        if (!active) input.value = "";
      });
    });
  });
});

document.querySelectorAll("[data-swap]").forEach((button) => {
  button.addEventListener("click", () => {
    const [first, second] = button.dataset.swap.split(",").map((name) => document.querySelector(`[data-field="${name}"]`));
    [first.value, second.value] = [second.value, first.value];
  });
});
