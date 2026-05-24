---
name: issue-to-pr
description: Cloud sandbox'ta çalışan, build'i yeniden üreten, testleri doğrulayan ve sıkı repo başına bütçeler içinde review-ready PR'lar açan async GitHub issue-to-PR agent'ı kur.
version: 1.0.0
phase: 19
lesson: 16
tags: [capstone, async-agent, github, fargate, daytona, swe-bench, budget, safety]
---

`@agent fix this` etiketli issue'ları olan bir GitHub repo verildiğinde, her etiketli issue'yu scope'lu credential'lar ve bounded maliyet ile review-ready PR'a çeviren self-hosted bir cloud agent gönder.

Build planı:

1. Fine-grained token'lı GitHub App: issues rw, PRs write, contents rw, workflows read. Force-push yok. Main üzerindeki branch protection doğrudan yazımları engeller.
2. Webhook receiver (Lambda veya Fly.io) label / PR-comment event'lerini filtreler ve SQS'e enqueue eder.
3. Dispatcher repo başına günlük $ ve PR-count tavanlarını zorlar; izin verilen job başına ECS Fargate task spawn'lar.
4. Environment inference: repo içeriğinden language + package manager + runtime tespit et. Yoksa Dockerfile'ı uçarken sentezle.
5. Task başına Daytona veya E2B sandbox. Repo'yu taze `git worktree` + agent branch'ine klonla.
6. Agent döngüsü (Claude Opus 4.7 veya GPT-5.4-Codex üzerinde mini-swe-agent veya SWE-agent v2). Tool'lar: ripgrep, tree-sitter repo-map, read_file, edit_file, run_tests, git. Tavanlar: 20 dolar, 30 tur, 30 dk.
7. Doğrula: sandbox-içi full CI; jacoco / coverage.py üzerinden coverage delta; delta < -%2 ise `needs-review` etiketle; CI kırmızıysa dur.
8. GitHub API üzerinden rationale, diff özeti, trace URL, maliyet, tur ile PR aç.
9. Observability: PR başına Langfuse trace; secret'lar için log scrub; repo başına budget dashboard'u.
10. 30 seed'li dahili issue üzerinde eval; üç issue'luk paylaşılan alt kümede Cursor Background Agents ve AWS Remote SWE Agents'a karşı karşılaştır.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | 30 issue üzerinde pass oranı | Uçtan uca başarı (CI yeşil + coverage OK) |
| 20 | PR kalitesi | Diff boyutu, coverage delta, style uyumluluğu |
| 20 | Çözülen issue başına maliyet ve latency | $/PR ve wall-clock/PR |
| 20 | Safety | Scope'lu token, repo başına bütçe, force-push yok, credential hijyeni |
| 15 | Operator UX | Rationale yorumları, retry imkanı, @-mention takip |

Sert ret durumları:

- Force-push yapabilen herhangi bir agent. Sert dışlama.
- Bütçe check'lerini atlayan dispatcher'lar. Runaway döngüler klasik failure'dır.
- Full CI sandbox-içi geçmeden açılan PR'lar.
- Redact edilmemiş token veya PII içeren trace arşivleri.

Reddetme kuralları:

- Main üzerinde branch protection olmadan kurulmayı reddet.
- Repo başına günlük bütçe (dolar ve PR count) olmadan çalıştırmayı reddet.
- Başarısız çalıştırmaları otomatik yeniden denemeyi reddet; tüm retry'lar insan label'ın yeniden uygulanmasını gerektirir.

Çıktı: GitHub App, webhook receiver, dispatcher + budget ledger, Fargate task definition, sandbox lifecycle manager, mini-swe-agent döngüsü, 30 issue'luk eval çalıştırması, Cursor Background Agents ve AWS Remote SWE Agents'a karşı yan yana karşılaştırma ve en kritik üç build-inference failure ile her birini azaltan Dockerfile-synthesis değişikliğini adlandıran bir yazımı içeren bir repo.
