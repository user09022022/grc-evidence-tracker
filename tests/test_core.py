"""Tests for the GRC Evidence Tracker's core logic."""

from datetime import date

import pytest

from grc_tracker import core, report, store
from grc_tracker.controls_data import (
    CONTROLS,
    FRAMEWORKS,
    SOC2_CONTROLS,
    SOC2_THEMES,
    THEMES,
    controls_by_id,
    controls_for,
    themes_for,
)

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


# --- SOC 2 catalogue (v0.2) ----------------------------------------------

def test_soc2_catalogue_covers_cc1_to_cc9():
    assert len(SOC2_CONTROLS) == 33
    series = {c["id"].split(".")[0] for c in SOC2_CONTROLS}
    assert series == {f"CC{i}" for i in range(1, 10)}


def test_soc2_catalogue_spans_all_nine_categories():
    assert {c["theme"] for c in SOC2_CONTROLS} == set(SOC2_THEMES)
    assert len(SOC2_THEMES) == 9


def test_soc2_catalogue_ids_are_unique_and_framework_tagged():
    ids = [c["id"] for c in SOC2_CONTROLS]
    assert len(ids) == len(set(ids))
    assert all(c["framework"] == "soc2" for c in SOC2_CONTROLS)
    assert all(c["framework"] == "iso27001" for c in CONTROLS)


def test_catalogues_are_separate_and_lookups_are_scoped():
    assert FRAMEWORKS == ("iso27001", "soc2")
    assert controls_for("iso27001") == CONTROLS
    assert controls_for("soc2") == SOC2_CONTROLS
    assert "CC6.1" in controls_by_id("soc2")
    assert "CC6.1" not in controls_by_id("iso27001")
    assert "A.8.13" in controls_by_id("iso27001")
    assert "A.8.13" not in controls_by_id("soc2")
    # The merged lookup resolves both, for reports over mixed stores.
    assert "CC6.1" in controls_by_id()
    assert "A.8.13" in controls_by_id()
    assert themes_for("soc2") == SOC2_THEMES
    with pytest.raises(ValueError):
        controls_for("nist")


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


def test_add_evidence_defaults_to_iso27001_framework(empty_store):
    item = core.add_evidence(
        empty_store, "A.7.2", "Badge access logs", "Facilities", "2026-12-15",
    )
    assert item["framework"] == "iso27001"


def test_add_evidence_soc2_records_framework(empty_store):
    item = core.add_evidence(
        empty_store, "CC6.1", "Access control matrix", "IT Operations",
        "2026-12-15", framework="soc2",
    )
    assert item["framework"] == "soc2"
    assert item["control_id"] == "CC6.1"


def test_add_evidence_rejects_control_from_other_framework(empty_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            empty_store, "A.8.13", "Backup results", "IT Operations",
            "2026-12-15", framework="soc2",
        )
    with pytest.raises(ValueError):
        core.add_evidence(
            empty_store, "CC6.1", "Access matrix", "IT Operations",
            "2026-12-15", framework="iso27001",
        )


def test_add_evidence_rejects_unknown_framework(empty_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            empty_store, "CC6.1", "Access matrix", "IT Operations",
            "2026-12-15", framework="nist",
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


def test_report_csv_includes_framework_for_soc2_items(tmp_path, empty_store):
    core.add_evidence(
        empty_store, "CC7.4", "Incident response plan", "IT Operations",
        "2026-11-10", framework="soc2",
    )
    core.add_evidence(
        empty_store, "A.5.24", "Incident management plan", "CISO Office",
        "2026-11-10",
    )
    path = str(tmp_path / "report.csv")
    report.write_csv(empty_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "id,framework,control_id,control_title" in text
    soc2_line = next(line for line in text.splitlines() if "CC7.4" in line)
    assert ",soc2,CC7.4," in soc2_line
    assert "Response to security incidents" in soc2_line
    iso_line = next(line for line in text.splitlines() if "A.5.24" in line)
    assert ",iso27001,A.5.24," in iso_line


def test_legacy_item_without_framework_still_reports(tmp_path):
    # Stores written by v0.1 have no "framework" key on their items.
    legacy = store.new_store()
    legacy["evidence"].append({
        "id": 1, "control_id": "A.8.13",
        "title": "Backup restore test results", "owner": "IT Operations",
        "due_date": "2026-11-10", "status": "requested",
        "created": "2026-11-16",
    })
    assert core.item_framework(legacy["evidence"][0]) == "iso27001"
    path = str(tmp_path / "report.csv")
    report.write_csv(legacy, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert ",iso27001,A.8.13," in text


def test_report_html_contents(tmp_path, populated_store):
    path = str(tmp_path / "report.html")
    report.write_html(populated_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "Counts by status" in text
    assert "Backup restore test results" in text  # appears in overdue list
    assert "MFA configuration export" not in text  # not overdue, not listed
