export function initSampleBrowser() {
  const search = document.querySelector<HTMLInputElement>("#sample-search");
  const pills = Array.from(document.querySelectorAll<HTMLButtonElement>("#type-pills .pill"));
  const cards = Array.from(document.querySelectorAll<HTMLElement>("#samples-grid .sample-card"));
  const empty = document.querySelector<HTMLElement>("#empty-state");

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
  };

  search.addEventListener("input", applyFilters);

  for (const pill of pills) {
    pill.addEventListener("click", () => {
      activeType = pill.dataset.type || "all";
      for (const item of pills) {
        item.classList.toggle("chip-button-active", item === pill);
      }
      applyFilters();
    });
  }

  applyFilters();
}
