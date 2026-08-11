# LEDAJANS kalıcı Cursor alt ajanları

Bu klasördeki `.md` dosyalar Cursor custom subagent tanımlarıdır. Ana ajan ilgili işte **onay sormadan** çağırır.

Yönlendirme: `../rules/ledajans-subagents.mdc`  
Protokol: `../../AGENT-HUB/COALITION-PROTOCOL.md`  
Stack: `../../AGENT-HUB/CURSOR-STACK-RESEARCH.md`

## Koalisyon davranışı
- **Lider** (`ceo-orchestrator`): görev dağıtır; gerekirse `[NEW:<rol>]` ile yeni ajan açar; `[SPAWN-REQ]` Kabul/Red; `[CEO-DECISION]` tie-break.
- **Uzmanlar**: birbirleriyle `[IDEA|OBJECT|AGREE|FB]` konuşur; karşı gelebilir; yeni ajan için yalnız lidere `[SPAWN-REQ]` yazar.
- Açık itiraz/FB varken deploy yok.
