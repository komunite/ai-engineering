---
name: dualpipe-planner
description: Bir eğitim cluster'ı için pipeline parallelism stratejisi planla (1F1B, Zero Bubble, DualPipe, DualPipeV).
version: 1.0.0
phase: 10
lesson: 19
tags: [pipeline-parallelism, dualpipe, dualpipev, zero-bubble, expert-parallelism, distributed-training]
---

Bir eğitim cluster spesifikasyonu (toplam GPU sayısı, interconnect topolojisi, accelerator modeli, GPU başına bellek), bir model şekli (toplam params, aktif params, MoE veya dense, beklenen katman sayısı) ve hedef eğitim-veri hacmi verildiğinde, bir pipeline parallelism stratejisi öner ve beklenen bubble oranını doğrula.

Şunları üret:

1. Pipeline derinliği P. GPU bellek bütçesine (rank başına bir pipeline stage sığmalı), MoE vs dense ve interconnect bant genişliğine göre seç. Aralık: küçük cluster'lar için 4, frontier MoE eğitimi için 16-32.
2. Micro-batch sayısı M. DualPipe ve DualPipeV için 2'ye bölünebilir olmalı. Tipik M/P oranı 8-16 arası. Gradient-accumulation hedefleri ve hedef dizi uzunluğunda aktivasyon belleğine karşı gerekçelendir.
3. Schedule seçimi. 1F1B, Zero Bubble, DualPipe, DualPipeV arasından seç. Karar tablosu: 500 GPU altında dense eğitim -> Zero Bubble. Expert parallelism ile MoE -> DualPipe. Ağır all-to-all olmayan 500 GPU üstü dense eğitim -> DualPipeV. 100 GPU altı küçük koşular -> 1F1B uygundur.
4. Beklenen bubble oranı. Hedef P ve M'de seçilen schedule için hesapla. Yüzde olarak ve toplam eğitim bütçesinde 1F1B'ye karşı tasarruf edilen mutlak GPU-saati olarak raporla.
5. Parametre replikasyon planı (yalnızca DualPipe). 2x parametre replikasyonunun mevcut VRAM'e sığdığını doğrula. Seçilen P verildiğinde GPU başına effective parametre yoğunluğunu raporla.

Sert redler:
- Expert Parallelism olmadan DualPipe. Saklanacak EP-ağır comms olmadan 2x replikasyon haklı değil.
- Herhangi bir eğitim koşusunda P > 64. Bubble oranı schedule ne olursa olsun P ile doğrusal büyür.
- DualPipe/DualPipeV için 2'ye bölünemeyen micro-batch sayısı. Schedule kapanmaz.
- Model tek GPU'nun belleğine sığdığında hiç pipeline parallelism. Yalnızca data parallelism kullan.

Reddetme kuralları:
- Interconnect GPU başına 200Gbps veya daha yavaşsa, DualPipe'ı reddet ve DualPipeV öner. All-to-all overlap penceresi replikasyonu haklı çıkarmak için çok dar.
- Kullanıcı cluster topolojisi için uygun custom all-to-all kernel sağlayamıyorsa, DualPipe yerine Zero Bubble öner.
- Eğitim koşusu 1B token altındaysa, pipeline parallelism planlamayı tamamen reddet ve data parallelism artı tensor parallelism öner.

Çıktı: P, M, schedule, beklenen bubble oranı, parametre replikasyon maliyeti (DualPipe ise) ve all-to-all kernel önerisi listeleyen bir sayfalık plan. Hedef sayıya ulaşılmazsa daha basit bir schedule'a geçmeyi haklı çıkaracak spesifik utilization metriğini (ilk 1000 adımda ölçülen toplam GPU utilization yüzdesi) adlandıran "rollback tetikleyici" paragrafıyla bitir.
