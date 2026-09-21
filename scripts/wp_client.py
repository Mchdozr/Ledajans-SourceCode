#!/usr/bin/env python3
"""WordPress REST oturumu. Plesk URL yerine her zaman https://ledajans.com."""
from __future__ import annotations

import os
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = "https://ledajans.com"
UA = "LEDAJANS-I18N/1.0"


def load_env() -> tuple[str, str, str]:
    data: dict[str, str] = {}
    path = os.path.join(ROOT, ".env")
    if os.path.isfile(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip("\"'")
    raw_site = os.environ.get("WP_SITE_URL") or data.get("WP_SITE_URL") or ORIGIN
    site = raw_site.rstrip("/")
    if "8880" in site or "ledajans.com" not in site.lower():
        site = ORIGIN
    user = os.environ.get("WP_USERNAME") or data.get("WP_USERNAME") or ""
    pw = (os.environ.get("WP_APP_PASSWORD") or data.get("WP_APP_PASSWORD") or "").replace(
        " ", ""
    )
    return site, user, pw


def _usernames(primary: str) -> list[str]:
    out: list[str] = []
    for u in (primary, "ledajans", "admin_nstxz7t4", "admin"):
        if u and u not in out:
            out.append(u)
    return out


def open_session(
    site: str | None = None,
    user: str | None = None,
    pw: str | None = None,
    timeout: int = 40,
) -> tuple[requests.Session, str, str]:
    env_site, env_user, env_pw = load_env()
    site = (site or env_site).rstrip("/")
    user = user if user is not None else env_user
    pw = (pw if pw is not None else env_pw).replace(" ", "")
    if not pw:
        raise RuntimeError("WP_APP_PASSWORD yok")
    headers = {"User-Agent": UA, "Accept": "application/json"}
    last_err = "auth fail"
    for uname in _usernames(user):
        sess = requests.Session()
        sess.headers.update(headers)
        sess.auth = (uname, pw)
        try:
            r = sess.get(f"{site}/wp-json/wp/v2/users/me", timeout=timeout)
        except requests.RequestException as exc:
            last_err = f"{type(exc).__name__}"
            continue
        if r.status_code == 200:
            return sess, site, uname
        last_err = f"{r.status_code} {(r.text or '')[:80]}"
    raise RuntimeError(f"WP REST giris basarisiz: {last_err}")


def list_all(
    sess: requests.Session,
    site: str,
    path: str,
    *,
    params: dict | None = None,
    timeout: int = 40,
) -> list[dict]:
    items: list[dict] = []
    page = 1
    base_params = dict(params or {})
    base_params.setdefault("per_page", 100)
    while page <= 40:
        q = dict(base_params)
        q["page"] = page
        r = sess.get(f"{site}/wp-json/{path}", params=q, timeout=timeout)
        if r.status_code != 200:
            break
        batch = r.json()
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        total = int(r.headers.get("X-WP-TotalPages") or 1)
        if page >= total:
            break
        page += 1
    return items
