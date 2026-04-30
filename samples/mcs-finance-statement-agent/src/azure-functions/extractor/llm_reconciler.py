"""
extractor/llm_reconciler.py
---------------------------
Post-processing pass that uses Azure OpenAI to fix three classes of label
errors that occur when Azure Content Understanding processes page-spanning
financial tables:

  1. suppress_noise_rows()       — heuristic, no LLM
     Removes syntactically impossible tokens: currency unit headers like
     "(Yen)", broken sentence fragments like "of the", or section-numbering
     stubs. Applied using an explicit allowlist of impossible-label patterns
     so that real ghost rows (proper label, missing values) are never removed.

  2. reconcile_suspect_ghost()   — LLM (one call per statement)
     Fixes rows where Azure CU dropped the true row label entirely:
       SUSPECT row = correct values attached to a lowercase fragment label
       GHOST row   = correct uppercase label with no values
     GPT-4o-mini receives both lists and returns a suspect->ghost mapping.
     The fragment label is replaced with the true ghost label; the ghost row
     is then removed.

  3. complete_truncated_labels() — LLM (one call per statement)
     Fixes labels that end mid-phrase at a preposition or conjunction
     ("and", "for", "of", ...) because Azure CU wrapped the cell text and
     the continuation ended up after the values on the next token.
     All truncated labels are sent in a single batch for completion.

All LLM calls use response_format=json_object so no free-text parsing is
needed — the response is always a directly usable JSON structure.

Configuration (via .env):
  AZURE_OPENAI_ENDPOINT    — Azure OpenAI resource URL (no trailing slash)
  Authentication: Managed Identity (DefaultAzureCredential)
  Requires Cognitive Services OpenAI User role on the resource.
  AZURE_OPENAI_DEPLOYMENT  — Model deployment name (e.g. "gpt-4o-mini")
  AZURE_OPENAI_API_VERSION — API version (default: "2024-02-01")

Usage:
  Called automatically by statement_detector.build_statement_json when
  use_llm=True.  Can also be called directly:

    from extractor.llm_reconciler import reconcile
    rows, columns, cells = reconcile(statement_type, rows, columns, cells)
"""

import json
import os
import re
from typing import Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv(override=False)

# ---------------------------------------------------------------------------
# Azure OpenAI client  (lazy-initialised so import never fails if creds absent)
# ---------------------------------------------------------------------------

_client: Optional[AzureOpenAI] = None


def _get_client() -> AzureOpenAI:
    global _client
    if _client is None:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        api_ver  = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
        if not endpoint:
            raise EnvironmentError(
                "AZURE_OPENAI_ENDPOINT must be set in .env "
                "to use the LLM reconciler."
            )
        # Use API key if available, otherwise managed identity
        api_key = os.environ.get("AZURE_OPENAI_KEY")
        token_provider = None
        if not api_key:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default",
            )
        if api_key:
            _client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_ver,
                timeout=60.0,
            )
        else:
            _client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version=api_ver,
                timeout=60.0,
            )
    return _client


_DEPLOYMENT = lambda: os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# Helpers to navigate the cells list
# ---------------------------------------------------------------------------

def _build_grid(cells: list[dict]) -> dict[int, dict[int, str]]:
    """row_index -> {col_index -> content}"""
    grid: dict[int, dict[int, str]] = {}
    for c in cells:
        grid.setdefault(c["row"], {})[c["col"]] = c["content"]
    return grid


def _get_label(grid: dict, row: int) -> str:
    return grid.get(row, {}).get(0, "")


def _get_values(grid: dict, row: int) -> list[str]:
    d = grid.get(row, {})
    return [d[k] for k in sorted(k for k in d if k > 0)]


def _set_label(cells: list[dict], row: int, new_label: str) -> None:
    for c in cells:
        if c["row"] == row and c["col"] == 0:
            c["content"] = new_label
            return


def _remove_rows(cells: list[dict], row_indices: set[int]) -> list[dict]:
    return [c for c in cells if c["row"] not in row_indices]


