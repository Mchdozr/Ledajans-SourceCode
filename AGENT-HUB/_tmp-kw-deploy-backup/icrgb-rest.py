from __future__ import annotations

import base64
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
env: dict[str, str] = {}
for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    env[k.strip()] = v.strip().strip("\"'")

site = env.get("WP_SITE_URL", "https://ledajans.com").rstrip("/")
user, pw = env["WP_USERNAME"], env["WP_APP_PASSWORD"].replace(" ", "")
token = base64.b64encode(f"{user}:{pw}".encode()).decode("ascii")
auth = (user, pw)
H = {"User-Agent": "LEDAJANS-Audit/1.0", "Authorization": f"Basic {token}", "X-WP-Authorization": f"Basic {token}"}
UA = {"User-Agent": "Mozilla/5.0 LEDAJANS-Audit"}

if sys.argv[1:2] == ["run"]:
    name = sys.argv[2]
    rr = requests.get(f"{site}/wp-json/wp-abilities/v1/abilities/{name}", headers=H, auth=auth, timeout=30)
    print("schema", rr.status_code, rr.text[:800])
    rr = requests.get(f"{site}/wp-json/wp-abilities/v1/abilities/{name}/run", headers=H, auth=auth, timeout=60)
    print("GET run", rr.status_code, rr.text[:3000])
    if rr.status_code >= 400:
        rr = requests.post(f"{site}/wp-json/wp-abilities/v1/abilities/{name}/run", json={"input": {}}, headers=H, auth=auth, timeout=60)
        print("POST run", rr.status_code, rr.text[:3000])
    sys.exit(0)

if sys.argv[1:2] == ["linkposts"]:
    rr = requests.get(f"{site}/wp-json/wp-abilities/v1/abilities/rank-math/get-link-report/run", params={"input[include_posts]": "true"}, headers=H, auth=auth, timeout=90)
    (OUT_DIR := Path(__file__).resolve().parent / "icrgb-linkreport.json").write_text(rr.text, encoding="utf-8")
    print(rr.status_code, len(rr.text))
    sys.exit(0)

if sys.argv[1:2] == ["ids"]:
    rr = requests.get(f"{site}/wp-json/wp/v2/posts", params={"include": ",".join(sys.argv[2:]), "status": "any", "context": "edit", "_fields": "id,status,slug,link,title,lang,categories,modified"}, headers=H, auth=auth, timeout=40)
    for x in rr.json():
        s = requests.get(x["link"], headers=UA, timeout=20, allow_redirects=False).status_code
        print(x["id"], x["status"], s, x["link"], "|", x["title"]["raw"], "|", x.get("lang"), x["modified"])
    sys.exit(0)

if sys.argv[1:2] == ["rules"]:
    rr = requests.get(f"{site}/wp-json/redirection/v1/redirect", params={"per_page": 200, "orderby": "id", "direction": "desc"}, headers=H, auth=auth, timeout=40)
    d = rr.json()
    print("total", d.get("total"))
    for x in d.get("items", []):
        print(x["id"], x["enabled"], x["group_id"], x["match_type"], x["action_type"], x["action_code"], x["regex"], x["url"], "->", x.get("action_data"), "hits", x.get("hits"), x.get("last_access"))
    rr = requests.get(f"{site}/wp-json/redirection/v1/group", headers=H, auth=auth, timeout=40)
    print("groups", rr.text[:800])
    rr = requests.get(f"{site}/wp-json/redirection/v1/setting", headers=H, auth=auth, timeout=40)
    print("settings", rr.text[:1500])
    sys.exit(0)

if sys.argv[1:2] == ["redstatus"]:
    for ep in ("plugin", "plugin/database"):
        rr = requests.get(f"{site}/wp-json/redirection/v1/{ep}", headers=H, auth=auth, timeout=40)
        print(ep, rr.status_code, rr.text[:1500])
    sys.exit(0)

if sys.argv[1:2] == ["content"]:
    rr = requests.get(f"{site}/wp-json/wp/v2/posts", params={"include": ",".join(sys.argv[2:]), "_fields": "id,slug,content"}, headers=H, auth=auth, timeout=40)
    for x in rr.json():
        import re as _re
        t = _re.sub(r"\s+", " ", _re.sub(r"<[^>]+>", " ", x["content"]["rendered"])).strip()
        print(x["id"], x["slug"], len(t), t[:400].encode("ascii", "replace").decode())
    sys.exit(0)

if sys.argv[1:2] == ["rmmeta"]:
    for pid in sys.argv[2:]:
        rr = requests.get(f"{site}/wp-json/wp/v2/pages/{pid}", params={"context": "edit", "_fields": "meta"}, headers=H, auth=auth, timeout=30)
        m = rr.json().get("meta") or {}
        print(pid, {k: m.get(k) for k in ("rank_math_focus_keyword", "rank_math_robots", "rank_math_description")})
    sys.exit(0)

