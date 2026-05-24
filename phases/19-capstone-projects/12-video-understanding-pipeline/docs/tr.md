# Capstone 12 — Video Anlama Pipeline'ı (Sahne, QA, Arama)

> Twelve Labs Marengo + Pegasus'u ürünleştirdi. VideoDB CRUD-for-video API'sini yayınladı. AI2'nin Molmo 2'si açık VLM checkpoint'leri yayınladı. Gemini long-context saatlerce videoyu nativ olarak işler. TimeLens-100K ölçekte temporal grounding'i tanımladı. 2026 pipeline'ı oturdu: sahne segmentasyonu, per-scene caption + embedding, transcript hizalama, multi-vector index ve (start, end) timestamp'leri artı frame preview'leriyle yanıt veren bir sorgu. Capstone 100 saat ingest etmek, public benchmark'lara ulaşmak ve counting ve action sorularında hallucination ölçmek.

**Tür:** Bitirme
**Diller:** Python (pipeline), TypeScript (UI)
**Ön koşullar:** Faz 4 (CV), Faz 6 (speech), Faz 7 (transformer'lar), Faz 11 (LLM engineering), Faz 12 (multimodal), Faz 17 (infrastructure)
**Egzersize edilen fazlar:** P4 · P6 · P7 · P11 · P12 · P17
**Süre:** 30 saat

## Sorun

Uzun-form video QA, 2026 ölçeğinde en bandwidth-aç multimodal sorun. Gemini 2.5 Pro 2-saatlik bir videoyu nativ okuyabilir, ama 100 saat videoyu sorgulanabilir bir korpusa ingest etmek hâlâ sahne-seviyesinde bir index gerektiriyor. Üretim şekli sahne segmentasyonu (TransNetV2 veya PySceneDetect), bir VLM ile per-scene captioning (Gemini 2.5, Qwen3-VL-Max veya Molmo 2), transcript hizalama (kelime timestamp'leri ile Whisper-v3-turbo) ve caption, frame embedding ve transcript'i yan yana saklayan bir multi-vector index'i kombine eder. Sorgu pipeline'ı (start, end) timestamp'leri artı frame preview'leriyle yanıt verir.

Benchmark'lar public (ActivityNet-QA, NeXT-GQA) artı kendi 100-sorguluk custom set'in. Counting ve action-type sorularında hallucination bilinen-zor başarısızlık sınıfı; capstone bunu açıkça ölçer.

## Kavram

Ingest'te üç pipeline paralel çalışır. **Sahne segmentasyonu** videoyu sahnelere keser. **VLM captioning** sahne başına bir caption ve bir keyframe'den bir frame embedding üretir. **ASR hizalama** kelime-seviyesinde timestamp'ler üretir. Üç stream (scene_id, time range) ile join'lenir. Her sahne multi-vector index'te (Qdrant) üç vektör tipi alır: caption embedding'i, keyframe embedding'i, transcript embedding'i.

Sorgu zamanında, doğal-dil sorusu üç vektörün hepsine karşı ateşlenir; sonuçlar RRF ile merge'lenir; bir temporal-grounding adapter (TimeLens-tarzı) top sahnesi içindeki (start, end) window'unu rafine eder. VLM sentezleyici (Gemini 2.5 Pro veya Qwen3-VL-Max) sorgu + top sahneleri + cropped frame'leri alır ve cited timestamp'ler ve bir frame preview ile yanıt verir.

Hallucination ölçümü önemli. Counting ("odaya kaç kişi giriyor?") ve action-type ("şef karıştırmadan önce döküyor mu?") soruları meşhur şekilde güvenilmez. Doğruluğu descriptive sorulardan ayrı raporla.

## Mimari

```
video dosyası / URL
      |
      v
PySceneDetect / TransNetV2  (sahne segmentasyonu)
      |
      +--- per-scene keyframe --- VLM caption + frame embedding'i
      |                            (Gemini 2.5 Pro / Qwen3-VL-Max / Molmo 2)
      |
      +--- audio kanalı --- Whisper-v3-turbo ASR + kelime timestamp'leri
      |
      v
multi-vector Qdrant: {caption_emb, keyframe_emb, transcript_emb}
      |
sorgu:
  üçüne karşı dense sorgu -> RRF merge -> top-k sahne
      |
      v
TimeLens / VideoITG temporal grounding (sahne içinde start/end rafine)
      |
      v
VLM synth: sorgu + top sahneler + frame preview'leri
      |
      v
yanıt + (start, end) timestamp'ler + frame thumb'lar + citation'lar
```

## Stack

- Sahne segmentasyonu: TransNetV2 (2024-26 state-of-the-art) veya PySceneDetect
- ASR: kelime timestamp'leriyle faster-whisper üzerinden Whisper-v3-turbo
- VLM captioner + cevaplayıcı: Gemini 2.5 Pro veya Qwen3-VL-Max veya Molmo 2
- Temporal grounding: TimeLens-100K-eğitilmiş adapter veya VideoITG
- Index: multi-vector destekli Qdrant (caption / frame / transcript)
- UI: HTML5 video player ve sahne thumbnail'leriyle Next.js 15
- Eval: ActivityNet-QA, NeXT-GQA, custom 100-soruluk el-etiketli set
- Hallucination benchmark'ı: el-etiketleri olan counting ve action-type alt kümeler

## İnşa Et

1. **Ingest walker.** YouTube URL'leri veya local MP4'leri kabul et. Gerekirse 720p'ye downscale et. `{video_id, file_path}` persist et.

2. **Sahne segmentasyonu.** `[{scene_id, start_ms, end_ms, keyframe_path}]` üretmek için TransNetV2 veya PySceneDetect çalıştır. 100 saat hedefi: ~6k-8k sahne.

3. **ASR geçişi.** Audio'da Whisper-v3-turbo çalıştır; kelime-seviyesinde timestamp'leri export et; per-scene transcript dilimlerine böl.

4. **VLM captioning.** Sahne başına Gemini 2.5 Pro'yu (veya Qwen3-VL-Max'i) keyframe ve kısa bir caption template'iyle çağır. Caption + frame embedding'i üret.

5. **Multi-vector index.** Üç adlandırılmış vektörle Qdrant collection. Payload: `{video_id, scene_id, start_ms, end_ms, keyframe_url}`.

6. **Sorgu.** Doğal-dil sorusu üç dense sorgu ateşler; reciprocal rank fusion ile merge'le; top-k=5 sahne.

7. **Temporal grounding.** Sahne içinde (start, end) window'unu rafine etmek için top sahnede TimeLens-tarzı adapter çalıştır.

8. **VLM synth.** Gemini 2.5 Pro'yu sorgu + top-3 sahne klipleri (görüntü veya kısa klipler olarak) + transcript'lerle çağır. `(video_id, start_ms, end_ms)` citation'larını zorunlu kıl.

9. **Eval.** ActivityNet-QA ve NeXT-GQA çalıştır. 100-sorguluk custom set inşa et. Genel doğruluk + per-class breakdown raporla (counting, action, descriptive).

## Kullan

```
$ video-qa ask --url=https://youtube.com/watch?v=X "ilk dakikada kavşaktan kaç araba geçiyor?"
[scene]    23 sahne tespit edildi
[asr]      transcript tamam, 4m12s
[index]    69 vektör yazıldı (23 sahne x 3)
[query]    top sahne: scene 3 [01:32-01:54], güven 0.84
[ground]   rafine window: [00:12-00:58]
[synth]    gemini 2.5 pro, 1.4s
yanıt:     5 araba kavşaktan 00:12 ile 00:58 arasında geçer.
citation'lar: [scene 3: 00:12-00:58]
          [00:14, 00:27, 00:44, 00:51, 00:57'de frame preview]
```

## Yayınla

Teslimat `outputs/skill-video-qa.md`. Bir YouTube URL'i veya yüklenmiş video verildiğinde, pipeline sahneleri index'ler ve timestamp'li citation'larla soruları yanıtlar.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Temporal grounding IoU | Holdout grounding set'inde intersection-over-union |
| 20 | QA doğruluğu | NeXT-GQA ve custom 100-sorgu |
| 20 | Ingest throughput'u | Dolar başına saat video |
| 20 | UI ve citation UX'i | Timestamp link'leri, thumbnail strip, jump-to-frame |
| 15 | Hallucination oranı | Counting ve action-type doğruluğu ayrı |
| **100** | | |

## Alıştırmalar

1. Captioning geçişinde Gemini 2.5 Pro'yu Qwen3-VL-Max ile değiştir. İnsan-derecelendirilmiş 50-sahnelik örnekte caption kalite delta'sını raporla.

2. Per-scene frame embedding'i multi-vector yerine bir pool'lanmış vektöre indirge. Retrieval regresyonunu ölç.

3. Bir "counting strict" modu inşa et: sentezleyici her sayılan instance'ı bir timestamp ile çıkarır ve kullanıcı doğrulamak için tıklar. Kullanıcı doğrulamasının hallucination'ı azaltıp azaltmadığını ölç.

4. Ingest maliyeti benchmark'la: üç VLM seçimi boyunca dolar başına saat video. Sweet spot'u seç.

5. Speaker-diarized transcript ekle: audio'da pyannote speaker diarization çalıştır ve per-speaker transcript'leri embed et. "Alice X hakkında ne dedi?" sorgularını göster.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Sahne segmentasyonu | "Shot detection" | Videoyu shot sınırlarında sahnelere kesme |
| Multi-vector index | "Caption + frame + transcript" | Gösterim başına adlandırılmış vektörlü Qdrant collection |
| Temporal grounding | "Tam olarak ne zaman oldu" | Bir sorgu yanıtı için (start, end) window'unu rafine etme |
| Frame embedding | "Visual gösterim" | Bir keyframe'in vector embedding'i; sahne-visual benzerliği için kullanılır |
| RRF fusion | "Reciprocal rank fusion" | Çoklu sıralı listeler boyunca merge stratejisi; klasik hybrid-retrieval hilesi |
| Counting hallucination | "Yanlış sayma" | "Kaç X" sorularında VLM'lerin bilinen başarısızlık modu |
| ActivityNet-QA | "Video-QA benchmark'ı" | Uzun-form video QA doğruluk benchmark'ı |

## İleri Okuma

- [AI2 Molmo 2](https://allenai.org/blog/molmo2) — açık VLM checkpoint'leri
- [TimeLens (CVPR 2026)](https://github.com/TencentARC/TimeLens) — ölçekte temporal grounding
- [Gemini Video long-context](https://deepmind.google/technologies/gemini) — hosted referans
- [VideoDB](https://videodb.io) — CRUD-for-video API referansı
- [Twelve Labs Marengo + Pegasus](https://www.twelvelabs.io) — ticari referans
- [TransNetV2](https://github.com/soCzech/TransNetV2) — sahne segmentasyon modeli
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) — klasik açık alternatif
- [ActivityNet-QA](https://arxiv.org/abs/1906.02467) — referans eval benchmark'ı
