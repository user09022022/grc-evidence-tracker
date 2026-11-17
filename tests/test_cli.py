"""End-to-end tests of the CLI entry point."""

import os

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


def test_cli_add_before_init_fails_cleanly(tmp_path, capsys):
    code, _ = run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-01-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err
