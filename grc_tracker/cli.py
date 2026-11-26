"""Command-line interface for the GRC Evidence Tracker."""

import argparse
import os
import sys
from datetime import date

from . import report as report_mod
from .controls_data import (
    CONTROLS_BY_ID,
    DEFAULT_FRAMEWORK,
    FRAMEWORKS,
    controls_for,
    themes_for,
)
from .core import (
    STATUSES,
    add_engagement,
    add_evidence,
    days_overdue,
    days_until_due,
    due_within_items,
    engagement_summaries,
    find_engagement,
    find_item,
    get_engagements,
    is_overdue,
    item_engagement,
    item_framework,
    item_history,
    scoped_items,
    status_counts,
    update_evidence,
)
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

    p_add_eng = sub.add_parser(
        "add-engagement", help="create a named engagement in the store",
    )
    p_add_eng.add_argument("--name", required=True, help="engagement name (unique)")
    p_add_eng.add_argument("--client", required=True, help="client name")
    p_add_eng.add_argument(
        "--framework", choices=FRAMEWORKS, default=DEFAULT_FRAMEWORK,
        help=f"framework for this engagement (default: {DEFAULT_FRAMEWORK})",
    )
    p_add_eng.add_argument(
        "--period", default="",
        help="engagement period, e.g. '2026' or '2026-Q4' (optional)",
    )

    sub.add_parser("engagements", help="list named engagements with counts")

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
        "--framework", choices=FRAMEWORKS, default=None,
        help="framework the control belongs to "
             f"(default: {DEFAULT_FRAMEWORK}, or the engagement's "
             "framework when --engagement is given)",
    )
    p_add.add_argument(
        "--engagement", default=None,
        help="named engagement this item belongs to (must already exist)",
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
    p_list.add_argument(
        "--engagement", default=None,
        help="only show items from this named engagement",
    )

    p_due = sub.add_parser(
        "due", help="list open items due within N days (including overdue)",
    )
    p_due.add_argument(
        "--days", type=int, default=7,
        help="look-ahead window in days (default: 7)",
    )
    p_due.add_argument(
        "--out", default=None,
        help="also write a reminder digest for owners to this text file",
    )
    p_due.add_argument(
        "--engagement", default=None,
        help="only show items from this named engagement",
    )

    p_update = sub.add_parser(
        "update", help="change an item's status, owner, or due date",
    )
    p_update.add_argument("id", type=int, help="evidence item id")
    p_update.add_argument(
        "--status", choices=STATUSES, default=None, help="new status",
    )
    p_update.add_argument("--owner", default=None, help="new owner")
    p_update.add_argument(
        "--due", default=None, help="new due date, YYYY-MM-DD",
    )

    p_show = sub.add_parser(
        "show", help="show one evidence item with its full history",
    )
    p_show.add_argument("id", type=int, help="evidence item id")

    p_report = sub.add_parser("report", help="export CSV + HTML status reports")
    p_report.add_argument(
        "--out", default=".", help="output directory (default: current directory)",
    )
    p_report.add_argument(
        "--format", choices=("all", "csv", "html", "xlsx"), default="all",
        help="report format to write: csv, html, or xlsx (Excel workbook, "
             "requires openpyxl); 'all' writes CSV + HTML (default: all)",
    )
    p_report.add_argument(
        "--engagement", default=None,
        help="scope counts and detail to this named engagement "
             "(the HTML report still includes the cross-engagement summary)",
    )
    return parser


def cmd_init(args):
    if init_store(args.data):
        print(f"Created data store: {args.data}")
    else:
        print(f"Data store already exists: {args.data} (left unchanged)")
    return 0


def cmd_add_engagement(args):
    store = load_store(args.data)
    engagement = add_engagement(
        store,
        name=args.name,
        client=args.client,
        framework=args.framework,
        period=args.period,
    )
    save_store(args.data, store)
    period = f", period: {engagement['period']}" if engagement["period"] else ""
    print(
        f"Added engagement {engagement['name']!r}: "
        f"client: {engagement['client']}, "
        f"framework: {engagement['framework']}{period}"
    )
    return 0


def cmd_engagements(args):
    store = load_store(args.data)
    engagements = get_engagements(store)
    if not engagements and not store["evidence"]:
        print("No engagements.")
        return 0
    today = date.today()
    for entry in engagement_summaries(store, today=today):
        record = entry["engagement"]
        if record is None:
            print(
                f"(no engagement) — {entry['total']} item(s), "
                f"{entry['overdue']} overdue"
            )
        else:
            period = f" | period: {record['period']}" if record.get("period") else ""
            print(
                f"{record['name']} | client: {record['client']} | "
                f"framework: {record['framework']}{period} | "
                f"{entry['total']} item(s), {entry['overdue']} overdue"
            )
    if not engagements:
        print("No engagements.")
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
    framework = args.framework
    engagement = getattr(args, "engagement", None)
    if engagement is not None:
        record = find_engagement(store, engagement)
        if framework is None:
            framework = record["framework"]
    if framework is None:
        framework = DEFAULT_FRAMEWORK
    item = add_evidence(
        store,
        control_id=args.control,
        title=args.title,
        owner=args.owner,
        due_date=args.due,
        status=args.status,
        framework=framework,
        engagement=engagement,
    )
    save_store(args.data, store)
    eng_note = (
        f", engagement: {item['engagement']}" if item.get("engagement") else ""
    )
    print(
        f"Added evidence #{item['id']}: [{item['framework']}/{item['control_id']}] "
        f"{item['title']} "
        f"(owner: {item['owner']}, due: {item['due_date']}, "
        f"status: {item['status']}{eng_note})"
    )
    return 0


def cmd_list(args):
    store = load_store(args.data)
    today = date.today()
    engagement = getattr(args, "engagement", None)
    items = scoped_items(store, engagement=engagement)
    if args.overdue:
        items = [i for i in items if is_overdue(i, today=today)]
    if not items:
        print("No evidence items.")
        return 0
    overdue_count = 0
    for item in items:
        flag = ""
        if is_overdue(item, today=today):
            aged = days_overdue(item, today=today)
            unit = "day" if aged == 1 else "days"
            flag = f"  ** OVERDUE ({aged} {unit} overdue) **"
            overdue_count += 1
        eng = item_engagement(item)
        eng_part = f" | engagement: {eng}" if eng else ""
        print(
            f"#{item['id']:<3} [{item_framework(item)}/{item['control_id']}] "
            f"{item['title']} | "
            f"owner: {item['owner']} | due: {item['due_date']} | "
            f"status: {item['status']}{eng_part}{flag}"
        )
    print(f"\n{len(items)} item(s), {overdue_count} overdue")
    return 0


def cmd_due(args):
    store = load_store(args.data)
    today = date.today()
    engagement = getattr(args, "engagement", None)
    items = due_within_items(
        store, within_days=args.days, today=today, engagement=engagement,
    )
    if args.out:
        report_mod.write_reminder_digest(
            store, args.out, within_days=args.days, today=today,
            engagement=engagement,
        )
    if not items:
        print(f"No items due within {args.days} day(s).")
    else:
        overdue_count = 0
        for item in items:
            if is_overdue(item, today=today):
                aged = days_overdue(item, today=today)
                unit = "day" if aged == 1 else "days"
                flag = f"  ** OVERDUE ({aged} {unit} overdue) **"
                overdue_count += 1
            else:
                remaining = days_until_due(item, today=today)
                if remaining == 0:
                    flag = "  ** DUE TODAY **"
                elif remaining == 1:
                    flag = "  (due in 1 day)"
                else:
                    flag = f"  (due in {remaining} days)"
            print(
                f"#{item['id']:<3} [{item_framework(item)}/{item['control_id']}] "
                f"{item['title']} | "
                f"owner: {item['owner']} | due: {item['due_date']} | "
                f"status: {item['status']}{flag}"
            )
        print(
            f"\n{len(items)} item(s) due within {args.days} day(s), "
            f"{overdue_count} overdue"
        )
    if args.out:
        print(f"Wrote reminder digest: {args.out}")
    return 0


def cmd_update(args):
    store = load_store(args.data)
    item = update_evidence(
        store,
        item_id=args.id,
        status=args.status,
        owner=args.owner,
        due_date=args.due,
    )
    save_store(args.data, store)
    print(
        f"Updated evidence #{item['id']}: [{item_framework(item)}/{item['control_id']}] "
        f"{item['title']} "
        f"(owner: {item['owner']}, due: {item['due_date']}, status: {item['status']})"
    )
    return 0


def cmd_show(args):
    store = load_store(args.data)
    item = find_item(store, args.id)
    today = date.today()
    framework = item_framework(item)
    control = CONTROLS_BY_ID.get(item["control_id"], {})
    control_title = control.get("title", "Unknown control")
    print(
        f"Evidence #{item['id']}: [{framework}/{item['control_id']}] "
        f"{item['title']}"
    )
    print(f"  Control:   {item['control_id']} — {control_title}")
    print(f"  Framework: {framework}")
    print(f"  Engagement: {item_engagement(item) or '(none)'}")
    print(f"  Title:     {item['title']}")
    print(f"  Owner:     {item['owner']}")
    print(f"  Due:       {item['due_date']}")
    print(f"  Status:    {item['status']}")
    if item.get("created"):
        print(f"  Created:   {item['created']}")
    if is_overdue(item, today=today):
        aged = days_overdue(item, today=today)
        unit = "day" if aged == 1 else "days"
        print(f"  Overdue:   yes ({aged} {unit} overdue)")
    else:
        print("  Overdue:   no")
    print("  History:")
    if item.get("created"):
        print(f"    {item['created']}  created")
    history = item_history(item)
    if not history and not item.get("created"):
        print("    (no history recorded)")
    for entry in history:
        print(
            f"    {entry['date']}  {entry['field']}: "
            f"{entry['old']} -> {entry['new']}"
        )
    return 0


def cmd_report(args):
    store = load_store(args.data)
    os.makedirs(args.out, exist_ok=True)
    fmt = getattr(args, "format", "all")
    engagement = getattr(args, "engagement", None)
    written = []
    if fmt in ("all", "csv"):
        csv_path = os.path.join(args.out, "report.csv")
        report_mod.write_csv(store, csv_path, engagement=engagement)
        written.append(csv_path)
    if fmt in ("all", "html"):
        html_path = os.path.join(args.out, "report.html")
        report_mod.write_html(store, html_path, engagement=engagement)
        written.append(html_path)
    if fmt == "xlsx":
        xlsx_path = os.path.join(args.out, "report.xlsx")
        report_mod.write_xlsx(store, xlsx_path, engagement=engagement)
        written.append(xlsx_path)
    counts = status_counts(store, engagement=engagement)
    overdue = sum(
        1 for i in scoped_items(store, engagement=engagement) if is_overdue(i)
    )
    for path in written:
        print(f"Wrote {path}")
    print(
        f"Summary: {counts['total']} item(s) — "
        f"requested: {counts['requested']}, received: {counts['received']}, "
        f"verified: {counts['verified']}, overdue: {overdue}"
    )
    return 0


COMMANDS = {
    "init": cmd_init,
    "add-engagement": cmd_add_engagement,
    "engagements": cmd_engagements,
    "controls": cmd_controls,
    "add-evidence": cmd_add_evidence,
    "list": cmd_list,
    "due": cmd_due,
    "update": cmd_update,
    "show": cmd_show,
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
