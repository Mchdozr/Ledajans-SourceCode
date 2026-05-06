# ALT AGENT PROMPT STANDARDI (REPORT-ONLY)

## Zorunlu Kurallar
- Mod: `report-only`
- Commit/push yasak.
- Sadece `AGENT-HUB/*.md` dosyalarına yaz.
- Kod/deploy değişikliği yapma.
- Kod tarafı gerekiyorsa yalnızca `Proposed Changes` başlığında öneri ver.
- Kritik sorun varsa satır bazında `[BLOCKER]` etiketi kullan.

## Zorunlu Okuma Sırası
1. `AGENT-HUB/STATE.md`
2. `AGENT-HUB/TASKS.md`
3. Kendi rol raporu: `AGENT-HUB/REPORTS/<yyyy-mm-dd>-<rol>.md`
4. `AGENT-HUB/MASTER-PLAN.md`

## Zorunlu Çıktı Protokolü
- Çıktı sadece kendi rol rapor dosyasına yazılır.
- Mevcut şablon başlıkları korunur.
- Her yeni turda aşağıdaki alt başlık eklenir:
  - `## Execution Update - <yyyy-mm-dd HH:mm TR>`
  - `### Completed Analysis`
  - `### Team Sync Notes`
  - `### Proposed Changes (No Apply)`
  - `### QA / Risk Check`
  - `### Data/Approval Needs`
  - `### Next Step (Owner + ETA)`

## Profesyonel Web Yönetim Ekibi Davranışı
- Sadece itiraz üretme; her turda çözüm, sahiplik ve kalite kontrol maddesi çıkar.
- Diğer raporlardan gelen görüşleri `Team Sync Notes` içinde "Kabul/Revize/Red" olarak işle.
- Her öneride teknik etki + SEO etkisi + risk kısa notu bulunmalı.
- Uygulama yok; yalnız uygulanabilir teknik görev tanımı ve dosya bazlı öneri üret.

## Otomatik Feedback Döngü Etiketleri (Zorunlu)
- Başka bir role aksiyon isteyen geri bildirim formatı:
  - `[TO:<rol>] [FB:<id>] <talep/çözüm beklentisi>`
  - Örnek: `[TO:gsc] [FB:TS001] canonical çakışması için URL Inspection sonucu paylaş`
- Geri bildirimi çözen rol, aynı ID ile kapatır:
  - `[RESOLVED:<id>] <çözüm özeti>`
- Her turda kural:
  - En az 1 adet `[TO:...] [FB:...]` veya açık feedback’e `[RESOLVED:...]` yanıtı üret.
  - Açık feedback bırakıldıysa `Next Step` içinde owner ve round ETA yaz.

## Hazır Prompt Şablonu
```
Rol: <rol>
Repo: /workspace
Kurallar:
- report-only mod
- commit/push yapma
- sadece AGENT-HUB/*.md yaz
- kod değişikliğini uygulama, sadece Proposed Changes ver

Görev:
1) STATE.md + TASKS.md + MASTER-PLAN.md + kendi rol raporunu oku.
2) Kendi rol raporunu aynı dosyada güncelle.
3) Zorunlu "Execution Update" bloklarını ekle.
4) Team Sync Notes içinde diğer rollerden gelen maddeleri değerlendir (Kabul/Revize/Red).
5) QA/Risk kontrolü ve Owner+ETA içeren Next Step yaz.
6) Kritik sorun varsa [BLOCKER] ekle.
7) Kısa özet dön.

Zorunlu çıktı dosyası:
AGENT-HUB/REPORTS/<yyyy-mm-dd>-<rol>.md
```
