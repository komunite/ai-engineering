---
name: production-rag
description: Role + jurisdiction filtreleme, prompt caching, guardrails ve canlı drift izleme ile düzenlemeye tabi bir domain'de RAG chatbot deploy et.
version: 1.0.0
phase: 19
lesson: 08
tags: [capstone, rag, chatbot, regulated, llama-guard, nemo-guardrails, ragas, langfuse]
---

Düzenlemeye tabi bir corpus (legal sözleşmeler, klinik araştırma protokolleri, sigorta poliçeleri veya benzeri) verildiğinde, doğrulanabilir citation'larla yanıt veren, role ve jurisdiction erişim politikalarına uyan ve drift için izlenen bir chatbot deploy et.

Build planı:

1. Corpus'u docling veya Unstructured ile parse et; görsel açıdan zengin dökümanları ColPali üzerinden yönlendir. Role ve jurisdiction etiketli chunk'lar yay.
2. Dense (Voyage-3 veya Nomic-embed-v2) pgvector + pgvectorscale'e; sparse BM25 Tantivy üzerinden index'le.
3. LangGraph konuşma agent'ı bağla: retrieve (role + jurisdiction ile filtrele, hybrid dense+BM25, reciprocal rank fusion), rerank (bge-reranker-v2-gemma-2b veya Voyage rerank-2), synth (prompt caching ile Claude Sonnet 4.7).
4. Prompt'ları stable prefix'lerle birleştir: system preamble -> policy bloğu -> reranked context -> user query. %60-80 prompt-cache hit oranını hedefle.
5. Guardrails: input ve output üzerinde Llama Guard 4, off-domain ve policy-forbidden sorular için NeMo Guardrails v0.12 rail'leri, output üzerinde Presidio PII scrub, citation enforcement post-filter.
6. (answer, citations) ile 200 soruluk uzman etiketli golden set kur. Exact-citation match, answer correctness, RAGAS faithfulness üzerinde skorla.
7. 50-prompt red team kur (PAIR, TAP, PII extraction, off-domain, cross-jurisdiction probe'lar).
8. Retrieval nDCG ve citation sadakatini haftalık izleyen Arize Phoenix drift dashboard'u; %5 düşüşte alarm.
9. Langfuse maliyet raporu: prompt-cache hit oranı, sorgu başına token, aşama başına $/sorgu.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | RAGAS faithfulness + answer relevance | 200 soruluk golden set üzerinde online skorlar |
| 20 | Citation doğruluğu | Doğrulanabilir kaynak anchor'larına sahip yanıtların oranı |
| 20 | Guardrail kapsamı | Llama Guard 4 geçiş oranı + jailbreak suite sonucu |
| 20 | Maliyet / latency mühendisliği | Prompt-cache hit oranı, p95 latency, $/sorgu |
| 15 | Drift izleme dashboard'u | Haftalık retrieval kalite trendi olan canlı Phoenix dashboard |

Sert ret durumları:

- Cross-jurisdiction veri sızdıran herhangi bir chatbot. Role+jurisdiction filtreleme retrieval'dan önce zorlanmalı, sonra değil.
- Cache prefix'lerini bozan synthesis prompt'ları (system ile context arasında policy'yi yeniden sıralamak). Cache ekonomisini yok eder.
- Loglanmış red-team çalıştırmaları olmayan guardrail konfigürasyonları.
- Citation'sız yanıtlar; doğrulanabilir anchor'sız citation'lar.

Reddetme kuralları:

- Her chunk'ta jurisdiction tag'i olmadan düzenlemeye tabi bir domain'de deploy etmeyi reddet.
- Uzman etiketli golden set soruları üzerinde retrieval eğitmeyi reddet. Contamination eval kredibilitesini yok eder.
- README'de açık bir SOC2/HIPAA/GDPR uygulanabilirlik matrisi olmadan "compliant" iddia etmeyi reddet.

Çıktı: ingestion pipeline'ı, LangGraph konuşma agent'ı, 200 soruluk golden set, 50-prompt red team, Phoenix drift dashboard, Langfuse cost dashboard ve gözlemlediğin en kritik üç citation-breakage örüntüsü ile her birine yönelik retrieval veya prompt düzeltmesini adlandıran bir yazımı içeren bir repo.
