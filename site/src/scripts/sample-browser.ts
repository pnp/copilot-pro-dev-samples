export function initSampleBrowser() {
  const search = document.querySelector<HTMLInputElement>("#sample-search");
  const type = document.querySelector<HTMLSelectElement>("#sample-type");
  const cards = Array.from(document.querySelectorAll<HTMLElement>("#samples-grid [data-sample-card]"));
  const empty = document.querySelector<HTMLElement>("#empty-state");
  const summary = document.querySelector<HTMLElement>("#active-summary");

  if (!search || !type || !empty || !summary) {
    throw new Error("Sample catalog controls could not be initialized.");
  }

  const query = new URLSearchParams(window.location.search);
  search.value = query.get("q") ?? "";
  const requestedType = query.get("type");
  if (requestedType && Array.from(type.options).some((option) => option.value === requestedType)) {
    type.value = requestedType;
  }

  const applyFilters = () => {
    const text = search.value.trim().toLowerCase();
    let visible = 0;
    for (const card of cards) {
      const matchesType = type.value === "all" || card.dataset.type === type.value;
      const matchesText = `${card.dataset.title} ${card.dataset.folder} ${card.dataset.description}`.includes(text);
      card.hidden = !matchesType || !matchesText;
      if (!card.hidden) visible += 1;
    }
    empty.hidden = visible > 0;
    summary.textContent = `Showing ${visible} of ${cards.length} samples`;
    const nextQuery = new URLSearchParams();
    if (text) nextQuery.set("q", search.value.trim());
    if (type.value !== "all") nextQuery.set("type", type.value);
    window.history.replaceState({}, "", `${window.location.pathname}${nextQuery.size ? `?${nextQuery}` : ""}${window.location.hash}`);
  };

  const clear = () => {
    search.value = "";
    type.value = "all";
    applyFilters();
    search.focus();
  };

  search.addEventListener("input", applyFilters);
  type.addEventListener("change", applyFilters);
  document.querySelector("#clear-filters")?.addEventListener("click", clear);
  document.querySelector("#empty-clear")?.addEventListener("click", clear);
  applyFilters();
}
