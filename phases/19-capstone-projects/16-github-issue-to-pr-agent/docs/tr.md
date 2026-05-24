# Capstone 16 — GitHub Issue-to-PR Otonom Agent'ı

> AWS Remote SWE Agents, Cursor Background Agent'lar, OpenAI Codex cloud ve Google Jules — hepsi aynı 2026 ürün şeklini yayınlıyor: bir issue'ya label ver, bir PR al. Bir agent'ı bir cloud sandbox'ta çalıştır, testlerin geçtiğini doğrula ve gerekçeyle review-ready bir PR post et. Zor kısımlar repo'nun build environment'ını otomatik olarak yeniden üretmek, credential leakage'i önlemek, per-repo bütçeleri uygulamak ve agent'ın force-push yapamamasını sağlamak. Bu capstone self-hosted versiyonu inşa eder ve hosted alternatiflere karşı maliyet ve pass oranı üzerinde karşılaştırır.

**Tür:** Bitirme
**Diller:** Python (agent), TypeScript (GitHub App), YAML (Actions)
**Ön koşullar:** Faz 11 (LLM engineering), Faz 13 (tools), Faz 14 (agent'lar), Faz 15 (otonom), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P11 · P13 · P14 · P15 · P17
**Süre:** 30 saat

## Sorun

Async cloud coding agent'ı interactive coding agent'larından (capstone 01) ayrı bir ürün kategorisi. UX bir GitHub label. Bir issue'ya `@agent fix this` label'ı verirsin, bir worker bir cloud sandbox'ta spin up eder, repo'yu klonlar, testleri çalıştırır, dosyaları edit'ler, doğrular ve agent'ın gerekçesi gövdede olan bir PR açar. Interactive loop yok, terminal yok. AWS Remote SWE Agents, Cursor Background Agents, OpenAI Codex cloud, Google Jules ve Factory Droids — hepsi bunda yakınsıyor.

Mühendislik zorlukları somut: environment yeniden üretimi (agent repo'yu cache'lenmiş bir dev image olmadan sıfırdan build etmek zorunda), flaky test'ler (yeniden çalıştırılmalı veya izole edilmeli), credential scoping (minimal fine-grained permission'lı bir GitHub App), repo başına gün başına bütçe uygulaması ve no-force-push policy. Capstone hosted alternatiflere karşı pass oranını, maliyeti ve safety'yi ölçer.

## Kavram

Trigger bir GitHub webhook (issue label veya PR yorumu). Bir dispatcher work'ü ECS Fargate veya Lambda'ya enqueue eder. Worker repo'yu repo'dan inferred generic bir Dockerfile (dil, framework) ile bir Daytona veya E2B sandbox'a çeker. Agent Claude Opus 4.7 veya GPT-5.4-Codex'e karşı bir mini-swe-agent veya SWE-agent v2 loop'u çalıştırır. Iterate eder: kodu oku, fix öner, patch uygula, testleri çalıştır.

Verification gating adımı. PR açılmadan önce full CI sandbox'ta geçmeli. Coverage delta hesaplanır; eşiği aşacak kadar negatifse, PR açılır ama `needs-review` label'lanır. Agent gerekçeyi PR description'ı olarak post eder artı reviewer'ın takipler için ping atabileceği bir `@agent` thread'i.

Safety iki farklı GitHub yüzeyi üzerinden scoped: App `workflows: read` ve dar repo content/PR scope'larıyla kısa-ömürlü bir installation token sağlar; branch protection (app permission'ları değil) "no direct writes to `main`" ve "no force-push"u zorlar — app asla bypass list'e eklenmez. `.github/workflows`'a path-scoped read-only erişim gerçek bir GitHub App primitive'i değil, bu yüzden agent'ın dosya edit'lerindeki allow-list'i worker'da bunu zorlamak zorunda. Repo başına gün başına bütçe tavanları dispatcher'da uygulanır (örn. repo başına gün başına max 5 PR, PR başına $20).

## Mimari

```
GitHub issue `@agent fix` label'lı veya PR yorumu
            |
            v
    GitHub App webhook -> AWS Lambda dispatcher
            |
            v
    ECS Fargate task (veya GitHub Actions self-hosted runner)
       - repo'yu çek
       - Dockerfile infer et (dil, package manager)
       - target runtime'lı Daytona / E2B sandbox
       - clone -> git worktree -> agent branch
            |
            v
    mini-swe-agent / SWE-agent v2 loop
       Claude Opus 4.7 veya GPT-5.4-Codex
       tool'lar: ripgrep, tree-sitter, read/edit, run_tests, git
            |
            v
    sandbox-içinde CI geçtiğini doğrula + coverage delta check
            |
            v (doğrulandı)
    git push + GitHub App üzerinden PR aç
       PR body = gerekçe + diff özeti + trace URL
       label: needs-review
            |
            v
    operatör inceler; takipler için agent'a @-mention atabilir
```

## Stack

- Trigger: fine-grained token'lı GitHub App; Lambda veya Fly.io üzerinden webhook receiver
- Worker: ECS Fargate task (veya GitHub Actions self-hosted runner)
- Sandbox: task başına Daytona devcontainer'ı veya E2B sandbox'ı
- Agent loop: Claude Opus 4.7 / GPT-5.4-Codex üzerinden mini-swe-agent baseline'ı veya SWE-agent v2
- Retrieval: tree-sitter repo-map + ripgrep
- Doğrulama: sandbox-içinde full CI + coverage delta gate'i
- Observability: PR body'den linklenen per-PR trace arşivli Langfuse
- Bütçe: per-repo günlük dolar tavanı; repo başına gün başına max PR

## İnşa Et

