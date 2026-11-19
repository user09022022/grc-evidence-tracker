"""Core logic: evidence items, validation, overdue detection, summaries."""

from datetime import date, timedelta

from .controls_data import DEFAULT_FRAMEWORK, FRAMEWORKS, controls_by_id

STATUSES = ("requested", "received", "verified")


def item_framework(item):
    """Return an evidence item's framework, defaulting legacy items.

    Items stored before v0.2 have no "framework" key; they belong to
    the ISO 27001 catalogue, which was the only one at the time.
    """
    return item.get("framework") or DEFAULT_FRAMEWORK


def parse_date(value):
    """Parse an ISO date string (YYYY-MM-DD) into a datetime.date.

    Raises ValueError with a readable message on bad input.
    """
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid date {value!r}: expected YYYY-MM-DD."
        ) from None


def _next_id(store):
    ids = [item["id"] for item in store["evidence"]]
    return (max(ids) + 1) if ids else 1


def add_evidence(store, control_id, title, owner, due_date, status="requested",
                 framework=DEFAULT_FRAMEWORK):
    """Validate and append an evidence item to *store*; return the item.

    Raises ValueError for an unknown framework, a control id that does
    not belong to that framework's catalogue, an unknown status, or a
    malformed due date.
    """
    if framework not in FRAMEWORKS:
        raise ValueError(
            f"Unknown framework {framework!r}: "
            f"expected one of {', '.join(FRAMEWORKS)}."
        )
    if control_id not in controls_by_id(framework):
        raise ValueError(
            f"Unknown control id {control_id!r} for framework {framework!r}. "
            f"Run `controls --framework {framework}` to see its catalogue."
        )
    if status not in STATUSES:
        raise ValueError(
            f"Invalid status {status!r}: expected one of {', '.join(STATUSES)}."
        )
    parse_date(due_date)  # validate format; the string form is stored
    item = {
        "id": _next_id(store),
        "framework": framework,
        "control_id": control_id,
        "title": title,
        "owner": owner,
        "due_date": due_date,
        "status": status,
        "created": date.today().isoformat(),
    }
    store["evidence"].append(item)
    return item


def is_overdue(item, today=None):
    """An item is overdue when its due date has passed and it is not verified."""
    today = today or date.today()
    return item["status"] != "verified" and parse_date(item["due_date"]) < today


def overdue_items(store, today=None):
    """Return all overdue evidence items, oldest due date first."""
    items = [i for i in store["evidence"] if is_overdue(i, today=today)]
    return sorted(items, key=lambda i: i["due_date"])


def days_until_due(item, today=None):
    """Return days from *today* until the item's due date.

    Positive when the due date is in the future, zero when it is
    today, and negative when it has already passed.
    """
    today = today or date.today()
    return (parse_date(item["due_date"]) - today).days


def days_overdue(item, today=None):
    """Return how many days the item is overdue, or 0 if it is not.

    Verified items and items not yet past due return 0, matching the
    `is_overdue` rule.
    """
    today = today or date.today()
    if not is_overdue(item, today=today):
        return 0
    return (today - parse_date(item["due_date"])).days


def due_within_items(store, within_days=7, today=None):
    """Return open items due within *within_days* days, soonest first.

    "Open" means not yet verified. Overdue items and items due today
    are always included (they are already due); the window only
    extends into the future. Raises ValueError for a negative window.
    """
    if within_days < 0:
        raise ValueError(
            f"Invalid window {within_days!r}: --days must be 0 or more."
        )
    today = today or date.today()
    cutoff = today + timedelta(days=within_days)
    items = [
        i for i in store["evidence"]
        if i["status"] != "verified" and parse_date(i["due_date"]) <= cutoff
    ]
    return sorted(items, key=lambda i: i["due_date"])


def status_counts(store):
    """Return a dict of evidence counts keyed by status, plus a total."""
    counts = {status: 0 for status in STATUSES}
    for item in store["evidence"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    counts["total"] = len(store["evidence"])
    return counts
