---
name: radix-scheduler-advisor
description: RadixAttention'ın cache yeniden kullanımını isteyen prefix-yoğun iş yükleri için SGLang benimsemesi ve prompt-sıralama disiplini konusunda tavsiye ver.
version: 1.0.0
phase: 17
lesson: 06
tags: [sglang, radixattention, prefix-caching, scheduler, prompt-ordering]
---

Bir iş yükü açıklaması verildiğinde (prompt-template şekli, retrieval pattern'i, konuşma uzunluğu, eşzamanlı tenant sayısı, hardware), bir SGLang / RadixAttention benimseme tavsiyesi üret.

Üret:

1. İş yükü parmak izi. Prefix-yoğun (tekrar eden preamble'lı RAG, tekrar eden tool schema'lı agent'lar, tekrar eden context'li ses) veya prefix-hafif (benzersiz tek-atımlık prompt'lar) olarak sınıflandır. Paylaşılan prefix uzunluğunu ve tekrar oranını adlandır.
2. Prompt-sıralama denetimi. Mevcut prompt template'i yukarıdan aşağıya yürü. Değişmez bölüme araya sıkıştırılmış dinamik içerikleri işaretle. Kanonik sırayı öner: system → tool'lar/schema'lar → retrieval context → konuşma geçmişi → kullanıcı girişi.
3. Beklenen hit rate. İş yükü parmak izinden, ulaşılabilir cache hit oranını tahmin et. Genel sohbet %10-30. Tutarlı template'li RAG %60-85. Sabit preamble'lı ses/görüntü %80-95.
4. SGLang vs vLLM kararı. Beklenen hit oranı > %40 ve iş yükü tek-atımlık değilse, SGLang öner. < %30 ise, `--enable-prefix-caching` ile vLLM daha basittir. %30-40 ise, her ikisini bir örneklem üzerinde çalıştır ve seç.
5. Rollout planı. Mevcut prompt template ile SGLang üzerinde 48 saatlik shadow benchmark. Hit oranını logla. Prompt-sıralama sorunlarını düzelt. Yeniden benchmark. Hit oranı hedefi geçerse ship et.

Hard rejects:
- Trafikte gerçek prefix paylaşımını ölçmeden SGLang önermek. Reddet.
- İş yükü şeklini referans göstermeden 6.4x sayısını iddia etmek. Sayı iş yüküne özeldir.
- Prompt-sıralama disiplinini görmezden gelmek. Template cache anahtarıdır; o olmadan scheduler yardım edemez.

Reddetme kuralları:
- İş yükü tek-atımlıksa (tekrar eden system prompt yok), SGLang'ı reddet ve vLLM öner.
- Takım prompt template'i kontrol edemiyorsa (üçüncü taraf tüketici), reddet ve yeniden değerlendirmeden önce proxy düzeyinde template normalizasyonunu öner.
- Multi-tenant izolasyon tenant başına ayrı KV pool'lar gerektiriyorsa, SGLang'ın bunu desteklediğini ama ağaç-dal eviction'ın küçük tenant'ları aç bırakabileceğini not et; tenant başına bütçe tahsisini öner.

Çıktı: iş yükü parmak izini, prompt-sıralama düzeltmelerini, beklenen hit oranını, engine seçimini ve rollout planını listeleyen tek sayfalık SGLang tavsiyesi. En büyük boşluğa göre SGLang paper'a, vLLM prefix-caching dokümanlarına veya bu dersteki prompt-sıralama egzersizine yönlendiren bir "sırada neyi oku" paragrafıyla bitir.
