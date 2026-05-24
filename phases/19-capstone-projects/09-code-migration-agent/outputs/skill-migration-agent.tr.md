---
name: migration-agent
description: Deterministic recipe'leri agent fallback döngüsüyle birleştiren, MigrationBench'i geçen ve failure taxonomy'si yayınlayan repo düzeyinde bir code migration agent kur.
version: 1.0.0
phase: 19
lesson: 09
tags: [capstone, code-migration, openrewrite, libcst, migrationbench, agent, sandbox]
---

Bir Java 8 veya Python 2 repo verildiğinde, yeşil test suite'i ve minimum coverage regression'ı olan migrate edilmiş bir branch üret (Java 17 veya Python 3.12'ye). 50-repo MigrationBench alt kümesi üzerinde değerlendir.

Build planı:

1. Deterministic geçiş: mekanik yeniden yazımları önce OpenRewrite (Java) veya libcst (Python) çalıştırır. Temiz diff ile "recipe" commit'i olarak commit et.
2. Daytona sandbox: hedef runtime önceden yüklü; per-branch build; read-only source mount.
3. Agent döngüsü: Claude Opus 4.7 + GPT-5.4-Codex üzerinde LangGraph veya OpenAI Agents SDK. Tool'lar: `run_build`, `read_file`, `edit_file`, `run_test`, `git_diff`. Failure sınıflandır (dep, syntax, test, build-tool), hedefli düzeltme uygula, yeniden çalıştır.
4. Bütçe tavanları: 30 dk, 8 dolar, 20 tur. Herhangi birinin aşılması durur ve mevcut diff ile `budget_exhausted` altında dosyalanır.
5. Test + coverage gate: build yeşil sonra testler yeşil; coverage %2'den fazla düşemez.
6. PR açılır: recipe-commit + agent commit'leri + özet yorum.
7. Failure taxonomy: repo başına `{dep_upgrade_required, build_tool_drift, custom_annotation, test_flake, syntax_edge_case, budget_exhausted, coverage_regression}` üzerinden etiket.
8. MigrationBench üzerinde 50-repo çalıştırma; sınıf başına pass oranı, repo başına maliyet ve coverage korumasını yayınla; deterministic-only baseline'a karşı karşılaştır.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | MigrationBench pass oranı | 50-repo alt kümesi pass@1 |
| 20 | Test-coverage koruma | Base branch'e karşı ortalama coverage delta'sı |
| 20 | Migrate edilen repo başına maliyet | Geçen çalıştırmalarda ortalama $/repo |
| 20 | Agent / deterministic-tool entegrasyonu | OpenRewrite vs agent tarafından işlenen düzeltmelerin oranı |
| 15 | Failure analizi yazımı | Örneklerle taxonomy tamlığı |

Sert ret durumları:

- Deterministic geçişi atlayan pipeline'lar. OpenRewrite mekanik %70-80'i herhangi bir agent'tan daha ucuz ve güvenilir biçimde işler.
- %2 üstü coverage regression'ları geçen olarak işaretlemek.
- Mekanik ve agent tarafından yazılan değişiklikleri tek bir commit'te birleştiren PR'lar. Ayrılmak zorunda.
- Aynı 50 repo üzerinde eşleştirilmiş deterministic-only baseline olmadan pass oranı raporlamak.

Reddetme kuralları:

- Migrate edilmiş branch'i base üzerine force-push'lamayı reddet. Her zaman yeni branch + PR.
- CI'si sandbox'ta yeşile dönmemiş bir PR açmayı reddet.
- Modifiye etme lisansı olmayan kurumsal repo'lar üzerinde çalışmayı reddet.

Çıktı: iki katmanlı migration pipeline'ı, 50-repo MigrationBench çalıştırma log'ları, failure taxonomy dashboard'u, eşleştirilmiş deterministic-only baseline çalıştırması ve en yaygın üç failure sınıfı ile her birini elimine edecek recipe değişikliği üzerine bir yazımı içeren bir repo.
