# Capstone 17 — Kişisel AI Tutor (Adaptive, Multimodal, Memory'li)

> Khanmigo (Khan Academy), Duolingo Max, Google LearnLM / Gemini for Education, Quizlet Q-Chat ve Synthesis Tutor — hepsi 2026'da ölçekte adaptive multimodal tutoring yayınladı. Ortak şekil bir Sokratik policy (asla sadece cevabı dökme), her etkileşimden sonra güncellenen bir learner model (Bayesian knowledge tracing tarzı), voice + text + photo-math input, curriculum graph retrieval, spaced-repetition scheduling ve yaş-uygun içerik için sert safety filtreleri. Capstone, konu-spesifik bir tutor (K-12 cebir veya intro Python) yayınlamak, 10 öğrenciyle iki haftalık bir efficacy çalışması çalıştırmak ve bir content-safety denetimini geçmek.

**Tür:** Bitirme
**Diller:** Python (backend, learner model), TypeScript (web app), SQL (Postgres + Neo4j üzerinden curriculum graph)
**Ön koşullar:** Faz 5 (NLP), Faz 6 (speech), Faz 11 (LLM engineering), Faz 12 (multimodal), Faz 14 (agent'lar), Faz 17 (infrastructure), Faz 18 (safety)
**Egzersize edilen fazlar:** P5 · P6 · P11 · P12 · P14 · P17 · P18
**Süre:** 30 saat

## Sorun

Adaptive tutoring eskiden ed-tech araştırma niş'iydi. 2026'ya geldiğinde bir tüketici ürünü. Khanmigo çoğu US okul bölgesi boyunca deploy edildi. Duolingo Max on milyonlarca MAU'ya ulaştı. Google'ın LearnLM / Gemini for Education'ı Google Classroom'da tutoring'i besler. Quizlet Q-Chat flashcard'ların yanında oturuyor. Synthesis Tutor meraklı-çocuklar-için-tutor olarak virality vurdu. Ortak elementler: multimodal input (yaz, konuş, denklemleri fotoğrafla), Sokratik pedagoji (önce sor, sonra açıkla), her etkileşimden sonra güncellenen bir learner model ve sıkı yaş-uygun safety.

Belirli bir cohort için bunlardan birini inşa edeceksin. Ölçüm çıtası gerçek bir efficacy çalışması: 10 öğrenciyle iki hafta üzerinde pre-test ve post-test skorları. Voice loop doğal hissetmeli (capstone 03 sub-stack'i). Memory privacy'ye saygılı olmalı. Safety filter K-12 için COPPA-aware red-team'i geçmeli.

## Kavram

Dört bileşen. **Tutor policy'si** Sokratik bir loop: öğrenci cevabı sorduğunda, policy yönlendirici bir soru sorar; doğru aldığında, sonraki konsepte geçer; takıldıklarında, scaffold'lanmış bir ipucu sunar. **Learner model** her etkileşimden sonra curriculum node başına mastery olasılığını güncelleyen Bayesian knowledge tracing (veya basit bir varyantı). **Curriculum graph** prerequisite kenarlarıyla konseptlerin Neo4j'i; policy sonraki konsepti seçmek için graph'ı yürür. **Memory** geçmiş etkileşimleri, hataları ve tercihleri tutan bir episodic + semantic store (agentmemory-tarzı).

UX multimodal. Yazılı cevaplar için text input. LiveKit + Whisper üzerinden voice input (capstone 03'ü yeniden kullan). Math problemleri için dots.ocr veya PaliGemma 2 üzerinden photo input. Cartesia Sonic-2 üzerinden voice output. Safety Llama Guard 4 artı bir yaş-uygun filter (yetişkin içerik, şiddet, self-harm'i bloklar) ve bir COPPA-aware memory retention policy'si kullanır.

Efficacy çalışması teslimat. 10 öğrenci, pre-test ve post-test, iki hafta. Learning gain delta'sını ve confidence interval'ını raporla. Non-adaptive bir baseline'a (aynı içerik tutor policy'si olmadan lineer olarak teslim edilmiş) karşı karşılaştır.

## Mimari

```
öğrenci cihazı
  |
  +-- text         -> web app
  +-- voice        -> LiveKit Agents (ASR + TTS)
  +-- photo math   -> dots.ocr / PaliGemma 2
       |
       v
  tutor policy (LangGraph)
       - Sokratik decision head
       - next-concept chooser (curriculum graph walk)
       - hint scaffolder
       - mastery update
       |
       v
  learner model (BKT / item-response theory)
       - per-concept mastery olasılığı
       - spaced-repetition scheduler (SM-2 veya FSRS)
       |
       v
  memory (agentmemory-tarzı)
       - episodic: her etkileşim
       - semantic: öğrenilmiş hatalar, tercihler
       - retention policy: COPPA / GDPR aware
       |
       v
  curriculum graph (Neo4j)
       - prerequisite kenarlar
       - eklenmiş OER içerik
       |
       v
  safety:
    Llama Guard 4 + yaş-uygun filter
    learner ID scope'uyla korunan memory erişimi
```

## Stack

- Konu seçimi: K-12 cebir veya intro Python (derinlik için birini seç)
- Tutor policy'si: Claude Sonnet 4.7 üzerinden LangGraph (prompt caching'li)
- Learner model: Bayesian knowledge tracing (klasik) veya spacing için FSRS
- Curriculum graph: konseptlerin + prerequisite kenarların + OER içeriğin Neo4j'i
- Memory: agentmemory-tarzı kalıcı vector + episodic + semantic store
- Voice: LiveKit Agents 1.0 + Cartesia Sonic-2 (capstone 03 sub-stack'ini yeniden kullan)
- Photo math: denklem tanıma için dots.ocr veya PaliGemma 2
- Safety: Llama Guard 4 + custom yaş-uygun filter
- Eval: Bloom-seviyesi soru üretimi, pre/post test harness'ı, efficacy çalışma tooling'i

## İnşa Et

1. **Curriculum graph.** Prerequisite kenarlarla 50-150 konsept node'lu bir Neo4j inşa et (örn. "sayı doğrusu"ndan "quadratic formula"ya K-12 cebir). Node başına OER içerik ekle (Open Textbook, OpenStax).

2. **Learner model.** Bayesian knowledge tracing'i prior'larla initialize et: guess, slip, learn-rate. Her etkileşimden sonra per-concept mastery'yi güncelle. Öğrenci başına persist et.

3. **Tutor policy'si.** Node'larla LangGraph: `read_signal` (öğrencinin cevabı doğru / kısmi / takılmış mıydı?), `select_concept` (en yüksek-öncelikli konsepti seçen curriculum graph walk), `scaffold` (Sokratik prompt), `update_mastery`.

4. **Memory.** Her etkileşim bir episodic store'a yazar. Hatalar ve tercihler semantic memory'ye promote edilir. COPPA-aware retention policy: 1 yıl sonra auto-delete, ebeveyn-erişilebilir.

5. **Voice path.** Tutor policy'sine bağlı LiveKit Agents worker'ı. Whisper-v3-turbo üzerinden ASR. Cartesia Sonic-2 üzerinden TTS. Barge-in destekli (capstone 03 mekaniklerini yeniden kullan).

6. **Photo-math path.** Görüntü yükle veya yakala; denklemi tanımak için dots.ocr veya PaliGemma 2 çalıştır; yapılı input olarak tutor'a besle.

7. **Safety.** Her model çıktısı Llama Guard 4 + yaş-uygun filter'dan geçer (self-harm, yetişkin içerik, şiddet'i bloklar). Memory erişimi learner ID ile scoped; silme için ebeveyn erişim yüzeyi.

