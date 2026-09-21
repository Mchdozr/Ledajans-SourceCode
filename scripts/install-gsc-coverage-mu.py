#!/usr/bin/env python3
"""GSC coverage PHP'yi mu-plugin olarak yaz (write-files / zip / File Manager yolu)."""
from __future__ import annotations

import base64
import io
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from wp_client import load_env, open_session  # noqa: E402

SRC = os.path.join(ROOT, "wordpress-gsc-coverage.php")
UA = "LEDAJANS-GSC-MU/1.3"


def plugin_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(SRC, "ledajans-gsc-coverage/ledajans-gsc-coverage.php")
    return buf.getvalue()


def main() -> int:
    if not os.path.isfile(SRC):
        print("HATA: wordpress-gsc-coverage.php yok")
        return 1
    raw = open(SRC, "rb").read()
    if b"ledajans_gsc_go" not in raw:
        print("HATA: GSC imza yok")
        return 1
    if b"preg_match('#^/(en|de)$#'" in raw or b"preg_match('#^/(en|de)/#'" in raw:
        print("HATA: catch-all hâlâ PHP'de — kopyalama")
        return 1
    try:
        sess, site, user = open_session()
    except RuntimeError as exc:
        print("AUTH", exc)
        print("File Manager: wp-content/mu-plugins/ledajans-gsc-coverage.php")
        return 2
    print("auth_ok", user, site)
    b64 = base64.b64encode(raw).decode("ascii")
    headers = {"User-Agent": UA, "Content-Type": "application/json"}
    for payload in (
        {"gsc_b64": b64, "path": "mu-plugins/ledajans-gsc-coverage.php"},
        {"mu_b64": b64, "filename": "ledajans-gsc-coverage.php"},
        {"files": {"wp-content/mu-plugins/ledajans-gsc-coverage.php": b64}},
    ):
        r = sess.post(
            f"{site}/wp-json/ledajans/v1/write-files",
            json=payload,
            headers=headers,
            timeout=120,
        )
        print("write-files", r.status_code, (r.text or "")[:240])
        if r.status_code in (200, 201):
            return 0
    zbytes = plugin_zip()
    r2 = sess.post(
        f"{site}/wp-json/wp/v2/plugins",
        headers={"User-Agent": UA},
        files={"file": ("ledajans-gsc-coverage.zip", zbytes, "application/zip")},
        data={"status": "active"},
        timeout=120,
    )
    print("plugin_zip", r2.status_code, (r2.text or "")[:300])
    if r2.status_code in (200, 201):
        return 0
    print("FALLBACK File Manager kopya: wp-content/mu-plugins/ledajans-gsc-coverage.php")
    return 1


if __name__ == "__main__":
    sys.exit(main())
