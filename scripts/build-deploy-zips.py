#!/usr/bin/env python3
"""Panelden (komutsuz) dagitim icin eklenti zip'leri uretir: deploy/zips/*.zip

Her zip ayri bir gecici eklentidir (ledajans-deployer-N). WP Admin > Eklentiler > Yeni Ekle > Eklenti Yukle
ile yuklenip etkinlestirilince payload'i yerine kopyalar (eskisini uploads/ledajans-backup/<etiket>/ altina yedekler)
ve ust kisimda sonuc bildirimi gosterir. Is bitince eklentiler silinir.
"""
import importlib.util, io, json, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("d", os.path.join(ROOT, "scripts", "deploy-lcp-images.py"))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
TAG = "lcp-panel-20261117"
SRC = open(os.path.join(ROOT, "deploy", "ledajans-deployer.php"), encoding="utf-8").read()
OUT = os.path.join(ROOT, "deploy", "zips"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))

def plugin_php(n, label):
    s = SRC.replace("ledajans_deployer_", f"ledajans_deployer{n}_")
    s = s.replace("Plugin Name: LEDAJANS Deployer (gecici)", f"Plugin Name: LEDAJANS Deployer {label} (gecici)")
    s = s.replace("'ledajans-deploy/v1', '/result'", f"'ledajans-deploy/v1', '/result{n}'")
    # admin bildirimi
    s += f'''
add_action('admin_notices', function () {{
    $r = get_option('ledajans_deployer{n}_result');
    if (!is_array($r)) {{ return; }}
    $cls = empty($r['err']) ? 'notice-success' : 'notice-error';
    echo '<div class="notice ' . $cls . '"><p><strong>LEDAJANS Deployer {label}:</strong> '
        . (isset($r['mode']) && $r['mode'] === 'rollback'
            ? 'geri yuklenen ' . count((array) $r['restored']) . ', silinen ' . count((array) $r['removed'])
            : 'yazilan ' . count((array) $r['ok']) . ', yedeklenen ' . count((array) $r['backup']))
        . ', hata ' . count((array) $r['err'])
        . (empty($r['err']) ? ' — TAMAM. Simdi bu eklentiyi devre disi birakip silin.' : ' — ' . esc_html(implode(' | ', (array) $r['err'])))
        . '</p></div>';
}});
'''
    # paylasilan yedek haritasi/olusturulanlar: tum parcalar ayni anahtar (geri alma tek seferde)
    s = s.replace(f"'ledajans_deployer{n}_map_'", "'ledajans_deployer_map_'").replace(f"'ledajans_deployer{n}_created_'", "'ledajans_deployer_created_'")
    return s

def build(n, files, mode, label):
    slug = f"ledajans-deployer-{n}"
    buf = io.BytesIO(); man = {"tag": TAG, "part": label, "mode": mode, "files": []}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{slug}/{slug}.php", plugin_php(n, label))
        for i, (p, dest) in enumerate(files):
            ext = os.path.splitext(p)[1].lower(); arc = f"payload/{i:03d}{'.txt' if ext == '.php' else ext}"
            zf.write(p, f"{slug}/{arc}"); man["files"].append({"src": arc, "dest": dest})
        zf.writestr(f"{slug}/manifest.json", json.dumps(man, ensure_ascii=False))
    name = f"{n}-ledajans-deployer-{'geri-al' if mode == 'rollback' else 'parca-' + label.replace('/', '-')}.zip"
    open(os.path.join(OUT, name), "wb").write(buf.getvalue())
    print(f"{name}  {len(buf.getvalue()) // 1024} KiB  {len(files)} dosya")

items = d.collect(); parts = d.plan_parts(items, 1_500_000)
for i, p in enumerate(parts, 1):
    build(i, p, "deploy", f"{i}/{len(parts)}")
build(9, [], "rollback", "GERI-AL")
