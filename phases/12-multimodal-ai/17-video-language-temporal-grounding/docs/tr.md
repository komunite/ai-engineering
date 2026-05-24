# Video-Language Modelleri: Temporal Token'lar ve Grounding

> Video bir fotoğraf yığını değil. 5 saniyelik bir klibin bir görsel modelinin temsil edemeyeceği causal sıralaması, eylem fiilleri ve olay zamanlaması var. Video-LLaMA (Zhang et al., Haziran 2023) ses-görsel grounding ile ilk açık video-LLM'i gönderdi. VideoChat ve Video-LLaVA kalıbı ölçekledi. 2025'e kadar Qwen2.5-VL'in TMRoPE'si frontier proprietary modellerle farkı kapattı. Her sistem temporal token'ları farklı çözdü — klip başına Q-former, frame başına concat-pool, token başına TMRoPE. Bu ders kalıpları okur, uniform-vs-dynamic bir frame sampler inşa eder ve temporal grounding görevlerinde değerlendirir.

**Tür:** Yapım
**Diller:** Python (stdlib, frame sampler + temporal-grounding değerlendirici)
**Ön koşullar:** Faz 12 · 08 (LLaVA-OneVision)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Temporal positional encoding'in vision encoder'dan bağımsız olarak video VLM performansını neden değiştirdiğini açıkla.
- Uniform, dynamic-FPS ve event-driven frame sampling'i saniye başına token vs grounding doğruluğunda karşılaştır.
- Q-former-per-clip (Video-LLaMA) vs pooled-per-frame (Video-LLaVA) vs M-RoPE-per-token (Qwen2.5-VL) tasarımlarını betimle.
- Dört video benchmark'ını söyle: VideoMME, TempCompass, EgoSchema, Video-MMMU.

## Sorun

