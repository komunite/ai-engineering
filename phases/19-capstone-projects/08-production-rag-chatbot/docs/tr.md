# Capstone 08 — Regüle Edilmiş Bir Dikey İçin Üretim RAG Chatbot'u

> Harvey, Glean, Mendable ve LlamaCloud — hepsi 2026'da aynı üretim şeklini çalıştırıyor. Görsellerle docling veya Unstructured ve ColPali ile ingest. Hybrid search. bge-reranker-v2-gemma ile re-rank. %60-80 hit oranında prompt caching ile Claude Sonnet 4.7 ile sentezleme. Llama Guard 4 ve NeMo Guardrails ile guard. Langfuse ve Phoenix ile izle. 200-soruluk golden set'te RAGAS ile derecelendir. Regüle bir domain'de (legal, klinik, sigorta) bir tane inşa et ve capstone golden set'i, red team'i ve drift dashboard'unu geçmek.

**Tür:** Bitirme
**Diller:** Python (pipeline + API), TypeScript (chat UI)
**Ön koşullar:** Faz 5 (NLP), Faz 7 (transformer'lar), Faz 11 (LLM engineering), Faz 12 (multimodal), Faz 17 (infrastructure), Faz 18 (safety)
**Egzersize edilen fazlar:** P5 · P7 · P11 · P12 · P17 · P18
**Süre:** 30 saat

## Sorun

Regüle-domain RAG (legal kontratlar, klinik trial protokolleri, sigorta poliçeleri) 2026'nın en çok yayınlanan üretim şekli, çünkü ROI bariz ve riskler somut. Harvey (Allen & Overy) legal için inşa etti. Mendable developer-docs versiyonunu yayınlıyor. Glean enterprise search'ü kapsar. Pattern: yüksek-fidelity ingest, hybrid retrieve with rerank, citation enforcement ve prompt caching ile sentezleme, çoklu safety katmanlarıyla guard ve drift'i sürekli izle.

Zor kısımlar model değil. Yetki-aware compliance (HIPAA, GDPR, SOC2), citation-seviyesinde auditability, maliyet kontrolü (prompt caching hit oranı yüksek olduğunda %60-90 indirim alır), RAGAS faithfulness ile hallucination tespiti ve kaynak dokümanlar index yetişmeden güncellendiğinde drift tespiti. Bu capstone senden 200-soruluk bir golden set'te bunu yan yana bir red-team suite'i ile gönderme istiyor.

## Kavram

Pipeline'ın iki tarafı var. **Ingestion**: docling veya Unstructured yapılı dokümanları parse eder; ColPali görsel olarak zengin olanları yönetir; chunk'lar özetler, tag'ler ve role-based access etiketleri alır. Vektörler pgvector + pgvectorscale'e (50M vektör altında) veya Qdrant Cloud'a gider; sparse BM25 yan yana çalışır. **Conversation**: LangGraph memory ve multi-turn'ü yönetir; her sorgu hybrid retrieval çalıştırır, bge-reranker-v2-gemma-2b ile rerank eder, prompt-cached Claude Sonnet 4.7 ile sentezler, çıktıyı Llama Guard 4 ve NeMo Guardrails'tan geçirir ve citation-anchor'lı bir cevap emit eder.

Eval stack'inin dört katmanı var. Doğruluk için **Golden set** (citation'lı 200 etiketli S/C). Safety için **Red team** (jailbreak'ler, PII çıkarma denemeleri, off-domain sorular). Tur başına otomatik olarak faithfulness / answer relevance / context precision için **RAGAS**. Haftalık retrieval kalitesini ve hallucination skorunu izleyen **Drift dashboard** (Arize Phoenix).

Prompt caching maliyet kaldıracı. Claude 4.5+ ve GPT-5+ system prompt'ları + retrieve edilmiş context'i caching destekler. %60-80 hit oranında, sorgu başına maliyet 3-5x düşer. Yüksek cache hit oranlarına ulaşmak için pipeline kararlı prefix'ler için tasarlanmalı (system prompt + reranked context önce).

## Mimari

```
dokümanlar (kontratlar, protokoller, poliçeler)
      |
      v
docling / Unstructured parse + görseller için ColPali
      |
      v
chunk'lar + özetler + role-label'ler + yetki tag'leri
      |
      v
pgvector + pgvectorscale  +  BM25 (Tantivy)
      |
sorgu + role + yetki
      |
      v
LangGraph konuşma agent'ı
   +--- retrieve (hybrid)
   +--- role + yetki ile filtrele
   +--- rerank (bge-reranker-v2-gemma-2b veya Voyage rerank-2)
   +--- sentezle (Claude Sonnet 4.7, prompt cached)
   +--- guard (Llama Guard 4 + NeMo Guardrails + Presidio output PII scrub)
   +--- cite + return
      |
      v
eval:
  RAGAS faithfulness / answer_relevance / context_precision (online)
  Langfuse annotation queue (örneklenmiş)
  Arize Phoenix drift (haftalık)
  red team suite (pre-release)
```

## Stack

- Ingestion: yapılı dokümanlar için Unstructured.io veya docling; görsel-zengin PDF'ler için ColPali
- Vector DB: 50M vektör altında pgvector + pgvectorscale; aksi takdirde Qdrant Cloud
- Sparse: field weight'leriyle Tantivy BM25
- Orkestrasyon: LlamaIndex Workflows (ingestion) + LangGraph (conversation)
- Re-ranker: self-hosted bge-reranker-v2-gemma-2b veya hosted Voyage rerank-2
- LLM: prompt caching'li Claude Sonnet 4.7; fallback self-hosted Llama 3.3 70B
- Eval: online RAGAS 0.2, hallucination ve jailbreak suite'leri için DeepEval
- Observability: annotation queue'lu self-hosted Langfuse; drift için Arize Phoenix
- Guardrails: Llama Guard 4 input/output sınıflandırıcı, NeMo Guardrails v0.12 policy, Presidio PII scrub
- Compliance: chunk'lar üzerinde role-based access label'ları; GDPR/HIPAA için yetki tag'leri

## İnşa Et

1. **Ingestion.** Korpusunu Unstructured veya docling ile parse et (ciddi bir build için 1000-10000 doküman). Taranmış / görsel-ağır sayfalar için ColPali üzerinden route et. Özetler, role-label'lar, yetki tag'leriyle chunk'lar üret.

2. **Index.** pgvector + pgvectorscale'e dense embedding'ler (Voyage-3 veya Nomic-embed-v2). Tantivy üzerinden BM25 yan-index. Payload olarak role ve yetki filter'ları.

3. **Hybrid retrieve.** Önce role+yetki ile filtrele; sonra paralel dense + BM25; reciprocal rank fusion ile birleştir; top-20 reranker'a; top-5 synth'e.

4. **Prompt caching'le sentezle.** System prompt + statik policy'ler cache header'ında; reranked context cache extension olarak; kullanıcı sorusu cache'siz suffix olarak. Steady state'te %60-80 cache hit oranını hedefle.

5. **Guardrails.** Input'ta Llama Guard 4; NeMo Guardrails rail'leri off-domain soruları veya policy-yasaklı konuları blokla; Presidio çıktıdaki kazara PII'leri scrub'lar; citation enforcement post-filter.

6. **Golden set.** Bir domain uzmanı tarafından (cevap, citation'lar) ile etiketlenmiş 200 S/C çifti. Agent'ı exact-citation match, cevap doğruluğu, faithfulness (RAGAS) üzerinde skorla.

7. **Red team.** 50 adversarial prompt: jailbreak'ler (PAIR, TAP), PII exfiltration denemeleri, off-domain, cross-yetki sızıntıları. Pass/fail ve severity ile skorla.

8. **Drift dashboard.** Arize Phoenix retrieval kalitesini (nDCG, citation faithfulness) haftalık izler. %5 düşüşte alert.

9. **Maliyet raporu.** Langfuse: prompt-caching hit oranı, sorgu başına token'lar, aşama bazında $/sorgu breakdown'u.

## Kullan

```
$ chat --role=analyst --jurisdiction=GDPR
> kontratımız altında EU kullanıcı profilleri için data-retention yükümlülüğü nedir?
[retrieve]  GDPR + analyst-role'a filtreli hybrid top-20
[rerank]    top-5 tutuldu
[synth]     claude-sonnet-4.7, cache hit %74, 0.8s
cevap:
  Kontrat (Bölüm 12.4, Master Services Agreement tarihli 2024-03-11)
  GDPR Madde 17 uyarınca fesihten itibaren 30 gün içinde EU kullanıcı profili
  silmesini zorunlu kılar. DPA değişikliği (DPA-v2.1, Bölüm 5) bunu "restricted"
  kategori veri için 14 güne uzatır.
  citation'lar: [MSA-2024-03-11 s12.4, DPA-v2.1 s5]
```

## Yayınla

`outputs/skill-production-rag.md` teslimat'ı açıklar. Compliance label'larıyla deploy edilmiş, rubriğin geçtiği, canlı drift monitoring ile gözlemlenen regüle-domain chatbot.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | RAGAS faithfulness + answer relevance | Golden set'te online skorlar (200 S/C) |
| 20 | Citation doğruluğu | Doğrulanabilir kaynak anchor'lı cevapların oranı |
| 20 | Guardrail kapsamı | Llama Guard 4 pass oranı + jailbreak suite sonuçları |
| 20 | Maliyet / gecikme mühendisliği | Prompt-cache hit oranı, p95 gecikme, $/sorgu |
| 15 | Drift monitoring dashboard'u | Haftalık retrieval-quality trendiyle Phoenix canlı dashboard |
| **100** | | |

## Alıştırmalar

1. Farklı bir yetki altında ikinci bir korpus dilimi inşa et (örn. GDPR ile birlikte HIPAA). 20-soruluk cross-yetki probe'unda role+yetki filtrelemenin cross-leak'i önlediğini göster.

2. Bir hafta üretim trafiğinde prompt-cache hit oranını ölç. Cache prefix'i kıran sorguları belirle. Yeniden yapılandır.

3. 10k-token özet buffer'ı ile multi-turn memory ekle. Konuşma büyüdükçe faithfulness'in düşüp düşmediğini ölç.

4. Claude Sonnet 4.7'yi self-hosted Llama 3.3 70B ile değiştir. $/sorgu ve faithfulness delta'sını ölç.

5. "Emin değilim" modu ekle: top reranked skorlar bir eşiğin altındaysa, agent cevap vermek yerine "güvenilir citation'lara sahip değilim" der. False-confidence azalmasını ölç.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Prompt caching | "Cached system + context" | Claude/OpenAI özelliği: cache'lenmiş prefix token'ları hit'te %60-90 indirimli |
| RAGAS | "RAG evaluator'ı" | Faithfulness, answer relevance, context precision'ın otomatik skorlaması |
| Golden set | "Etiketli eval" | Citation'lı 200+ uzman-etiketli S/C; ground truth |
| Yetki tag'i | "Compliance label" | Chunk'lara eklenmiş GDPR/HIPAA/SOC2 kapsamı; retrieval filter tarafından zorlanır |
| Citation faithfulness | "Grounded answer rate" | Retrieve edilebilir kaynak span'larıyla desteklenen iddiaların oranı |
| Drift | "Retrieval quality decay" | nDCG veya citation skorundaki haftalık değişim; alert eşiği %5 |
| Red team | "Adversarial eval" | Pre-release jailbreak, PII çıkarma, off-domain probe'lar |

## İleri Okuma

- [Harvey AI](https://www.harvey.ai) — referans legal üretim stack'i
- [Glean enterprise search](https://www.glean.com) — enterprise ölçeğinde referans RAG
- [Mendable dokümantasyonu](https://mendable.ai) — developer-docs RAG referansı
- [LlamaCloud Parse + Index](https://docs.llamaindex.ai/en/stable/examples/llama_cloud/llama_parse/) — managed ingestion
- [Anthropic prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) — maliyet-kaldıraç referansı
- [RAGAS 0.2 dokümantasyonu](https://docs.ragas.io/) — kanonik RAG eval framework'ü
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — referans drift observability
- [Llama Guard 4](https://ai.meta.com/research/publications/llama-guard-4/) — 2026 safety sınıflandırıcısı
- [NeMo Guardrails v0.12](https://docs.nvidia.com/nemo-guardrails/) — policy rail framework'ü
