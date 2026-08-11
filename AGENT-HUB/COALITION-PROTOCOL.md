# Koalisyon Protokolü

Tüm ajanlar bu protokole uyar. Kelime öncelikleri: `KEYWORD-GUARD.json`.

## Yönetişim modeli

```
ceo-orchestrator (lider)
  ├─ spawn / onay / red
  ├─ öncelik ve sprint
  └─ çatışma kararı (tie-break)
       │
uzman ajanlar ⇄ fikir / itiraz / kabul
  └─ spawn talebi yalnız lidere
```

- **Lider** gerekli gördüğünde yeni ajan/rol açar (kalıcı `.cursor/agents/<rol>.md` + TASKS).
- **Uzman ajanlar** yeni ajan isteğini lidere bildirir; kendileri spawn etmez.
- Ajanlar birbirleriyle fikir alışverişi yapar, **karşı gelebilir**; açık itiraz varken deploy kilitlenir.

## Tur Zamanlaması (TR)

| Saat | Faz | Komut | Ajanlar |
|------|-----|-------|---------|
| 09:30 | Keşif | `run-coalition-cycle.py --phase discover` | ceo-orchestrator, gsc-serp, tech-seo |
| 13:00 | Uygulama | `coalition-apply.py` | wordpress-deploy, qa-auditor, risk-guardian |
| 17:00 | Kapanış | `run-coalition-cycle.py --phase close` | ceo-orchestrator, qa-auditor |

## Kelime Önceliği

1. **P0** — `led ekran*` (savunma): SERP #1, GSC avg ≤ 5
2. **P1** — 7 ürün kategorisi (büyüme): GSC avg ≤ 10

Alarm → otomatik sprint (`TASKS.md` P-016…P-022 veya `[ALARM:P0]` / `[ALARM:P1]`).

---

## 1) Lider spawn (self-spawn)

CEO şu durumlarda yeni ajan açar:

- Mevcut roller görevi karşılamıyorsa
- P0/P1 alarm için paralel uzmanlık gerekiyorsa
- `[SPAWN-REQ:*]` onaylandıysa
- Blokajı aşmak için geçici uzman gerekirse

### Lider komutları

```
[NEW:<rol-adı>]
[SPAWN-APPROVED:<req-id>] [NEW:<rol-adı>] <brief>
[SPAWN-REJECTED:<req-id>] <neden>
```

Lider onayında:

1. `TASKS.md` → `[NEW:<rol>]` satırı
2. `AGENT-HUB/REPORTS/<tarih>-<rol>.md` şablon (auto_orchestrator)
3. Kalıcıysa `.cursor/agents/<rol>.md` oluştur / öner
4. Router kuralına tetik satırı ekle (veya öner)

---

## 2) Spawn talebi (uzman → lider)

Uzman ajan **doğrudan** yeni ajan oluşturmaz. Format:

```
[TO:ceo-orchestrator] [SPAWN-REQ:<id>] [ROLE:<rol-adı>] <gerekçe + başarı metriği>
```

Örnek:

```
[TO:ceo-orchestrator] [SPAWN-REQ:SP-042] [ROLE:cro] CTA/telefon dönüşüm analizi; P0 led ekran CTR için 14g metrik
```

`auto_orchestrator.py` → `## Spawn Request Queue`. Lider her turda Open talepleri Kabul/Red ile kapatır.

---

## 3) Fikir alışverişi ve itiraz

### Fikir
```
[TO:<rol>] [IDEA:<id>] <öneri>
```

### İtiraz (karşı gelme — zorunlu alternatif)
```
[TO:<rol>] [OBJECT:<id>] <itiraz + alternatif çözüm>
```

### Kabul
```
[TO:<rol>] [AGREE:<id>] <kabul gerekçesi>
```

### Aksiyon talebi / çözüm
```
[TO:<rol>] [FB:<id>] <talep>
[RESOLVED:<id>] <çözüm özeti>
```

### Tartışma kuralları

1. Her turda en az 1: `[IDEA|OBJECT|AGREE|FB|RESOLVED|SPAWN-REQ]`
2. `[OBJECT:*]` açıkken ilgili `[APPLY:*]` yapılamaz (deploy kilidi)
3. 2 turda çözülmeyen OBJECT → lider **tie-break** yazar:
   ```
   [CEO-DECISION:<id>] <nihai karar + owner>
   ```
4. `Team Sync Notes` içinde: **Kabul / Revize / Red** + kısa gerekçe
5. Kişisel saldırı yok; teknik/SEO/risk gerekçesi zorunlu

`OBJECT` ve cevap bekleyen `FB` → `Auto Feedback Queue` (Open).  
`RESOLVED` / `CEO-DECISION` / `AGREE` ile kapanır.

---

## Deploy Kilidi

`coalition-apply.py` **çalışmaz** (exit 2) eğer:

- Açık `[FB:*]` veya `[OBJECT:*]` (çözülmemiş)
- Açık `[SPAWN-REQ:*]` (lider kararı bekliyor) — isteğe bağlı: sadece T2+ için; varsayılan: spawn talebi deploy’u kilitlemez, yalnızca FB/OBJECT kilitler
- `BLOCKER-ALERT.md` aktif
- `.coalition-status.json` → `"deploy_locked": true`

---

## Risk Katmanları

| Tier | Örnek | Uygulama |
|------|-------|----------|
| T1 | Blog, meta, iç link, schema | Otomatik |
| T2 | Performans patch, hero, alt text | Otomatik + rollback notu |
| T3 | robots, canonical, noindex, ana sayfa hero | BLOCKER — log only |

## Uygulama Kuyruğu

```
[APPLY:T1] scripts/publish-blog-post.py Blog/slug.html --publish
[APPLY:T2] deploy-to-wordpress.py (slug: led-ekran-nedir)
```

## CSS Kilidi (visual-ux)

- Blog: `ledajans-seo-article` + CTA `#f46f2c`
- Ürün sayfaları: mevcut `Urunlerimiz/` stillerine uyum
- Global tema CSS değişikliği yasak

## P0 / P1 Alarm

- P0: SERP rank ≥ 2 veya GSC `led ekran` +2 → savunma sprint
- P1: kategori +3 veya >10 → onpage + içerik + iç link + schema

## Doğrulama

```bash
python3 deploy-to-wordpress.py --dry-run
python3 scripts/run-coalition-cycle.py --phase discover
```
