---
name: vllm-scheduler-reader
description: Scheduler düzeyi knob'ları okuyarak bir vLLM serving config'ini teşhis et ve PagedAttention, continuous batching ve chunked prefill arasında hangisinin darboğaz olduğunu belirle.
version: 1.0.0
phase: 17
lesson: 04
tags: [vllm, paged-attention, continuous-batching, chunked-prefill, serving, scheduler]
---

Bir vLLM serving config'i verildiğinde (model, dtype, hardware, `--gpu-memory-utilization`, `--max-num-batched-tokens`, `--enable-chunked-prefill`, `--speculative-model` veya `--speculative-config`, max eşzamanlılık ve TTFT ortalama/P99, ITL ortalama/P99, throughput tok/s gözlemlenmiş metrik seti), scheduler düzeyinde bir teşhis üret.

Üret:

1. Config okuması. Her flag için, kontrol ettiği scheduler davranışını ve 2026 varsayılanını adlandır. Varsayılan olmayan bir değere ayarlanmış flag'leri işaretle ve nedenini belirt.
2. Darboğaz tespiti. Darboğazı şunlardan biri olarak sınıflandır: PagedAttention yetersiz tahsis edilmiş (KV block açlığı), continuous-batching stall (WAITING kuyruk büyümesi), chunked-prefill yanlış boyutlandırılmış (TTFT tail spike), decode compute-bound (ITL taban), veya HBM-bound (batch sığmıyor). Raporlanan metriklerle gerekçelendir.
3. Knob önerileri. Spesifik, sıralı eylemler — hangi flag'i çevirilecek, hangi değer denenecek ve hangi metrik izlenecek. Önce scheduler düzeyi tuning tüketilmeden "daha fazla GPU dene" önerme.
4. Uyumluluk kontrolü. Özellikle vLLM v0.18.0 için: `--enable-chunked-prefill` + `--speculative-model` kombinasyonunu hard incompatibility olarak işaretle. İkisi de istenirse belgelenmiş istisna olarak V1'de N-gram GPU speculative decoding'i öner.
5. Sırada ne okunmalı. Teşhisin ortaya çıkardığına göre vLLM v0.18.0 release notes'a, PagedAttention paper'ına veya Aleksa Gordic V1 scheduler walkthrough'una yönlendir.

Hard rejects:
- Dört temel metrik (TTFT, ITL, throughput, eşzamanlılık) olmadan teşhis koymak. Reddet ve metrik setini iste.
- Speculative decoding config'ini kontrol etmeden `--enable-chunked-prefill` önermek.
- `DCGM_FI_DEV_GPU_UTIL`'i scaling sinyali olarak görmek. vLLM KV'yi önceden tahsis eder; duty-cycle sayıları yanıltıcıdır.

Reddetme kuralları:
- Raporlanan throughput bir H100'de 100 tok/s altındaysa, darboğaz muhtemelen vLLM değildir — client tarafında tokenizer, Python GIL veya request düzeyi serileştirme kontrol et.
- `--gpu-memory-utilization` 0.7 altına ayarlanmışsa, daha fazla tuning yapmayı reddet — operatör HBM'yi masada bırakmayı seçmiş ve fix, scheduler flag'lerini çevirmeden önce tavanı yükseltmektir.
- Operatör draft-model speculation üzerinde speculative-decoding + chunked-prefill tarifi isterse, reddet ve v0.18.0 uyumsuzluğunu adlandır. Bunun yerine Phase 17 · 05'teki EAGLE-3'e yönlendir.

Çıktı: flag'leri, darboğazı, sıralı önerileri, uyumluluk notlarını ve sırada-okunacak işaretçiyi listeleyen tek sayfalık scheduler teşhisi. Tespit edilen darboğaza göre P99 ITL, block tahsis hızı veya WAITING queue depth'ten birini adlandıran bir "sırada neyi ölç" paragrafıyla bitir.
