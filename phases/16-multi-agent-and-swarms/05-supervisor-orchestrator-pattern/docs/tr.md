# Supervisor / Orchestrator-Worker Deseni

> Bir lead agent planlar ve delege eder; uzmanlaşmış worker'lar paralel context'lerde yürütür ve geri rapor verir. Bu, Anthropic'in Research sisteminin (lead olarak Claude Opus 4, subagent olarak Sonnet 4) ardındaki desendir, dahili araştırma eval'lerinde tek-agent Opus 4'ün üzerinde +%90.2 ölçülmüştür. Anthropic'in engineering yazısı, BrowseComp'taki varyansın %80'inin yalnızca token kullanımıyla açıklandığını rapor eder — çoklu-agent büyük ölçüde her subagent yeni bir context penceresi aldığı için kazanır. Bu ders supervisor desenini primitive'lerden inşa eder ve üretim dağıtımlarından 2026 mühendislik derslerini kapsar.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib, `threading`)
**Ön koşullar:** Faz 16 · 04 (Primitive Model)
**Süre:** ~75 dakika

## Sorun

Araştırma, tek-agent sistemlerinin başarısız olduğu prototipik görevdir. "2023 ve 2026 arasında çoklu-agent sistemlerinde ne değişti?" diye sorarsın. Tek bir agent beş makaleyi sırayla okur, context'inin yarısını metinleriyle doldurur ve sonra hepsi hakkında birlikte akıl yürütmek zorunda kalır. Beşincisine ulaştığında ilk makaleyi unutmuştur. Paralelleştiremez.

Supervisor deseni bunu düzeltir: bir lead agent aramayı planlar, her alt soruyu bir worker'a delege eder ve sentezler. Her worker dar bir soru için kendi 200k-token penceresini alır. Lead asla ham makaleleri görmez — yalnızca worker özetlerini.

Anthropic'in üretim Research sistemi tek bir Opus 4'e karşı dahili araştırma eval'lerinde +%90.2 rapor ediyor. Aynı yazı, BrowseComp varyansının %80'inin *yalnızca token kullanımı* tarafından açıklandığını not ediyor. Subagent başına taze context ana mekanizmadır.

## Kavram

### Desen

```
                 ┌──────────────┐
                 │   Lead       │  planlar, parçalara ayırır,
                 │  (Opus 4)    │  sentezler
                 └──┬────┬───┬──┘
                    │    │   │
            ┌───────┘    │   └───────┐
            ▼            ▼           ▼
      ┌─────────┐  ┌─────────┐  ┌─────────┐
      │ Worker1 │  │ Worker2 │  │ Worker3 │
      │(Sonnet) │  │(Sonnet) │  │(Sonnet) │
      └─────────┘  └─────────┘  └─────────┘
         taze        taze         taze
         context     context      context
```

Lead asla ham materyalleri okumaz. Worker'lar lead sentezleyene kadar birbirinin işini görmez. Her ok dar bir artefakt ile bir handoff'tur.

### Neden kazanır

Üç mekanizma:

1. **Subagent başına taze context.** "FIPA-ACL mirası"nı keşfeden bir worker, lead'in planlama için harcadığı 40k token'ı taşımaz. Tek bir soru için 200k pencere alır.
2. **Prompt üzerinden uzmanlaşma.** Lead'in prompt'u "parçala ve sentezle", "araştır" değildir. Her worker'ın prompt'u dardır: "X'te ne değiştiğini bul." Odaklı prompt'lar odaklı çıktılar üretir.
3. **Paralelizm.** Worker'lar eş zamanlı çalışır. Duvar-saati zamanı kabaca `max(worker_times) + plan + synthesis`, `sum(worker_times)` değildir.

### Mühendislik dersleri (Anthropic 2025)

Anthropic yazısı 2026 hâlâ alakalı birkaç üretim dersi listeler:

