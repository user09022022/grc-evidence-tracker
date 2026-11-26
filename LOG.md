# Build Log

## 2026-11-25 — v0.6 (Multi-engagement support)

One store no longer means one engagement: a firm running several
audits at once can keep them apart without juggling JSON files.

**Features**
- Named engagements — `add-engagement --name --client --framework
  --period` creates an engagement record (`core.add_engagement`,
  duplicate/empty names, empty client and unknown framework
  rejected); `engagements` lists every engagement with its item and
  overdue counts, plus any unassigned items. The store gains an
  `engagements` list (store version 2); pre-v0.6 stores load with an
  empty list and their items are treated as unassigned.
- Scoped evidence — `add-evidence --engagement NAME` assigns an item
  to an existing engagement (unknown names rejected; the framework
  is inherited from the engagement, and an explicitly passed
  `--framework` that disagrees with it is rejected). Every item
  records its `engagement` (or none), shown in `list` and `show`.
- Scoped commands — `list`, `due` (including its reminder digest)
  and `report` all accept `--engagement NAME`, backed by
  `core.scoped_items` / scoped `status_counts`, `overdue_items` and
  `due_within_items`; an unknown name fails cleanly instead of
  silently returning an empty view.
- Reports — the CSV and Excel detail gain an `engagement` column,
  and the HTML report always includes a cross-engagement summary
  (`core.engagement_summaries`): one row per engagement with client,
  framework, period, total, by-status and overdue counts, plus a
  "(no engagement)" row when unassigned items exist. A scoped HTML
  report still carries the full cross-engagement summary.

**Tests** — pytest suite extended with engagement creation and
validation, framework inheritance/mismatch, scoping for list/due/
counts/reports/digest, cross-engagement summaries, legacy-store
handling, and CLI end-to-end runs for `add-engagement`,
`engagements`, and the `--engagement` flags:
**115 passed, 0 failed** (was 85 at v0.5).

## 2026-11-23 — v0.5 (Excel export)

Status reporting now produces a workbook an engagement team can
open, filter and present, without giving up the dependency-free core.

**Features**
- `report --format xlsx` — writes `report.xlsx`, a formatted Excel
  workbook produced by `report.write_xlsx`: a Summary sheet
  (generation date, counts by status, total and overdue count, with
  bold header/total rows) and a Detail sheet (one row per item with
  the same columns as the CSV report, styled header, frozen top row,
  auto-filter and overdue rows highlighted).
- `report --format {all,csv,html,xlsx}` — `csv` / `html` write just
  that one format; the default `all` keeps the previous behaviour
  (CSV + HTML) so existing workflows are unchanged.
- `openpyxl` is the project's first third-party dependency, and it
  stays optional: it is declared as the `xlsx` extra in
  `pyproject.toml` and imported lazily inside `write_xlsx`, so every
  other command still runs on the standard library alone. Without
  openpyxl, the xlsx format fails cleanly with install guidance.

**Tests** — pytest suite extended with workbook structure, summary
counts, detail rows (including SOC 2 framework and the empty store),
and CLI end-to-end runs for `--format xlsx` and `--format csv`
(the xlsx tests skip cleanly when openpyxl is not installed):
**85 passed, 0 failed** (was 78 at v0.4).

## 2026-11-20 — v0.4 (Status workflow commands)

Corrections no longer mean editing the JSON store by hand, and a
single item can be inspected with everything that has happened to it.

**Features**
- `update <id>` command — changes an item's status, owner and/or due
  date in place (`--status` / `--owner` / `--due`), backed by
  `core.update_evidence`. Validation matches `add-evidence` (status
  must be a known status, due date must be YYYY-MM-DD, owner must not
  be empty); an unknown id, no fields, or values that already match
  the item are rejected without touching the store.
- Change history — every new item starts with an empty `history`
  list, and each field `update` actually changes appends a
  `{date, field, old, new}` entry (in status / owner / due-date
  order), exposed via `core.find_item` / `core.item_history`.
  Items stored before v0.4 (no `history` key) are treated as having
  no recorded changes and can be updated normally.
- `show <id>` command — prints one item in full: control id and
  title, framework, title, owner, due date, status, creation date
  and overdue aging, followed by its full history (creation line
  plus one line per recorded change, `field: old -> new`).

**Tests** — pytest suite extended with update validation and
history rules (accumulation across updates, partial no-ops, legacy
items, reload round-trip) and CLI end-to-end runs for `update`
and `show`, including their failure modes:
**78 passed, 0 failed** (was 54 at v0.3).

## 2026-11-18 — v0.3 (Due-date reminders)

Chasing outstanding evidence gets its own command and an aging view.

**Features**
- `due` command — lists open (not verified) items that are overdue or
  due within N days (`--days`, default 7), soonest due first. Overdue
  items show their aging, upcoming items show days remaining, and
  items due today are flagged `** DUE TODAY **`. A negative window is
  rejected.
- Aging in `list` — the overdue flag now carries the count, e.g.
  `** OVERDUE (6 days overdue) **` (singular "1 day" handled), backed
  by new `core.days_overdue` / `core.days_until_due` helpers and
  `core.due_within_items` for the window logic.
- Reminder digest — `due --out reminders.txt` writes a plain-text
  digest (`report.format_reminder_digest` / `write_reminder_digest`)
  grouping the same due items by owner with due dates and aging,
  ready to paste into an email to the owners who owe evidence.

**Tests** — pytest suite extended with day-count and window rules
(including the zero-day window and verified-item exclusion),
digest grouping/formatting, and CLI end-to-end runs for `due`,
its `--days`/`--out` flags, and the aged `list` flag:
**54 passed, 0 failed** (was 36 at v0.2).

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