if sys.argv[1:2] == ["abilities"]:
    rr = requests.get(f"{site}/wp-json/wp-abilities/v1/abilities", params={"per_page": 100}, headers=H, auth=auth, timeout=30)
    print(rr.status_code, [x.get("name") for x in rr.json()] if rr.ok else rr.text[:300])
    rr = requests.get(f"{site}/wp-json/wp/v2/plugins", params={"_fields": "plugin,status,name"}, headers=H, auth=auth, timeout=30)
    print("plugins", rr.status_code)
    if rr.ok:
        for x in rr.json():
            print("  ", x["status"], x["plugin"], x["name"])
    else:
        print(rr.text[:300])
    rr = requests.get(f"{site}/wp-json/ledajans/v1", headers=H, auth=auth, timeout=30)
    print("ledajans ns", rr.status_code, list((rr.json().get("routes") or {}).keys()) if rr.ok else rr.text[:200])
    sys.exit(0)

if sys.argv[1:2] == ["redir"]:
    rr = requests.get(f"{site}/wp-json/wp/v2/pages/5891", params={"context": "edit", "_fields": "id,status,slug,title,link,modified,date,parent"}, headers=H, auth=auth, timeout=30)
    print("5891", rr.status_code, rr.text[:400])
    for q in ("ic-mekan", "flexible", "gob-ic", "rental"):
        rr = requests.get(f"{site}/wp-json/redirection/v1/redirect", params={"filterBy[url]": q, "per_page": 50}, headers=H, auth=auth, timeout=30)
        d = rr.json() if rr.ok else {}
        print("REDIR", q, rr.status_code, [(x.get("id"), x.get("url"), x.get("action_data"), x.get("enabled")) for x in d.get("items", [])] if d else rr.text[:200])
    rr = requests.get(f"{site}/wp-json/rankmath/v1/redirections", headers=H, auth=auth, timeout=30)
    print("RM", rr.status_code, rr.text[:300])
    rr = requests.get(f"{site}/wp-json/redirection/v1/404", params={"filterBy[url]": "ic-mekan", "per_page": 10}, headers=H, auth=auth, timeout=30)
    print("404LOG", rr.status_code, rr.text[:600])
    sys.exit(0)

if sys.argv[1:2] == ["trash2"]:
    rr = requests.get(f"{site}/wp-json/wp/v2/posts", params={"status": "trash", "per_page": 100, "page": 2, "context": "edit", "_fields": "id,status,slug,modified"}, headers=H, auth=auth, timeout=40)
    for x in rr.json():
        print("  ", x["id"], x["status"], x["slug"], x["modified"])
    for q in ("rental", "rgb panel", "flexible", "gob"):
        for t in ("posts", "pages"):
            rr = requests.get(f"{site}/wp-json/wp/v2/{t}", params={"search": q, "status": "publish,draft,trash,private", "per_page": 50, "context": "edit", "_fields": "id,status,slug,modified"}, headers=H, auth=auth, timeout=40)
            print("SEARCH", q, t, rr.status_code, [(x["id"], x["status"], x["slug"]) for x in rr.json()] if rr.ok else rr.text[:200])
    sys.exit(0)

if sys.argv[1:2] == ["status"]:
    for st in ("trash", "draft", "private", "pending"):
        for t in ("pages", "posts"):
            rr = requests.get(
                f"{site}/wp-json/wp/v2/{t}",
                params={"status": st, "per_page": 100, "context": "edit", "_fields": "id,status,slug,modified"},
                headers=H, auth=auth, timeout=40,
            )
            print(st, t, rr.status_code, rr.headers.get("X-WP-Total"))
            if rr.ok:
                for x in rr.json():
                    print("  ", x["id"], x["status"], x["slug"], x["modified"])
            else:
                print("  ", rr.text[:200])
    sys.exit(0)

r = requests.get(f"{site}/bu-sayfa-yok-xyz-12345/", headers=UA, timeout=20, allow_redirects=False)
print("random404", r.status_code, r.headers.get("Location"), r.headers.get("X-Redirect-By"))

slugs = sys.argv[1:] or ["h1-25-ic-mekan-rgb-panel", "p0-93-ic-mekan-led-ekran"]
for slug in slugs:
    for t in ("pages", "posts"):
        rr = requests.get(
            f"{site}/wp-json/wp/v2/{t}",
            params={"slug": slug, "status": "any", "context": "edit", "_fields": "id,status,slug,link,parent,modified"},
            headers=H, auth=auth, timeout=25,
        )
        print(slug, t, rr.status_code, rr.text[:300])
    rr = requests.get(f"{site}/wp-json/wp/v2/search", params={"search": slug.replace("-", " ")[:30], "per_page": 5}, headers=H, auth=auth, timeout=25)
    print(slug, "search", rr.status_code, rr.text[:400])
