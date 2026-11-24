"""Report export: CSV/HTML reports, an Excel workbook, reminder digest."""

import csv
import html
from datetime import date

from .controls_data import CONTROLS_BY_ID
from .core import (
    days_overdue,
    days_until_due,
    due_within_items,
    is_overdue,
    item_framework,
    overdue_items,
    status_counts,
)

CSV_FIELDS = [
    "id", "framework", "control_id", "control_title", "title", "owner",
    "due_date", "status", "overdue",
]


def write_csv(store, path, today=None):
    """Write one row per evidence item to *path* (CSV)."""
    today = today or date.today()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in store["evidence"]:
            writer.writerow({
                "id": item["id"],
                "framework": item_framework(item),
                "control_id": item["control_id"],
                "control_title": CONTROLS_BY_ID[item["control_id"]]["title"],
                "title": item["title"],
                "owner": item["owner"],
                "due_date": item["due_date"],
                "status": item["status"],
                "overdue": "yes" if is_overdue(item, today=today) else "no",
            })
    return path


def write_html(store, path, today=None):
    """Write a simple standalone HTML status report to *path*."""
    today = today or date.today()
    counts = status_counts(store)
    overdue = overdue_items(store, today=today)

    count_rows = "\n".join(
        f"      <tr><td>{html.escape(status)}</td><td>{counts[status]}</td></tr>"
        for status in ("requested", "received", "verified")
    )
    if overdue:
        overdue_rows = "\n".join(
            "      <tr>"
            f"<td>{item['id']}</td>"
            f"<td>{html.escape(item_framework(item))}/{html.escape(item['control_id'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(item['owner'])}</td>"
            f"<td>{html.escape(item['due_date'])}</td>"
            f"<td>{html.escape(item['status'])}</td>"
            "</tr>"
            for item in overdue
        )
        overdue_section = (
            "    <table>\n"
            "      <tr><th>#</th><th>Control</th><th>Evidence</th>"
            "<th>Owner</th><th>Due</th><th>Status</th></tr>\n"
            f"{overdue_rows}\n"
            "    </table>"
        )
    else:
        overdue_section = "    <p>No overdue items.</p>"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>GRC Evidence Tracker — Status Report</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; }}
  table {{ border-collapse: collapse; margin-bottom: 1.5rem; }}
  th, td {{ border: 1px solid #999; padding: 0.3rem 0.6rem; text-align: left; }}
  th {{ background: #eee; }}
</style>
</head>
<body>
  <h1>GRC Evidence Tracker — Status Report</h1>
  <p>Generated {today.isoformat()} · {counts['total']} evidence item(s) · {len(overdue)} overdue</p>
  <h2>Counts by status</h2>
  <table>
    <tr><th>Status</th><th>Count</th></tr>
{count_rows}
    <tr><td><strong>Total</strong></td><td><strong>{counts['total']}</strong></td></tr>
  </table>
  <h2>Overdue items</h2>
{overdue_section}
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path


XLSX_FIELDS = CSV_FIELDS

_XLSX_DETAIL_WIDTHS = {
    "id": 6, "framework": 12, "control_id": 12, "control_title": 42,
    "title": 42, "owner": 20, "due_date": 12, "status": 12, "overdue": 10,
}


def write_xlsx(store, path, today=None):
    """Write a formatted Excel workbook for *store* to *path*.

    The workbook has two sheets: "Summary" (generation date, counts
    by status, total and overdue count) and "Detail" (one row per
    evidence item, same columns as the CSV report, with a filter,
    frozen header row and overdue rows highlighted).

    This is the only report format that needs a third-party package:
    openpyxl is imported lazily here so the rest of the tool stays
    standard-library only. Raises ValueError with install guidance
    when openpyxl is not available.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ValueError(
            "Excel export requires the openpyxl package: "
            "install it with `pip install openpyxl` or "
            "`pip install .[xlsx]`."
        ) from None
    today = today or date.today()
    counts = status_counts(store)
    overdue = overdue_items(store, today=today)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4472C4")
    overdue_fill = PatternFill("solid", fgColor="FCE4E4")
    title_font = Font(bold=True, size=14)

    wb = Workbook()

    summary = wb.active
    summary.title = "Summary"
    summary["A1"] = "GRC Evidence Tracker — Status Report"
    summary["A1"].font = title_font
    summary["A2"] = f"Generated {today.isoformat()}"
    summary.append([])
    summary.append(["Status", "Count"])
    for cell in summary[4]:
        cell.font = header_font
        cell.fill = header_fill
    for status in ("requested", "received", "verified"):
        summary.append([status, counts[status]])
    summary.append(["Total", counts["total"]])
    summary.append(["Overdue", len(overdue)])
    for row in (8, 9):
        for cell in summary[row]:
            cell.font = Font(bold=True)
    summary.column_dimensions["A"].width = 16
    summary.column_dimensions["B"].width = 10

    detail = wb.create_sheet("Detail")
    detail.append(XLSX_FIELDS)
    for cell in detail[1]:
        cell.font = header_font
        cell.fill = header_fill
    for item in store["evidence"]:
        item_overdue = is_overdue(item, today=today)
        detail.append([
            item["id"],
            item_framework(item),
            item["control_id"],
            CONTROLS_BY_ID[item["control_id"]]["title"],
            item["title"],
            item["owner"],
            item["due_date"],
            item["status"],
            "yes" if item_overdue else "no",
        ])
        if item_overdue:
            for cell in detail[detail.max_row]:
                cell.fill = overdue_fill
    for idx, field in enumerate(XLSX_FIELDS, start=1):
        detail.column_dimensions[get_column_letter(idx)].width = (
            _XLSX_DETAIL_WIDTHS[field]
        )
    detail.freeze_panes = "A2"
    if store["evidence"]:
        detail.auto_filter.ref = (
            f"A1:{get_column_letter(len(XLSX_FIELDS))}{detail.max_row}"
        )

    wb.save(path)
    return path


def _due_label(item, today):
    """Human-readable aging label for a due/overdue item."""
    overdue = days_overdue(item, today=today)
    if overdue:
        unit = "day" if overdue == 1 else "days"
        return f"{overdue} {unit} overdue"
    remaining = days_until_due(item, today=today)
    if remaining == 0:
        return "due today"
    if remaining == 1:
        return "due in 1 day"
    return f"due in {remaining} days"


def format_reminder_digest(store, within_days=7, today=None):
    """Return a plain-text reminder digest grouped by owner.

    Covers the same items as `core.due_within_items`: open items that
    are overdue or due within *within_days* days. The text is written
    to be pasted into an email to the owners who owe evidence.
    """
    today = today or date.today()
    items = due_within_items(store, within_days=within_days, today=today)
    lines = [
        "GRC Evidence Tracker — Reminder Digest",
        f"Generated {today.isoformat()} · "
        f"{len(items)} item(s) due within {within_days} day(s) "
        "(including overdue)",
        "",
    ]
    if not items:
        lines.append("No items are due in this window. Nothing to chase.")
        lines.append("")
        return "\n".join(lines)
    by_owner = {}
    for item in items:
        by_owner.setdefault(item["owner"], []).append(item)
    for owner in sorted(by_owner):
        owned = by_owner[owner]
        lines.append(f"{owner} ({len(owned)} item(s))")
        for item in owned:
            lines.append(
                f"  - #{item['id']} [{item_framework(item)}/{item['control_id']}] "
                f"{item['title']} — due {item['due_date']} "
                f"({_due_label(item, today)}), status: {item['status']}"
            )
        lines.append("")
    return "\n".join(lines)


def write_reminder_digest(store, path, within_days=7, today=None):
    """Write the reminder digest for *store* to *path* (text)."""
    text = format_reminder_digest(store, within_days=within_days, today=today)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path
