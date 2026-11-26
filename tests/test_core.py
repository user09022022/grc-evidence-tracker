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


# --- Due-date reminders (v0.3) -------------------------------------------

def test_days_overdue_counts_past_due_days(populated_store):
    backup, training = populated_store["evidence"][0], populated_store["evidence"][1]
    assert core.days_overdue(backup, today=TODAY) == 6    # due Nov 10
    assert core.days_overdue(training, today=TODAY) == 4  # due Nov 12


def test_days_overdue_is_zero_when_not_overdue(populated_store):
    verified, future = populated_store["evidence"][2], populated_store["evidence"][3]
    assert core.days_overdue(verified, today=TODAY) == 0
    assert core.days_overdue(future, today=TODAY) == 0


def test_days_overdue_singular_for_one_day(empty_store):
    item = core.add_evidence(
        empty_store, "A.8.15", "Log samples", "IT Operations", "2026-11-15",
    )
    assert core.days_overdue(item, today=TODAY) == 1


def test_days_until_due_sign_convention(populated_store):
    backup, future = populated_store["evidence"][0], populated_store["evidence"][3]
    assert core.days_until_due(backup, today=TODAY) == -6
    assert core.days_until_due(future, today=TODAY) == 15


def test_due_within_includes_overdue_and_window(populated_store):
    due = core.due_within_items(populated_store, within_days=7, today=TODAY)
    titles = [i["title"] for i in due]
    # Overdue items are included; the Dec 1 item (15 days out) is not.
    assert titles == [
        "Backup restore test results",
        "Security awareness training records",
    ]


def test_due_within_wider_window_includes_future_item(populated_store):
    due = core.due_within_items(populated_store, within_days=20, today=TODAY)
    assert [i["title"] for i in due][-1] == "MFA configuration export"
    assert len(due) == 3


def test_due_within_excludes_verified_items(populated_store):
    due = core.due_within_items(populated_store, within_days=365, today=TODAY)
    assert all(i["status"] != "verified" for i in due)
    assert "Approved information security policy" not in {
        i["title"] for i in due
    }


def test_due_within_zero_days_is_overdue_plus_due_today(empty_store):
    core.add_evidence(
        empty_store, "A.8.13", "Past due", "IT Operations", "2026-11-10",
    )
    core.add_evidence(
        empty_store, "A.8.15", "Due today", "IT Operations", "2026-11-16",
    )
    core.add_evidence(
        empty_store, "A.8.5", "Due tomorrow", "IT Operations", "2026-11-17",
    )
    due = core.due_within_items(empty_store, within_days=0, today=TODAY)
    assert [i["title"] for i in due] == ["Past due", "Due today"]


def test_due_within_rejects_negative_window(populated_store):
    with pytest.raises(ValueError):
        core.due_within_items(populated_store, within_days=-1, today=TODAY)


def test_reminder_digest_groups_items_by_owner(populated_store):
    text = report.format_reminder_digest(
        populated_store, within_days=7, today=TODAY,
    )
    assert "Reminder Digest" in text
    assert "IT Operations (1 item(s))" in text
    assert "HR (1 item(s))" in text
    assert "Backup restore test results" in text
    assert "6 days overdue" in text
    assert "4 days overdue" in text
    # The verified item and the far-future item are not chased.
    assert "Approved information security policy" not in text
    assert "MFA configuration export" not in text


def test_reminder_digest_shows_days_remaining_for_upcoming(populated_store):
    text = report.format_reminder_digest(
        populated_store, within_days=20, today=TODAY,
    )
    assert "due in 15 days" in text


def test_reminder_digest_empty_window(tmp_path, empty_store):
    text = report.format_reminder_digest(empty_store, within_days=7, today=TODAY)
    assert "No items are due in this window" in text
    path = str(tmp_path / "digest.txt")
    assert report.write_reminder_digest(
        empty_store, path, within_days=7, today=TODAY,
    ) == path
    assert open(path, encoding="utf-8").read() == text


