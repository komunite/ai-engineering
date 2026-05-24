# Agno ve Mastra: Üretim Runtime'ları

> Agno (Python) ve Mastra (TypeScript) 2026 üretim-runtime eşleşmesi. Agno mikrosaniye agent instantiation'ı ve stateless FastAPI backend'leri hedefliyor. Mastra agent'lar, tool'lar, workflow'lar, birleşik model routing ve composite storage'ı Vercel AI SDK substrate'inde yayınlıyor.

**Tür:** Öğrenim
**Diller:** Python, TypeScript
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 13 (LangGraph)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Agno'nun performans hedeflerini ve ne zaman önemli olduklarını tanı.
- Mastra'nın üç primitifini — Agent'lar, Tool'lar, Workflow'lar — ve desteklenen server adapter'larını adlandır.
- Stateless session-scope'lu bir FastAPI backend'inin neden önerilen Agno üretim yolu olduğunu açıkla.
- Belirli bir stack için Agno vs Mastra seç (Python-first vs TypeScript-first).

## Sorun

LangGraph, AutoGen, CrewAI framework-ağırlıklı. "Sadece agent döngüsü, hızlı, kendi runtime'ımda" isteyen ekipler Agno'ya (Python) ya da Mastra'ya (TypeScript) uzanır. Her ikisi de framework-sahipli primitiflerin bir kısmını ham hız ve çevreleyen stack'e daha sıkı uyum için takas eder.

## Kavram

### Agno

- Python runtime, eski adı Phi-data.
- "Graph yok, chain yok ya da karmaşık desen yok — sadece saf python."
- Dokümanlarından performans hedefleri: ~2μs agent instantiation, agent başına ~3.75 KiB bellek, ~23 model sağlayıcı.
- Üretim yolu: stateless session-scope'lu FastAPI backend. Her istek taze bir agent başlatır; session state bir DB'de yaşar.
- Native multimodal (text, image, audio, video, file) ve agentic RAG.

Hız hedefleri saniyede binlerce kısa-süreli agent'ın olduğunda önemli (chat fan-in, evaluation pipeline'lar). Bir agent 10 dakika çalıştığında daha az önemli.

### Mastra

- TypeScript, Vercel AI SDK üzerine kurulu.
- Üç primitif: **Agent'lar**, **Tool'lar** (Zod-tipli), **Workflow'lar**.
- Unified Model Router — 94 sağlayıcıda 3,300+ model (Mart 2026).
- Composite storage: bellek, workflow'lar, observability farklı backend'lere; ölçekte observability için ClickHouse önerilir.
- Apache 2.0, source kaynağı altında source-available enterprise lisansı altında `ee/` dizinleri.
- Express, Hono, Fastify, Koa için server adapter'ları; birinci-sınıf Next.js ve Astro entegrasyonu.
- Debugging için Mastra Studio yayınlanır (localhost:4111).
- 22k+ GitHub yıldızı, 1.0'da 300k+ haftalık npm download (Ocak 2026).

### Konumlanma

Hiçbiri LangGraph olmaya çalışmıyor. Şunlarda rekabet ederler:

- **Dil uyumu.** Python-first ekipler için Agno; TypeScript-first için Mastra.
- **Runtime ergonomisi.** Agno = near-zero overhead; Mastra = Vercel ekosistemiyle entegre.
- **Observability.** Her ikisi de Langfuse/Phoenix/Opik (Ders 24) ile entegre ama Mastra Studio birinci parti.

### Hangisini ne zaman seçmeli

- **Agno** — Python backend, çok kısa-süreli agent'lar, güçlü perf gereksinimleri, FastAPI shop.
- **Mastra** — TypeScript backend, Next.js / Vercel deploy, unified multi-provider model routing, Zod-tipli tool'lar.
- **LangGraph** (Ders 13) — dayanıklı state ve açık graph akıl yürütmesi ham hızdan daha önemli olduğunda.
- **OpenAI / Claude Agent SDK** — sağlayıcının ürünleştirilmiş şeklini istediğinde (Ders 16–17).

### Bu desen nerede ters gider

- **Perf-for-perf's-sake.** Workload istek başına bir yavaş agent çağrısı iken "2μs" iyi geldiği için Agno'yu seçmek. Overhead darboğaz değil.
- **Ekosistem lock-in.** Mastra'nın Vercel-flavored entegrasyonu Vercel'de artı, başka yerde eksi.
- **Enterprise lisans karmaşası.** Mastra'nın `ee/` dizinleri source-available, Apache 2.0 değil. Fork etmeyi planlıyorsan lisansları oku.

## İnşa Et

Bu ders öncelikle karşılaştırmalı — tek bir kod artefakti her iki framework'e hakkını veremez. Yan yana bir oyuncak için `code/main.py`'a bak: minimal bir "agent çalıştır, çıktıyı stream et, session persist et" akışı iki kere uygulanmış (bir kez Agno-şekilli, bir kez Mastra-şekilli).

Çalıştır:

```
python3 code/main.py
```

Yapısal olarak farklı ama fonksiyonel olarak eşdeğer iki trace.

## Kullan

- **Agno** — hız ve FastAPI şekli gerektiren Python backend.
- **Mastra** — çok sağlayıcılı ve workflow primitif'li TypeScript backend.
- Her ikisi de birinci-parti observability hook'ları yayar. Her ikisi de Langfuse ile entegre.

## Yayınla

`outputs/skill-runtime-picker.md` stack, latency bütçesi ve operasyonel şekle göre Agno, Mastra, LangGraph ya da bir sağlayıcı SDK'sını seçer.

## Alıştırmalar

1. Agno dokümanlarını oku. Stdlib ReAct döngüsünü (Ders 01) Agno'ya port et. Ne kayboldu? Ne kaldı?
2. Mastra dokümanlarını oku. Aynı döngüyü Mastra'ya port et. Tool typing'de ne değişti (Zod vs hiçbir şey)?
3. Benchmark: stack'inde agent instantiation latency'sini ölç. Agno'nun 2μs'i workload'ına önemli mi?
4. Bir göç tasarla: CrewAI'yi Python'da çalıştırıyorsan, Agno'ya geçersen ne bozulur?
5. Mastra'nın `ee/` lisans şartlarını oku. Hangi kısıtlamalar bir açık-kaynak fork'unu etkilerdi?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Agno | "Hızlı Python agent'lar" | Stateless session-scope'lu agent runtime |
| Mastra | "Vercel AI SDK üzerinde TypeScript agent'lar" | Agent'lar + Tool'lar + Workflow'lar + Model Router |
| Unified Model Router | "Multi-provider erişimi" | 94 sağlayıcıda 3,300+ model için tek client |
| Composite storage | "Birden çok backend" | Bellek/workflow'lar/observability her biri farklı store'a |
| Mastra Studio | "Yerel debugger" | Agent'ları introspect etmek için localhost:4111 UI |
| Source-available | "OSS değil" | Lisans source okumayı izin verir ama commercial use'u kısıtlar |

## İleri Okuma

- [Agno Agent Framework docs](https://www.agno.com/agent-framework) — performans hedefleri, FastAPI entegrasyonu
- [Mastra docs](https://mastra.ai/docs) — primitifler, server adapter'ları, Model Router
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — durumlu-graph alternatifi
- [Comet Opik](https://www.comet.com/site/products/opik/) — Mastra entegrasyonları tarafından cite edilen observability karşılaştırmaları
