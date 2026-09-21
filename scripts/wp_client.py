#!/usr/bin/env python3
"""WordPress REST oturumu. Plesk URL yerine her zaman https://ledajans.com."""
from __future__ import annotations

import base64
import os
import re

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = "https://ledajans.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LEDAJANS-I18N/1.0"


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
    raw_site = data.get("WP_SITE_URL") or os.environ.get("WP_SITE_URL") or ORIGIN
    site = raw_site.rstrip("/")
    if "8880" in site or "ledajans.com" not in site.lower():
        site = ORIGIN
    user = data.get("WP_USERNAME") or os.environ.get("WP_USERNAME") or ""
    pw = (
        data.get("WP_APP_PASSWORD")
        or data.get("WP_PASSWORD")
        or os.environ.get("WP_APP_PASSWORD")
        or os.environ.get("WP_PASSWORD")
        or ""
    )
    return site, user, pw


def _usernames(primary: str) -> list[str]:
    out: list[str] = []
    for u in (primary, "cursor", "ledajans", "admin_nstxz7t4", "admin"):
        if u and u not in out:
            out.append(u)
    return out


def _passwords(primary: str) -> list[str]:
    out: list[str] = []
    for p in (primary, primary.rstrip("."), primary.replace(" ", "")):
        if p and p not in out:
            out.append(p)
    return out


def _apply_basic(sess: requests.Session, user: str, pw: str) -> None:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    basic = f"Basic {token}"
    sess.auth = (user, pw)
    sess.headers["Authorization"] = basic
    sess.headers["X-WP-Authorization"] = basic
    sess.headers["X-Authorization"] = basic


def _nonce_from_html(html: str) -> str:
    for pat in (
        r'wpApiSettings\s*=\s*\{[^}]*"nonce"\s*:\s*"([^"]+)"',
        r'restNonce"\s*:\s*"([^"]+)"',
        r'name="_wpnonce"\s+value="([^"]+)"',
    ):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return ""


def _cookie_session(site: str, user: str, pw: str, timeout: int) -> requests.Session | None:
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA, "Accept": "text/html,application/json"})
    try:
        sess.get(f"{site}/wp-login.php", timeout=timeout)
        r = sess.post(
            f"{site}/wp-login.php",
            data={
                "log": user,
                "pwd": pw,
                "wp-submit": "Log In",
                "redirect_to": f"{site}/wp-admin/",
                "testcookie": "1",
            },
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return None
    if not any(c.name.startswith("wordpress_logged_in") for c in sess.cookies):
        return None
    nonce = _nonce_from_html(r.text or "")
    if not nonce:
        try:
            admin = sess.get(f"{site}/wp-admin/", timeout=timeout)
            nonce = _nonce_from_html(admin.text or "")
        except requests.RequestException:
            nonce = ""
    if nonce:
        sess.headers["X-WP-Nonce"] = nonce
    sess.headers["Accept"] = "application/json"
    try:
        me = sess.get(f"{site}/wp-json/wp/v2/users/me", timeout=timeout)
    except requests.RequestException:
        return None
    if me.status_code == 200:
        return sess
    return None


def open_session(
    site: str | None = None,
    user: str | None = None,
    pw: str | None = None,
    timeout: int = 40,
) -> tuple[requests.Session, str, str]:
    env_site, env_user, env_pw = load_env()
    site = (site or env_site).rstrip("/")
    user = user if user is not None else env_user
    pw = pw if pw is not None else env_pw
    if not pw:
        raise RuntimeError("WP_APP_PASSWORD yok")
    headers = {"User-Agent": UA, "Accept": "application/json"}
    last_err = "auth fail"
    for uname in _usernames(user):
        for candidate in _passwords(pw):
            sess = requests.Session()
            sess.headers.update(headers)
            _apply_basic(sess, uname, candidate)
            try:
                r = sess.get(f"{site}/wp-json/wp/v2/users/me", timeout=timeout)
            except requests.RequestException as exc:
                last_err = f"{type(exc).__name__}"
                continue
            if r.status_code == 200:
                return sess, site, uname
            last_err = f"rest {r.status_code} {(r.text or '')[:80]}"
            cookie = _cookie_session(site, uname, candidate, timeout)
            if cookie is not None:
                _apply_basic(cookie, uname, candidate)
                return cookie, site, uname
            last_err = f"login+rest fail user={uname}"
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