def test_write_reminder_digest_creates_file(tmp_path, populated_store):
    path = str(tmp_path / "reminders.txt")
    report.write_reminder_digest(populated_store, path, within_days=7, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "Security awareness training records" in text


# --- Status workflow: update / show (v0.4) --------------------------------

def test_add_evidence_starts_with_empty_history(populated_store):
    assert all(i["history"] == [] for i in populated_store["evidence"])


def test_find_item_returns_matching_item(populated_store):
    item = core.find_item(populated_store, 2)
    assert item["title"] == "Security awareness training records"


def test_find_item_rejects_unknown_id(populated_store):
    with pytest.raises(ValueError):
        core.find_item(populated_store, 999)


def test_update_status_changes_value_and_records_history(populated_store):
    item = core.update_evidence(
        populated_store, 1, status="received", today=TODAY,
    )
    assert item["status"] == "received"
    assert core.item_history(item) == [{
        "date": "2026-11-16", "field": "status",
        "old": "requested", "new": "received",
    }]


def test_update_owner_and_due_date_together(populated_store):
    item = core.update_evidence(
        populated_store, 1, owner="Security Team", due_date="2026-12-10",
        today=TODAY,
    )
    assert item["owner"] == "Security Team"
    assert item["due_date"] == "2026-12-10"
    fields = [e["field"] for e in core.item_history(item)]
    assert fields == ["owner", "due_date"]


def test_update_all_three_fields_records_three_entries(populated_store):
    item = core.update_evidence(
        populated_store, 2, status="verified", owner="People Team",
        due_date="2026-11-20", today=TODAY,
    )
    assert item["status"] == "verified"
    assert [e["field"] for e in core.item_history(item)] == [
        "status", "owner", "due_date",
    ]


def test_update_history_accumulates_across_updates(populated_store):
    core.update_evidence(populated_store, 1, status="received", today=TODAY)
    item = core.update_evidence(
        populated_store, 1, status="verified", today=date(2026, 11, 18),
    )
    history = core.item_history(item)
    assert len(history) == 2
    assert history[0]["new"] == "received"
    assert history[1] == {
        "date": "2026-11-18", "field": "status",
        "old": "received", "new": "verified",
    }


def test_update_rejects_unknown_id(populated_store):
    with pytest.raises(ValueError):
        core.update_evidence(populated_store, 999, status="received")


def test_update_rejects_no_fields(populated_store):
    with pytest.raises(ValueError):
        core.update_evidence(populated_store, 1)


def test_update_rejects_unchanged_values(populated_store):
    with pytest.raises(ValueError):
        core.update_evidence(populated_store, 1, status="requested")
    # A failed/no-op update leaves the item and its history untouched.
    assert populated_store["evidence"][0]["history"] == []


def test_update_partial_noop_only_records_real_changes(populated_store):
    item = core.update_evidence(
        populated_store, 1, status="requested", owner="New Owner",
        today=TODAY,
    )
    assert [e["field"] for e in core.item_history(item)] == ["owner"]


def test_update_rejects_invalid_status(populated_store):
    with pytest.raises(ValueError):
        core.update_evidence(populated_store, 1, status="done")


def test_update_rejects_invalid_due_date(populated_store):
    with pytest.raises(ValueError):
        core.update_evidence(populated_store, 1, due_date="Dec 10")


def test_update_rejects_empty_owner(populated_store):
    with pytest.raises(ValueError):
        core.update_evidence(populated_store, 1, owner="   ")


def test_update_legacy_item_without_history(populated_store):
    legacy = store.new_store()
    legacy["evidence"].append({
        "id": 1, "control_id": "A.8.13",
        "title": "Backup restore test results", "owner": "IT Operations",
        "due_date": "2026-11-10", "status": "requested",
        "created": "2026-11-16",
    })
    assert core.item_history(legacy["evidence"][0]) == []
    item = core.update_evidence(legacy, 1, status="received", today=TODAY)
    assert item["status"] == "received"
    assert len(core.item_history(item)) == 1


def test_update_then_reload_round_trip(tmp_path, populated_store):
    core.update_evidence(populated_store, 1, status="received", today=TODAY)
    path = str(tmp_path / "data.json")
    store.save_store(path, populated_store)
    loaded = store.load_store(path)
    item = core.find_item(loaded, 1)
    assert item["status"] == "received"
    assert core.item_history(item)[0]["field"] == "status"


# --- Multi-engagement support (v0.6) --------------------------------------

@pytest.fixture()
def engagement_store(empty_store):
    core.add_engagement(
        empty_store, "acme-iso-2026", "Acme Corp",
        framework="iso27001", period="2026", today=TODAY,
    )
    core.add_engagement(
        empty_store, "globex-soc2-2026", "Globex",
        framework="soc2", period="2026-H2", today=TODAY,
    )
    core.add_evidence(
        empty_store, "A.8.13", "Backup restore test results",
        "IT Operations", "2026-11-10", status="requested",
        engagement="acme-iso-2026",
    )
    core.add_evidence(
        empty_store, "A.5.1", "Approved policy",
        "CISO Office", "2026-11-05", status="verified",
        engagement="acme-iso-2026",
    )
    core.add_evidence(
        empty_store, "CC6.1", "Access control matrix",
        "IT Operations", "2026-11-10", status="received",
        framework="soc2", engagement="globex-soc2-2026",
    )
    core.add_evidence(
        empty_store, "A.8.5", "Unassigned MFA export",
        "IT Operations", "2026-12-01", status="requested",
    )
    return empty_store


def test_new_store_has_empty_engagements():
    assert store.new_store()["engagements"] == []


def test_add_engagement_records_fields(empty_store):
    eng = core.add_engagement(
        empty_store, "acme-2026", "Acme Corp", framework="soc2",
        period="2026", today=TODAY,
    )
    assert eng == {
        "name": "acme-2026", "client": "Acme Corp", "framework": "soc2",
        "period": "2026", "created": "2026-11-16",
    }
    assert core.find_engagement(empty_store, "acme-2026") == eng


def test_add_engagement_rejects_duplicate_name(engagement_store):
    with pytest.raises(ValueError):
        core.add_engagement(engagement_store, "acme-iso-2026", "Other")


def test_add_engagement_rejects_empty_name_and_client(empty_store):
    with pytest.raises(ValueError):
        core.add_engagement(empty_store, "  ", "Acme Corp")
    with pytest.raises(ValueError):
        core.add_engagement(empty_store, "acme", "  ")


def test_add_engagement_rejects_unknown_framework(empty_store):
    with pytest.raises(ValueError):
        core.add_engagement(empty_store, "acme", "Acme", framework="nist")


def test_find_engagement_rejects_unknown_name(engagement_store):
    with pytest.raises(ValueError):
        core.find_engagement(engagement_store, "nope")


def test_add_evidence_records_engagement(engagement_store):
    item = engagement_store["evidence"][0]
    assert item["engagement"] == "acme-iso-2026"
    assert core.item_engagement(item) == "acme-iso-2026"
    unassigned = engagement_store["evidence"][3]
    assert core.item_engagement(unassigned) is None


def test_add_evidence_rejects_unknown_engagement(engagement_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            engagement_store, "A.8.13", "Nope", "Owner", "2026-12-15",
            engagement="missing",
        )


def test_add_evidence_rejects_framework_mismatch_with_engagement(engagement_store):
    with pytest.raises(ValueError):
        core.add_evidence(
            engagement_store, "CC6.1", "Nope", "Owner", "2026-12-15",
            framework="soc2", engagement="acme-iso-2026",
        )


def test_item_engagement_legacy_item_without_key():
    legacy = {"id": 1, "control_id": "A.8.13"}
    assert core.item_engagement(legacy) is None


def test_scoped_items_filters_by_engagement(engagement_store):
    scoped = core.scoped_items(engagement_store, engagement="acme-iso-2026")
    assert [i["title"] for i in scoped] == [
        "Backup restore test results", "Approved policy",
    ]
    assert len(core.scoped_items(engagement_store)) == 4
    with pytest.raises(ValueError):
        core.scoped_items(engagement_store, engagement="missing")


def test_status_counts_scoped_to_engagement(engagement_store):
    counts = core.status_counts(engagement_store, engagement="acme-iso-2026")
    assert counts == {"requested": 1, "received": 0, "verified": 1, "total": 2}
    assert core.status_counts(engagement_store)["total"] == 4


def test_overdue_and_due_within_scoped_to_engagement(engagement_store):
    overdue = core.overdue_items(
        engagement_store, today=TODAY, engagement="globex-soc2-2026",
    )
    assert [i["title"] for i in overdue] == ["Access control matrix"]
    due = core.due_within_items(
        engagement_store, within_days=7, today=TODAY,
        engagement="acme-iso-2026",
    )
    assert [i["title"] for i in due] == ["Backup restore test results"]


def test_engagement_summaries_cover_all_and_unassigned(engagement_store):
    summaries = core.engagement_summaries(engagement_store, today=TODAY)
    assert [s["engagement"]["name"] if s["engagement"] else None
            for s in summaries] == [
        "acme-iso-2026", "globex-soc2-2026", None,
    ]
    acme, globex, unassigned = summaries
    assert acme["total"] == 2 and acme["overdue"] == 1
    assert acme["counts"] == {"requested": 1, "received": 0, "verified": 1}
    assert globex["total"] == 1 and globex["overdue"] == 1
    assert unassigned["total"] == 1 and unassigned["overdue"] == 0


def test_engagement_summaries_no_unassigned_entry_when_all_assigned(empty_store):
    core.add_engagement(empty_store, "acme", "Acme", today=TODAY)
    core.add_evidence(
        empty_store, "A.8.13", "Backup", "IT", "2026-12-01",
        engagement="acme",
    )
    summaries = core.engagement_summaries(empty_store, today=TODAY)
    assert len(summaries) == 1
    assert summaries[0]["engagement"]["name"] == "acme"


def test_legacy_store_without_engagements_key_still_works():
    legacy = {"version": 1, "evidence": []}
    assert core.get_engagements(legacy) == []
    eng = core.add_engagement(legacy, "acme", "Acme", today=TODAY)
    assert legacy["engagements"] == [eng]


def test_report_csv_scoped_and_includes_engagement(tmp_path, engagement_store):
    path = str(tmp_path / "report.csv")
    report.write_csv(engagement_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert ",acme-iso-2026,A.8.13," in text
    assert ",globex-soc2-2026,CC6.1," in text
    scoped_path = str(tmp_path / "scoped.csv")
    report.write_csv(
        engagement_store, scoped_path, today=TODAY,
        engagement="acme-iso-2026",
    )
    scoped = open(scoped_path, encoding="utf-8").read()
    assert "Backup restore test results" in scoped
    assert "Access control matrix" not in scoped
    assert "Unassigned MFA export" not in scoped


def test_report_html_cross_engagement_summary(tmp_path, engagement_store):
    path = str(tmp_path / "report.html")
    report.write_html(engagement_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "<h2>Engagements</h2>" in text
    assert "acme-iso-2026" in text
    assert "Acme Corp" in text
    assert "globex-soc2-2026" in text
    assert "Globex" in text
    assert "(no engagement)" in text


def test_report_html_scoped_counts_keep_cross_summary(tmp_path, engagement_store):
    path = str(tmp_path / "report.html")
    report.write_html(
        engagement_store, path, today=TODAY, engagement="acme-iso-2026",
    )
    text = open(path, encoding="utf-8").read()
    assert "Engagement: acme-iso-2026" in text
    assert "2 evidence item(s)" in text
    # Cross-engagement summary still covers the other engagement.
    assert "globex-soc2-2026" in text


def test_report_xlsx_scoped_to_engagement(tmp_path, engagement_store):
    path = str(tmp_path / "report.xlsx")
    report.write_xlsx(
        engagement_store, path, today=TODAY, engagement="globex-soc2-2026",
    )
    ws = _load_xlsx(path)["Detail"]
    assert ws.max_row == 2  # header + 1 scoped item
    row = [c.value for c in ws[2]]
    assert row[2] == "globex-soc2-2026"
    assert row[3] == "CC6.1"
    summary = _load_xlsx(path)["Summary"]
    rows = {r[0].value: r[1].value for r in summary.iter_rows(min_row=4)}
    assert rows["Total"] == 1


def test_reminder_digest_scoped_to_engagement(engagement_store):
    text = report.format_reminder_digest(
        engagement_store, within_days=7, today=TODAY,
        engagement="globex-soc2-2026",
    )
    assert "Access control matrix" in text
    assert "Backup restore test results" not in text


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
    assert "id,framework,engagement,control_id,control_title" in text
    soc2_line = next(line for line in text.splitlines() if "CC7.4" in line)
    assert ",soc2,,CC7.4," in soc2_line
    assert "Response to security incidents" in soc2_line
    iso_line = next(line for line in text.splitlines() if "A.5.24" in line)
    assert ",iso27001,,A.5.24," in iso_line


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
    assert ",iso27001,,A.8.13," in text


# --- Excel export (v0.5) ---------------------------------------------------

openpyxl = pytest.importorskip("openpyxl")


def _load_xlsx(path):
    return openpyxl.load_workbook(path)


def test_report_xlsx_has_summary_and_detail_sheets(tmp_path, populated_store):
    path = str(tmp_path / "report.xlsx")
    assert report.write_xlsx(populated_store, path, today=TODAY) == path
    wb = _load_xlsx(path)
    assert wb.sheetnames == ["Summary", "Detail"]


def test_report_xlsx_summary_counts(tmp_path, populated_store):
    path = str(tmp_path / "report.xlsx")
    report.write_xlsx(populated_store, path, today=TODAY)
    ws = _load_xlsx(path)["Summary"]
    assert "Status Report" in ws["A1"].value
    assert ws["A2"].value == "Generated 2026-11-16"
    rows = {row[0].value: row[1].value for row in ws.iter_rows(min_row=4)}
    assert rows == {
        "Status": "Count", "requested": 2, "received": 1,
        "verified": 1, "Total": 4, "Overdue": 2,
    }
    # Header and total rows are formatted bold.
    assert ws["A4"].font.bold is True
    assert ws["A8"].font.bold is True


def test_report_xlsx_detail_rows_match_csv_columns(tmp_path, populated_store):
    path = str(tmp_path / "report.xlsx")
    report.write_xlsx(populated_store, path, today=TODAY)
    ws = _load_xlsx(path)["Detail"]
    header = [c.value for c in ws[1]]
    assert header == report.CSV_FIELDS
    assert ws.max_row == 5  # header + 4 items
    first = [c.value for c in ws[2]]
    assert first == [
        1, "iso27001", None, "A.8.13", "Information backup",
        "Backup restore test results", "IT Operations",
        "2026-11-10", "requested", "yes",
    ]
    verified = [c.value for c in ws[4]]
    assert verified[-1] == "no"  # verified items are never overdue
    assert ws.freeze_panes == "A2"
    assert ws.auto_filter.ref == "A1:J5"


def test_report_xlsx_detail_includes_soc2_framework(tmp_path, empty_store):
    core.add_evidence(
        empty_store, "CC6.1", "Access control matrix", "IT Operations",
        "2026-11-10", framework="soc2",
    )
    path = str(tmp_path / "report.xlsx")
    report.write_xlsx(empty_store, path, today=TODAY)
    ws = _load_xlsx(path)["Detail"]
    row = [c.value for c in ws[2]]
    assert row[1] == "soc2"
    assert row[2] is None  # no engagement; openpyxl reads "" back as None
    assert row[3] == "CC6.1"
    assert row[4] == "Logical access security"


def test_report_xlsx_empty_store(tmp_path, empty_store):
    path = str(tmp_path / "report.xlsx")
    report.write_xlsx(empty_store, path, today=TODAY)
    wb = _load_xlsx(path)
    rows = {r[0].value: r[1].value for r in wb["Summary"].iter_rows(min_row=4)}
    assert rows["Total"] == 0
    assert rows["Overdue"] == 0
    assert wb["Detail"].max_row == 1  # header only


def test_report_html_contents(tmp_path, populated_store):
    path = str(tmp_path / "report.html")
    report.write_html(populated_store, path, today=TODAY)
    text = open(path, encoding="utf-8").read()
    assert "Counts by status" in text
    assert "Backup restore test results" in text  # appears in overdue list
    assert "MFA configuration export" not in text  # not overdue, not listed
