"""Load the frozen definitions (config/definitions.toml)."""
from __future__ import annotations

import os
import tomllib
from functools import lru_cache

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(ROOT, "config", "definitions.toml")
DATA_DIR = os.path.join(ROOT, "data", "h1")
REPORTS_DIR = os.path.join(ROOT, "reports")


@lru_cache(maxsize=1)
def load() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    # session lookup: NY hour -> label
    cfg["_session_of_hour"] = {h: name for name, hours in cfg["sessions"].items() for h in hours}
    return cfg
