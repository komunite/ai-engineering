---
name: video-qa
description: Sahne segmentasyonu, multi-vector index'leme, temporal grounding ve timestamp'li citation'lar ile video anlama pipeline'ı kur.
version: 1.0.0
phase: 19
lesson: 12
tags: [capstone, video, multimodal, gemini, qwen-vl, molmo, transnet, qdrant]
---

100 saat video verildiğinde, doğal dil sorularını (start, end) timestamp'leri artı frame önizlemeleriyle yanıtlayan bir ingestion pipeline ve query sistemi kur.

Build planı:

1. Videoları ingest et (YouTube URL'leri veya MP4); gerekirse 720p'ye downscale et.
2. TransNetV2 veya PySceneDetect ile sahne segmentasyonu; `[{scene_id, start_ms, end_ms, keyframe_path}]` yay.
3. Word-level timestamp'ler üreten Whisper-v3-turbo (faster-whisper) ile ASR; sahne başına dilimle.
4. Gemini 2.5 Pro veya Qwen3-VL-Max veya Molmo 2 ile VLM captioning; caption + frame embedding yay.
5. Sahne başına üç adlandırılmış vector (caption_emb, frame_emb, transcript_emb) ve payload {video_id, scene_id, start_ms, end_ms, keyframe_url} ile Qdrant multi-vector index.
6. Query: üç paralel dense sorgu; merge için reciprocal rank fusion; top-k=5 sahne.
7. Temporal grounding (TimeLens adapter veya VideoITG) top sahne içinde (start, end) rafine eder.
8. Query + top-3 sahne klipleri + transkript ile VLM synthesis (Gemini 2.5 Pro); `(video_id, start_ms, end_ms)` citation'ları zorunlu kıl.
9. ActivityNet-QA, NeXT-GQA artı 100 sorguluk elle etiketli custom set üzerinde eval. Genel ve soru sınıfı başına (descriptive, counting, action-type) doğruluğu raporla.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Temporal grounding IoU | Held-out grounding set üzerinde IoU |
| 20 | QA doğruluğu | NeXT-GQA ve 100 sorguluk custom set |
| 20 | Ingest throughput | Dolar başına index'lenen video saati |
| 20 | UI ve citation UX | Timestamp link'leri, thumbnail şeridi, jump-to-frame |
| 15 | Hallucination oranı | Counting ve action-type doğruluğu ayrı raporlanır |

Sert ret durumları:

- Sahne başına tek vector pool eden pipeline'lar. Sınıf ayrımlarının görünmesi için multi-vector zorunludur.
- (start, end) citation'ları olmayan yanıtlar.
- Counting/action alt küme dökümü olmadan tek bir genel doğruluk raporlamak.
- Sahne frame'lerini doğrudan almayan VLM synthesis (text-only girdiler visual grounding'i kaybeder).

Reddetme kuralları:

- Lisans kaynağı belirsiz videoları sunmayı reddet; her video_id'de lisans tag'i zorunlu.
- Ölçülen throughput'un üzerindeki ingest oranlarında "real-time" yanıt iddia etmeyi reddet.
- Counting/action hallucination sayısını genel doğruluk figürünün içinde gizlemeyi reddet.

Çıktı: sahne segmentasyon + ASR + captioning pipeline'ı, multi-vector Qdrant collection, temporal grounding adapter, timestamp deep-link'li Next.js 15 viewer, üç benchmark eval sonuçları (ActivityNet-QA, NeXT-GQA, custom) ve gözlemlediğin üç counting veya action-type failure sınıfı ile her birini azaltan retrieval veya synthesis değişikliğini adlandıran bir yazımı içeren bir repo.