8. **Efficacy çalışması.** 10 öğrenci, pre-test (standartlaştırılmış 30-soruluk baseline), iki haftalık tutor etkileşimi (haftada 3 oturum), post-test. Aynı içerikte non-adaptive 10-öğrencilik baseline cohort'a karşı karşılaştır.

9. **Haftalık ilerleme raporları.** Öğrenci başına, explore edilen konuların, mastery yörüngelerinin ve önerilen sonraki adımların PDF özetini auto-üret.

## Kullan

```
öğrenci: "3x + 6 = 12'nin neden x = 2 anlamına geldiğini anlamıyorum"
[signal]   takılmış
[concept]  'değişkenleri izole etme' (prerequisite: toplama-çıkarma-eşitlik)
[scaffold] "başlamak için her iki taraftan hangi sayıyı çıkarırsın?"
öğrenci: "6"
[signal]   doğru
[mastery]  toplama-çıkarma-eşitlik: 0.62 -> 0.77
[concept]  'değişkenleri izole etme'ye devam et
[scaffold] "harika. şimdi 3x / 3 neye eşit?"
```

## Yayınla

Teslimat `outputs/skill-ai-tutor.md`. Multimodal input, learner model, memory, safety ve ölçülen efficacy'li konu-spesifik adaptive tutor.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Learning gain delta'sı | 10-öğrencilik iki-haftalık çalışmada pre/post-test delta |
| 20 | Sokratik fidelity | Transcript örneklerinde rubrik skoru |
| 20 | Multimodal UX | Voice + photo + text uçtan uca tutarlılığı |
| 20 | Safety + privacy postürü | Llama Guard 4 pass oranı + COPPA-aware retention |
| 15 | Curriculum genişliği ve graph kalitesi | Konsept kapsamı + prerequisite graph tutarlılığı |
| **100** | | |

