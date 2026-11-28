"""End-to-end tests of the CLI entry point."""

import os
from datetime import date, timedelta

from grc_tracker import cli


def run_cli(tmp_path, *argv):
    data = str(tmp_path / "data.json")
    return cli.main(["--data", data, *argv]), data


def test_cli_init_add_list_report(tmp_path, capsys):
    code, data = run_cli(tmp_path, "init")
    assert code == 0

    code, _ = run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-01-01",
    )
    assert code == 0

    code, _ = run_cli(tmp_path, "list")
    assert code == 0
    out = capsys.readouterr().out
    assert "Backup policy" in out
    assert "OVERDUE" in out  # due date is in the past, status requested

    out_dir = str(tmp_path / "out")
    code, _ = run_cli(tmp_path, "report", "--out", out_dir)
    assert code == 0
    assert os.path.exists(os.path.join(out_dir, "report.csv"))
    assert os.path.exists(os.path.join(out_dir, "report.html"))


def test_cli_controls_lists_catalogue(tmp_path, capsys):
    code, _ = run_cli(tmp_path, "controls")
    assert code == 0
    out = capsys.readouterr().out
    for theme in ("Organizational", "People", "Physical", "Technological"):
        assert theme in out
    assert "26 control(s) [iso27001]" in out


def test_cli_controls_soc2_lists_cc_series(tmp_path, capsys):
    code, _ = run_cli(tmp_path, "controls", "--framework", "soc2")
    assert code == 0
    out = capsys.readouterr().out
    assert "33 control(s) [soc2]" in out
    assert "CC1.1" in out
    assert "CC6.1" in out
    assert "CC9.2" in out
    assert "Logical and Physical Access Controls" in out
    assert "A.8.13" not in out


def test_cli_controls_soc2_theme_filter(tmp_path, capsys):
    code, _ = run_cli(
        tmp_path, "controls", "--framework", "soc2",
        "--theme", "System Operations",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "CC7.4" in out
    assert "CC6.1" not in out
    assert "5 control(s) [soc2]" in out


def test_cli_controls_rejects_theme_from_other_framework(tmp_path, capsys):
    code, _ = run_cli(
        tmp_path, "controls", "--framework", "soc2", "--theme", "People",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_add_soc2_evidence_end_to_end(tmp_path, capsys):
    code, data = run_cli(tmp_path, "init")
    assert code == 0
    code, _ = run_cli(
        tmp_path, "add-evidence", "--framework", "soc2",
        "--control", "CC6.1", "--title", "Access control matrix",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "[soc2/CC6.1]" in out

    code, _ = run_cli(tmp_path, "list")
    assert code == 0
    out = capsys.readouterr().out
    assert "[soc2/CC6.1]" in out
    assert "Access control matrix" in out

    # A SOC 2 control without the flag defaults to iso27001 and fails.
    code, _ = run_cli(
        tmp_path, "add-evidence",
        "--control", "CC7.4", "--title", "Incident plan",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err


def _iso(days_from_today):
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def test_cli_list_shows_days_overdue(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", _iso(-3),
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "list")
    assert code == 0
    out = capsys.readouterr().out
    assert "OVERDUE (3 days overdue)" in out


def test_cli_due_lists_overdue_and_upcoming_only(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Overdue item",
        "--owner", "IT Operations", "--due", _iso(-2),
    )
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.15", "--title", "Due soon item",
        "--owner", "HR", "--due", _iso(3),
    )
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.5", "--title", "Far future item",
        "--owner", "HR", "--due", _iso(30),
    )
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.5.1", "--title", "Verified old item",
        "--owner", "CISO Office", "--due", _iso(-10), "--status", "verified",
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "due")
    assert code == 0
    out = capsys.readouterr().out
    assert "Overdue item" in out
    assert "OVERDUE (2 days overdue)" in out
    assert "Due soon item" in out
    assert "due in 3 days" in out
    assert "Far future item" not in out
    assert "Verified old item" not in out
    assert "2 item(s) due within 7 day(s), 1 overdue" in out


def test_cli_due_days_flag_widens_window(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.5", "--title", "Far future item",
        "--owner", "HR", "--due", _iso(30),
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "due")
    assert code == 0
    assert "No items due within 7 day(s)." in capsys.readouterr().out
    code, _ = run_cli(tmp_path, "due", "--days", "30")
    assert code == 0
    out = capsys.readouterr().out
    assert "Far future item" in out
    assert "due in 30 days" in out


def test_cli_due_rejects_negative_days(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "due", "--days", "-1")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_due_out_writes_reminder_digest(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Overdue item",
        "--owner", "IT Operations", "--due", _iso(-1),
    )
    capsys.readouterr()
    digest = str(tmp_path / "reminders.txt")
    code, _ = run_cli(tmp_path, "due", "--out", digest)
    assert code == 0
    out = capsys.readouterr().out
    assert f"Wrote reminder digest: {digest}" in out
    text = open(digest, encoding="utf-8").read()
    assert "Reminder Digest" in text
    assert "IT Operations (1 item(s))" in text
    assert "Overdue item" in text
    assert "1 day overdue" in text


def test_cli_update_changes_status_and_persists(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "update", "1", "--status", "received")
    assert code == 0
    out = capsys.readouterr().out
    assert "Updated evidence #1" in out
    assert "status: received" in out

    code, _ = run_cli(tmp_path, "list")
    assert code == 0
    out = capsys.readouterr().out
    assert "status: received" in out


def test_cli_update_owner_and_due(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    capsys.readouterr()
    code, _ = run_cli(
        tmp_path, "update", "1",
        "--owner", "Security Team", "--due", "2026-12-20",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "owner: Security Team" in out
    assert "due: 2026-12-20" in out


def test_cli_update_unknown_id_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "update", "99", "--status", "received")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_update_without_fields_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "update", "1")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_update_rejects_invalid_due_date(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "update", "1", "--due", "Dec 20")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_show_prints_item_and_history(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", _iso(-5),
    )
    run_cli(tmp_path, "update", "1", "--status", "received")
    run_cli(tmp_path, "update", "1", "--owner", "Security Team")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "show", "1")
    assert code == 0
    out = capsys.readouterr().out
    assert "Evidence #1: [iso27001/A.8.13] Backup policy" in out
    assert "A.8.13 — Information backup" in out
    assert "Owner:     Security Team" in out
    assert "Status:    received" in out
    assert "Overdue:   yes (5 days overdue)" in out
    assert "History:" in out
    assert "created" in out
    assert "status: requested -> received" in out
    assert "owner: IT Operations -> Security Team" in out


