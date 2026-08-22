"""Simple JSON cache next to main.py — app cycle count and the last tuning set.

Nothing sensitive is stored, so this sits in the project root rather than a
platform data dir. Treat it as a cache, not a store of record: p4a re-extracts
the app directory on update, so it can legitimately vanish.

Every operation is total — a missing, corrupt, or read-only file falls back to
defaults rather than stopping the app from starting.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'tuner_cache.json')

DEFAULTS: dict = {
    'tuning': 'Standard',
    'selected_string': -1,
    'launches': 0,
    'last_opened': '',
}


def load() -> dict:
    data = dict(DEFAULTS)
    try:
        with open(CACHE_PATH, encoding='utf-8') as fh:
            saved = json.load(fh)
        if isinstance(saved, dict):
            for key, default in DEFAULTS.items():
                if key not in saved:
                    continue
                try:
                    # Coerce to the default's type here so no caller has to guard
                    # against a hand-edited file holding the wrong kind of value.
                    data[key] = type(default)(saved[key])
                except (TypeError, ValueError):
                    pass        # wrong type on disk — keep the default
    except Exception:
        pass                # missing / corrupt / unreadable — defaults are fine
    return data


def save(**kw) -> dict:
    data = load()
    data.update({k: v for k, v in kw.items() if k in DEFAULTS})
    try:
        with open(CACHE_PATH, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        pass                # read-only location — running cacheless is fine
    return data


def bump_launch() -> dict:
    """Count this run and stamp it. Returns the restored values."""
    data = load()
    data['launches'] += 1       # load() guarantees this is an int
    data['last_opened'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    return save(**data)
