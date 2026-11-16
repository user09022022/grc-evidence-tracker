"""JSON data store handling for the GRC Evidence Tracker."""

import json
import os

DEFAULT_PATH = "grc_data.json"
STORE_VERSION = 1


def new_store():
    """Return an empty store structure."""
    return {"version": STORE_VERSION, "evidence": []}


def init_store(path):
    """Create a new store file at *path*.

    Returns True if the file was created, False if it already existed
    (in which case the existing file is left untouched).
    """
    if os.path.exists(path):
        return False
    save_store(path, new_store())
    return True


def load_store(path):
    """Load and return the store at *path*.

    Raises FileNotFoundError if the store does not exist yet.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No data store at {path!r}. Run `init` first."
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_store(path, store):
    """Persist *store* to *path* as JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(store, fh, indent=2)
        fh.write("\n")
