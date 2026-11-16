# Build Log

## 2026-11-16 — v0.1 (initial release)

First working version of the GRC Evidence Tracker, a Python 3
(standard library only) CLI for managing audit evidence requests.

**Features**
- `init` — creates a local JSON data store (`grc_data.json`).
- `controls` — lists the bundled catalogue of 26 ISO 27001:2022
  Annex A controls across the Organizational, People, Physical and
  Technological themes; `--theme` filters by theme.
- `add-evidence` — records an evidence item (control id, title, owner,
  due date, status: requested / received / verified) with validation
  of control id, status and date format.
- `list` — shows evidence items and flags overdue ones (past due and
  not verified); `--overdue` shows only overdue items.
- `report` — exports `report.csv` (full detail with overdue flags)
  and `report.html` (counts by status + overdue list).

**Structure** — `grc_tracker` package (`cli`, `core`, `controls_data`,
`store`, `report`) with a thin `grc.py` entry point and a
`grc-tracker` console script via `pyproject.toml`.

**Tests** — pytest suite in `tests/` covering the store, the control
catalogue, add/list logic, overdue rules, CSV/HTML reports and CLI
end-to-end runs: **22 passed, 0 failed**.
