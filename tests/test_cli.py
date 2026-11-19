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


def test_cli_add_before_init_fails_cleanly(tmp_path, capsys):
    code, _ = run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-01-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err
