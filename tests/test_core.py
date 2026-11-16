"""Tests for the GRC Evidence Tracker's core logic."""

from datetime import date

import pytest

from grc_tracker import core, report, store
from grc_tracker.controls_data import CONTROLS, THEMES

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
        empty_store, "A.6.3", "Security awareness training records",
        "HR", "2026-11-12", status="received",
    )
    core.add_evidence(
        empty_store, "A.5.1", "Approved information security policy",
        "CISO Office", "2026-11-05", status="verified",
    )
    core.add_evidence(
        empty_store, "A.8.5", "MFA configuration export",
        "IT Operations", "2026-12-01", status="requested",
    )
    return empty_store


# --- Store ---------------------------------------------------------------

def test_init_creates_store_file(tmp_path):
    path = str(tmp_path / "data.json")
    assert store.init_store(path) is True
    loaded = store.load_store(path)
    assert loaded["evidence"] == []


def test_init_does_not_overwrite_existing_store(tmp_path):
    path = str(tmp_path / "data.json")
    assert store.init_store(path) is True
    assert store.init_store(path) is False


def test_load_missing_store_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        store.load_store(str(tmp_path / "nope.json"))


# --- Control catalogue ---------------------------------------------------

def test_catalogue_has_at_least_20_controls():
    assert len(CONTROLS) >= 20


def test_catalogue_spans_all_four_themes():
    assert {c["theme"] for c in CONTROLS} == set(THEMES)


def test_catalogue_ids_are_unique():
    ids = [c["id"] for c in CONTROLS]
    assert len(ids) == len(set(ids))


# --- Adding evidence -----------------------------------------------------

def test_add_evidence_assigns_incrementing_ids(populated_store):
    assert [i["id"] for i in populated_store["evidence"]] == [1, 2, 3, 4]


def test_add_evidence_defaults_to_requested(empty_store):
    item = core.add_evidence(
        empty_store, "A.7.2", "Badge access logs", "Facilities", "2026-12-15",
    )
    assert item["status"] == "requested"


def test_add_evidence_rejects_unknown_control(empty_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            empty_store, "A.9.99", "Nope", "Owner", "2026-12-15",
        )


def test_add_evidence_rejects_invalid_status(empty_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            empty_store, "A.7.2", "Badge access logs", "Facilities",
            "2026-12-15", status="done",
        )


def test_add_evidence_rejects_invalid_date(empty_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            empty_store, "A.7.2", "Badge access logs", "Facilities", "Dec 15",
        )


def test_add_and_reload_round_trip(tmp_path, populated_store):
    path = str(tmp_path / "data.json")
    store.save_store(path, populated_store)
    loaded = store.load_store(path)
    assert len(loaded["evidence"]) == 4
    assert loaded["evidence"][0]["control_id"] == "A.8.13"


# --- Overdue logic ---------------------------------------------------------

def test_overdue_when_past_due_and_not_verified(populated_store):
    overdue = core.overdue_items(populated_store, today=TODAY)
    titles = {i["title"] for i in overdue}
    assert titles == {
        "Backup restore test results",          # past due, requested
        "Security awareness training records",  # past due, received
    }


def test_verified_item_is_never_overdue(populated_store):
    item = populated_store["evidence"][2]
    assert item["status"] == "verified"
    assert core.is_overdue(item, today=TODAY) is False


def test_item_due_today_is_not_overdue(empty_store):
    item = core.add_evidence(
        empty_store, "A.8.15", "Log samples", "IT Operations", "2026-11-16",
    )
    assert core.is_overdue(item, today=TODAY) is False


def test_future_item_is_not_overdue(populated_store):
    item = populated_store["evidence"][3]
    assert core.is_overdue(item, today=TODAY) is False


# --- Summaries and reports -------------------------------------------------

def test_status_counts(populated_store):
    counts = core.status_counts(populated_store)
    assert counts == {"requested": 2, "received": 1, "verified": 1, "total": 4}


def test_report_csv_contents(tmp_path, populated_store):
    path = str(tmp_path / "report.csv")
    report.write_csv(populated_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "control_id,control_title" in text
    assert "Backup restore test results" in text
    # The overdue flag column marks the past-due requested item.
    overdue_line = next(
        line for line in text.splitlines() if "Backup restore" in line
    )
    assert overdue_line.rstrip().endswith(",yes")
    verified_line = next(
        line for line in text.splitlines() if "Approved information" in line
    )
    assert verified_line.rstrip().endswith(",no")


def test_report_html_contents(tmp_path, populated_store):
    path = str(tmp_path / "report.html")
    report.write_html(populated_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "Counts by status" in text
    assert "Backup restore test results" in text  # appears in overdue list
    assert "MFA configuration export" not in text  # not overdue, not listed