- **Çabayı sorgu karmaşıklığına ölçeklendir.** Basit sorgular: bir agent, 3-10 tool çağrısı. Karmaşık sorgular: 10+ agent. Lead bunu tahmin etmeli, arayan değil.
- **Önce geniş, sonra dar.** Önce geniş alt-sorulara parçala, sonra cevap derinliği hak ediyorsa alt-soru başına daha fazla worker doğur.
- **Rainbow deployment'lar.** Agent'lar uzun süreli ve stateful'dur. Geleneksel blue-green çalışmaz. Anthropic rainbow kullanır: eskiler boşalırken yeni sürümlerin kademeli rollout'u.
- **Token kullanımı baskındır.** Çoklu-agent tek-agent'ın ~15× token'ı. Yalnızca görev değeri maliyeti haklı çıkardığında çalıştır.

### LangGraph dönüşü

LangGraph başlangıçta `langgraph-supervisor` kütüphanesini yüksek seviye bir `create_supervisor` helper ile gönderdi. 2025'te LangChain önerisini supervisor desenini doğrudan tool-calling üzerinden uygulamaya taşıdı, çünkü tool çağrıları *supervisor'ın ne gördüğü* üzerinde daha fazla kontrol sağlar (context engineering). Kütüphane hâlâ çalışır; dokümanlar artık tool-calling formunu önerir.

### Başarısızlık modları

- **Lead planı halüsinasyon yapar.** Lead, gerçek soruyu parçalara ayırmayan alt-sorular ürettiyse, worker'lar yanlış hedef üzerinde hassas araştırma yapar.
- **Worker'lar fazla keşfeder.** Açık kapsam sınırları olmadan worker'lar atanmış alt-sorularının ötesine kayar ve sentez adımını kirletir.
- **Sentez çatışmaları.** İki worker çelişen gerçekler döndürür. Lead ya yeniden sormalı (bir tur eklemeli) ya da anlaşmazlığı açıkça notetmelidir. Bir tarafı sessizce seçmek en kötü başarısızlıktır: kullanıcı anlaşmazlığın olduğunu asla bilmez.

### Supervisor ne zaman yanlış

- **Sıralı görevler.** Adım 2 gerçekten adım 1'in çıktısına ihtiyaç duyuyorsa, paralelizm hiçbir şey kazandırmaz. Pipeline kullan (CrewAI Sequential, LangGraph linear graph).
- **Basit sorgular.** Tek-agent onları daha hızlı ve daha ucuz halleder. Worker doğurmadan önce lead'in "çabayı ölçeklendir" kontrolünü kullan.
- **Katı determinizm.** Supervisor LLM-seçili delegasyon kullanır. Audit/replay uyarlanabilirlikten daha önemli olduğunda statik graflar daha iyidir.

## İnşa Et

`code/main.py` `threading` kullanarak üç paralel worker'lı bir supervisor uygular. Lead bir sorguyu alt-sorulara parçalar, worker'lar her alt-soru üzerinde eş zamanlı çalışır ve lead sentezler. Gerçek LLM yok — worker'lar fetch-ve-özetlemeyi simüle etmek için senaryolanmıştır.

Temel yapı:

- `Lead.plan(query)` bir sorguyu 3 alt-soruya böler.
- `Worker.run(sub_q)` sahte bir özet döndürür (üretimde herhangi bir tool-kullanan agent olabilir).
- `Lead.run(query)` worker'ları thread'lerde başlatır, join'ler ve sentezler.

Çalıştır:

```
python3 code/main.py
```

Çıktı planı, başlangıç/bitiş zaman damgalarıyla paralel worker izlerini ve son sentezi gösterir. Duvar-saati kazanımlarını görebilirsin: üç 0.3 saniyelik worker 0.9 değil, ~0.35 saniyede çalışır.

## Kullan

`outputs/skill-supervisor-designer.md` bir kullanıcı sorgusu alır ve supervisor-desen tasarımı üretir: lead sistem prompt'u, worker rolleri, alt-soru parçalama kuralları ve sentez template'i. Yeni bir araştırma-stili agent sistemi inşa etmeden önce bunu kullan.

## Yayınla

Bir supervisor deseni dağıtmadan önce kontrol listesi:

