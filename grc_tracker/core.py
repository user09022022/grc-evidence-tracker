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


def item_engagement(item):
    """Return an evidence item's engagement name, or None.

    Items stored before v0.6 have no "engagement" key; they belong to
    no named engagement (they are "unassigned").
    """
    return item.get("engagement") or None


# --- Engagements (v0.6) ----------------------------------------------------

def get_engagements(store):
    """Return the store's engagement list (empty for legacy stores)."""
    return list(store.get("engagements") or [])


def find_engagement(store, name):
    """Return the engagement called *name* from *store*.

    Raises ValueError if no engagement has that name.
    """
    for engagement in store.get("engagements") or []:
        if engagement["name"] == name:
            return engagement
    raise ValueError(f"No engagement named {name!r}.")


def add_engagement(store, name, client, framework=DEFAULT_FRAMEWORK,
                   period="", today=None):
    """Validate and append a named engagement to *store*; return it.

    An engagement groups evidence for one client, framework and
    period (for example one ISO 27001 audit season). Raises ValueError
    for an empty or duplicate name, an empty client, or an unknown
    framework.
    """
    if name is None or not str(name).strip():
        raise ValueError("Engagement name must not be empty.")
    name = str(name).strip()
    if client is None or not str(client).strip():
        raise ValueError("Engagement client must not be empty.")
    if framework not in FRAMEWORKS:
        raise ValueError(
            f"Unknown framework {framework!r}: "
            f"expected one of {', '.join(FRAMEWORKS)}."
        )
    engagements = store.setdefault("engagements", [])
    if any(e["name"] == name for e in engagements):
        raise ValueError(f"Engagement {name!r} already exists.")
    today = today or date.today()
    engagement = {
        "name": name,
        "client": str(client).strip(),
        "framework": framework,
        "period": (period or "").strip(),
        "created": today.isoformat(),
    }
    engagements.append(engagement)
    return engagement


def require_engagement(store, engagement):
    """Return the engagement dict for *engagement*, or None if unset.

    Raises ValueError when a name is given but no such engagement
    exists — scoping by a misspelled name must never silently return
    an empty view.
    """
    if engagement is None:
        return None
    return find_engagement(store, engagement)


def scoped_items(store, engagement=None):
    """Return evidence items, filtered to *engagement* when given.

    With no engagement, every item is returned (in store order).
    Raises ValueError for an unknown engagement name.
    """
    if engagement is None:
        return list(store["evidence"])
    require_engagement(store, engagement)
    return [
        i for i in store["evidence"] if item_engagement(i) == engagement
    ]


def engagement_summaries(store, today=None):
    """Return per-engagement count summaries for cross-engagement views.

    One entry per named engagement (in store order), each a dict with
    the engagement record plus total / by-status / overdue counts for
    its items. When items exist that belong to no named engagement,
    a final entry with ``engagement`` set to None covers them.
    """
    today = today or date.today()
    summaries = []
    for engagement in get_engagements(store):
        items = [
            i for i in store["evidence"]
            if item_engagement(i) == engagement["name"]
        ]
        counts = {status: 0 for status in STATUSES}
        for item in items:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        summaries.append({
            "engagement": engagement,
            "total": len(items),
            "counts": counts,
            "overdue": sum(1 for i in items if is_overdue(i, today=today)),
        })
    unassigned = [
        i for i in store["evidence"] if item_engagement(i) is None
    ]
    if unassigned:
        counts = {status: 0 for status in STATUSES}
        for item in unassigned:
            counts[item["status"]] = counts.get(item["status"], 0) + 1
        summaries.append({
            "engagement": None,
            "total": len(unassigned),
            "counts": counts,
            "overdue": sum(
                1 for i in unassigned if is_overdue(i, today=today)
            ),
        })
    return summaries


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
                 framework=DEFAULT_FRAMEWORK, engagement=None):
    """Validate and append an evidence item to *store*; return the item.

    Raises ValueError for an unknown framework, a control id that does
    not belong to that framework's catalogue, an unknown status, or a
    malformed due date. When *engagement* is given it must name an
    existing engagement, and *framework* must match that engagement's
    framework.
    """
    if framework not in FRAMEWORKS:
        raise ValueError(
            f"Unknown framework {framework!r}: "
            f"expected one of {', '.join(FRAMEWORKS)}."
        )
    if engagement is not None:
        record = find_engagement(store, engagement)
        if record["framework"] != framework:
            raise ValueError(
                f"Engagement {engagement!r} uses framework "
                f"{record['framework']!r}, not {framework!r}."
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
        "engagement": engagement,
        "control_id": control_id,
        "title": title,
        "owner": owner,
        "due_date": due_date,
        "status": status,
        "created": date.today().isoformat(),
        "history": [],
    }
    store["evidence"].append(item)
    return item


