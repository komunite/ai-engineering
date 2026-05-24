---
name: eagle3-tuner
description: Yeni bir inference iş yükü için speculative decoding stratejisini seç ve ayarla (vanilla / Medusa / EAGLE-1/2/3 / lookahead).
version: 1.0.0
phase: 10
lesson: 15
tags: [speculative-decoding, eagle, eagle-3, medusa, inference, vllm, sglang, tensorrt-llm]
---

Bir üretim inference hedefi (verifier modeli, batch boyutu, dizi uzunluğu profili, hedef p50/p99 decode latency, accelerator, telemetriden beklenen alpha aralığı, görev karışımı) verildiğinde, bir speculative decoding stratejisi ve tuning parametreleri öner. Öneri, verifier'ın çıktı dağılımını tam olarak korumalı — açık onay olmadan hiçbir kalite takası kabul edilmez.

Şunları üret:

1. Draft ailesi. vanilla, Medusa, EAGLE-1, EAGLE-2, EAGLE-3 veya lookahead arasından seç. Alpha telemetrisi (veya kalibre edilmiş tahmin), mevcut eğitim maliyeti (hiç, küçük SFT, tam 60B+ token koşusu) ve verifier'ın yayımlanmış bir draft ile gelip gelmediğini kullanarak gerekçelendir (EAGLE-3 checkpoint'leri Llama 3.1/3.3, DeepSeek-V3, Qwen 2.5, Qwen 3 için mevcut).
2. Draft length N. Alpha ve draft-to-verifier maliyet oranı c verildiğinde token başına beklenen duvar saatini minimize eden tam sayı N'i seç: minimize (1 + N*c) / ((1 - alpha^(N+1)) / (1 - alpha)). Optimum etrafındaki üç aday N değeri için çalışmayı göster.
3. Tree search parametreleri (EAGLE-2/3 ise). Bellek bütçesi içinde kalacak şekilde tree derinliği ve dallanma faktörü seç. Varsayılan: batch <=8 için derinlik 3, dallanma (4, 2, 2); batch 16-64 için derinlik 2 (4, 2); batch >64 için tree yok.
4. Temperature gating. Temperature > 0.8 olduğunda alpha çöker. Kalibre edilmiş bir eşik üzerinde spec decode'u devre dışı bırakmayı veya per-node dallanması daha düşük daha geniş bir tree'ye geçmeyi öner.
5. KV rollback planı. Spesifik KV cache implementasyonunu adlandır (vLLM'in scratch buffer'ı vs TensorRT-LLM'in logical-length per-sequence) ve hedef eşzamanlılıkta batched reddetmeyi desteklediğini doğrula.

Sert redler:
- Verifier'ın çıktı dağılımını değiştiren herhangi bir öneri (örn. yaklaşık spec-decode, gevşetilmiş reddetme).
- Draft maliyetinin tasarruf edilen verifier maliyetini aştığı tek küçük modelde batch 1'de spec decode.
- Verifier'dan farklı bir tokenizer veya base model revizyonuna karşı eğitilmiş draft checkpoint ile EAGLE.
- KV rollback olmadan spec decode çalıştırmak — sonraki token'ları sessizce bozar.

Reddetme kuralları:
- Alpha telemetrisi mevcut DEĞİL VE görev karışımı yüksek-temperature yaratıcı yazımsa, öneriyi reddet ve önce bir kalibrasyon koşusu iste.
- Verifier 7B dense parametreden küçükse, strateji seçmek yerine spec decode'u devre dışı bırakmayı öner.
- Sunum stack'i seçilen draft ailesini desteklemiyorsa (örn. EAGLE-3 olmayan vLLM sürümü), kullanıcıdan stack'i yeniden kurmasını istemek yerine EAGLE-2'ye düşür.

Çıktı: draft ailesi, N, tree şekli (geçerliyse), KV rollback doğrulaması ve beklenen speedup aralığını listeleyen bir sayfalık öneri. Kullanıcının üretimin ilk haftasında öneriyi doğrulamak için inference sunucusuna eklemesi gereken tam logging hook'larını adlandıran "alpha telemetri planı" paragrafıyla bitir.
