"""Tests for per-control coverage and the web dashboard (v0.7)."""

import threading
import urllib.error
import urllib.request
from datetime import date

import pytest

from grc_tracker import core, dashboard, store
from grc_tracker.controls_data import ALL_CONTROLS

TODAY = date(2026, 11, 16)


@pytest.fixture()
def empty_store():
    return store.new_store()


@pytest.fixture()
def populated_store(empty_store):
    core.add_evidence(
        empty_store, "A.8.13", "Backup restore test results",
        "IT Operations", "2026-11-10", status="requested",
    )
    core.add_evidence(
        empty_store, "A.8.13", "Backup policy document",
        "IT Operations", "2026-12-01", status="verified",
    )
    core.add_evidence(
        empty_store, "A.6.3", "Security awareness training records",
        "HR", "2026-11-12", status="received",
    )
    core.add_evidence(
        empty_store, "CC6.1", "Access control matrix",
        "IT Operations", "2026-11-10", status="requested",
        framework="soc2",
    )
    return empty_store


# --- Per-control coverage --------------------------------------------------

def test_coverage_covers_every_bundled_control(populated_store):
    coverage = core.control_coverage(populated_store, today=TODAY)
    assert len(coverage) == len(ALL_CONTROLS) == 59
    assert [e["control"]["id"] for e in coverage] == [
        c["id"] for c in ALL_CONTROLS
    ]


def test_coverage_counts_items_per_control(populated_store):
    by_id = {
        e["control"]["id"]: e
        for e in core.control_coverage(populated_store, today=TODAY)
    }
    backup = by_id["A.8.13"]
    assert backup["covered"] is True
    assert backup["total"] == 2
    assert backup["counts"] == {"requested": 1, "received": 0, "verified": 1}
    assert backup["overdue"] == 1  # only the requested past-due item
    soc2 = by_id["CC6.1"]
    assert soc2["total"] == 1 and soc2["overdue"] == 1


def test_coverage_marks_uncovered_controls(populated_store):
    by_id = {
        e["control"]["id"]: e
        for e in core.control_coverage(populated_store, today=TODAY)
    }
    uncovered = by_id["A.5.1"]
    assert uncovered["covered"] is False
    assert uncovered["total"] == 0
    assert uncovered["counts"] == {
        "requested": 0, "received": 0, "verified": 0,
    }
    assert uncovered["overdue"] == 0


def test_coverage_empty_store_has_nothing_covered(empty_store):
    coverage = core.control_coverage(empty_store, today=TODAY)
    assert not any(e["covered"] for e in coverage)


def test_coverage_scoped_to_engagement(empty_store):
    core.add_engagement(empty_store, "acme", "Acme Corp", today=TODAY)
    core.add_evidence(
        empty_store, "A.8.13", "Scoped backup",
        "IT Operations", "2026-11-10", engagement="acme",
    )
    core.add_evidence(
        empty_store, "A.8.13", "Unscoped backup",
        "IT Operations", "2026-11-10",
    )
    scoped = {
        e["control"]["id"]: e
        for e in core.control_coverage(
            empty_store, today=TODAY, engagement="acme",
        )
    }
    assert scoped["A.8.13"]["total"] == 1
    with pytest.raises(ValueError):
        core.control_coverage(empty_store, today=TODAY, engagement="missing")


# --- Dashboard rendering ---------------------------------------------------

def test_render_dashboard_shows_counts_overdue_and_coverage(populated_store):
    page = dashboard.render_dashboard(populated_store, today=TODAY)
    assert "Dashboard" in page
    assert "4 evidence item(s) · 3 overdue" in page
    assert "Counts by status" in page
    # Overdue table: both past-due open items, with aging.
    assert "Backup restore test results" in page
    assert "Security awareness training records" in page
    assert "Access control matrix" in page
    assert "6 day(s)" in page
    # Coverage summary and rows for covered controls only.
    assert "3 of 59 controls have evidence mapped." in page
    assert "Control coverage" in page
    assert "Information backup" in page
    # The verified, not-yet-due item is not in the overdue table, and
    # an uncovered control title does not appear as a coverage row.
    assert page.count("Backup policy document") == 0


