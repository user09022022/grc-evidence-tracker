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


def test_cli_add_before_init_fails_cleanly(tmp_path, capsys):
    code, _ = run_cli(
        tmp_path, "add-evidence",
        "--control", "A.8.13", "--title", "Backup policy",
        "--owner", "IT Operations", "--due", "2026-01-01",
    )
    assert code == 1
    assert "Error" in capsys.readouterr().err
