# Agent Workbench Pack

Güvenilir agent çalışması isteyen herhangi bir repo için drop-in workbench.

## Ne elde edersin

- Pack'in geri kalanına kısa router olarak `AGENTS.md`.
- Kurallar, reliability politikası, handoff protokolü, reviewer rubric için `docs/`.
- State, board ve scope contract için JSON Schema'lar olarak `schemas/`.
- Init, feedback runner, verification gate, handoff generator olarak `scripts/`.
- İdempotent installer olarak `bin/install.sh`.

## Hızlı başlangıç

```
bin/install.sh
$EDITOR task_board.json
python3 scripts/init_agent.py
```

## Versiyonlama

`VERSION` dosyası kontrattır. Major bump'lar state migration gerektirir.
