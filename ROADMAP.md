# Roadmap

Planned increments, in order. Each increment ships only when the full
test suite passes, and is recorded in [LOG.md](LOG.md).

## v0.2 — SOC 2 control set
- Add the SOC 2 Trust Services Criteria (CC1–CC9 series) as a second
  bundled catalogue.
- `--framework {iso27001,soc2}` flag on `controls` and `add-evidence`;
  store records which framework each item belongs to.

## v0.3 — Due-date reminders
- `due` command listing items due within N days (default 7).
- Highlight aging in `list`: days overdue shown next to the flag.
- Optional reminder digest written to a text file for emailing owners.

## v0.4 — Status workflow commands
- `update` command to change an item's status / owner / due date in
  place (today a correction means editing the JSON by hand).
- `show <id>` command printing one item with its full history.

## v0.5 — Excel export
- `report --format xlsx` producing a formatted workbook
  (summary sheet + detail sheet). Adds the `openpyxl` dependency;
  the core tool stays standard-library only.

## v0.6 — Multi-engagement support
- Named engagements inside one store (client, framework, period).
- All commands scoped by `--engagement`; cross-engagement summary
  in the HTML report.

## v0.7 — Web dashboard
- Read-only local dashboard served with `http.server` (standard
  library): status counts, overdue table, per-control coverage.
- Auto-refresh from the JSON store.

## Later ideas
- Evidence file attachments with SHA-256 hashing for integrity.
- Import evidence requests from a CSV PBC list.
- Per-owner workload view ("who owes the most items").
