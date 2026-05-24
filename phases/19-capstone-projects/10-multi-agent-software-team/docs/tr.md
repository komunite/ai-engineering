# Capstone 10 — Multi-Agent Yazılım Mühendisliği Ekibi

> SWE-AF'nin factory mimarisi, MetaGPT'nin rol-tabanlı prompt'laması, AutoGen 0.4'ün tipli actor graph'ı, Cognition'ın Devin'i ve Factory'nin Droid'leri — hepsi aynı 2026 şekline yakınsadı: bir architect planlar, N coder paralel worktree'lerde çalışır, bir reviewer kapılar, bir tester doğrular. Paralel worktree'ler wall-clock'u throughput'a çevirir. Shared state ve handoff protokolleri başarısızlık yüzeyi olur. Capstone ekibi inşa etmek, SWE-bench Pro üzerinde değerlendirmek ve hangi handoff'ların kırıldığını ve ne kadar sık olduğunu raporlamak.

**Tür:** Bitirme
**Diller:** Python / TypeScript (agent'lar), Shell (worktree script'leri)
**Ön koşullar:** Faz 11 (LLM engineering), Faz 13 (tools), Faz 14 (agent'lar), Faz 15 (otonom), Faz 16 (multi-agent), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P11 · P13 · P14 · P15 · P16 · P17
**Süre:** 40 saat

## Sorun

Tek-agent coding harness'ları büyük task'larda bir tavana vuruyor. Herhangi bir bireysel agent zayıf olduğu için değil, 200k-token context'in mimari planı artı dört paralel codebase dilimini artı reviewer yorumunu artı test çıktısını tutamamasından. Multi-agent factory'ler sorunu böler: architect plana sahip, coder'lar paralel worktree'lerde implementasyona sahip, reviewer kapılar, tester doğrular. SWE-AF'nin "factory" mimarisi, MetaGPT'nin rolleri, AutoGen'in tipli actor graph'ı — üçü de aynı şekli tarif ediyor.

Başarısızlık yüzeyi handoff. Architect coder'ların implement edemeyeceği bir şey planlar. Coder'lar çelişen diff'ler üretir. Reviewer hallucinated bir fix'i onaylar. Tester hâlâ yazan bir coder ile yarışır. Bu ekiplerden birini inşa edeceksin, 50 SWE-bench Pro issue'sunda çalıştıracaksın, her handoff'u izleyeceksin ve post-mortem'i yayınlayacaksın.

## Kavram

Rol'ler tipli agent'lar. **Architect** (Claude Opus 4.7) issue'yu okur, bir plan yazar ve onu açık arayüzlerle alt-task'lara böler. **Coder'lar** (Claude Sonnet 4.7, N paralel instance, her biri `git worktree` + Daytona sandbox'ta) alt-task'ları bağımsız implement eder. **Reviewer** (GPT-5.4) merge edilmiş diff'i okur ve onaylar veya belirli değişiklikler talep eder. **Tester** (Gemini 2.5 Pro) test suite'i izolasyonda çalıştırır ve artifact'lerle pass/fail raporlar.