## Alıştırmalar

1. Efficacy çalışmasını adaptive learner model'iyle ve onsuz (random konsept sırası) çalıştır. Delta'yı raporla. Adaptive'in kazanmasını bekle, ama boyutu ilgi çekici sayı.

2. Multimodal probe ekle: aynı konsept sorusu text, voice ve photo olarak teslim edilir. Öğrencilerin tercih ettikleri modalite ile daha hızlı yakınsayıp yakınsamadığını ölç.

3. Ebeveyn dashboard'u inşa et: practice edilen konular, mastery yörüngeleri, yaklaşan konseptler, safety event'leri (herhangi bir guardrail hit'i). COPPA-aligned.

4. Bir dil-değiştir modu ekle: tutor İspanyolca input kabul eder ve İspanyolca öğretir. X-Guard kapsamını ölç.

5. Memory privacy'sini stress et: öğrenci A'nın bir voice-clip yeniden-ingest saldırısı üzerinden bile öğrenci B'nin verisini göremeyeceğini doğrula. Denenen erişimi logla ve alert ver.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Sokratik policy | "Sor, dökme" | Tutor cevap vermek yerine yönlendirici bir soru sorar |
| Bayesian knowledge tracing | "BKT" | Konsept başına mastery olasılığı için klasik learner-model denklemleri |
| FSRS | "Free Spaced Repetition Scheduler" | 2024 spaced-repetition scheduler'ı, SM-2'den daha iyi |
| Curriculum graph | "Concept DAG'ı" | Prerequisite kenarlarıyla konseptlerin Neo4j'i |
| Episodic memory | "Per-interaction log'u" | Her etkileşim sonradan retrieve için saklanır |
| Semantic memory | "Öğrenilmiş pattern store'u" | Episodic'ten promote edilen sıkıştırılmış hatalar ve tercihler |
| COPPA | "Çocuk privacy yasası" | 13 yaş altı çocuklardan veri toplamayı kısıtlayan US yasası |

## İleri Okuma

- [Khanmigo (Khan Academy)](https://www.khanmigo.ai) — referans tüketici K-12 tutor'ı
- [Duolingo Max](https://blog.duolingo.com/duolingo-max/) — referans dil-öğrenme tutor'ı
- [Google LearnLM / Gemini for Education](https://blog.google/technology/google-deepmind/learnlm) — hosted referans modeli
- [Quizlet Q-Chat](https://quizlet.com) — alternatif referans
- [Synthesis Tutor](https://www.synthesis.com) — startup referansı
- [FSRS algoritması](https://github.com/open-spaced-repetition/fsrs4anki) — spaced-repetition scheduler'ı
- [Bayesian Knowledge Tracing](https://en.wikipedia.org/wiki/Bayesian_knowledge_tracing) — learner-model klasiği
- [LiveKit Agents](https://github.com/livekit/agents) — voice stack'i
