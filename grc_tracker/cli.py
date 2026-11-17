"""Command-line interface for the GRC Evidence Tracker."""

import argparse
import os
import sys
from datetime import date

from . import report as report_mod
from .controls_data import (
    DEFAULT_FRAMEWORK,
    FRAMEWORKS,
    controls_for,
    themes_for,
)
from .core import STATUSES, add_evidence, is_overdue, item_framework, status_counts
from .store import DEFAULT_PATH, init_store, load_store, save_store


def build_parser():
    parser = argparse.ArgumentParser(
        prog="grc",
        description="Track audit evidence requests for ISO 27001 / SOC 2 engagements.",
    )
    parser.add_argument(
        "--data", default=DEFAULT_PATH,
        help=f"path to the JSON data store (default: {DEFAULT_PATH})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create a new local JSON data store")

    p_controls = sub.add_parser("controls", help="list bundled controls")
    p_controls.add_argument(
        "--framework", choices=FRAMEWORKS, default=DEFAULT_FRAMEWORK,
        help=f"control catalogue to list (default: {DEFAULT_FRAMEWORK})",
    )
    p_controls.add_argument(
        "--theme", default=None,
        help="only show controls from this theme/category "
             "(valid values depend on --framework)",
    )

    p_add = sub.add_parser("add-evidence", help="record an evidence request")
    p_add.add_argument(
        "--framework", choices=FRAMEWORKS, default=DEFAULT_FRAMEWORK,
        help=f"framework the control belongs to (default: {DEFAULT_FRAMEWORK})",
    )
    p_add.add_argument("--control", required=True, help="control id, e.g. A.8.13 or CC6.1")
    p_add.add_argument("--title", required=True, help="evidence item title")
    p_add.add_argument("--owner", required=True, help="person/team who must provide it")
    p_add.add_argument("--due", required=True, help="due date, YYYY-MM-DD")
    p_add.add_argument(
        "--status", choices=STATUSES, default="requested",
        help="initial status (default: requested)",
    )

    p_list = sub.add_parser("list", help="list evidence items, flagging overdue ones")
    p_list.add_argument(
        "--overdue", action="store_true", help="only show overdue items",
    )

    p_report = sub.add_parser("report", help="export CSV + HTML status reports")
    p_report.add_argument(
        "--out", default=".", help="output directory (default: current directory)",
    )
    return parser


def cmd_init(args):
    if init_store(args.data):
        print(f"Created data store: {args.data}")
    else:
        print(f"Data store already exists: {args.data} (left unchanged)")
    return 0


def cmd_controls(args):
    themes = themes_for(args.framework)
    if args.theme is not None and args.theme not in themes:
        raise ValueError(
            f"Unknown theme {args.theme!r} for framework {args.framework!r}: "
            f"expected one of {', '.join(themes)}."
        )
    catalogue = controls_for(args.framework)
    controls = [c for c in catalogue if args.theme is None or c["theme"] == args.theme]
    current_theme = None
    for control in controls:
        if control["theme"] != current_theme:
            current_theme = control["theme"]
            print(f"\n{current_theme}")
            print("-" * len(current_theme))
        print(f"  {control['id']:<8} {control['title']}")
    print(f"\n{len(controls)} control(s) [{args.framework}]")
    return 0


def cmd_add_evidence(args):
    store = load_store(args.data)
    item = add_evidence(
        store,
        control_id=args.control,
        title=args.title,
        owner=args.owner,
        due_date=args.due,
        status=args.status,
        framework=args.framework,
    )
    save_store(args.data, store)
    print(
        f"Added evidence #{item['id']}: [{item['framework']}/{item['control_id']}] "
        f"{item['title']} "
        f"(owner: {item['owner']}, due: {item['due_date']}, status: {item['status']})"
    )
    return 0


def cmd_list(args):
    store = load_store(args.data)
    today = date.today()
    items = store["evidence"]
    if args.overdue:
        items = [i for i in items if is_overdue(i, today=today)]
    if not items:
        print("No evidence items.")
        return 0
    overdue_count = 0
    for item in items:
        flag = ""
        if is_overdue(item, today=today):
            flag = "  ** OVERDUE **"
            overdue_count += 1
        print(
            f"#{item['id']:<3} [{item_framework(item)}/{item['control_id']}] "
            f"{item['title']} | "
            f"owner: {item['owner']} | due: {item['due_date']} | "
            f"status: {item['status']}{flag}"
        )
    print(f"\n{len(items)} item(s), {overdue_count} overdue")
    return 0


def cmd_report(args):
    store = load_store(args.data)
    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "report.csv")
    html_path = os.path.join(args.out, "report.html")
    report_mod.write_csv(store, csv_path)
    report_mod.write_html(store, html_path)
    counts = status_counts(store)
    overdue = sum(1 for i in store["evidence"] if is_overdue(i))
    print(f"Wrote {csv_path}")
    print(f"Wrote {html_path}")
    print(
        f"Summary: {counts['total']} item(s) — "
        f"requested: {counts['requested']}, received: {counts['received']}, "
        f"verified: {counts['verified']}, overdue: {overdue}"
    )
    return 0


COMMANDS = {
    "init": cmd_init,
    "controls": cmd_controls,
    "add-evidence": cmd_add_evidence,
    "list": cmd_list,
    "report": cmd_report,
}


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
