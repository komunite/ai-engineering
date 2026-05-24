# Capstone 01 — Terminal-Native Coding Agent

> 2026'ya gelindiğinde bir coding agent'ın şekli oturdu. Bir TUI harness, stateful bir plan, sandbox'lanmış bir tool yüzeyi, planlayan-aksiyon alan-gözlemleyen-iyileşen bir loop. Claude Code, Cursor 3 ve OpenCode 50 metreden bakınca aynı görünür. Bu capstone senden uçtan uca bir tane inşa etmeni istiyor — CLI in, pull request out — ve onu SWE-bench Pro üzerinde mini-swe-agent ve Live-SWE-agent'a karşı ölçmeni. İşin zor kısmının model çağrısı değil, tool loop'u, sandbox ve 50 turluk bir koşunun maliyet tavanı olduğunu öğreneceksin.

**Tür:** Bitirme
**Diller:** TypeScript / Bun (harness), Python (eval script'leri)
**Ön koşullar:** Faz 11 (LLM engineering), Faz 13 (tools ve protokoller), Faz 14 (agent'lar), Faz 15 (otonom sistemler), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P0 · P5 · P7 · P10 · P11 · P13 · P14 · P15 · P17 · P18
**Süre:** 35 saat

## Sorun

Coding agent'lar 2026'da baskın yapay zeka uygulama kategorisi haline geldi. Claude Code (Anthropic), Composer 2 ve Agent Tabs ile Cursor 3 (Cursor), Amp (Sourcegraph), OpenCode (112k yıldız), Factory Droids ve Google Jules — hepsi aynı mimarinin varyasyonlarını yayınlıyor: bir terminal harness, izinlendirilmiş bir tool yüzeyi, bir sandbox ve bir frontier model etrafında kurulmuş bir plan-aksiyon-gözlem loop'u. Sınır dar — Live-SWE-agent, Opus 4.5 ile SWE-bench Verified'da %79.2'ye ulaştı — ama mühendislik zanaatı geniş. Başarısızlık modlarının çoğu model hatası değil. Tool-loop instabilitesi, context zehirlenmesi, kontrolsüz token maliyeti ve yıkıcı filesystem operasyonları.

Bu agent'lar hakkında dışarıdan akıl yürütemezsin. Bir tane inşa etmek, ripgrep 8MB eşleşme döndürünce loop'un 47. turda çökmesini izlemek ve truncation katmanını yeniden inşa etmek zorundasın. Bu capstone'un amacı bu.

## Kavram

Harness'ın dört yüzeyi var. **Plan**, modelin her tur yeniden yazdığı bir TodoWrite-tarzı durum nesnesi tutar. **Act**, tool çağrılarını yönlendirir (read, edit, run, search, git). **Observe**, stdout / stderr / exit kodlarını yakalar, truncate eder ve özeti geri besler. **Recover**, context window'u patlatmadan veya sonsuz döngüye girmeden tool hatalarını yönetir. 2026 şekli bir şey daha ekler: **hook'lar**. `PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Notification`, `Stop` ve `PreCompact` — operatörün policy, telemetri ve guardrails enjekte ettiği yapılandırılabilir extension noktaları.

Sandbox E2B veya Daytona. Her task, read-write mount'lanmış git worktree'si olan taze bir devcontainer'da çalışır. Harness host filesystem'a asla dokunmaz. Worktree başarı veya başarısızlık sonrası yıkılır. Maliyet kontrolü üç katmanda zorunlu kılınır: tur başına token tavanı, oturum başına dolar bütçesi ve sert tur limiti (tipik olarak 50). Observability katmanı, self-hosted Langfuse'a gönderilen GenAI semantic conventions'lı OpenTelemetry span'ları.

## Mimari

```
  kullanıcı CLI  ->  harness (Bun + Ink TUI)
                  |
                  v
           plan / act / observe loop  <--->  Claude Sonnet 4.7 / GPT-5.4-Codex / Gemini 3 Pro
                  |                          (OpenRouter üzerinden, model-agnostik)
                  v
           tool dispatcher (MCP StreamableHTTP client)
                  |
     +------------+------------+----------+
     v            v            v          v
  read/edit    ripgrep     tree-sitter   git/run
     |            |            |          |
     +------------+------------+----------+
                  |
                  v
           E2B / Daytona sandbox  (worktree izole)
                  |
                  v
           hooks: Pre/Post, Session, Prompt, Compact
                  |
                  v
           OpenTelemetry -> Langfuse (span'lar, token'lar, $)
                  |
                  v
           GitHub app üzerinden PR
```

## Stack

- Harness runtime: Bun 1.2 + Ink 5 (terminal-içi React)
- Model erişimi: Claude Sonnet 4.7, GPT-5.4-Codex, Gemini 3 Pro, Opus 4.5 (en zor task'lar için) ile OpenRouter birleşik API'si
- Tool transport: Model Context Protocol StreamableHTTP (MCP 2026 revizyonu)
- Sandbox: E2B sandbox'ları (JS SDK) veya Daytona devcontainer'ları
- Kod arama: ripgrep subprocess, 17 dil için tree-sitter parser'lar (pre-compiled)
- İzolasyon: task başına `git worktree add`, başarı / başarısızlıkta temizlik
- Eval harness: SWE-bench Pro (verified alt küme) + Terminal-Bench 2.0 + kendi 30-task holdout'un
- Observability: `gen_ai.*` semconv'lı OpenTelemetry SDK → self-hosted Langfuse
- PR gönderimi: fine-grained token'lı GitHub App, scope hedef repo ile sınırlı

## İnşa Et

1. **TUI ve komut loop'u.** Ink ile bir Bun projesi iskeleyle. `agent run <repo> "<task>"` kabul et. Bölünmüş bir görünüm bas: plan paneli (üst), tool-call stream'i (orta), token bütçesi (alt). Ctrl-C'de çıkıştan önce `SessionEnd` hook'unu tetikleyen iptal ekle.

2. **Plan state.** Tipli bir TodoWrite şeması tanımla (notlarla pending / in_progress / done item'lar). Model her tur full state'i bir tool çağrısı olarak yeniden yazsın — incremental mutate ettirme. Çökmelerin devam edebilmesi için plan'ı `.agent/state.json`'a persist et.

3. **Tool yüzeyi.** Altı tool tanımla: `read_file`, `edit_file` (diff preview ile), `ripgrep`, `tree_sitter_symbols`, `run_shell` (timeout'lu), `git` (status / diff / commit / push). Harness'ın transport-agnostik olması için MCP StreamableHTTP üzerinden expose et. Her tool truncated çıktı döndürsün (çağrı başına 4k token cap).

4. **Sandbox wrap'leme.** Her task bir E2B sandbox'ı spawn eder. `git worktree add -b agent/$TASK_ID` taze bir branch ekler. Tüm tool çağrıları sandbox içinde yürütülür. Host filesystem'a erişilemez.

5. **Hooks.** Sekiz 2026 hook tipinin hepsini implement et. En az dört kullanıcı-yazılı hook'u bağla: (a) `PreToolUse` worktree dışındaki `rm -rf`'i bloklayan yıkıcı-komut guard'ı, (b) `PostToolUse` token muhasebesi, (c) `SessionStart` bütçe initialization'ı, (d) `Stop` bir final trace bundle yazar.

6. **Eval loop'u.** SWE-bench Pro Python'un 30-issue'lık bir alt kümesini klonla. Harness'ını her birine karşı çalıştır. mini-swe-agent (minimal baseline) ile pass@1, task başına tur ve task başına $ üzerinde karşılaştır. Sonuçları `eval/results.jsonl`'e yaz.

7. **Maliyet kontrolü.** Sert kesintiler: 50 tur, 200k context, task başına $5. `PreCompact` hook'u 150k işaretinde eski turları bir prior-state bloğuna özetler, plan'ı kaybetmeden yeni gözlemlere yer açar.

8. **PR gönderimi.** Başarıda son adım `git push` + plan ve diff özetini gövdede içeren bir PR açan bir GitHub API çağrısıdır.

## Kullan

```
$ agent run ./my-repo "worker.rs'deki race condition'ı düzelt"
[plan]  1 worker.rs'i bul ve mutex kullanımlarını sırala
        2 contention altındaki shared state'i tanımla
        3 fix öner, testleri doğrula
[tool]  ripgrep mutex.*lock -t rust           (44 eşleşme, truncated)
[tool]  read_file src/worker.rs 120..180
[tool]  edit_file src/worker.rs (+8 -3)
[tool]  run_shell cargo test worker::          (geçti)
[plan]  1 done · 2 done · 3 done
[done]  PR açıldı: #482   tur=9   token=38k   maliyet=$0.41
```

## Yayınla

Teslim skill'i `outputs/skill-terminal-coding-agent.md`'de yaşıyor. Bir repo path'i ve bir task açıklaması verildiğinde, sandbox'ta tam plan-aksiyon-gözlem loop'unu çalıştırır ve bir PR URL'i artı bir trace bundle döndürür. Bu capstone için rubrik:

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Baseline'a karşı SWE-bench Pro pass@1 | Senin harness vs mini-swe-agent, 30 eşleştirilmiş Python task'ında |
| 20 | Mimari netliği | Plan/act/observe ayrımı, hook yüzeyi, tool şeması — Live-SWE-agent layout'una karşı incelenir |
| 20 | Safety | Sandbox-kaçış testleri, izin promptları, yıkıcı-komut guard'ı red-team'i geçer |
| 20 | Observability | Trace bütünlüğü (tool çağrılarının %100'ü span'lanmış), tur başına token muhasebesi |
| 15 | Geliştirici UX'i | Cold-start < 2s, crash recovery plan'ı resume eder, Ctrl-C tool ortasında temiz iptal eder |
| **100** | | |

## Alıştırmalar

1. Backing model'i Claude Sonnet 4.7'den vLLM üzerinde sunulan Qwen3-Coder-30B'ye değiştir. pass@1 ve task başına $'ı karşılaştır. Açık modelin nerede yetersiz kaldığını raporla.

2. PR gönderiminden önce diff'i okuyan ve bir revizyon loop'u talep edebilen bir `reviewer` alt-agent ekle. False-positive review'ların SWE-bench pass oranını tek-agent baseline'ının altına düşürüp düşürmediğini ölç (ipucu: genelde evet).

3. Sandbox'ı stress-test et: harici bir URL'yi `curl`'lemeye çalışan bir task ve worktree dışına yazan bir task yaz. Her ikisinin de PreToolUse hook'u tarafından bloklandığını doğrula. Denemeleri logla.

4. Daha küçük bir modelle (Haiku 4.5) `PreCompact` özetlemesi implement et. 3x compaction'da ne kadar plan fidelity'sinin kaybolduğunu ölç.

5. MCP StreamableHTTP transport'unu stdio ile değiştir. Cold-start ve çağrı başına gecikmeyi benchmark et. Local-only kullanım için bir kazanan seç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Harness | "Agent loop'u" | Tool'ları yönlendiren, plan state'ini tutan ve bütçeleri zorlayan, modeli çevreleyen kod |
| Hook | "Agent event listener" | Harness tarafından sekiz lifecycle event'inden birinde çalıştırılan, kullanıcı-yazılı bir script |
| Worktree | "Git sandbox'ı" | Ayrı bir path'te linked bir git checkout; ana klona dokunmadan atılabilir |
| TodoWrite | "Plan state" | Modelin her tur yeniden yazdığı, tipli pending/in-progress/done item listesi |
| StreamableHTTP | "MCP transport" | 2026 MCP revizyonu: çift-yönlü streaming'li uzun-ömürlü HTTP bağlantısı; SSE'yi değiştirir |
| Token ceiling | "Context bütçesi" | Tur başına veya oturum başına input+output token cap'i; compaction veya sonlandırma tetikler |
| pass@1 | "Tek-deneme geçme oranı" | İlk koşuda retry veya test-set'e bakmadan çözülen SWE-bench task'larının oranı |

## İleri Okuma

- [Claude Code dokümantasyonu](https://docs.anthropic.com/en/docs/claude-code) — Anthropic'in referans harness'ı
- [Cursor 3 changelog](https://cursor.com/changelog) — Agent Tabs ve Composer 2 ürün notları
- [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) — SWE-bench harness karşılaştırması için minimal baseline
- [Live-SWE-agent](https://github.com/OpenAutoCoder/live-swe-agent) — Opus 4.5 ile SWE-bench Verified'da %79.2
- [OpenCode](https://opencode.ai) — açık harness, 112k yıldız
- [SWE-bench Pro leaderboard](https://www.swebench.com) — bu capstone'un hedeflediği değerlendirme
- [Model Context Protocol 2026 roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/) — StreamableHTTP, capability metadata
- [OpenTelemetry GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — tool çağrıları ve token kullanımı için span şeması