30 FPS'te 1 dakikalık video 1800 frame. Frame başına 196 görsel token'da (224'te ViT-B) bu 352k token — herhangi 2024-çağı LLM context'inden büyük.

Üç azaltma stratejisi var:

1. Frame'leri alt-örnekle (içeriğe bağlı olarak 1-8 FPS).
2. Her frame'in patch token'larını agresif pool'la (3x3 ya da 4x4 bilinear pool).
3. 16 frame klip alıp 64 token çıkaran bir Q-former üzerinden sıkıştır.

Her trade-off farklı. Subsampling temporal detayı kaybeder. Pooling spatial detayı kaybeder. Q-former ikisinden de biraz kaybeder ama token tasarrufu sağlar.

Temporal pozisyon kodlaması diğer eksen: model frame 5'in frame 6'dan önce geldiğini nasıl bilir? Seçenekler basit 1D temporal RoPE (Video-LLaMA), öğrenilmiş temporal embedding'ler (Video-LLaVA) ve TMRoPE (Qwen2.5-VL, tam 3D).

## Kavram

### Video-LLaMA: klip başına Q-former + ses dalı

Video-LLaMA (2023) ilk açık video-LLM'di. Mimari:

- 2 FPS'te 16 frame klip (yani 8 saniye).
- Frame başına ViT feature'ları -> tüm 16 frame üzerinde cross-attend eden Video Q-former -> 32 öğrenilmiş query -> LLM.
- Paralel ses dalı: waveform -> ImageBind ses encoder'ı -> Audio Q-former -> 32 query -> LLM.

Güç: ses-görsel joint akıl yürütme. Zayıflık: sabit klip uzunluğu, keyfi zaman grounding yok.

### VideoChat ve Video-LLaVA

VideoChat Video-LLaMA fikrini tuttu ama sesi düşürdü ve basitleştirdi. Video-LLaVA (Lin et al., 2023) hem görseller hem video frame'leri üzerinde tek görsel encoder eğitti ("alignment before projection"), birleştirilmiş bir temsil verdi. İkisi de donmuş-CLIP-encoder + MLP + LLM.

Hiçbiri uzun video ele almıyor. İkisi de 8-16 frame sistemleri.

### Qwen2.5-VL ve TMRoPE

Qwen2.5-VL TMRoPE'yi tanıttı — Temporal-Modality Rotary Position Embedding. Her patch token'ı, t'nin gerçek timestamp olduğu (frame indeksi değil) (t, h, w) pozisyonunu taşır.

Basit temporal embedding'den anahtar farklar:

- Mutlak zaman, indeks değil. Model "4.2 saniyede" görür, "frame 15'te" değil.
- Klip başına değil, token başına rotasyon. Her görsel token timestamp'ine göre bağımsız döner.
- Dinamik FPS ile uyumlu. Burada 2 FPS'te ve orada 4 FPS'te örnek alırsan, TMRoPE eşit olmayan aralığı natively halleder.

TMRoPE "kedi kaç saniyede zıplıyor?" sorgularını mümkün kılar. Model "4.2 saniyede" çıkarabilir. Video-LLaMA yalnızca "klibin başlarında" diyebilirdi.

### Frame sampling stratejileri

Uniform: süre üzerinde eşit N frame örnek al. Basit, hareket zirvelerini kaybeder.

Dynamic FPS: hareket yoğunluğuna göre adaptif örnek al. Optical flow ya da frame differencing yoğun örnekleme için yüksek-hareket segmentleri seçer. Qwen2.5-VL bunda eğitir.

Event-driven: hafif bir detector çalıştır, aksiyon olduğu yerden daha çok örnekle. VideoAgent tarafından kullanılır.

Keyframe + context: shot sınırlarında + birkaç komşu frame'de örnek al. Sinematik içerik için kullanılır.

### Frame başına pooling

1 FPS ve frame başına 576 token'da 5 dakikalık klip 172,800 token. Qwen2.5-VL-72B'nin 128k context'i ile yapılabilir ama pahalı.

3x3 bilinear pool frame başına 64 token'a azaltır -> 5 dakika için 19,200 token. Çoğu görev için tatlı nokta.

Spatial detayın daha az önemli olduğu agent workflow'ları için daha agresif pool (6x6 -> frame başına 16 token).

### Dört video benchmark'ı

- VideoMME: kapsamlı video anlama, kısa + orta + uzun.
- TempCompass: ince taneli temporal akıl yürütme, "önce" / "sonra" soruları.
- EgoSchema: uzun-ufuklu birinci-şahıs video.
- Video-MMMU: multimodal multi-disipline video soruları.

Tam bir video-VLM değerlendirmesi dördüne de vurur. Farklı eksenleri stres yaparlar — TempCompass tamamen sıralamayla ilgili, EgoSchema 3+ dakika akıl yürütme hakkında, VideoMME süreleri kapsar.

### Grounding çıkış formatları

Temporal grounding için çıkış formatları:

- Serbest metin: "Kedi 4 saniye işareti civarında zıplar." Ayrıştırması kolay ama belirsiz.
- Yapılandırılmış JSON: `{"event": "jump", "start": 4.1, "end": 4.3}`. Qwen2.5-VL bunu eğitir.
- Token tabanlı: cevapla interleave edilmiş özel `<time>4.1</time>` token'ları. Qwen2.5-VL'in iç formatı.

Token tabanlı aşağı akış kullanım için en doğru. Qwen2.5-VL'in JSON çıkış formatı doğrudan ayrıştırır.

### 2026 best practice

2026'da video VLM'ler için:

- Encoder: M-RoPE ya da TMRoPE ile SigLIP 2 (Qwen2.5-VL).
- Frame sampling: max-frame cap'li dynamic FPS (harekete bağlı 1-4).
- Frame başına pooling: 3x3 bilinear.
- Çıkış: zaman + olay alanlarıyla yapılandırılmış JSON.
- Benchmark'lar: genel için VideoMME + TempCompass; uzun-ufuk için EgoSchema.

## Kullan

`code/main.py` şunları içerir:

- Uniform ve dynamic-FPS frame sampler'lar.
- Bir oyuncak temporal-grounding değerlendiricisi: zaman T'de "ground truth" olay ve model çıktısı verildiğinde, toleransla doğruluk skorla.
- Video-LLaMA (16 frame, Q-former), Video-LLaVA (8 frame, MLP), Qwen2.5-VL (dynamic FPS + TMRoPE) arası karşılaştırma.

## Yayınla

Bu ders `outputs/skill-video-vlm-frame-planner.md` üretir. Bir video görevi (izleme, action recognition, temporal grounding, summarization) verildiğinde, frame sampler, pooling faktörü, çıkış formatı ve beklenen doğruluk katmanı seçer.

## Alıştırmalar

1. 3 dakikalık yemek demosu için uniform vs dynamic FPS seç. Bir token sayısı ile haklı çıkar.

2. TMRoPE basit bir temporal embedding tablosunun yapamadığı tam olarak neyi ekler?

3. Bir VLM'in yaymayı öğrenebileceği temporal grounding için bir JSON şeması yaz. Hata durumlarını dahil et.

4. Video-LLaVA'nın "Alignment Before Projection" üzerine Bölüm 3'ünü oku. Bu neden ayrı görsel ve video encoder eğitmekten daha iyi?

5. VideoMME liderlik tablosu verildiğinde, 2026 itibariyle üst açık model ile üst proprietary model arasındaki fark nedir? Bu farkın ne kadarı temporal encoding'e vs base LLM ölçeğine atfedilebilir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Temporal grounding | "Zaman-yerelleşmiş cevaplar" | VLM bir olayın ne zaman olduğu için spesifik timestamp aralığı çıkarır |
| TMRoPE | "Time-Multimodal RoPE" | Mutlak timestamp'lerle 3D rotary position, Qwen2.5-VL tarafından kullanılır |
| Dynamic FPS | "Motion-aware sampling" | Yüksek-hareket segmentlerinde daha çok frame örnek al, statik olanlarda daha az |
| Frame pooling | "Frame başına spatial sıkıştırma" | LLM'den önce bilinear interpolation ile frame başına patch'leri azalt |
| Video Q-former | "Klip sıkıştırıcı" | N frame'i K öğrenilmiş query'ye eşleyen cross-attention bottleneck |
| VideoMME | "Video bench" | Kapsamlı kısa/orta/uzun video benchmark'ı, 2500+ örnek |

## İleri Okuma

- [Zhang et al. — Video-LLaMA (arXiv:2306.02858)](https://arxiv.org/abs/2306.02858)
- [Li et al. — VideoChat (arXiv:2305.06355)](https://arxiv.org/abs/2305.06355)
- [Lin et al. — Video-LLaVA (arXiv:2311.10122)](https://arxiv.org/abs/2311.10122)
- [Qwen Team — Qwen2.5-VL (arXiv:2502.13923)](https://arxiv.org/abs/2502.13923)
- [Lin et al. — VILA-1.5 (arXiv:2312.07533)](https://arxiv.org/abs/2312.07533)
