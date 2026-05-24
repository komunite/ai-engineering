# Capstone 09 — Kod Migration Agent'ı (Repo-Seviyesinde Dil / Runtime Yükseltmesi)

> Amazon'un MigrationBench (Java 8'den 17'ye) ve Google'ın App Engine Py2-to-Py3 migrator'ı 2026 çıtasını koydu. Moderne'nin OpenRewrite'ı ölçekte deterministik AST rewrite'ları yapar. Grit aynı sorunu codemod-tarzı DSL ile hedefler. Üretim pattern'i ikisini birleştirir: güvenli rewrite'lar için deterministik bir substrate artı belirsiz case'ler için bir agent katmanı, per-branch build'ler için bir sandbox ve PR açılmadan önce green'e dönen bir test harness. Capstone 50 gerçek repo migrate etmek ve bir failure taxonomy ile bir pass oranı yayınlamak.

**Tür:** Bitirme
**Diller:** Python (agent), Java / Python (hedefler), TypeScript (dashboard)
**Ön koşullar:** Faz 5 (NLP), Faz 7 (transformer'lar), Faz 11 (LLM engineering), Faz 13 (tools), Faz 14 (agent'lar), Faz 15 (otonom), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P5 · P7 · P11 · P13 · P14 · P15 · P17
**Süre:** 30 saat

## Sorun

Büyük-ölçekli kod migration 2026 coding agent'larının en temiz üretim uygulamalarından biri. Ground truth bariz (migration sonrası test suite geçiyor mu?), reward'lar gerçek (Java-8 fleet migration'ı headcount-ölçeğinde bir proje) ve benchmark'lar public (MigrationBench 50-repo alt kümesi). Moderne'nin OpenRewrite'ı deterministik tarafı yönetir. Agent katmanı OpenRewrite tariflerinin yapamadığı her şeyi yönetir: belirsiz rewrite'lar, build-system drift'i, long-tail syntax, transitive dependency breakage.

Bir Java 8 repo'su (veya Python 2 repo'su) alıp green-CI migrate edilmiş bir branch üreten bir agent inşa edeceksin. Pass oranı, test-coverage koruması, repo başına maliyet ölçeceksin ve bir failure taxonomy inşa edeceksin. Deterministik-only baseline'ına karşı yan yana, agent'ın değerinin gerçekte nerede yaşadığını sana söyler.

## Kavram

Pipeline'ın iki katmanı var. **Deterministik substrate** (Java için OpenRewrite, Python için libcst) mekanik rewrite'ların büyük kısmını güvenli şekilde çalıştırır: import'lar, method signature'ları, null-safety düzenlemeleri, try-with-resources, deprecated API yer değiştirmeleri. Hızlı ve auditable diff'ler üretir. **Agent katmanı** (Claude Opus 4.7 ve GPT-5.4-Codex üzerinden OpenAI Agents SDK veya LangGraph) tariflerin yapamadığı case'leri yönetir: build-file yükseltmeleri (Maven/Gradle/pyproject), transitive dependency çakışmaları, test flake'leri, custom annotation'lar.

Her repo target runtime pre-installed olan bir Daytona sandbox alır. Agent iterate eder: build çalıştır, başarısızlıkları sınıflandır, fix uygula, yeniden çalıştır. Sert limit'ler: repo başına 30 dakika, repo başına $8, 20 agent turu. Tüm testler geçerse ve coverage delta negatif değilse, branch bir PR açar. Değilse, repo evidence ile bir failure class altında dosyalanır.

Failure taxonomy teslimat. 50 repo boyunca, ne bozuldu? Transitive dep'ler? Custom annotation'lar? Build tool sürümü? Migration ile alakasız test flake'leri? Her class bir sayı ve örnek bir diff alır. Gelecek tarif yazarları top üçü hedef alabilir.

## Mimari

```
hedef repo
      |
      v
OpenRewrite / libcst deterministik tarifler
   (güvenli, hızlı, auditable, fix'lerin ~%70-80'i)
      |
      v
branch başına Daytona sandbox'ı
      |
      v
agent loop (Claude Opus 4.7 / GPT-5.4-Codex):
   - build çalıştır -> başarısızlıkları yakala
   - başarısızlıkları sınıflandır (build, test, lint)
   - fix uygula (patch veya tarif retry)
   - yeniden çalıştır
   - bütçe: 30 dk, $8, 20 tur
      |
      v
test + coverage delta gate
      |
      v (geçti)
PR aç
      |
      v (başarısız)
failure class altında dosyala + repro ekle
```

## Stack

- Deterministik substrate: OpenRewrite (Java) veya libcst (Python)
- Agent: Claude Opus 4.7 + GPT-5.4-Codex üzerinden OpenAI Agents SDK veya LangGraph
- Sandbox: branch başına Daytona devcontainer'ları, pre-installed target runtime (Java 17 / Python 3.12)
- Build sistemleri: Maven, Gradle, uv (Python)
- Benchmark'lar: Amazon MigrationBench 50-repo alt kümesi (Java 8'den 17'ye), Google App Engine Py2-to-Py3 repo'ları
- Test harness: paralel runner, Jacoco (Java) veya coverage.py (Python) üzerinden coverage
- Observability: her diff chunk'ı ile repo başına Langfuse + trace bundle
- Dashboard: per-class sayılarla ve örnek diff'lerle failure-taxonomy dashboard'u

## İnşa Et

1. **Tarif geçişi.** Önce OpenRewrite (Java) veya libcst (Python) tariflerini çalıştır. Mekanik olan migration'ların %70-80'ini yakala. "recipe" commit olarak commit et.

2. **Build trial.** Daytona sandbox: target runtime kur, build çalıştır. Green ise, testlere atla. Red ise, agent'a handoff yap.

