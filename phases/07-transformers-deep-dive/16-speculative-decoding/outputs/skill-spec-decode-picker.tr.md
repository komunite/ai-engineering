---
name: spec-decode-picker
description: Yeni bir LLM çıkarım iş yükü için speculative decoding stratejisi (vanilla / Medusa / EAGLE / lookahead) ve ayar parametrelerini seç.
version: 1.0.0
phase: 7
lesson: 16
tags: [inference, decoding, latency, speculative, optimization]
---

# Speculative Decoding Seçici

Bir mühendise vanilla speculative, Medusa, EAGLE veya lookahead decoding arasında seçim yapma ve belirli bir iş yükü için `N` (draft uzunluğu) ayarlama konusunda yardım et.

## Toplanacak girdiler

1. **Doğrulayıcı model** — son çıktıyı hangi LLM üretir. Boyut önemlidir (hızlanma için draft maliyeti < doğrulayıcı maliyeti olmalı).
2. **İş yükü türü** — kod, sohbet, yapılandırılmış çıktı, özetleme. Kabul oranını belirler.
3. **Sampling stratejisi** — greedy, düşük-T, yüksek-T, beam. Yüksek-T sampling kabulü düşürür.
4. **Donanım hedefi** — bellek bütçesi ayrı bir draft modelini sığdırıp sığdıramayacağını belirler.
5. **Mühendislik bütçesi** — Medusa ve EAGLE fine-tuning gerektirir; vanilla ve lookahead gerektirmez.
6. **Gecikme hedefi** — etkileşimli sohbet (<500ms TTFT, token başına <50ms) vs batch (önce throughput).

## Karar kuralları

- **Hızlı başlangıç, eğitim yok**: aynı aileden 1B–3B modelli vanilla draft. Tipik 2×.
- **Fine-tune yapabilirsin**: doğrulayıcının hidden state'lerini kullanarak EAGLE-2 veya EAGLE-3. Tipik 3–4×.
- **Fine-tune yapabilirsin ama iki model çalıştıramazsın**: Medusa (doğrulayıcıya ekstra head'ler). 2–3×.
- **Eğitim bütçesi yok, draft model mevcut değil**: lookahead decoding. 1.3–1.6×.
- **Batch ağırlıklı sunum**: continuous batching daha önemlidir; doğrulayıcı zaten doygun olduğu için batch büyüdükçe speculative kazanımları azalır.
- **Yüksek temperature veya stokastik sampling**: kabul keskin şekilde düşer. Daha düşük N (2–3) düşün veya devre dışı bırak.
- **Yapılandırılmış çıktı (JSON, kod)**: kabul yüksektir. Maksimum hızlanma için N'i 7+'ya çıkar.

## Ayarlama

- **N (draft uzunluğu)**: 5'te başla. Kabulü ölç. α > 0.9 ise, 7'ye çıkar. α < 0.6 ise, 3'e düşür.
- **Draft temperature**: doğrulayıcının temperature'ı ile eşleştir. Uyumsuz draft sampling α'yı kaybeder.
- **Tree derinliği (EAGLE-2 / Medusa)**: 3–5 dal; daha geniş ağaçlar sadece α > 0.8'de yardımcı olur.
- **Draft model boyutu**: α > 0.7'ye ulaşan en küçük. 70B doğrulayıcı için 1B draft tipiktir; doğrulayıcının tokenizer / embedding uyumluluğunun altına inme.

## Her zaman işaretle

- Draft ve doğrulayıcının tokenizer'ı paylaştığını kontrol et. Farklı BPE bölmeleri speculative garantileri kırar.
- Spec decoding vLLM'de continuous batching ile etkileşir: batch zaten doygunken istek başına hızlanma düşer.
- EAGLE'ın hidden-state girdisi doğrulayıcı dahili yapısını gerektirir; her zaman HF API'leri üzerinden açık değildir. vLLM veya SGLang runtime'larını tercih et.
- Medusa head'leri doğrulayıcının kendi çıktıları üzerinde supervised fine-tune gerektirir. Veri toplama adımı genellikle baskın maliyettir.

## Çıktı formatı

Şunu döndür:

1. **Öneri** — bir strateji adı ve ayar parametreleri (örn. "EAGLE-2, N=5, tree_depth=4").
2. **Beklenen hızlanma** — açık α varsayımı ile.
3. **Uyumluluk kontrolleri** — tokenizer eşleşmesi, runtime desteği, KV cache rollback desteği.
4. **Fallback planı** — birincil strateji düşük performans gösterirse, sırada ne deneneceği.
5. **Ölçüm planı** — temsili bir örneklem üzerinde kabul oranı ve hızlanmayı nasıl doğrulayacağın.
