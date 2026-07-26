#!/usr/bin/env python3
"""www.ledajans.com DNS + HTTPS + 301 → apex kontrolü."""

from __future__ import annotations

import http.client
import socket
import ssl
import sys
import urllib.error
import urllib.request

APEX = "ledajans.com"
WWW = "www.ledajans.com"
EXPECTED_IP = "194.36.84.221"


def resolve_a(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return [f"RESOLVE_FAIL:{exc}"]
    ips: list[str] = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips


def cert_sans(host: str, ip: str | None = None) -> tuple[bool, list[str], str]:
    target = ip or host
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((target, 443), timeout=15) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
    except ssl.SSLCertVerificationError as exc:
        return False, [], f"CERT_VERIFY_FAIL:{exc}"
    except OSError as exc:
        return False, [], f"TLS_FAIL:{exc}"

    sans: list[str] = []
    for typ, val in cert.get("subjectAltName", ()) or ():
        if typ == "DNS":
            sans.append(val)
    ok = host in sans or any(
        s.startswith("*.") and host.endswith(s[1:]) for s in sans
    )
    return ok, sans, "ok"


def head(url: str, timeout: int = 20) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "ledajans-www-check/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl()
    except urllib.error.HTTPError as exc:
        loc = exc.headers.get("Location", "")
        return exc.code, loc or ""
    except Exception as exc:  # noqa: BLE001 — CLI özet
        return 0, f"ERR:{exc}"


def head_via_ip(ip: str, host: str, path: str = "/", scheme: str = "http") -> tuple[int, str]:
    """DNS yokken sunucu Host yönlendirmesini IP üzerinden kontrol et."""
    conn: http.client.HTTPConnection | http.client.HTTPSConnection
    if scheme == "https":
        ctx = ssl._create_unverified_context()
        conn = http.client.HTTPSConnection(ip, 443, timeout=15, context=ctx)
    else:
        conn = http.client.HTTPConnection(ip, 80, timeout=15)
    try:
        conn.request(
            "HEAD",
            path,
            headers={"Host": host, "User-Agent": "ledajans-www-check/1.0"},
        )
        resp = conn.getresponse()
        loc = resp.getheader("Location") or ""
        return resp.status, loc
    except Exception as exc:  # noqa: BLE001
        return 0, f"ERR:{exc}"
    finally:
        conn.close()


def main() -> int:
    failed = 0
    print("=== DNS ===")
    apex_ips = resolve_a(APEX)
    www_ips = resolve_a(WWW)
    print(f"  {APEX}: {', '.join(apex_ips)}")
    print(f"  {WWW}: {', '.join(www_ips)}")
    if EXPECTED_IP not in apex_ips:
        print(f"  FAIL apex IP beklenen {EXPECTED_IP}")
        failed += 1
    if www_ips and not any(x.startswith("RESOLVE_FAIL") for x in www_ips):
        if EXPECTED_IP not in www_ips and not set(www_ips) & set(apex_ips):
            print("  WARN www IP apex ile aynı değil (yine de erişilebilir olabilir)")
        print("  OK www çözülüyor")
    else:
        print("  FAIL www NXDOMAIN / çözülemiyor — Natro/Plesk DNS’e A veya CNAME ekleyin")
        failed += 1

    print("=== SSL SAN (www) ===")
    if www_ips and not any(x.startswith("RESOLVE_FAIL") for x in www_ips):
        ok, sans, msg = cert_sans(WWW)
        print(f"  SAN: {', '.join(sans) if sans else msg}")
        if ok:
            print("  OK sertifika www kapsıyor")
        else:
            print("  FAIL sertifikada www yok — Plesk Let’s Encrypt yenile (www işaretli)")
            failed += 1
    else:
        print("  SKIP (DNS yok)")

    print("=== Redirect ===")
    dns_ok = www_ips and not any(x.startswith("RESOLVE_FAIL") for x in www_ips)
    if dns_ok:
        for url in (f"http://{WWW}/", f"https://{WWW}/"):
            code, loc = head(url)
            loc_ok = loc.startswith("https://ledajans.com")
            status = "OK" if (code in (301, 308) and loc_ok) else "FAIL"
            if status == "FAIL":
                failed += 1
            print(f"  {status} {url} → {code} {loc}")
    else:
        print("  DNS yok — sunucu Host testi (IP):")
        for scheme in ("http", "https"):
            code, loc = head_via_ip(EXPECTED_IP, WWW, "/", scheme)
            loc_ok = loc.startswith("https://ledajans.com")
            status = "OK" if (code in (301, 308) and loc_ok) else "FAIL"
            print(f"  {status} {scheme}://{WWW}/ via {EXPECTED_IP} → {code} {loc}")

    print("=== Apex ===")
    code, loc = head(f"https://{APEX}/")
    if code == 200:
        print(f"  OK https://{APEX}/ → {code}")
    else:
        print(f"  FAIL https://{APEX}/ → {code} {loc}")
        failed += 1

    print()
    if failed:
        print(f"SONUC: {failed} hata — scripts/PLESK-WWW-APEX-FIX.md")
        return 1
    print("SONUC: www → apex zinciri sağlıklı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
