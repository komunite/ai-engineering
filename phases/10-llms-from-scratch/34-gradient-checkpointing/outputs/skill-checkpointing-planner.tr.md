---
name: checkpointing-planner
description: Bir eğitim config'i ve HBM bütçesi verildiğinde katman başına bir activation recomputation politikası seç (none / selective / full / offload).
version: 1.0.0
phase: 10
lesson: 34
tags: [gradient-checkpointing, activation-recomputation, selective-checkpoint, fsdp-offload, training-memory]
---

Eğitim config'i (katman sayısı L, hidden size d, dizi uzunluğu S, microbatch B, değer başına dtype byte, attention kernel, tensor-parallel derecesi TP, pipeline-parallel derecesi PP, MoE ise expert-parallel derecesi EP) ve ağırlıklar ile optimizer state'inden sonra rank başına HBM bütçesi verildiğinde, şunu üret:

1. Katman başına politika. Stack'teki her katman ailesi (embedding, attention, FFN, MoE expert, norm, output head) için none, selective, full veya offload seç. S 4_096'yı aştığında attention için selective varsayılan; residual stream'ler ve norm'larda none varsayılan; yalnızca o katmanın aktivasyonları için ölçülen PCIe transfer süresi ölçülen recompute süresinden az olduğunda FFN'de offload varsayılan.
2. Segment boyutu k. Full checkpointing açıksa, uniform katman maliyeti için k'yı round(sqrt(L)) seç, aktivasyon belleği bütçeye baskın olduğunda daha küçük k. Ekstra FLOP yüzdesini forward FLOP'larının (1/k)'sı olarak raporla.
3. FlashAttention etkileşimi. Attention kernel'inin softmax'i zaten recompute edip etmediğini doğrula. Evet ise, selective attention checkpointing az şey kazandırır; none'a indir. Kernel'i adıyla belirt (FlashAttention-2/3, xFormers memory-efficient, vanilla).
4. TP / PP planı. TP için, recompute'ta gather veya rescatter gerektiren aktivasyonları ve adım başına eklenen iletişim byte'larını adlandır. PP için, hangi pipeline stage'lerinin uçtan uca checkpoint'lendiğini doğrula, böylece reverse microbatch'ler geriye akmadan önce aktivasyon belleğini boşaltır.
5. Bütçe matematiği. Politika öncesi ve sonrası aktivasyon belleğini tahmin et (rank başına MB). FLOP overhead'ini fwd+bwd'nin yüzdesi olarak tahmin et. %10 boşlukla HBM bütçesine sığmayan herhangi bir planı reddet.

Selective yalnızca attention'da bütçeyi kapatıyorsa her katmanda full checkpointing'i reddet; profile aynı bellek tasarrufu için FLOP overhead'in selective'den kat kat yüksek olduğunu gösterir ve tam oran iş yüküne özgüdür. Katmanın hedef PCIe link'inde ölçülen aktivasyon transfer süresi ölçülen recompute süresini aştığında offload'u reddet; recompute kazanır. Seçilen framework amax history'yi snapshot etmediğinde FP8 eğitimi için "her yerde checkpoint"i reddet; recompute scale'i sürükler ve sessizce gradient'leri bozar.

Örnek girdi: "L=64, d=8192, S=8192, B=1, bf16, FlashAttention-3, TP=8, PP=4, ağırlıklar sonrası rank başına HBM bütçesi 32 GB, 8 expert ve EP=8 ile MoE."

Örnek çıktı:
- Katman başına politika: attention selective, FFN none, MoE expert full, embedding none, output head offload.
- Segment boyutu: full yalnızca MoE'de k=8'de uygulanır; expert yolunda %12 FLOP overhead, başka yerde 0.
- FlashAttention etkileşimi: FA-3 softmax'i zaten recompute eder; selective katman wrapper'da, kernel içinde değil.
- TP / PP planı: recompute'ta attention input'un TP gather'ı, adım başına 0.3 GB ekstra comms; PP stage'leri her biri full forward'ını checkpoint eder; PP stage 3 son backward için aktivasyonlarını tutar.
- Bütçe matematiği: politikasız 38 GB aktivasyon, politikalı 11 GB. Toplam FLOP overhead %7.5 fwd+bwd.