def find_item(store, item_id):
    """Return the evidence item with *item_id* from *store*.

    Raises ValueError if no item has that id.
    """
    for item in store["evidence"]:
        if item["id"] == item_id:
            return item
    raise ValueError(f"No evidence item with id {item_id}.")


def item_history(item):
    """Return an item's change history, oldest first.

    Items stored before v0.4 have no "history" key; they are treated
    as having no recorded changes (their creation is still shown from
    the item's "created" date).
    """
    return list(item.get("history") or [])


def update_evidence(store, item_id, status=None, owner=None, due_date=None,
                    today=None):
    """Change an item's status, owner and/or due date in place.

    Only the fields passed as non-None are considered. Each field
    whose value actually changes is recorded in the item's history
    as ``{"date", "field", "old", "new"}`` and the item is returned.

    Raises ValueError if the item does not exist, if no field is
    provided, if every provided value already matches the item, or
    if a provided status or due date is invalid (an empty owner is
    likewise rejected).
    """
    item = find_item(store, item_id)
    if status is None and owner is None and due_date is None:
        raise ValueError(
            "Nothing to update: provide at least one of "
            "status, owner, or due date."
        )
    if status is not None and status not in STATUSES:
        raise ValueError(
            f"Invalid status {status!r}: expected one of {', '.join(STATUSES)}."
        )
    if owner is not None and not owner.strip():
        raise ValueError("Owner must not be empty.")
    if due_date is not None:
        parse_date(due_date)  # validate format; the string form is stored
    today = today or date.today()
    history = item.setdefault("history", [])
    changes = []
    for field, new_value in (
        ("status", status), ("owner", owner), ("due_date", due_date),
    ):
        if new_value is None:
            continue
        old_value = item[field]
        if new_value == old_value:
            continue
        history.append({
            "date": today.isoformat(),
            "field": field,
            "old": old_value,
            "new": new_value,
        })
        item[field] = new_value
        changes.append(field)
    if not changes:
        raise ValueError(
            "No changes: the new value(s) already match the item."
        )
    return item


def is_overdue(item, today=None):
    """An item is overdue when its due date has passed and it is not verified."""
    today = today or date.today()
    return item["status"] != "verified" and parse_date(item["due_date"]) < today


def overdue_items(store, today=None, engagement=None):
    """Return overdue evidence items, oldest due date first.

    When *engagement* is given, only that engagement's items count.
    """
    items = [
        i for i in scoped_items(store, engagement=engagement)
        if is_overdue(i, today=today)
    ]
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


def due_within_items(store, within_days=7, today=None, engagement=None):
    """Return open items due within *within_days* days, soonest first.

    "Open" means not yet verified. Overdue items and items due today
    are always included (they are already due); the window only
    extends into the future. When *engagement* is given, only that
    engagement's items count. Raises ValueError for a negative window
    or an unknown engagement name.
    """
    if within_days < 0:
        raise ValueError(
            f"Invalid window {within_days!r}: --days must be 0 or more."
        )
    today = today or date.today()
    cutoff = today + timedelta(days=within_days)
    items = [
        i for i in scoped_items(store, engagement=engagement)
        if i["status"] != "verified" and parse_date(i["due_date"]) <= cutoff
    ]
    return sorted(items, key=lambda i: i["due_date"])


def status_counts(store, engagement=None):
    """Return evidence counts keyed by status, plus a total.

    When *engagement* is given, only that engagement's items count.
    """
    items = scoped_items(store, engagement=engagement)
    counts = {status: 0 for status in STATUSES}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    counts["total"] = len(items)
    return counts
