---
name: multi-agent-team
description: Architect, paralel coder'lar, reviewer ve tester'dan oluşan multi-agent yazılım ekibi kur; SWE-bench Pro'ya karşı ölç ve handoff post-mortem'i üret.
version: 1.0.0
phase: 19
lesson: 10
tags: [capstone, multi-agent, swe-bench, langgraph, a2a, worktree, roles]
---

Bir GitHub issue URL'si ve bir paralellik seviyesi verildiğinde, merge-ready bir PR üreten multi-agent yazılım ekibi deploy et. 50 SWE-bench Pro issue üzerinde değerlendir ve handoff-failure histogramı yayınla.

Build planı:

1. Task board: file-backed (veya Redis) JSONL store olarak tipli mesajlar. Mesaj türleri: plan_request, subtask, diff_ready, review_needed, review_feedback, approved, test_needed, test_passed, test_failed, replan_needed.
2. Architect (Opus 4.7): issue'yu okur, plan yazar, açık interface'lerle (dokunulan dosyalar, public function'lar, test etkisi) subtask DAG'ı yayar.
3. N coder (Sonnet 4.7): her biri bir subtask alır, taze `git worktree add` + Daytona sandbox spawn'lar, bağımsız implemente eder.
4. Merge coordinator: three-way merge; LLM aracılı çakışma çözümü yalnızca dosya düzeyinde örtüşmede.
5. Reviewer (GPT-5.4): merge edilmiş diff'i okur; yazdığı diff'leri onaylayamaz; ilgili coder'a yönlendirilen approved veya review_feedback yayar.
6. Tester (Gemini 2.5 Pro): test suite'i temiz sandbox'ta çalıştırır; artifact'lerle test_passed veya test_failed yayar.
7. Handoff muhasebesi: her cross-role mesaj payload size ve model ile Langfuse span'ı olur. Token amplification = total_tokens / single_agent_baseline_tokens hesapla.
8. Bariz bug probe enjekte et (çalıştırmaların %10'una) reviewer false-approve oranını ölçmek için.
9. 50 SWE-bench Pro issue üzerinde çalıştır; pass@1, single-agent baseline'a karşı wall-clock, rol başına token dağılımı, handoff-failure histogramı yayınla.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | 50 issue'luk alt küme pass@1 |
| 20 | Paralel speedup | Single-agent baseline'a karşı wall-clock |
| 20 | Review kalitesi | Enjekte edilmiş bug probe'unda false-approval oranı |
| 20 | Token verimliliği | Çözülen issue başına single-agent'a karşı toplam token |
| 15 | Koordinasyon mühendisliği | Merge-conflict çözümü, handoff-failure histogramı |

Sert ret durumları:

- Yazdığı veya önerdiği diff'leri onaylayabilen reviewer. Sert kısıt.
- Eşleştirilmiş single-agent baseline çalıştırması olmayan raporlar. Multi-agent yalnızca pass@1'de değil, *dolar başına* kazanmak zorunda.
- Tipli A2A mesajları yerine free-form string mesajlar içeren task board'lar.
- Çakışan diff'leri replan'a yönlendirmek yerine sessizce düşüren merge coordinator'lar.

Reddetme kuralları:

- Rol başına bütçe tavanı (token + dolar) olmadan çalıştırmayı reddet.
- Tester'ı temiz sandbox'ta doğrulamamış bir PR açmayı reddet.
- Coder'ları tek çalıştırmada 8'in üzerine ölçeklendirmeyi reddet. Üstünde koordinasyon overhead'i baskın gelir.

Çıktı: task board + rol worker'ları, 50 issue SWE-bench Pro çalıştırma log'u, eşleştirilmiş single-agent baseline çalıştırması, rol etiketli span'ler ve rol başına token dağılımları olan bir Langfuse dashboard'u, enjekte edilmiş bug probe raporu ve en sık kırılan üç handoff ile her birini azaltan mesaj şeması veya prompt değişikliğini adlandıran bir post-mortem içeren bir repo.
