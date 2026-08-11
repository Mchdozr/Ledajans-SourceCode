# ALT AGENT PROMPT STANDARDI (apply-with-gates)

Protokol: `AGENT-HUB/COALITION-PROTOCOL.md`

## Zorunlu Kurallar
- Mod: `apply-with-gates` (T1/T2 `[APPLY:*]`; T3 yalnız öneri + `[BLOCKER]`)
- Model: `inherit` (ana sohbet **Auto**); Task'ta başka model geçilmez
- Secret commit yok.
- CSS kilidi: `ledajans-seo-article`, CTA `#f46f2c`
- **Spawn yasak:** Yeni ajan için lidere talep et (aşağıda). Kendin `.cursor/agents/` oluşturma.

## Zorunlu Okuma
1. `AGENT-HUB/STATE.md`
2. `AGENT-HUB/TASKS.md`
3. `AGENT-HUB/KEYWORD-GUARD.json` (P0/P1)
4. `AGENT-HUB/COALITION-PROTOCOL.md`
5. Kendi raporun: `AGENT-HUB/REPORTS/<yyyy-mm-dd>-<rol>.md`

## Tartışma ve itiraz (zorunlu)
Her turda en az 1 etiket:

| Etiket | Anlam |
|--------|-------|
| `[TO:<rol>] [IDEA:<id>] …` | Fikir öner |
| `[TO:<rol>] [OBJECT:<id>] …` | Karşı gel (+ alternatif zorunlu) |
| `[TO:<rol>] [AGREE:<id>] …` | Kabul |
| `[TO:<rol>] [FB:<id>] …` | Aksiyon talebi |
| `[RESOLVED:<id>] …` | Çözüm |
| `[TO:ceo-orchestrator] [SPAWN-REQ:<id>] [ROLE:<rol>] …` | Yeni ajan iste |

`Team Sync Notes`: diğer roller için **Kabul / Revize / Red**.

## Spawn talebi (lider dışı ajanlar)
```
[TO:ceo-orchestrator] [SPAWN-REQ:SP-001] [ROLE:cro] <gerekçe + metrik>
```
Onay/red yalnız `ceo-orchestrator` verir.

## Zorunlu çıktı bloğu
Her tur kendi raporuna ekle:
- `## Execution Update - <yyyy-mm-dd HH:mm TR>`
- `### Completed Analysis`
- `### Team Sync Notes` (IDEA/OBJECT/AGREE)
- `### Proposed Changes` / `[APPLY:T1|T2]` (uygunsa)
- `### QA / Risk Check`
- `### Data/Approval Needs`
- `### Next Step (Owner + ETA)`

## Hazır Prompt
```
Rol: <rol>
Kurallar: COALITION-PROTOCOL.md + apply-with-gates
1) STATE/TASKS/KEYWORD-GUARD/kendi raporu oku
2) Diğer raporları oku; IDEA/OBJECT/AGREE/FB üret veya RESOLVED kapat
3) Gerekirse SPAWN-REQ lidere
4) T1/T2 için [APPLY:...] işaretle; T3 önerme
5) Next Step: owner + ETA
Çıktı: AGENT-HUB/REPORTS/<yyyy-mm-dd>-<rol>.md
```
