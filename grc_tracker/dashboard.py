"""Read-only local web dashboard (v0.7), standard library only.

The dashboard is served with ``http.server`` and re-reads the JSON
store from disk on every request, so a page left open in a browser
always shows the latest data: the generated HTML carries a
``<meta http-equiv="refresh">`` tag (30 seconds by default) and each
refresh is a fresh read of the store — there is no cached state in
the server to go stale. The handler only implements GET; every
other method is refused with 405, so the dashboard can never change
the store.
"""

import html
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .core import (
    control_coverage,
    days_overdue,
    item_framework,
    overdue_items,
    status_counts,
)
from .store import load_store

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_REFRESH = 30


def render_dashboard(store, today=None, refresh=DEFAULT_REFRESH,
                     engagement=None):
    """Return the dashboard page for *store* as an HTML string.

    The page shows counts by status, an overdue table (oldest due
    first, with aging), a cross-engagement summary when the store
    uses engagements (via the report helper), and per-control
    coverage: how many of the bundled controls have evidence mapped
    to them, with a row for every covered control. When *refresh*
    is a positive number of seconds the page asks the browser to
    reload itself on that interval; 0 disables auto-refresh. When
    *engagement* is given, counts, the overdue table and coverage
    are scoped to that engagement (an unknown name raises
    ValueError, via the core scoping helpers).
    """
    if refresh is None or refresh < 0:
        raise ValueError(
            f"Invalid refresh {refresh!r}: must be 0 or more seconds."
        )
    today = today or date.today()
    counts = status_counts(store, engagement=engagement)
    overdue = overdue_items(store, today=today, engagement=engagement)
    coverage = control_coverage(store, today=today, engagement=engagement)
    covered = [entry for entry in coverage if entry["covered"]]

    refresh_tag = (
        f'  <meta http-equiv="refresh" content="{refresh}">\n'
        if refresh else ""
    )
    scope_note = (
        f" · Engagement: {html.escape(engagement)}" if engagement else ""
    )

    count_rows = "\n".join(
        f"      <tr><td>{html.escape(status)}</td><td>{counts[status]}</td></tr>"
        for status in ("requested", "received", "verified")
    )

    if overdue:
        overdue_rows = "\n".join(
            "      <tr>"
            f"<td>{item['id']}</td>"
            f"<td>{html.escape(item_framework(item))}/"
            f"{html.escape(item['control_id'])}</td>"
            f"<td>{html.escape(item['title'])}</td>"
            f"<td>{html.escape(item['owner'])}</td>"
            f"<td>{html.escape(item['due_date'])}</td>"
            f"<td>{html.escape(item['status'])}</td>"
            f"<td>{days_overdue(item, today=today)} day(s)</td>"
            "</tr>"
            for item in overdue
        )
        overdue_section = (
            "    <table>\n"
            "      <tr><th>#</th><th>Control</th><th>Evidence</th>"
            "<th>Owner</th><th>Due</th><th>Status</th>"
            "<th>Overdue by</th></tr>\n"
            f"{overdue_rows}\n"
            "    </table>"
        )
    else:
        overdue_section = "    <p>No overdue items.</p>"

    if covered:
        coverage_rows = "\n".join(
            "      <tr>"
            f"<td>{html.escape(entry['control']['framework'])}/"
            f"{html.escape(entry['control']['id'])}</td>"
            f"<td>{html.escape(entry['control']['title'])}</td>"
            f"<td>{entry['total']}</td>"
            f"<td>{entry['counts']['requested']}</td>"
            f"<td>{entry['counts']['received']}</td>"
            f"<td>{entry['counts']['verified']}</td>"
            f"<td>{entry['overdue']}</td>"
            "</tr>"
            for entry in covered
        )
        coverage_section = (
            "    <table>\n"
            "      <tr><th>Control</th><th>Title</th><th>Items</th>"
            "<th>Requested</th><th>Received</th><th>Verified</th>"
            "<th>Overdue</th></tr>\n"
            f"{coverage_rows}\n"
            "    </table>"
        )
    else:
        coverage_section = "    <p>No controls have evidence yet.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
{refresh_tag}<title>GRC Evidence Tracker — Dashboard</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; }}
  table {{ border-collapse: collapse; margin-bottom: 1.5rem; }}
  th, td {{ border: 1px solid #999; padding: 0.3rem 0.6rem; text-align: left; }}
  th {{ background: #eee; }}
</style>
</head>
<body>
  <h1>GRC Evidence Tracker — Dashboard</h1>
  <p>Generated {today.isoformat()} · {counts['total']} evidence item(s) · {len(overdue)} overdue{scope_note}</p>
  <h2>Counts by status</h2>
  <table>
    <tr><th>Status</th><th>Count</th></tr>
{count_rows}
    <tr><td><strong>Total</strong></td><td><strong>{counts['total']}</strong></td></tr>
  </table>
  <h2>Overdue items</h2>
{overdue_section}
  <h2>Control coverage</h2>
  <p>{len(covered)} of {len(coverage)} controls have evidence mapped.</p>
{coverage_section}
</body>
</html>
"""


def make_handler(data_path, refresh=DEFAULT_REFRESH, engagement=None):
    """Return a request-handler class serving the store at *data_path*.

    The store is loaded from disk on every GET, so changes made with
    the CLI while the server runs appear on the next (auto-)refresh.
    """

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/index.html"):
                self.send_error(404, "Not Found")
                return
            try:
                store = load_store(data_path)
                page = render_dashboard(
                    store, refresh=refresh, engagement=engagement,
                )
            except (FileNotFoundError, ValueError) as exc:
                self.send_error(500, f"Dashboard unavailable: {exc}")
                return
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _refuse(self):
            self.send_error(405, "Method Not Allowed: dashboard is read-only")

        do_POST = _refuse
        do_PUT = _refuse
        do_DELETE = _refuse
        do_PATCH = _refuse

        def log_message(self, format, *args):  # keep the console quiet
            pass

    return DashboardHandler


def create_server(data_path, host=DEFAULT_HOST, port=DEFAULT_PORT,
                  refresh=DEFAULT_REFRESH, engagement=None):
    """Create (but do not start) the dashboard HTTP server.

    Raises ValueError for an out-of-range port or a negative refresh
    interval. Port 0 is allowed and asks the OS for a free port,
    which is how the tests run a real server without collisions.
    """
    if not (0 <= port <= 65535):
        raise ValueError(
            f"Invalid port {port!r}: expected a port between 0 and 65535."
        )
    if refresh is None or refresh < 0:
        raise ValueError(
            f"Invalid refresh {refresh!r}: must be 0 or more seconds."
        )
    handler = make_handler(data_path, refresh=refresh, engagement=engagement)
    return ThreadingHTTPServer((host, port), handler)


def serve_dashboard(data_path, host=DEFAULT_HOST, port=DEFAULT_PORT,
                    refresh=DEFAULT_REFRESH, engagement=None):
    """Serve the dashboard for the store at *data_path* until stopped.

    Blocks in ``serve_forever``; a keyboard interrupt shuts the
    server down cleanly. Returns the server's (host, port) once it
    has stopped.
    """
    server = create_server(
        data_path, host=host, port=port, refresh=refresh,
        engagement=engagement,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return server.server_address