3. **Agent loop.** Tool'larla LangGraph: `run_build`, `read_file`, `edit_file`, `run_test`, `git_diff`. Agent başarısızlığı sınıflandırır (dep, syntax, test, build-tool) ve hedefli bir fix uygular. Yeniden çalıştır.

4. **Bütçe cap'leri.** Repo başına 30 dakika wall-clock, $8 maliyet, 20 agent turu. Herhangi bir ihlal durdurur ve mevcut diff ile "budget_exhausted" altında dosyalar.

5. **Test + coverage gate.** Build green'e döndükten sonra test suite'i çalıştır. Coverage'ı base repo ile karşılaştır. Coverage %2'den fazla düştüyse, "coverage_regression" altında dosyala.

6. **PR aç.** Başarıda branch'i push et, diff ve hangi tariflerin uygulandığını ve hangi commit'leri agent'ın yazdığını özetleyen bir summary ile PR aç.

7. **Failure taxonomy.** Her başarısız repo için bir class ile tag'le: `dep_upgrade_required`, `build_tool_drift`, `custom_annotation`, `test_flake`, `syntax_edge_case`, `budget_exhausted`. Bir dashboard inşa et.

8. **50-repo run.** MigrationBench alt kümesinde execute et. Per-class pass oranı, repo başına maliyet, coverage koruma ve deterministik-only baseline'ına karşı karşılaştırma raporla.

## Kullan

```
$ migrate legacy-java-service --target java17
[recipe]   27 rewrite uygulandı (JUnit 4->5, HashMap initializer, try-with-resources)
[build]    BAŞARISIZ: sun.misc.BASE64Encoder sembolü bulunamadı
[agent]    tur 1 sınıflandırma: removed_jdk_api
[agent]    tur 2 uygula: sun.misc.BASE64Encoder -> java.util.Base64
[build]    OK
[tests]    412/412 geçiyor; coverage %84.1 -> %84.3
[pr]       açıldı #1841  maliyet=$3.20  tur=4
```

## Yayınla

Teslimat `outputs/skill-migration-agent.md`. Bir repo verildiğinde, deterministik tarifleri sonra bir agent loop'unu yürütür ve green migrate edilmiş bir branch üretir veya repo'yu bir taxonomy class altında dosyalar.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | MigrationBench pass oranı | 50-repo alt kümesi pass@1 |
| 20 | Test-coverage koruması | Base'e karşı ortalama coverage delta |
| 20 | Migrate edilen repo başına maliyet | Geçen koşularda $/repo |
| 20 | Agent / deterministik-tool entegrasyonu | OpenRewrite'ın yönettiği vs agent'ın yazdığı fix'lerin oranı |
| 15 | Failure analizi yazımı | Örneklerle taxonomy eksiksizliği |
| **100** | | |

## Alıştırmalar

1. Migrate pipeline'ını sadece OpenRewrite ile (agent yok) çalıştır. Pass oranını full pipeline ile karşılaştır. Agent'ın tek başına farkı yarattığı case'leri belirle.

2. Bir "lint-clean" check implement et: migration'dan sonra bir style linter çalıştır (Java için spotless, Python için ruff). Yeni lint hataları görünürse PR'ı başarısız kıl. Coverage-korundu-ama-style-regresyon oranını ölç.

3. Bir "minimal-diff" optimizer ekle: agent'ın branch'i testleri geçtikten sonra, ikinci bir geçişle gereksiz değişiklikleri trim et. Diff-boyut azalmasını raporla.

4. Üçüncü bir migration'a extend et: Node 18'den Node 22'ye. Sandbox wrap'lemeyi yeniden kullan; tarif katmanını custom bir codemod ile değiştir.

5. UX metriği olarak first-green-build'e kadar süreyi (TTFGB) ölç. Hedef: p50 10 dakika altı.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Deterministik substrate | "Tarif motoru" | OpenRewrite / libcst: safety garantili declarative AST rewrite'lar |
| Codemod | "Kod-değiştiren program" | Kaynak kodu mekanik olarak değiştiren bir rewrite kuralı |
| Build drift | "Tool sürüm skew'i" | Major sürümler arası ince Maven / Gradle / uv davranış değişiklikleri |
| Failure class | "Taxonomy bucket'ı" | Bir repo'nun neden migrate olmadığının etiketli sebebi: dep, syntax, test, build-tool, bütçe |
| Coverage delta | "Coverage koruması" | Base'den migrate edilmiş branch'e test coverage %'sindeki değişim |
| Agent turu | "Tool-call round'u" | Agent loop'unda bir plan -> act -> observe döngüsü |
| Bütçe tükenmesi | "Tavanı vurma" | Repo 30-dk / $8 / 20-tur limitini geçmeden tüketti |

## İleri Okuma

- [Amazon MigrationBench](https://aws.amazon.com/blogs/devops/amazon-introduces-two-benchmark-datasets-for-evaluating-ai-agents-ability-on-code-migration/) — kanonik 2026 benchmark'ı
- [Moderne.io OpenRewrite platformu](https://www.moderne.io) — deterministik substrate referansı
- [OpenRewrite dokümantasyonu](https://docs.openrewrite.org) — tarif yazımı
- [Grit.io](https://www.grit.io) — alternatif codemod DSL
- [OpenAI sandbox'lı migration cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/sandboxed-code-migration/sandboxed_code_migration_agent) — Agents SDK referansı
- [Google App Engine Py2'den Py3'e migrator'ı](https://cloud.google.com/appengine) — alternatif migration benchmark'ı
- [libcst](https://github.com/Instagram/LibCST) — Python deterministik substrate'i
- [Daytona sandbox'ları](https://daytona.io) — referans per-branch sandbox'ı
