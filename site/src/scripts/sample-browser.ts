export function initSampleBrowser() {
  const search = document.querySelector<HTMLInputElement>("#sample-search");
  const pills = Array.from(document.querySelectorAll<HTMLButtonElement>("#type-pills .pill"));
  const cards = Array.from(document.querySelectorAll<HTMLElement>("#samples-grid .sample-card"));
  const empty = document.querySelector<HTMLElement>("#empty-state");
  const clearFilters = document.querySelector<HTMLButtonElement>("#clear-filters");
  const visibleCount = document.querySelector<HTMLElement>("#visible-count");
  const activeSummary = document.querySelector<HTMLElement>("#active-summary");
  const catalogCount = document.querySelector<HTMLElement>("#catalog-count");

  if (!search || pills.length === 0 || cards.length === 0) {
    return;
  }

  let activeType = "all";

  const applyFilters = () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;

    for (const card of cards) {
      const byType = activeType === "all" || card.dataset.type === activeType;
      const haystack = `${card.dataset.title} ${card.dataset.folder} ${card.dataset.description}`;
      const byQuery = haystack.includes(query);
      const show = byType && byQuery;

      card.classList.toggle("hidden", !show);
      if (show) {
        visible += 1;
      }
    }

    if (empty) {
      empty.classList.toggle("hidden", visible !== 0);
    }

    if (visibleCount) {
      visibleCount.textContent = String(visible);
    }

    if (catalogCount) {
      catalogCount.textContent = String(visible);
    }

    if (activeSummary) {
      const typeLabel = activeType === "all" ? "all sample types" : activeType;
      const queryLabel = query.length > 0 ? `matching “${search.value.trim()}”` : "with no search term";
      activeSummary.textContent = `Showing ${typeLabel} ${queryLabel}.`;
    }
  };

  search.addEventListener("input", applyFilters);

  for (const pill of pills) {
    pill.addEventListener("click", () => {
      activeType = pill.dataset.type || "all";
      for (const item of pills) {
        item.classList.toggle("chip-button-active", item === pill);
        item.setAttribute("aria-pressed", String(item === pill));
      }
      applyFilters();
    });
  }

  clearFilters?.addEventListener("click", () => {
    activeType = "all";
    search.value = "";
    for (const item of pills) {
      const isAll = item.dataset.type === "all";
      item.classList.toggle("chip-button-active", isAll);
      item.setAttribute("aria-pressed", String(isAll));
    }
    applyFilters();
    search.focus();
  });

  applyFilters();
}
