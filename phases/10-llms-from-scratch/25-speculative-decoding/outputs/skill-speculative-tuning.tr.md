---
name: speculative-tuning
description: Bir decode iş yükünü profille ve speculative decoding için draft modeli, draft length K, temperature gate ve fallback politikası seç.
version: 1.0.0
phase: 10
lesson: 25
tags: [speculative-decoding, draft-model, alpha, throughput, inference, decode-latency]
---

Hedef model (boyut, aile, tokenizer), iş yükü telemetrisi (görev karışımı, prompt-vs-decode token oranı, p50/p99 decode latency, accelerator ve HBM boşluğu, ortalama batch boyutu, sampling temperature dağılımı) ve mevcut draft checkpoint'leri verildiğinde, şunu üret:

1. Draft seçimi. Aynı aile küçük (Llama-70B için Llama-3.2-1B), distilled draft (Qwen3-0.6B-spec), hedefe bolt-on edilmiş Medusa head'ler veya yüzde 30 FLOP maliyet oranından daha yakın bir draft yoksa "spec decode yok" arasından seç. Tokenizer eşleşmesini hedefe karşı byte-byte doğrula; uyumsuz bir tokenizer'ı reddet.
2. Draft length K. E[tokens] / (1 + K x c) argmax'ı (c, draft-to-target maliyet oranı). 5_000 token in-distribution veri üzerinde bir kalibrasyon koşusundan ölçülen alpha kullanarak K = 2, 3, 4, 5, 6 için çalışmayı göster. Varsayılan chat için K=4, kod için K=6, yüksek-temperature yaratıcı yazım için K=2.
3. Temperature gate. Spec decode'un devre dışı bırakıldığı bir temperature eşiği ayarla. Varsayılan 0.8; kalibrasyon alpha'nın daha erken çöktüğünü gösterirse 0.6'ya düşür. 50 mikrosaniyeden fazla ekleyen per-request inceleme gerektiren herhangi bir temperature gate'i reddet.
4. Tree bütçesi. Sunum stack'i tree drafting'i destekliyorsa, batch 8 altı için küçük sabit tree (derinlik 2, branch 3-2) seç; batch 32 üstü için düz chain. Verifier'ın KV scratch boyutunu byte olarak belirt ve HBM boşluğuna sığdığını doğrula.
5. Fallback politikası. Metriği (son 1_000 verify üzerinde sliding-window ölçülen alpha) ve sunucunun o request stream'i için plain autoregressive decode'a geri düştüğü eşiği (alpha 0.4 altında) adlandır. Fallback kararının per-request ömrünü dahil et.

Verifier compute-bound olduğu noktanın üzerindeki batch boyutunda spec decode'u reddet. Bu noktanın üzerinde speculator'un emmesi gereken kullanılmayan FLOP'lar artık yok; throughput düşer. Ölçülen alpha 0.4 altındaki herhangi bir görev ailesi için spec decode'u reddet; draft overhead baskın olur ve duvar saati latency kötüleşir. Hedefe karşı tutulan 1_000 token örnekte doğrulanmamış bir draft'ı reddet: doğrulanmamış bir draft sessiz bir KL drift'tir.

Örnek girdi: "8xH100 üzerinde Llama-3.3-70B, chat iş yükü, batch 16, p50 decode 28 ms, p99 60 ms, temperature dağılımı ortalama 0.4 / max 1.2, kalibrasyon chat'te alpha 0.78, kodda 0.61 gösteriyor."

Örnek çıktı:
- Draft: Llama-3.2-1B-Instruct-spec. Aynı tokenizer, aynı aile, oran c yaklaşık 0.03.
- K: 4. E[tokens/verify] = chat'te 3.4, kodda 2.5. K=5 chat'te 0.1 token kazandırır ve 0.03 ekstra c öder; reddet.
- Temperature gate: 0.8. 0.8 üzerinde kalibrasyon setinde alpha 0.45 altına düşer.
- Tree bütçesi: derinlik 2 branch (3, 2). Batch 16'da 480 MB KV scratch sığar.
- Fallback: son 1_000 verify üzerinde sliding-window alpha 0.40 altında 30 saniye için o stream'de spec decode'u devre dışı bırakır, sonra tekrar yoklar.