def test_render_dashboard_empty_store(populated_store):
    page = dashboard.render_dashboard(store.new_store(), today=TODAY)
    assert "0 evidence item(s) · 0 overdue" in page
    assert "No overdue items." in page
    assert "0 of 59 controls have evidence mapped." in page
    assert "No controls have evidence yet." in page


def test_render_dashboard_auto_refresh_meta_tag(populated_store):
    page = dashboard.render_dashboard(populated_store, today=TODAY)
    assert '<meta http-equiv="refresh" content="30">' in page
    custom = dashboard.render_dashboard(
        populated_store, today=TODAY, refresh=10,
    )
    assert '<meta http-equiv="refresh" content="10">' in custom
    disabled = dashboard.render_dashboard(
        populated_store, today=TODAY, refresh=0,
    )
    assert 'http-equiv="refresh"' not in disabled


def test_render_dashboard_rejects_negative_refresh(populated_store):
    with pytest.raises(ValueError):
        dashboard.render_dashboard(populated_store, today=TODAY, refresh=-1)


def test_render_dashboard_escapes_html(populated_store):
    populated_store["evidence"][0]["title"] = "<script>alert(1)</script>"
    populated_store["evidence"][0]["owner"] = "A & B"
    page = dashboard.render_dashboard(populated_store, today=TODAY)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
    assert "A &amp; B" in page


def test_render_dashboard_scoped_to_engagement(empty_store):
    core.add_engagement(empty_store, "acme", "Acme Corp", today=TODAY)
    core.add_evidence(
        empty_store, "A.8.13", "Scoped backup",
        "IT Operations", "2026-11-10", engagement="acme",
    )
    core.add_evidence(
        empty_store, "A.8.15", "Unscoped logs",
        "IT Operations", "2026-11-10",
    )
    page = dashboard.render_dashboard(
        empty_store, today=TODAY, engagement="acme",
    )
    assert "Engagement: acme" in page
    assert "1 evidence item(s)" in page
    assert "Scoped backup" in page
    assert "Unscoped logs" not in page
    with pytest.raises(ValueError):
        dashboard.render_dashboard(
            empty_store, today=TODAY, engagement="missing",
        )


# --- HTTP server -----------------------------------------------------------

@pytest.fixture()
def running_server(tmp_path, populated_store):
    path = str(tmp_path / "data.json")
    store.save_store(path, populated_store)
    server = dashboard.create_server(path, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    yield f"http://{host}:{port}", path
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.headers, response.read().decode()


def test_server_serves_dashboard_at_root(running_server):
    base, _ = running_server
    status, headers, body = _get(base + "/")
    assert status == 200
    assert "text/html" in headers["Content-Type"]
    assert "Backup restore test results" in body
    status, _, body = _get(base + "/index.html")
    assert status == 200
    assert "Dashboard" in body


def test_server_unknown_path_is_404(running_server):
    base, _ = running_server
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        _get(base + "/nope")
    assert excinfo.value.code == 404


def test_server_is_read_only(running_server):
    base, _ = running_server
    request = urllib.request.Request(
        base + "/", data=b"{}", method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(request, timeout=5)
    assert excinfo.value.code == 405


def test_server_rereads_store_on_each_request(running_server, tmp_path):
    base, path = running_server
    _, _, body = _get(base + "/")
    assert "Late addition" not in body
    loaded = store.load_store(path)
    core.add_evidence(
        loaded, "A.8.15", "Late addition",
        "IT Operations", "2026-12-01",
    )
    store.save_store(path, loaded)
    _, _, body = _get(base + "/")
    # Auto-refresh from the JSON store: no server restart needed.
    assert "5 evidence item(s)" in body


def test_server_missing_store_reports_500(tmp_path):
    server = dashboard.create_server(
        str(tmp_path / "nope.json"), host="127.0.0.1", port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            _get(f"http://{host}:{port}/")
        assert excinfo.value.code == 500
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_create_server_rejects_bad_port_and_refresh(tmp_path):
    path = str(tmp_path / "data.json")
    store.save_store(path, store.new_store())
    with pytest.raises(ValueError):
        dashboard.create_server(path, port=70000)
    with pytest.raises(ValueError):
        dashboard.create_server(path, port=-1)
    with pytest.raises(ValueError):
        dashboard.create_server(path, refresh=-5)
