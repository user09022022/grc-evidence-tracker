"""Report export: CSV detail file and a simple HTML status page."""

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