İletişim shared bir task board (dosya-tabanlı veya Redis) üzerinden. Her rol işleyebileceği task'ları consume eder. Handoff'lar A2A-protokol-tipli mesajlar. Koordinasyon konuları: merge-conflict çözümü (coordinator rolü veya otomatik üç-yollu merge), shared-state senkronizasyonu (coder'lar başladığında plan donar; replan'lar ayrı event'ler) ve reviewer gatekeeping (reviewer kendi değişikliklerini veya önerdiği değişiklikleri onaylayamaz).

Token amplification gizli maliyet. Her rol sınırı özet prompt'ları ve handoff context'i ekler. 40-turluk bir tek-agent koşusu dört rol boyunca 160 toplam tur olur. Rubrik özellikle token verimliliğini tek-agent baseline'ına karşı ağırlıklandırır çünkü soru "multi-agent çalışıyor mu" değil, "dolar başına kazanıyor mu" sorusu.

## Mimari

```
GitHub issue URL'i
      |
      v
Architect (Opus 4.7)
   issue'yu okur, alt-task'lar + arayüzlerle plan üretir
      |
      v
Task board (dosya / Redis)
      |
   +-- alt-task 1 ---+-- alt-task 2 ---+-- alt-task 3 ---+-- alt-task 4 ---+
   v                v                v                v                v
Coder A          Coder B          Coder C          Coder D          (4 paralel)
 (Sonnet)         (Sonnet)         (Sonnet)         (Sonnet)
 worktree A       worktree B       worktree C       worktree D
 Daytona          Daytona          Daytona          Daytona
      |                |                |                |
      +--------+-------+-------+--------+
               v
           merge coordinator  (üç-yollu merge + conflict çözümü)
               |
               v
           Reviewer (GPT-5.4)
               |
               v
           Tester  (Gemini 2.5 Pro)  -> geçer? -> PR aç
                                     -> başarısız? -> coder'a geri yönlendir
```

## Stack

- Orkestrasyon: shared state + per-agent sub-graph'larla LangGraph
- Mesajlaşma: tipli inter-agent mesajları için A2A protokol (Google 2025)
- Modeller: Opus 4.7 (architect), Sonnet 4.7 (coder'lar), GPT-5.4 (reviewer), Gemini 2.5 Pro (tester)
- Worktree izolasyonu: coder başına `git worktree add` + Daytona sandbox
- Merge coordinator: custom üç-yollu merge + LLM-aracılı conflict çözümü
- Eval: SWE-bench Pro (50 issue), SWE-AF senaryoları, unit test'ler için HumanEval++
- Observability: rol-etiketli span'larla Langfuse, per-agent token muhasebesi
- Deployment: her rolü ayrı bir Deployment + backlog'da HPA olan K8s

## İnşa Et

1. **Task board.** Tipli mesajlarla dosya-tabanlı JSONL: `plan_request`, `subtask`, `diff_ready`, `review_needed`, `test_needed`, `approved`, `rejected`, `replan_needed`. Agent'lar tag'lere subscribe olur.

2. **Architect.** GitHub issue'yu okur, açık alt-task arayüzleri gerektiren bir plan template'iyle Opus 4.7'yi çalıştırır (dokunulan dosyalar, public fonksiyonlar, test etkisi). Alt-task DAG'i ile bir `plan_request` emit eder.

3. **Coder'lar.** N paralel worker, her biri board'dan bir alt-task claim eder. Her biri taze bir `git worktree add` branch'i artı bir Daytona sandbox spawn eder. Alt-task'ı implement eder. Patch + test delta'ları ile `diff_ready` emit eder.

4. **Merge coordinator.** Tüm-coder'lar-bittiğinde, N branch'i üç-yollu staging branch'ine merge eder. Sadece dosya-seviyesinde overlap olduğunda LLM-aracılı conflict çözümü.

5. **Reviewer.** GPT-5.4 merge edilmiş diff'i okur. Kendi yazdığı diff'leri onaylayamaz. `approved` (no-op) veya ilgili coder'a route edilen spesifik change request'lerle `review_feedback` emit eder.

6. **Tester.** Gemini 2.5 Pro test suite'i temiz bir sandbox'ta çalıştırır. Artifact'leri yakalar. `test_passed` veya stacktrace'lerle `test_failed` emit eder. Başarısız testler başarısız alt-task'a sahip coder'a geri loop'lar.

7. **Handoff muhasebesi.** Bir rol sınırını geçen her mesaj payload size ve kullanılan model ile Langfuse'ta bir span alır. Alt-task başına token amplification hesapla (coder_tokens + reviewer_tokens + tester_tokens + architect_share / coder_tokens).

8. **Eval.** 50 SWE-bench Pro issue üzerinde çalıştır. pass@1 ve çözülen issue başına $'ı tek-agent baseline'ına (tek worktree'de tek Sonnet 4.7) karşı karşılaştır.

9. **Post-mortem.** Her başarısız issue için kırılan handoff'u belirle (plan çok belirsiz, merge conflict, reviewer false-approve, tester flake). Bir handoff-failure histogramı üret.

## Kullan

```
$ team run --issue https://github.com/acme/widget/issues/842
[architect] plan: 4 alt-task (parser, cache, api, migration)
[board]     paralel worktree'lerde 4 coder'a dağıtıldı
[coder-A]   alt-task parser  -> 42 satır, testler lokal geçiyor
[coder-B]   alt-task cache   -> 88 satır, testler lokal geçiyor
[coder-C]   alt-task api     -> 31 satır, testler lokal geçiyor
[coder-D]   alt-task migration -> 19 satır, testler lokal geçiyor
[merge]     üç-yollu merge: 0 conflict
[reviewer]  cache üzerinde yorumlar (thread pool sizing); coder-B'ye yönlendirildi
[coder-B]   revizyon: 92 satır; submit eder
[reviewer]  onaylandı
[tester]    412 testin hepsi geçti
[pr]        açıldı #3382   4 coder, 1 revizyon, $4.90, 18m
```

## Yayınla

Teslimat `outputs/skill-multi-agent-team.md`. Bir issue URL'i ve paralellik seviyesi verildiğinde, ekip per-rol token muhasebesiyle merge-ready bir PR üretir.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | SWE-bench Pro pass@1 | Eşleştirilmiş 50-issue alt kümesi, pass@1 |
| 20 | Paralel hızlanma | Tek-agent baseline'ına karşı wall-clock |
| 20 | İnceleme kalitesi | Enjekte edilmiş-bug probe'unda false-approval oranı |
| 20 | Token verimliliği | Çözülen issue başına tek-agent'a karşı toplam token |
| 15 | Koordinasyon mühendisliği | Merge-conflict çözümü, handoff-failure histogramı |
| **100** | | |

## Alıştırmalar

1. Tur ortasında bir diff'e bariz bir bug enjekte et (ana gövdeden önce ekstra `return None`). Reviewer'ın false-approve oranını ölç. False-approval %5 altına gelene kadar reviewer prompt'unu tune et.

2. İki coder'a indirge (architect + coder + reviewer + tester, coder iki alt-task'ı sıralı çalıştırır). Wall-clock ve pass oranını karşılaştır.

3. Merge coordinator'ı tek-yazıcı kısıtıyla değiştir (alt-task'lar disjoint dosya set'lerine dokunur). Architect üzerinde planning yükünü ölç.

4. Reviewer'ı GPT-5.4'ten Claude Opus 4.7'ye değiştir. False-approval oranını ve token maliyet delta'sını ölç.

5. Beşinci bir rol ekle: documenter (Haiku 4.5). İncelemeden sonra bir changelog girişi üretir. Dokümantasyon kalitesinin ekstra token harcamasını haklı çıkarıp çıkarmadığını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Paralel worktree | "İzole branch" | Coder başına taze bir working tree üreten `git worktree add` |
| Task board | "Shared message bus" | Agent'ların subscribe olduğu tipli mesajların dosya veya Redis store'u |
| Handoff | "Rol sınırı" | Bir rolün context'inden diğerine geçen herhangi bir mesaj |
| Token amplification | "Multi-agent overhead" | Roller boyunca toplam token / aynı task için tek-agent token |
| A2A protokol | "Agent-to-agent" | Google'ın 2025 tipli inter-agent mesaj spec'i |
| Merge coordinator | "Integrator" | Üç-yollu merge çalıştıran ve conflict'lere aracılık eden bileşen |
| False approval | "Reviewer hallucination'ı" | Reviewer bilinen bug'larla bir diff'i onaylar |

## İleri Okuma

- [SWE-AF factory mimarisi](https://github.com/Agent-Field/SWE-AF) — referans 2026 multi-agent factory'si
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT) — rol-tabanlı multi-agent framework'ü
- [AutoGen v0.4](https://github.com/microsoft/autogen) — Microsoft'un tipli actor framework'ü
- [Cognition AI (Devin)](https://cognition.ai) — referans ürün
- [Factory Droids](https://www.factory.ai) — alternatif referans ürün
- [Google A2A protokol](https://developers.google.com/agent-to-agent) — inter-agent mesajlaşma spec'i
- [git worktree dokümantasyonu](https://git-scm.com/docs/git-worktree) — izolasyon substrate'i
- [SWE-bench Pro](https://www.swebench.com) — değerlendirme hedefi
