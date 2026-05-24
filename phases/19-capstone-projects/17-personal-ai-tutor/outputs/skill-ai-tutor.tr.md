---
name: ai-tutor
description: Bayesian knowledge tracing, müfredat grafiği, safety filtreleri ve ölçülmüş iki haftalık efficacy çalışmasıyla belirli bir konu için adaptif multimodal kişisel tutor gönder.
version: 1.0.0
phase: 19
lesson: 17
tags: [capstone, tutor, adaptive, bkt, fsrs, livekit, multimodal, coppa]
---

Bir konu (K-12 cebir veya Python'a giriş) verildiğinde, text + voice + photo-math girdili, Bayesian knowledge tracing learner model'li, müfredat grafiği güdümlü konsept seçimli, COPPA-aware memory'li ve safety filtreli kişisel tutor kur. 10 öğrenciyle iki haftalık efficacy çalışması çalıştır.

Build planı:

1. Neo4j'de müfredat grafiği: prerequisite edge'leri ve ekli OER içeriği (OpenStax, Open Textbook) olan 50-150 konsept node'u.
2. Learner model: konsept başına guess/slip/learn-rate prior'larıyla Bayesian knowledge tracing; öğrenci başına persist edilen state.
3. Tutor politikası (prompt caching ile Claude Sonnet 4.7 üzerinde LangGraph): read_signal -> select_concept (graph walk) -> scaffold (Sokratik) -> update_mastery.
4. Memory: agentmemory tarzı kalıcı episodic + semantic store; 1 yıl sonra COPPA-aware otomatik silme; ebeveyn-erişilebilir silme.
5. Voice: Whisper-v3-turbo ASR ve Cartesia Sonic-2 TTS'li LiveKit Agents worker; capstone 03 pipeline'ını yeniden kullan.
6. Photo math: denklem tanıma için dots.ocr veya PaliGemma 2; tutor'a yapılandırılmış girdi besle.
7. Safety: Llama Guard 4 input/output; self-harm/adult/violence bloklayan yaşa uygun filter; learner-scope'lu memory izolasyonu.
8. Öğrenci başına haftalık PDF ilerleme raporları.
9. Efficacy çalışması: 10 öğrenci, ön-test (standart 30 soruluk baseline), 2 hafta session (haftada 3), son-test; non-adaptive linear cohort'a karşı karşılaştır.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Öğrenme kazanım delta'sı | 10 öğrencili 2 haftalık çalışmada öncesi/sonrası test delta'sı |
| 20 | Sokratik sadakat | Transkript örneklerinde rubric skoru |
| 20 | Multimodal UX | Voice + photo + text uçtan uca tutarlılık |
| 20 | Safety + privacy duruşu | Llama Guard 4 geçiş oranı + COPPA-aware retention + öğrenciler arası izolasyon |
| 15 | Müfredat genişliği ve graph kalitesi | Konsept kapsamı + prerequisite graph tutarlılığı |

Sert ret durumları:

- Sıradaki soruyu sormak yerine cevap-dump eden tutor politikaları. Sokratik sert gereksinimdir.
- Etkileşim başına güncellenmeyen learner model'leri. BKT zemindir.
- COPPA-aware retention'sız memory. K-12 izleyici için kabul edilemez.
- Non-adaptive baseline cohort olmadan yapılan efficacy iddiaları.

Reddetme kuralları:

- Hem input hem output üzerinde Llama Guard 4 olmadan deploy etmeyi reddet.
- Ebeveyn-erişilebilir silme yüzeyi olmadan öğrenci verisi persist etmeyi reddet.
- Non-adaptive baseline'ı yan yana çalıştırmadan "adaptive" iddia etmeyi reddet.

Çıktı: müfredat grafiği, BKT learner model'i, LangGraph tutor politikası, multimodal input handler'ları, LiveKit voice pipeline'ı, safety pipeline'ı, ebeveyn dashboard'u, efficacy-study runner'ı, ön/son test harness'i ve güven aralıklarıyla linear baseline'a karşı öğrenme kazanım delta'sını belgeleyen bir yazımı içeren bir repo.
