"""Report export: CSV detail file and a simple HTML status page."""

import csv
import html
from datetime import date

from .controls_data import CONTROLS_BY_ID
from .core import is_overdue, overdue_items, status_counts

CSV_FIELDS = [
    "id", "control_id", "control_title", "title", "owner",
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
            f"<td>{html.escape(item['control_id'])}</td>"
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
