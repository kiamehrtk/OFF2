"""Minimal Tixr Studio API client.

Signing was derived by probing the live API — Tixr's docs sit behind a client
login. The hash is HMAC-SHA256 of the request PATH plus "?" plus the query
string with params sorted alphabetically, hex-encoded. Signing the query
string alone (the obvious reading) returns 9004 "Hash invalid".

Credentials come from the environment: locally from .env (gitignored), and in
CI from GitHub Actions secrets. Never hard-code them — this repo is public.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.request

BASE = "https://studio.tixr.com"


def load_env(path=None):
    """Read a .env file into os.environ without overwriting real env vars."""
    path = path or os.path.join(os.path.dirname(__file__), os.pardir, ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _sign(path, params, secret):
    qs = "&".join("%s=%s" % (k, params[k]) for k in sorted(params))
    digest = hmac.new(secret.encode(), (path + "?" + qs).encode(),
                      hashlib.sha256).hexdigest()
    return qs + "&hash=" + digest


def fetch_events(group_id, cpk, secret, page_size=100, timeout=30):
    path = "/v1/groups/%s/events" % group_id
    params = {"cpk": cpk, "t": str(int(time.time() * 1000)),
              "page_size": str(page_size)}
    url = "%s%s?%s" % (BASE, path, _sign(path, params, secret))
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def credentials(group):
    """Return (group_id, cpk, secret) for a group key like 'HARBOUR'."""
    load_env()
    names = ["TIXR_GROUP_" + group, "TIXR_CPK_" + group, "TIXR_SECRET_" + group]
    values = [os.environ.get(n) for n in names]
    missing = [n for n, v in zip(names, values) if not v]
    if missing:
        raise SystemExit("Missing credentials: %s\n"
                         "Set them in .env locally, or as GitHub Actions "
                         "secrets in CI." % ", ".join(missing))
    return values
