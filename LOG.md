# Build Log

## 2026-11-16 — v0.2 (SOC 2 control set)

Second bundled catalogue, so one store can track evidence for either
framework — or both.

**Features**
- `SOC2_CONTROLS` — the 33 SOC 2 Trust Services Criteria common
  criteria (CC1.1–CC9.2, AICPA 2017) across their nine categories
  (Organization and Management through Risk Mitigation), alongside the
  existing 26 ISO 27001 controls; every control now carries a
  `framework` key, and catalogues are looked up per framework
  (`controls_for` / `controls_by_id` / `themes_for`).
- `--framework {iso27001,soc2}` flag on `controls` (default
  `iso27001`, with `--theme` validated against the selected
  framework's themes/categories) and on `add-evidence` (default
  `iso27001`); a control id from the other framework is rejected.
- Store records which framework each item belongs to (`framework`
  field on every new item); listings and the add confirmation show it
  as `[framework/control]`, and the CSV report gains a `framework`
  column. Items stored by v0.1 (no `framework` key) are treated as
  `iso27001` everywhere.

**Tests** — pytest suite extended with SOC 2 catalogue coverage,
per-framework validation, mixed-framework and legacy-store reports,
and CLI end-to-end runs for both frameworks: **36 passed, 0 failed**
(was 22 at v0.1).

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
