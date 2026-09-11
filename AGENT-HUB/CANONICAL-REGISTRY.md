# Para Sayfa Canonical Registry

| Sayfa | Kanonik URL | Not |
|-------|-------------|-----|
| Ana sayfa | https://ledajans.com/ | www/http → 301 |
| LED ekran hub | https://ledajans.com/led-ekran/ | Cornerstone |
| İç mekan | https://ledajans.com/ic-mekan-led-ekran/ | |
| Dış mekan | https://ledajans.com/dis-mekan-led-ekran/ | Trailing slash zorunlu |
| Rental | https://ledajans.com/rental-ekran/ | `/case/rental-ekran/` kullanma |
| COB | https://ledajans.com/cob-ekran/ | |
| GOB | https://ledajans.com/gob-led-ekran/ | Sözlük: `/gob-led-nedir/` · karşılaştırma: `/gob-vs-cob-smd/` |
| Kontrol kartları | https://ledajans.com/kontrol-kartlari/ | `/case/kontrol-kartlari/` → 301 (cluster-301) |
| Güç kaynağı | https://ledajans.com/guc-kaynaklari/ | `/power-supply/` → 301 (onay sonrası) |

İç linklerde **yalnızca** bu URL'ler kullanılır.

**301 (TR):** `AGENT-HUB/cluster-301.csv` → Rank Math import (`AGENT-HUB/cluster-301-rankmath.csv`) veya Plesk nginx (`scripts/plesk-nginx-cluster-301-paste.conf`). Canlı: `/case/ic-mekan-led-ekran/`, `/case/dis-mekan-led-ekran/`, `/case/rental-ekran/` 301 OK. Rank Math REST 404; kalan CSV kuralları (junk slug, `/sozluk/gob-led-nedir/`, GOB SKU) henüz yazılmadı.

**EN/DE `/en/case/...` ve `/de/case/...`:** TR kanoniklere 301 **yapılmaz**. hreflang + self-canonical kalır.
