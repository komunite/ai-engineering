# AGENTS.md

Agent workbench ile çalışan bir repository içinde çalışıyorsun.

Eylem öncesi bunları oku:

1. `agent_state.json` — son session'ın nerede durduğu.
2. `task_board.json` — neyin uçuşta olduğu, neyin sırada olduğu.
3. `docs/agent-rules.md` — startup, forbidden, done, uncertainty, approval.
4. `docs/reliability-policy.md` — bu workbench'in absorbe etmek için tasarlandığı failure mode'lar.
5. `docs/handoff-protocol.md` — session sonunun ne üretmesi gerektiği.
6. `docs/reviewer-rubric.md` — tamamlanan işin nasıl yargılandığı.

Verification komutu: board'daki aktif görevin `acceptance_criteria`'sına bak.

Pack versiyonu: 1.0.0