def test_cli_show_without_updates_shows_creation_only(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.5", "--title", "MFA export",
        "--owner", "IT Operations", "--due", _iso(10),
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "show", "1")
    assert code == 0
    out = capsys.readouterr().out
    assert "Overdue:   no" in out
    assert "created" in out
    assert "->" not in out


def test_cli_show_unknown_id_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "show", "42")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_report_xlsx_writes_only_workbook(tmp_path, capsys):
    import pytest
    pytest.importorskip("openpyxl")
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    capsys.readouterr()
    out_dir = str(tmp_path / "out")
    code, _ = run_cli(tmp_path, "report", "--out", out_dir, "--format", "xlsx")
    assert code == 0
    out = capsys.readouterr().out
    xlsx_path = os.path.join(out_dir, "report.xlsx")
    assert f"Wrote {xlsx_path}" in out
    assert os.path.exists(xlsx_path)
    assert not os.path.exists(os.path.join(out_dir, "report.csv"))
    assert not os.path.exists(os.path.join(out_dir, "report.html"))


def test_cli_report_format_csv_writes_only_csv(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    out_dir = str(tmp_path / "out")
    code, _ = run_cli(tmp_path, "report", "--out", out_dir, "--format", "csv")
    assert code == 0
    assert os.path.exists(os.path.join(out_dir, "report.csv"))
    assert not os.path.exists(os.path.join(out_dir, "report.html"))
    assert not os.path.exists(os.path.join(out_dir, "report.xlsx"))


def test_cli_engagements_end_to_end(tmp_path, capsys):
    run_cli(tmp_path, "init")
    code, _ = run_cli(
        tmp_path, "add-engagement",
        "--name", "acme-iso-2026", "--client", "Acme Corp",
        "--framework", "iso27001", "--period", "2026",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "acme-iso-2026" in out
    assert "Acme Corp" in out

    code, _ = run_cli(
        tmp_path, "add-engagement",
        "--name", "globex-soc2-2026", "--client", "Globex",
        "--framework", "soc2", "--period", "2026-H2",
    )
    assert code == 0
    capsys.readouterr()

    # Framework is inherited from the engagement when not passed.
    code, _ = run_cli(
        tmp_path, "add-evidence", "--engagement", "globex-soc2-2026",
        "--control", "CC6.1", "--title", "Access control matrix",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "[soc2/CC6.1]" in out
    assert "engagement: globex-soc2-2026" in out

    code, _ = run_cli(
        tmp_path, "add-evidence", "--engagement", "acme-iso-2026",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    assert code == 0
    capsys.readouterr()

    code, _ = run_cli(tmp_path, "engagements")
    assert code == 0
    out = capsys.readouterr().out
    assert "acme-iso-2026" in out
    assert "globex-soc2-2026" in out
    assert "1 item(s)" in out

    code, _ = run_cli(tmp_path, "list", "--engagement", "acme-iso-2026")
    assert code == 0
    out = capsys.readouterr().out
    assert "Backup policy" in out
    assert "Access control matrix" not in out
    assert "1 item(s)" in out

    code, _ = run_cli(tmp_path, "list")
    assert code == 0
    out = capsys.readouterr().out
    assert "Backup policy" in out
    assert "Access control matrix" in out


def test_cli_add_engagement_duplicate_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-engagement",
        "--name", "acme", "--client", "Acme Corp",
    )
    capsys.readouterr()
    code, _ = run_cli(
        tmp_path, "add-engagement",
        "--name", "acme", "--client", "Other",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_add_evidence_unknown_engagement_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(
        tmp_path, "add-evidence", "--engagement", "missing",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_add_evidence_framework_mismatch_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-engagement",
        "--name", "acme-iso", "--client", "Acme", "--framework", "iso27001",
    )
    capsys.readouterr()
    code, _ = run_cli(
        tmp_path, "add-evidence", "--engagement", "acme-iso",
        "--framework", "soc2",
        "--control", "CC6.1", "--title", "Access matrix",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_list_unknown_engagement_fails_cleanly(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "list", "--engagement", "missing")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_due_scoped_to_engagement(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-engagement", "--name", "acme", "--client", "Acme",
    )
    run_cli(
        tmp_path, "add-engagement", "--name", "other", "--client", "Other",
    )
    run_cli(
        tmp_path, "add-evidence", "--engagement", "acme",
        "--control", "A.8.13", "--title", "Acme overdue",
        "--owner", "IT Operations", "--due", _iso(-2),
    )
    run_cli(
        tmp_path, "add-evidence", "--engagement", "other",
        "--control", "A.8.15", "--title", "Other overdue",
        "--owner", "HR", "--due", _iso(-2),
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "due", "--engagement", "acme")
    assert code == 0
    out = capsys.readouterr().out
    assert "Acme overdue" in out
    assert "Other overdue" not in out


def test_cli_report_scoped_to_engagement(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-engagement", "--name", "acme", "--client", "Acme",
    )
    run_cli(
        tmp_path, "add-evidence", "--engagement", "acme",
        "--control", "A.8.13", "--title", "Acme item",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.15", "--title", "Unassigned item",
        "--owner", "HR", "--due", "2026-12-01",
    )
    capsys.readouterr()
    out_dir = str(tmp_path / "out")
    code, _ = run_cli(
        tmp_path, "report", "--out", out_dir, "--engagement", "acme",
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "Summary: 1 item(s)" in out
    csv_text = open(
        os.path.join(out_dir, "report.csv"), encoding="utf-8",
    ).read()
    assert "Acme item" in csv_text
    assert "Unassigned item" not in csv_text
    html_text = open(
        os.path.join(out_dir, "report.html"), encoding="utf-8",
    ).read()
    assert "<h2>Engagements</h2>" in html_text
    assert "acme" in html_text
    assert "(no engagement)" in html_text


def test_cli_show_includes_engagement(tmp_path, capsys):
    run_cli(tmp_path, "init")
    run_cli(
        tmp_path, "add-engagement", "--name", "acme", "--client", "Acme",
    )
    run_cli(
        tmp_path, "add-evidence", "--engagement", "acme",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-12-01",
    )
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "show", "1")
    assert code == 0
    out = capsys.readouterr().out
    assert "Engagement: acme" in out


def test_cli_engagements_empty_store(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "engagements")
    assert code == 0
    assert "No engagements." in capsys.readouterr().out


def test_cli_serve_before_init_fails_cleanly(tmp_path, capsys):
    code, _ = run_cli(tmp_path, "serve")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_serve_rejects_bad_port(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "serve", "--port", "70000")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_serve_rejects_negative_refresh(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "serve", "--refresh", "-1")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_serve_rejects_unknown_engagement(tmp_path, capsys):
    run_cli(tmp_path, "init")
    capsys.readouterr()
    code, _ = run_cli(tmp_path, "serve", "--engagement", "missing")
    assert code == 1
    assert "Error" in capsys.readouterr().err


def test_cli_add_before_init_fails_cleanly(tmp_path, capsys):
    code, _ = run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-01-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err