- **Model eşleştirme.** Lead bir reasoning-tier model üzerinde (Opus sınıfı, `o3` sınıfı). Worker'lar daha hızlı, daha ucuz bir model üzerinde (Sonnet, `o4-mini`).
- **Worker timeout'u.** Medyan çalışma süresinin 2×'ünü aşan herhangi bir worker öldürülür; lead ya daha dar kapsamla yeniden doğurur ya da onsuz devam eder.
- **Worker başına token cap'i.** Sert sınır (örneğin beklenen sentez girdisinin 10×'u) kaçak bir worker'ın bütçeyi havaya uçurmasını önler.
- **Observability.** Lead'in planını, her worker'ın tool çağrılarını ve sentezi izle. Bu, herhangi bir post-hoc hata ayıklamanın temelidir.
- **Rainbow rollout.** Stateful uzun-süreli agent'lar hot swap değil, kademeli sürüm geçişi gerektirir.

## Alıştırmalar

1. `code/main.py`'yi çalıştır, sonra lead'i 3 yerine 5 worker doğuracak şekilde değiştir. Duvar-saati etkisini gözlemle. Bu demo'da hangi worker sayısında spawn overhead paralel tasarrufları aşar?
2. Bir worker timeout'u uygula: 0.5 saniyeden uzun çalışan herhangi bir worker'ı öldür ve lead'in kalan sonuçları sentezlemesini sağla. Bir worker'ın kesildiğini bilmek için hangi observability'ye ihtiyacın var?
3. Lead'in sentezine bir çatışma-tespit adımı ekle: iki worker çelişen cevaplar döndürdüyse, lead birini seçmek yerine anlaşmazlığı not eder. LLM çağırmadan çelişkiyi nasıl tespit edersin?
4. Anthropic'in Research-sistemi engineering yazısını oku. Bu oyuncak demonun üretimde çalışmak için benimsemesi gereken üç uygulamayı listele.
5. LangGraph'in `create_supervisor`'ını (legacy) yeni tool-calling önerisiyle karşılaştır. Hangisi supervisor'ın ne gördüğü üzerinde daha iyi kontrol verir? Anthropic neden sentezde ham worker context'ini değil yalnızca alt-cevapları açıkça geçer?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Supervisor | "Lead agent" | Planlayan, delege eden ve sentezleyen orchestrator agent. İşi kendi yapmaz. |
| Worker | "Subagent" | Supervisor tarafından dar kapsam ve kendi context penceresiyle çağrılan odaklı agent. |
| Orchestrator-worker | "Supervisor deseni" | Aynı şey, farklı isim. 2026 literatürü ikisini de kullanır. |
| Taze context | "Temiz pencere" | Bir worker'ın context'i lead'in geçmişinden değil, kendi sistem prompt'u ve atanmış sorusundan başlar. |
| Rainbow deployment | "Kademeli rollout" | Uzun-süreli stateful agent'lar blue-green değil, sürümlü drain-and-replace gerektirir. |
| Token baskınlığı | "Context değişkendir" | Anthropic'e göre araştırma-eval varyansının %80'i model seçiminden değil, toplam token kullanımından gelir. |
| Çabayı ölçeklendir | "Agent sayısını karmaşıklığa eşleştir" | Lead sorgu zorluğunu tahmin eder, ona göre 1 vs 10+ worker doğurur. |
| Sentez çatışması | "Worker'lar anlaşmaz" | İki worker çelişen gerçekler döndürür; lead birini sessizce seçmek yerine anlaşmazlığı yüzeye çıkarmalı. |

## İleri Okuma

- [Anthropic engineering — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — supervisor deseni için üretim referansı
- [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) — tool-calling supervisor artık önerilen form
- [LangGraph supervisor reference](https://reference.langchain.com/python/langgraph-supervisor) — legacy helper, 2026 üretiminde hâlâ kullanılır
- [OpenAI cookbook — Orchestrating Agents: Routines and Handoffs](https://developers.openai.com/cookbook/examples/orchestrating_agents) — handoff tabanlı supervisor varyantı