# ---------------------------------------------------------------------------
# Step 1 — suppress_noise_rows  (no LLM)
# ---------------------------------------------------------------------------

# Patterns that are NEVER valid financial line-item labels.
# Only match when the row also has no values (empty row).
_NOISE_LABEL_RE = re.compile(
    r"^\(Yen\)$"                          # currency unit
    r"|^\(Millions"                        # currency unit
    r"|\bof the$"                          # broken sentence tail
    r"|^of\b"                              # broken sentence tail
    r"|^Company:?$"                        # ref to reporting entity
    r"|^attributable to"                   # incomplete phrase
    r"|\bper share attributable\b"         # EPS sub-header fragment
    r"|^\d+\\?\)$"                         # section numbering stub e.g. "3\)"
    r"|^-+$",                              # dash separators
    re.IGNORECASE,
)


def suppress_noise_rows(
    rows: list[str],
    columns: list[str],
    cells: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """
    Remove rows that are syntactically impossible as financial line items
    and have no values.  Only applies an explicit allowlist of patterns
    so that real rows with missing values (ghost rows) are never removed.
    """
    grid = _build_grid(cells)
    drop: set[int] = set()

    for row_idx in sorted(grid):
        label = _get_label(grid, row_idx)
        vals  = _get_values(grid, row_idx)
        if not vals and _NOISE_LABEL_RE.search(label):
            drop.add(row_idx)

    if not drop:
        return rows, columns, cells

    new_cells = _remove_rows(cells, drop)
    new_rows  = [r for i, r in enumerate(rows) if i not in drop]
    return new_rows, columns, new_cells


# ---------------------------------------------------------------------------
# Step 2 — reconcile_suspect_ghost  (LLM)
# ---------------------------------------------------------------------------

# A suspect label starts with lowercase — it is a continuation fragment, not
# a real label.  It has values because Azure CU attached them to the fragment
# instead of to the (dropped) true label.
_SUSPECT_RE = re.compile(r"^[a-z]")

# A trailing-preposition label was truncated at a page wrap.
_TRUNCATED_RE = re.compile(
    r"\b(and|for|of|in|the|by|to|from|with|under|on|at)\s*$",
    re.IGNORECASE,
)


def _heuristic_match_ghosts(
    suspects: list[dict],
    ghosts: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Deterministic matching for unambiguous suspect-ghost pairs.

    Matches are resolved without an LLM call when:
      - There is exactly one suspect and one ghost (trivially paired).
      - A ghost label ends with the suspect's fragment text (e.g. ghost
        "Net decrease (increase) in receivables under" contains suspect
        fragment "securities borrowing transactions" is proximate).
      - A suspect fragment is a suffix/substring of exactly one ghost label.

    Returns (heuristic_matches, remaining_suspects, remaining_ghosts).
    Each match is {"suspect_row": int, "ghost_row": int}.
    """
    # Trivial case: exactly one of each — pair them directly.
    if len(suspects) == 1 and len(ghosts) == 1:
        return (
            [{"suspect_row": suspects[0]["row"], "ghost_row": ghosts[0]["row"]}],
            [],
            [],
        )

    matches: list[dict] = []
    matched_suspect_rows: set[int] = set()
    matched_ghost_rows: set[int] = set()

    for s in suspects:
        frag = s["label"].lower().strip()
        # Find ghosts whose label contains the fragment as a substring.
        candidates = [
            g for g in ghosts
            if g["row"] not in matched_ghost_rows
            and frag in g["label"].lower()
        ]
        if len(candidates) == 1:
            matches.append({
                "suspect_row": s["row"],
                "ghost_row": candidates[0]["row"],
            })
            matched_suspect_rows.add(s["row"])
            matched_ghost_rows.add(candidates[0]["row"])

    remaining_suspects = [s for s in suspects if s["row"] not in matched_suspect_rows]
    remaining_ghosts = [g for g in ghosts if g["row"] not in matched_ghost_rows]
    return matches, remaining_suspects, remaining_ghosts


def _apply_ghost_matches(
    matches: list[dict],
    valid_suspect_rows: set[int],
    valid_ghost_rows: set[int],
    grid: dict[int, dict[int, str]],
    rows: list[str],
    cells: list[dict],
    source: str,
) -> set[int]:
    """
    Apply validated suspect->ghost label swaps and return the set of ghost
    row indices to drop.

    Validates every match returned by the LLM or heuristic:
      - suspect_row must be in valid_suspect_rows
      - ghost_row must be in valid_ghost_rows
      - ghost_row must not already be claimed by a prior match (no duplicates)
    Invalid mappings are logged and skipped — never silently applied.
    """
    drop_after_swap: set[int] = set()
    used_ghosts: set[int] = set()

    for m in matches:
        suspect_row = m.get("suspect_row")
        ghost_row = m.get("ghost_row")

        # --- Guard: reject None / non-integer values ---
        if suspect_row is None or ghost_row is None:
            continue

        # --- Guard: reject row indices not in the sets we sent ---
        if suspect_row not in valid_suspect_rows:
            print(f"        [{source}] REJECTED: suspect_row {suspect_row} "
                  f"not in valid set {sorted(valid_suspect_rows)}")
            continue
        if ghost_row not in valid_ghost_rows:
            print(f"        [{source}] REJECTED: ghost_row {ghost_row} "
                  f"not in valid set {sorted(valid_ghost_rows)}")
            continue

        # --- Guard: reject duplicate ghost targets ---
        if ghost_row in used_ghosts:
            print(f"        [{source}] REJECTED: ghost_row {ghost_row} "
                  f"already matched to another suspect")
            continue

        ghost_label = _get_label(grid, ghost_row)
        if not ghost_label:
            continue

        # Apply the swap: update both cells and rows to stay in sync.
        old_label = _get_label(grid, suspect_row)
        _set_label(cells, suspect_row, ghost_label)
        if suspect_row < len(rows):
            rows[suspect_row] = ghost_label

        drop_after_swap.add(ghost_row)
        used_ghosts.add(ghost_row)
        print(f"        [{source}] row {suspect_row}: '{old_label}' -> '{ghost_label}'")

    return drop_after_swap


def reconcile_suspect_ghost(
    statement_type: str,
    rows: list[str],
    columns: list[str],
    cells: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """
    Match suspect rows (fragment label + correct values) to ghost rows
    (real label + no values), then swap the labels.

    Two-phase approach to minimise LLM cost:
      1. Heuristic pass — resolve unambiguous pairs deterministically.
      2. LLM pass — send only remaining ambiguous candidates to GPT-4o-mini.

    All matches (heuristic or LLM) are validated against the known set of
    suspect/ghost row indices before application.  Duplicate ghost targets
    and out-of-range indices are rejected with a logged warning.
    """
    grid = _build_grid(cells)

    suspects: list[dict] = []   # {"row": int, "label": str, "values": list}
    ghosts: list[dict] = []     # {"row": int, "label": str}

    for row_idx in sorted(grid):
        label = _get_label(grid, row_idx)
        vals = _get_values(grid, row_idx)
        if vals and _SUSPECT_RE.match(label):
            suspects.append({"row": row_idx, "label": label, "values": vals})
        elif not vals and label and not _SUSPECT_RE.match(label):
            ghosts.append({"row": row_idx, "label": label})

    if not suspects or not ghosts:
        return rows, columns, cells

    # Build validity sets from the candidates we identified — any row index
    # not in these sets is out-of-scope and must be rejected.
    valid_suspect_rows: set[int] = {s["row"] for s in suspects}
    valid_ghost_rows: set[int] = {g["row"] for g in ghosts}

    print(f"      [reconcile] {len(suspects)} suspects, {len(ghosts)} ghosts")

    # --- Phase 1: heuristic matching (free, deterministic) ---
    heuristic_matches, remaining_suspects, remaining_ghosts = (
        _heuristic_match_ghosts(suspects, ghosts)
    )

    all_drops: set[int] = set()

    if heuristic_matches:
        print(f"      [heuristic] resolved {len(heuristic_matches)} match(es) without LLM")
        drops = _apply_ghost_matches(
            heuristic_matches, valid_suspect_rows, valid_ghost_rows,
            grid, rows, cells, source="heuristic",
        )
        all_drops |= drops

    # --- Phase 2: LLM matching for remaining ambiguous candidates ---
    if remaining_suspects and remaining_ghosts:
        print(f"      [LLM] reconcile_suspect_ghost: "
              f"{len(remaining_suspects)} suspects, {len(remaining_ghosts)} ghosts")

        prompt = (
            f"You are reconciling a {statement_type.replace('_', ' ')} "
            f"where an OCR tool dropped some row labels at page boundaries.\n\n"
            f"SUSPECT ROWS — values are correct but the label is a continuation "
            f"fragment (NOT the true label):\n"
            f"{json.dumps(remaining_suspects, indent=2)}\n\n"
            f"GHOST ROWS — label is correct but values are missing (they were "
            f"attached to a suspect row instead):\n"
            f"{json.dumps(remaining_ghosts, indent=2)}\n\n"
            f"Match each suspect row to the ghost row whose label is the true "
            f"label for those values.\n"
            f"Not every suspect needs a match.\nNot every ghost needs a match.\n\n"
            f"Return ONLY a JSON object with key \"matches\" containing an array "
            f"of objects:\n  {{\"suspect_row\": <int>, \"ghost_row\": <int>}}"
        )

        client = _get_client()
        response = client.chat.completions.create(
            model=_DEPLOYMENT(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a financial data quality expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content
        try:
            result = json.loads(raw)
            llm_matches = result.get("matches", [])
        except (json.JSONDecodeError, AttributeError):
            print("      [LLM] reconcile_suspect_ghost: bad JSON response, skipping")
            llm_matches = []

        # Validated application — rejects out-of-set indices and duplicates.
        drops = _apply_ghost_matches(
            llm_matches, valid_suspect_rows, valid_ghost_rows,
            grid, rows, cells, source="LLM",
        )
        all_drops |= drops

    new_cells = _remove_rows(cells, all_drops)
    new_rows = [r for i, r in enumerate(rows) if i not in all_drops]
    return new_rows, columns, new_cells


# ---------------------------------------------------------------------------
# Step 3 — complete_truncated_labels  (LLM)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Common IFRS label completions — used by the heuristic pass to avoid an LLM
# call for well-known truncated phrases.  Keys are the truncated suffix
# (lowercased, stripped); values are the full completion suffix to append.
# ---------------------------------------------------------------------------
_KNOWN_COMPLETIONS: dict[str, str] = {
    "proceeds from sales and": "redemption of investment securities",
    "proceeds from sales and redemption of investment": "securities",
    "purchases of investment securities for": "banking business",
    "net decrease (increase) in receivables under": "securities borrowing transactions",
    "increase and decrease in derivative assets and": "liabilities",
    "proceeds from sales of investments in associates and": "joint ventures",
    "acquisitions of investments in associates and": "joint ventures",
    "net increase (decrease) in": "short-term borrowings",
    "per share attributable to owners of": "the Company",
    "equity attributable to owners of": "the Company",
    "profit (loss) attributable to owners of": "the Company",
    "cash equivalents at end of the": "period",
    "restricted cash equivalents at end of the": "period",
    "cash, cash equivalents, and restricted cash equivalents at end of the": "period",
    "cash and cash equivalents at end of the": "period",
    "cash and cash equivalents at beginning of the": "period",
}


def _heuristic_complete_labels(
    truncated: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Complete truncated labels using a lookup table of known IFRS phrases.

    Returns (completions, remaining) where completions is a list of
    {"row": int, "completed_label": str} and remaining is the list of
    truncated entries that could not be resolved heuristically.
    """
    completions: list[dict] = []
    remaining: list[dict] = []

    for entry in truncated:
        label_lower = entry["label"].lower().strip()
        matched = False
        for prefix, suffix in _KNOWN_COMPLETIONS.items():
            if label_lower == prefix or label_lower.endswith(prefix):
                completions.append({
                    "row": entry["row"],
                    "completed_label": entry["label"].rstrip() + " " + suffix,
                })
                matched = True
                break
        if not matched:
            remaining.append(entry)

    return completions, remaining


def _apply_label_completions(
    completions: list[dict],
    valid_rows: set[int],
    grid: dict[int, dict[int, str]],
    rows: list[str],
    cells: list[dict],
    source: str,
) -> None:
    """
    Apply validated label completions to both cells and rows.

    Rejects any row index not in valid_rows — prevents the LLM from
    silently overwriting labels on rows that were not sent for completion.
    """
    for comp in completions:
        row_idx = comp.get("row")
        new_label = comp.get("completed_label", "").strip()
        if row_idx is None or not new_label:
            continue

        # --- Guard: reject row indices not in the set we sent ---
        if row_idx not in valid_rows:
            print(f"        [{source}] REJECTED: row {row_idx} "
                  f"not in valid set {sorted(valid_rows)}")
            continue

        old_label = _get_label(grid, row_idx)
        _set_label(cells, row_idx, new_label)
        # Keep rows list in sync with cells.
        if row_idx < len(rows):
            rows[row_idx] = new_label
        print(f"        [{source}] row {row_idx}: '{old_label}' -> '{new_label}'")


def complete_truncated_labels(
    statement_type: str,
    rows: list[str],
    columns: list[str],
    cells: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """
    Complete labels that end mid-phrase at a preposition or conjunction.

    Two-phase approach to minimise LLM cost:
      1. Heuristic pass — resolve known IFRS phrases from a lookup table.
      2. LLM pass — send only remaining unknown truncations to GPT-4o-mini.

    All completions are validated: only row indices that were identified as
    truncated are accepted.  Out-of-range indices from the LLM are rejected.
    """
    grid = _build_grid(cells)

    truncated: list[dict] = []  # {"row": int, "label": str}
    for row_idx in sorted(grid):
        label = _get_label(grid, row_idx)
        vals = _get_values(grid, row_idx)
        if vals and _TRUNCATED_RE.search(label):
            truncated.append({"row": row_idx, "label": label})

    if not truncated:
        return rows, columns, cells

    # Build validity set — only these row indices may be modified.
    valid_rows: set[int] = {t["row"] for t in truncated}

    print(f"      [truncated] {len(truncated)} truncated labels detected")

    # --- Phase 1: heuristic completion (free, deterministic) ---
    heuristic_completions, remaining = _heuristic_complete_labels(truncated)

    if heuristic_completions:
        print(f"      [heuristic] completed {len(heuristic_completions)} label(s) from lookup table")
        _apply_label_completions(
            heuristic_completions, valid_rows, grid, rows, cells,
            source="heuristic",
        )

    # --- Phase 2: LLM completion for remaining unknown truncations ---
    if remaining:
        print(f"      [LLM] complete_truncated_labels: {len(remaining)} remaining")

        prompt = (
            f"You are correcting truncated row labels in a "
            f"{statement_type.replace('_', ' ')} financial statement.\n"
            f"Each label below was cut off mid-phrase by an OCR tool at a page boundary.\n"
            f"Complete each label to its full, standard IFRS financial statement wording.\n"
            f"Keep the completion minimal — only add the words needed to complete the phrase.\n\n"
            f"Labels to complete:\n{json.dumps(remaining, indent=2)}\n\n"
            f"Return ONLY a JSON object with key \"completions\" containing an array of objects:\n"
            f"  {{\"row\": <int>, \"completed_label\": \"<full label string>\"}}\n"
            f"Only include rows where you are confident in the completion."
        )

        client = _get_client()
        response = client.chat.completions.create(
            model=_DEPLOYMENT(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a financial data quality expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content
        try:
            result = json.loads(raw)
            llm_completions = result.get("completions", [])
        except (json.JSONDecodeError, AttributeError):
            print("      [LLM] complete_truncated_labels: bad JSON response, skipping")
            llm_completions = []

        _apply_label_completions(
            llm_completions, valid_rows, grid, rows, cells, source="LLM",
        )

    return rows, columns, cells


# ---------------------------------------------------------------------------
# Step 4 — align_underpopulated_columns  (subtotal-constrained solver)
# ---------------------------------------------------------------------------
# When Azure CU drops nil-dash markers ("—"), a row ends up with fewer values
# than expected.  The parser fills values left-to-right, so they land in the
# wrong columns.
#
# This step uses SECTION SUBTOTALS as ground truth to determine the correct
# column placement.  For each section (operating, investing, financing):
#   1. Parse the subtotal row's values (these are always fully populated).
#   2. Sum all fully-populated line-item rows in the section.
#   3. The remaining deficit per column = the sum of under-populated rows'
#      correct values for that column.
#   4. Try all possible column placements for each under-populated row and
#      pick the combination where the column sums match the deficit.
#
# This is deterministic, free (no LLM call), and constrained by arithmetic.
# Falls back to LLM only if subtotal matching fails.

from itertools import combinations as _combinations


def _parse_value_float(raw: str) -> float:
    """Parse a financial value string to float. Returns 0.0 for empty/unparseable."""
    s = raw.strip()
    if not s:
        return 0.0
    # Strip currency symbols
    s = re.sub(r"^[\$\u00a5\u20ac\u00a3]\s*", "", s)
    if not s:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "")
    try:
        val = float(s)
        return -val if neg else val
    except ValueError:
        return 0.0


def _find_sections(
    grid: dict[int, dict[int, str]],
    expected_cols: int,
) -> list[dict]:
    """
    Identify sections in a cash-flow-style statement.

    A section starts at a section_header and ends at a subtotal row (inclusive).
    Returns a list of dicts:
      {"subtotal_row": int, "subtotal_vals": [float, ...],
       "line_item_rows": [int, ...]}
    """
    # Walk rows in order to find subtotal rows and their preceding line items.
    sorted_rows = sorted(grid.keys())
    sections: list[dict] = []
    current_items: list[int] = []

    for row_idx in sorted_rows:
        label = grid[row_idx].get(0, "")
        vals = [grid[row_idx].get(c, "") for c in range(1, expected_cols + 1)]
        non_empty = [v for v in vals if v.strip()]

        label_lower = label.lower().strip()
        is_subtotal = (
            (label_lower.startswith("net cash") or
             label_lower.startswith("total ")) and
            len(non_empty) == expected_cols
        )

        if is_subtotal:
            sections.append({
                "subtotal_row": row_idx,
                "subtotal_vals": [_parse_value_float(v) for v in vals],
                "line_item_rows": list(current_items),
            })
            current_items = []
        elif non_empty:
            current_items.append(row_idx)

    return sections


def align_underpopulated_columns(
    statement_type: str,
    rows: list[str],
    columns: list[str],
    cells: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """
    Fix column alignment for rows that have fewer values than expected.

    Uses section subtotals as arithmetic constraints to determine the correct
    column placement.  For each section, computes the deficit between the
    subtotal and the sum of fully-populated rows, then searches for a column
    assignment of under-populated rows that closes the deficit.

    Falls back to LLM if subtotal-based solving is not possible (e.g. no
    subtotals available, or the combinatorial search finds no exact match).
    """
    expected_cols = len(columns)
    if expected_cols < 2:
        return rows, columns, cells

    grid = _build_grid(cells)

    # Classify rows.
    underpopulated_map: dict[int, list[str]] = {}  # row_idx -> non-empty values
    for row_idx in sorted(grid):
        vals = [grid[row_idx].get(c, "") for c in range(1, expected_cols + 1)]
        non_empty = [v for v in vals if v.strip()]
        empty_count = expected_cols - len(non_empty)
        if non_empty and empty_count > 0:
            underpopulated_map[row_idx] = non_empty

    if not underpopulated_map:
        return rows, columns, cells

    print(f"      [align] {len(underpopulated_map)} under-populated row(s) "
          f"(expected {expected_cols} cols)")

    # Find sections with subtotals.
    sections = _find_sections(grid, expected_cols)

    # For each section, solve the column alignment.
    solved: dict[int, list[int]] = {}  # row_idx -> column_mapping

    for sec in sections:
        subtotal = sec["subtotal_vals"]
        sec_underpop = [r for r in sec["line_item_rows"] if r in underpopulated_map]
        if not sec_underpop:
            continue

        # Sum fully-populated rows in this section.
        col_sums = [0.0] * expected_cols
        for r in sec["line_item_rows"]:
            if r not in underpopulated_map:
                for c in range(expected_cols):
                    col_sums[c] += _parse_value_float(
                        grid[r].get(c + 1, "")
                    )

        # Deficit per column = subtotal - sum of fully-populated rows.
        deficit = [subtotal[c] - col_sums[c] for c in range(expected_cols)]

        # For each under-populated row, generate all valid column placements.
        # Then search for the combination that closes the deficit.
        def _solve_rows(
            remaining: list[int],
            current_deficit: list[float],
        ) -> dict[int, list[int]] | None:
            """Recursive backtracking solver."""
            if not remaining:
                # Check if deficit is approximately zero.
                if all(abs(d) < 2.0 for d in current_deficit):
                    return {}
                return None

            row_idx = remaining[0]
            rest = remaining[1:]
            vals = underpopulated_map[row_idx]
            n_vals = len(vals)
            parsed_vals = [_parse_value_float(v) for v in vals]

            # Generate all possible column placements (combinations of n_vals
            # columns from expected_cols).
            for col_combo in _combinations(range(expected_cols), n_vals):
                # Check this placement.
                new_deficit = list(current_deficit)
                for vi, ci in enumerate(col_combo):
                    new_deficit[ci] -= parsed_vals[vi]

                result = _solve_rows(rest, new_deficit)
                if result is not None:
                    # col_combo is 0-indexed, convert to 1-indexed.
                    result[row_idx] = [c + 1 for c in col_combo]
                    return result

            return None

        solution = _solve_rows(sec_underpop, deficit)
        if solution:
            solved.update(solution)
            for r, mapping in solution.items():
                print(f"        [align-solve] row {r} '{_get_label(grid, r)}': "
                      f"values {underpopulated_map[r]} -> columns {mapping}")
        else:
            print(f"        [align] section ending at row {sec['subtotal_row']}: "
                  f"no exact solution found for {len(sec_underpop)} row(s)")

    # Apply solved alignments.
    for row_idx, col_mapping in solved.items():
        current_vals = underpopulated_map[row_idx]

        label_cell = None
        for c in cells:
            if c["row"] == row_idx and c["col"] == 0:
                label_cell = c
                break
        if not label_cell:
            continue

        rt = label_cell.get("row_type", "line_item")
        il = label_cell.get("indent_level", 0)

        # Remove existing value cells for this row.
        cells = [c for c in cells if not (c["row"] == row_idx and c["col"] > 0)]

        # Re-emit value cells at the correct column positions.
        for col_idx in range(1, expected_cols + 1):
            if col_idx in col_mapping:
                val_pos = col_mapping.index(col_idx)
                val = current_vals[val_pos]
            else:
                val = ""
            cells.append({
                "row": row_idx, "col": col_idx, "content": val,
                "kind": "content", "currency": None,
                "row_type": rt, "indent_level": il,
            })

        # Remove column_alignment_warning from label cell if present.
        if "column_alignment_warning" in label_cell:
            del label_cell["column_alignment_warning"]

    # LLM fallback for unsolved rows.
    unsolved = [r for r in underpopulated_map if r not in solved]
    if unsolved:
        print(f"      [align-LLM] {len(unsolved)} row(s) unsolved, using LLM fallback")

        unsolved_data = [
            {"row": r, "label": _get_label(grid, r),
             "values": underpopulated_map[r]}
            for r in unsolved
        ]

        # Gather all rows (fully populated) as context.
        context = []
        for row_idx in sorted(grid):
            vals = _get_values(grid, row_idx)
            non_empty = [v for v in vals if v.strip()]
            if len(non_empty) == expected_cols:
                context.append({
                    "row": row_idx,
                    "label": _get_label(grid, row_idx),
                    "values": non_empty,
                })

        prompt = (
            f"You are fixing column alignment in a {statement_type.replace('_', ' ')}.\n"
            f"Columns: {json.dumps(columns)}\n\n"
            f"Column 1 = Q current year, Column 2 = Q prior year, "
            f"Column 3 = FY current year, Column 4 = FY prior year.\n"
            f"FY values are ALWAYS >= Q values in absolute magnitude.\n"
            f"Prior-year-only items go in columns 2 or 4.\n\n"
            f"Reference rows:\n{json.dumps(context[:10], indent=2)}\n\n"
            f"Fix these rows:\n{json.dumps(unsolved_data, indent=2)}\n\n"
            f"Return JSON: {{\"alignments\": [{{\"row\": int, "
            f"\"column_mapping\": [col_idx, ...]}}]}}"
        )

        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=_DEPLOYMENT(),
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a financial data quality expert. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            result = json.loads(response.choices[0].message.content)
            for alignment in result.get("alignments", []):
                row_idx = alignment.get("row")
                col_mapping = alignment.get("column_mapping", [])
                if row_idx not in underpopulated_map:
                    continue
                vals = underpopulated_map[row_idx]
                if len(col_mapping) != len(vals):
                    continue
                if not all(isinstance(c, int) and 1 <= c <= expected_cols for c in col_mapping):
                    continue
                # Apply the alignment.
                label_cell = next((c for c in cells if c["row"] == row_idx and c["col"] == 0), None)
                if not label_cell:
                    continue
                rt = label_cell.get("row_type", "line_item")
                il = label_cell.get("indent_level", 0)
                cells = [c for c in cells if not (c["row"] == row_idx and c["col"] > 0)]
                for col_idx in range(1, expected_cols + 1):
                    val = vals[col_mapping.index(col_idx)] if col_idx in col_mapping else ""
                    cells.append({
                        "row": row_idx, "col": col_idx, "content": val,
                        "kind": "content", "currency": None,
                        "row_type": rt, "indent_level": il,
                    })
                if "column_alignment_warning" in label_cell:
                    del label_cell["column_alignment_warning"]
                print(f"        [align-LLM] row {row_idx} '{_get_label(grid, row_idx)}': "
                      f"values {vals} -> columns {col_mapping}")
        except Exception as e:
            print(f"      [align-LLM] fallback failed: {e}")

    return rows, columns, cells


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def reconcile(
    statement_type: str,
    rows: list[str],
    columns: list[str],
    cells: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """
    Run all four reconciliation steps in order:
      1. suppress_noise_rows            (heuristic, always runs)
      2. reconcile_suspect_ghost        (LLM, only when suspects+ghosts detected)
      3. complete_truncated_labels      (LLM, only when truncated labels detected)
      4. align_underpopulated_columns   (LLM, only when under-populated rows exist)

    Returns updated (rows, columns, cells).
    Raises EnvironmentError if Azure OpenAI credentials are missing.
    """
    rows, columns, cells = suppress_noise_rows(rows, columns, cells)
    rows, columns, cells = reconcile_suspect_ghost(statement_type, rows, columns, cells)
    rows, columns, cells = complete_truncated_labels(statement_type, rows, columns, cells)
    rows, columns, cells = align_underpopulated_columns(statement_type, rows, columns, cells)
    return rows, columns, cells
