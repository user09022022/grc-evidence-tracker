# GRC Evidence Tracker

A small command-line tool for managing audit evidence requests during
ISO 27001 and SOC 2 engagements. Auditors issue dozens of evidence
requests ("PBC lists") per engagement; this tool tracks who owes what,
by when, and what is still outstanding — with overdue items flagged
automatically and one-command status reports for engagement meetings.

Built with Python 3 standard library only — no dependencies.

## Features (v0.1)

- **Bundled control catalogue** — 26 ISO 27001:2022 Annex A controls
  spanning all four themes (Organizational, People, Physical,
  Technological), with control id and title.
- **Evidence tracking** — record each request with its control, title,
  owner, due date, and status (`requested` / `received` / `verified`).
- **Overdue detection** — any item past its due date that is not yet
  `verified` is flagged in listings and reports.
- **Reports** — export a CSV detail file and a standalone HTML status
  page (counts by status plus the overdue list).
- **Local JSON store** — all data lives in one portable `grc_data.json`
  file; no database or account needed.

## Install

Requires Python 3.9+.

```bash
git clone https://github.com/user09022022/grc-evidence-tracker.git
cd grc-evidence-tracker
pip install .          # provides the `grc-tracker` command
```

Or run it in place without installing:

```bash
python3 grc.py --help
```

## Usage

```bash
grc-tracker init                       # create grc_data.json
grc-tracker controls                   # list the bundled controls
grc-tracker controls --theme People    # filter by theme
grc-tracker add-evidence --control A.8.13 \
    --title "Backup restore test results" \
    --owner "IT Operations" --due 2026-11-10
grc-tracker list                       # list items, overdue flagged
grc-tracker list --overdue             # only overdue items
grc-tracker report --out ./reports     # write report.csv + report.html
```

Use `--data PATH` before the subcommand to keep separate stores
(e.g. one per engagement).

## Example session (real output)

```
$ python3 grc.py init
Created data store: grc_data.json

$ python3 grc.py controls --theme Technological

Technological
-------------
  A.8.2    Privileged access rights
  A.8.3    Information access restriction
  A.8.5    Secure authentication
  A.8.9    Configuration management
  A.8.13   Information backup
  A.8.15   Logging
  A.8.24   Use of cryptography
  A.8.34   Protection of information systems during audit testing

8 control(s)

$ python3 grc.py add-evidence --control A.8.13 --title "Backup restore test results" \
      --owner "IT Operations" --due 2026-11-10
Added evidence #1: [A.8.13] Backup restore test results (owner: IT Operations, due: 2026-11-10, status: requested)

$ python3 grc.py add-evidence --control A.6.3 --title "Security awareness training records" \
      --owner "HR" --due 2026-11-12 --status received
Added evidence #2: [A.6.3] Security awareness training records (owner: HR, due: 2026-11-12, status: received)

$ python3 grc.py list
#1   [A.8.13] Backup restore test results | owner: IT Operations | due: 2026-11-10 | status: requested  ** OVERDUE **
#2   [A.6.3] Security awareness training records | owner: HR | due: 2026-11-12 | status: received  ** OVERDUE **
#3   [A.5.1] Approved information security policy | owner: CISO Office | due: 2026-11-05 | status: verified
#4   [A.8.5] MFA configuration export | owner: IT Operations | due: 2026-12-01 | status: requested

4 item(s), 2 overdue

$ python3 grc.py report --out .
Wrote ./report.csv
Wrote ./report.html
Summary: 4 item(s) — requested: 2, received: 1, verified: 1, overdue: 2
```

The generated `report.csv`:

```csv
id,control_id,control_title,title,owner,due_date,status,overdue
1,A.8.13,Information backup,Backup restore test results,IT Operations,2026-11-10,requested,yes
2,A.6.3,"Information security awareness, education and training",Security awareness training records,HR,2026-11-12,received,yes
3,A.5.1,Policies for information security,Approved information security policy,CISO Office,2026-11-05,verified,no
4,A.8.5,Secure authentication,MFA configuration export,IT Operations,2026-12-01,requested,no
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest     # 22 tests, all passing
```

Project layout:

```
grc.py                  thin CLI entry point
grc_tracker/
    __init__.py
    cli.py              argument parsing and command handlers
    core.py             evidence logic, validation, overdue rules
    controls_data.py    bundled ISO 27001:2022 Annex A starter set
    store.py            JSON data store load/save
    report.py           CSV and HTML report export
tests/                  pytest suite (core logic + CLI end-to-end)
```

See [ROADMAP.md](ROADMAP.md) for planned increments and [LOG.md](LOG.md)
for the build history.

## Author

Giovan Alarcon Lancheros — IT audit & GRC professional.

## License

MIT
