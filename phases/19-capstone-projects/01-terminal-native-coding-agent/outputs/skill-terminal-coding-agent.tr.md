---
name: terminal-coding-agent
description: Bounded maliyet, sandbox tool'ları ve tam 2026 hook yüzeyiyle SWE-bench Pro üzerinde bir terminal-native coding agent kur ve değerlendir.
version: 1.0.0
phase: 19
lesson: 01
tags: [capstone, coding-agent, claude-code, swe-bench, mcp, hooks, sandbox]
---

Bir hedef repo ve doğal dilde bir görev verildiğinde, planlayan, sandbox içinde yürüten ve pull request açan bir harness kur. 30 görevlik SWE-bench Pro alt kümesinde mini-swe-agent baseline'ını eşit ya da üstüne çıkar, görev başına 5 dolar bütçenin altında kal.

Build planı:

1. Plan paneli, tool-call stream'i ve canlı token/dolar bütçesi olan bir Bun + Ink TUI harness ayağa kaldır.
2. Model Context Protocol StreamableHTTP üzerinden altı tool tanımla (read_file, edit_file, ripgrep, tree_sitter_symbols, run_shell, git). Her çağrı en fazla 4k token döner.
3. Her tool çağrısını taze bir `git worktree add` branch'inde E2B veya Daytona sandbox içinde çalıştır. Host filesystem'e asla dokunma.
4. Sekiz 2026 hook event'ini bağla: SessionStart, SessionEnd, PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, PreCompact. En az dört kullanıcı tarafından yazılmış hook gönder (destructive-command guard, token muhasebesi, OTel span emitter, trace bundle writer).
5. Üç bütçeyi zorla: 50 tur, 200k token, 5 dolar. PreCompact 150k'da tetiklenir ve eski turları özetler.
6. GenAI semantic convention'larıyla OpenTelemetry span'leri self-hosted Langfuse'a yay.
7. Başarı durumunda branch'i push et ve body'sinde plan ile trace bundle bulunan bir PR aç.
8. 30-issue'luk SWE-bench Pro Python alt kümesinde mini-swe-agent'a karşı değerlendir; görev başına pass@1, tur, token ve dolar değerlerini kaydet.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | mini-swe-agent baseline'ına karşı eşleştirilmiş 30 görevlik alt küme |
| 20 | Mimari netlik | Plan/act/observe ayrımı, hook yüzeyi, tool şeması okunabilirliği |
| 20 | Safety | Sandbox kaçış red-team'i + destructive-command guard denetimi |
| 20 | Observability | Tool çağrılarının %100'ü span'lenmiş, tur başına token muhasebesi |
| 15 | Geliştirici UX | 2 saniye altı cold-start, crash recovery, Ctrl-C iptal semantiği |

Sert ret durumları:

- Sandbox içinde değil de host filesystem üzerinde git'e shell out eden harness.
- Worktree dışına yazabilen ya da açık bir allowlist hook olmadan harici URL'lere curl atabilen herhangi bir agent.
- Aynı 30 issue üzerinde eşleştirilmiş baseline çalıştırması olmadan rapor edilen eval sayıları.
- Yeniden denemeler arasında `git reset --hard`'a bağlı "pass rate" iddiaları; SWE-bench Pro pass@1'dir.

Reddetme kuralları:

- Herhangi bir konfigürasyonda main'e doğrudan push'u reddet. Yalnızca PR branch'leri.
- Destructive-command guard'ı devre dışı bırakmayı reddet. Rubric'in sert gereksinimidir.
- Bütçe tavanı olmadan çalıştırmayı reddet. Açık uçlu çalıştırmalar eval karşılaştırmasını kirletir.

Çıktı: harness'i, eşleştirilmiş mini-swe-agent baseline çalıştırması olan sabit 30 görevlik SWE-bench Pro eval harness'ini, en az 5 tam çalıştırmaya ait OpenTelemetry trace arşivini ve harness'in çözüp baseline'ın çözemediği (ve tersi) görevleri adlandıran bir yazımı içeren bir repo. Gözlemlediğin en kritik üç failure mode'u ve her birini düzelten hook değişikliğini içeren bir bölümle bitir.
