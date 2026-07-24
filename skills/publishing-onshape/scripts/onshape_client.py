"""Minimal Onshape REST client. API keys via HTTP Basic; stdlib only.

Credentials come from ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY in the environment
or from ~/.config/onshape/credentials (KEY=VALUE lines). Values are never logged.
"""
from __future__ import annotations
import base64
import json
import os
import urllib.error
import urllib.request

BASE = "https://cad.onshape.com"
CRED_PATHS = [os.path.expanduser("~/.config/onshape/credentials"),
              os.path.expanduser("~/.onshape/credentials")]
COUNT_FILE = os.path.expanduser("~/.config/onshape/api_call_count")

_calls_this_run = 0


def calls_this_run() -> int:
    return _calls_this_run


def lifetime_calls() -> int:
    try:
        with open(COUNT_FILE) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def _bump_counter() -> None:
    """Count every request (failures hit the quota too)."""
    global _calls_this_run
    _calls_this_run += 1
    total = lifetime_calls() + 1   # read BEFORE the truncating open
    try:
        with open(COUNT_FILE, "w") as f:
            f.write(str(total))
    except OSError:
        pass


def load_credentials() -> tuple[str, str]:
    access = os.environ.get("ONSHAPE_ACCESS_KEY", "")
    secret = os.environ.get("ONSHAPE_SECRET_KEY", "")
    if access and secret:
        return access, secret
    for path in CRED_PATHS:
        if os.path.exists(path):
            kv = {}
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        kv[k.strip()] = v.strip().strip('"')
            access = kv.get("ONSHAPE_ACCESS_KEY", access)
            secret = kv.get("ONSHAPE_SECRET_KEY", secret)
            if access and secret:
                return access, secret
    raise SystemExit(
        "No Onshape API keys. Create them at https://cad.onshape.com/appstore/dev-portal\n"
        "and save to ~/.config/onshape/credentials as:\n"
        "  ONSHAPE_ACCESS_KEY=...\n  ONSHAPE_SECRET_KEY=...")


class OnshapeError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body[:2000]}")
        self.status = status
        self.body = body


def request(method: str, path: str, body: dict | None = None) -> dict:
    access, secret = load_credentials()
    token = base64.b64encode(f"{access}:{secret}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    _bump_counter()
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={
        "Authorization": "Basic " + token,
        "Accept": "application/json;charset=UTF-8; qs=0.09",
        "Content-Type": "application/json",
        "User-Agent": "printagent-publishing-onshape/0.1",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode()
    except urllib.error.HTTPError as e:
        raise OnshapeError(e.code, e.read().decode(errors="replace")) from None
    return json.loads(text) if text.strip() else {}