1. **GitHub App.** Fine-grained installation token: issues read+write, pull_requests write, contents read+write, workflows read. Branch protection (bunu yapabilen tek yüzey) "no direct push to `main`" ve "no force-push"u zorlar; app bypass list'te değil. Worker önerilen diff'te bir allow-list check olarak "no writes under `.github/workflows`"u zorlar, çünkü GitHub App permission'ları path-scoped değildir.

2. **Webhook receiver.** Lambda function issue label / PR comment webhook'larını kabul eder. `@agent fix this` label'ı ile filtreler. SQS'e enqueue eder.

3. **Dispatcher.** SQS'ten task'ları pop'lar. Per-repo per-day bütçeyi zorlar. Repo URL, issue body ve taze bir Daytona sandbox'la bir ECS Fargate task'ı spin up eder.

4. **Environment inference.** Dili tespit et (Python, Node, Go, Rust) ve package manager (uv, pnpm, go mod, cargo). Mevcut değilse uçuş sırasında bir Dockerfile üret.

5. **Agent loop.** Claude Opus 4.7 ile mini-swe-agent veya SWE-agent v2. Tool'lar: ripgrep, tree-sitter repo-map, read_file, edit_file, run_tests, git. Sert limit'ler: $20 maliyet, 30 dk wall-clock, 30 agent turu.

6. **Verification.** Loop sonlandıktan sonra full test suite'i sandbox-içinde çalıştır. jacoco / coverage.py üzerinden coverage delta hesapla. CI red ise: dur, PR açma. Coverage %2'den fazla düştüyse: `needs-review` label'ıyla PR aç.

7. **PR gönderimi.** Agent branch'ini push et. GitHub API üzerinden şunlarla PR aç: title, gerekçe, diff özeti, trace URL, maliyet, tur.

8. **Credential hijyeni.** Worker kısa-ömürlü bir GitHub App installation token ile çalışır. Log'lar arşivlemeden önce secret'lar için scrub'lanır.

9. **Eval.** Çeşitli zorlukta 30 seed edilmiş dahili issue. Pass oranı, PR kalitesi (diff size, style, coverage), maliyet, latency ölç. Aynı issue'larda Cursor Background Agents ve AWS Remote SWE Agents ile karşılaştır.

## Kullan

```
# github.com'da
  - kullanıcı issue #842'ye `@agent fix this` label'ı verir
  - PR #1903 14 dakika sonra görünür
  - body:
    > widget.dedupe()'da null comparator entry'sinden kaynaklanan NPE düzeltildi.
    > Regresyon testi widget_test.go::TestDedupeNullComparator eklendi.
    > Coverage delta: +%0.12
    > Tur: 7  Maliyet: $1.80  Trace: langfuse:...
    > Label: needs-review
```

## Yayınla

Teslimat `outputs/skill-issue-to-pr.md`. Sınırlı maliyet ve scoped credential'larla label'lı issue'ları review-ready PR'lara çeviren bir GitHub App + async cloud worker.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | 30 issue'da pass oranı | Uçtan uca başarı (CI green + coverage OK) |
| 20 | PR kalitesi | Diff size, coverage delta, style uyumluluğu |
| 20 | Çözülen issue başına maliyet ve latency | PR başına $ ve wall-clock |
| 20 | Safety | Scoped token, per-repo bütçe, no force-push, credential hijyeni |
| 15 | Operatör UX'i | Gerekçe yorumları, retry imkanı, @-mention takipler |
| **100** | | |

## Alıştırmalar

1. "Fix flaky test" modu ekle: `@agent stabilize-flake TestX` label'ı testi sandbox-içinde 50 kez çalıştırır ve onu stabilize eden minimal bir değişiklik önerir.

2. Üç paylaşılan issue'da Cursor Background Agents'a karşı maliyeti karşılaştır. Hangi tool'ların nerede kazandığını raporla.

3. Bir bütçe dashboard'u implement et: per-repo per-day maliyet, per-user maliyet. Anomalide alert.

4. CI çalıştırmadan bir draft PR açan bir "dry-run" modu inşa et, böylece reviewer'lar planı ucuza inceleyebilir.

5. Bir retention policy ekle: 7 günden eski merge edilmemiş PR branch'leri otomatik olarak silinir.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| GitHub App | "Scoped bot identity" | Fine-grained permission'lar + kısa-ömürlü installation token'lı App |
| Async cloud agent | "Background agent" | Terminalde değil, bir cloud sandbox'ta çalışan non-interactive worker |
| Environment inference | "Dockerfile synthesis" | Dil + package manager tespit et, yoksa bir Dockerfile üret |
| Verification | "CI-in-sandbox" | PR açmadan önce worker içinde full test suite çalıştır |
| Coverage delta | "Coverage koruması" | Base'den agent branch'e test coverage %'sindeki değişim |
| Per-repo bütçe | "Günlük tavan" | Dispatcher'da uygulanan dolar ve PR-count cap'i |
| Gerekçe | "PR body açıklaması" | Agent'ın neyin değiştiği ve neden değiştiğinin özeti; PR body'de gerekli |

## İleri Okuma

- [AWS Remote SWE Agents](https://github.com/aws-samples/remote-swe-agents) — kanonik async cloud agent referansı
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) — CLI referansı
- [Cursor Background Agents](https://docs.cursor.com/background-agent) — ticari alternatif
- [OpenAI Codex (cloud)](https://openai.com/codex) — hosted rakip
- [Google Jules](https://jules.google) — Google'ın hosted versiyonu
- [Factory Droids](https://www.factory.ai) — alternatif ticari referans
- [GitHub App dokümantasyonu](https://docs.github.com/en/apps) — scoped bot identity'si
- [Daytona cloud sandbox'ları](https://daytona.io) — referans sandbox
