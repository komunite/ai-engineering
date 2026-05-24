# Embodied VLA'lar: RT-2, OpenVLA, π0, GR00T

> Bir modelin bir web sitesinden tarif okuyup mutfak robotunda yürüttüğü ilk sefer RT-2 idi (Google DeepMind, Temmuz 2023). RT-2 eylemleri metin token'ları olarak ayrıklaştırdı, web verisi artı robot-eylem verisi üzerinde bir VLM'i co-fine-tune etti ve web-ölçek vision-language bilgisinin robotik kontrole transfer olduğunu kanıtladı. OpenVLA (Haziran 2024) açık 7B referansı gönderdi. Physical Intelligence'ın π0 serisi (2024-2025) flow-matching action expert'leri ekledi. NVIDIA'nın GR00T N1'i (Mart 2025) ölçekte humanoid robotlar için dual-system (System 1 / System 2) kontrol verdi. VLA primitive'i — vision-language-action, gören, okuyan ve eyleyen tek model — bu fazın anlama modelleri ile Faz 15'teki otonom sistemler arasındaki köprü.

**Tür:** Öğrenim
**Diller:** Python (stdlib, action tokenizer + VLA inference iskeleti)
**Ön koşullar:** Faz 12 · 05 (LLaVA), Faz 15 (Otonom Sistemler, referans)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Action tokenization'ı betimle: ayrık bin kodlaması (RT-2), FAST verimli eylem token'ları, sürekli flow-matching eylemler (π0).
- Web + robot verisi üzerinde co-fine-tuning'in neden yeni görevlere genel-bilgi transferini koruduğunu açıkla.
- OpenVLA (açık 7B Llama+VLM), π0 (flow-matching) ve GR00T N1 (dual-system)'ı aynı robot görevinde karşılaştır.
- Open X-Embodiment dataset'ini ve RT-X eğitim corpus'u olarak rolünü söyle.

## Sorun

Doğal dil instruction'larından ev işi yapan bir robot 1970'lerden beri araştırma hedefi. 2020'lerin cevabı: bir vision-language-action (VLA) modeli. VQA için kullanılan aynı VLM mimarisi, ama çıkış metin yerine eylemler (joint torque, end-effector pose, ayrık komutlar).

VLA'lara özgü zorluklar:

1. Eylem uzayları sürekli (joint açıları, kuvvetler) ve yüksek boyutlu (7-DOF kol + 3-DOF gripper = 30 Hz'de 10 dim).
2. Robot-spesifik eğitim verisi nadir. Open X-Embodiment ~1M trajectory; web text-image 5B+.
3. Kontrol frekansı önemli. 30 Hz kontrol döngüsü eylem başına 33ms bütçe demek.
4. Güvenlik. Yanlış eylem donanıma, insanlara ya da mülke zarar verir.

## Kavram

### Action tokenization (RT-2)

RT-2'nin hilesi: her joint hedefini kuantize edilmiş metin token'ı olarak temsil et. Normalize edilmiş [-1, 1] aralığını 256 bin'e ayrıklaştır, her bin'i bir vocabulary ID'ye eşle. 10-DOF eylem her kontrol adımında 10 token olur.

Bir karışım üzerinde PaLM-X VLM'i co-fine-tune et:

- Web image-text çiftleri (captioning, VQA).
- Robot demonstrasyonları, eylem token olarak.

Model "kırmızı küpü al"ı (dil) → görseli (vision) → 10-token eylem dizisini (ayrıklaştırılmış joint hedefler) görür. Web pretraining genel-bilgi transferini korur: RT-2 "hızlı hareket eden nesneye doğru hareket et"i takip edebilir, eğitim verisinde "hızlı hareket eden" olmasa bile.

VLM autoregressive decode tarafından sınırlanan RT-2 makalesinde 3-5 Hz'de çıkarım.

### OpenVLA — açık 7B referans

OpenVLA (Kim et al., Haziran 2024) açık-ağırlık RT-2 eşdeğeri. 7B Llama backbone, DINOv2 + SigLIP dual vision encoder, 256 bin üzerinde action tokenization.

Open X-Embodiment'ta eğitildi (22 robot boyunca 970k trajectory). Yeni robotlara uyarlama için LoRA fine-tuning desteği ile gönderiliyor.

Çıkarım: quantization ile A100'de 4-5 Hz. Yavaş manipülasyon için yeterli hızlı, yüksek-frekans kontrol için değil.

### FAST tokenizer — daha hızlı eylem decode

Pertsch et al. (2024) ayrık-bin tokenization'ın verimsiz olduğunu gösterdi — çoğu eylem bin-uzayının küçük bir bölgesinde kümelenir. FAST (Frequency-domain Action Sequence Tokenizer) eylem dizilerini DCT üzerinden sıkıştırır ve katsayıları kuantize eder.

30 adımlık eylem trajectory'si 300 ayrık-bin token yerine ~10 FAST token olur. Çıkarım kalite kaybı olmadan 3-5x hızlanır.

### π0 ve flow-matching eylemler

Physical Intelligence'ın π0'ı (Black et al., Ekim 2024) ayrık eylem token'larını bir flow-matching action expert ile değiştirir:

- Küçük bir eylem transformer'ı VLM'in hidden state'lerini okur ve rectified flow üzerinden sürekli 50 adımlık eylem dizisi çıkarır.
- Action head flow-matching loss ile eğitilir; VLM pretraining değişmez kalır.
- Çıkarım: tam eylem dizisi ~5 denoising adımında yayılır, efektif olarak 50 Hz kontrol.

π0'ın iddiası: geniş bir manipülasyon görev paketinde OpenVLA ve Octo'yu yener. Sürekli-eylem formülasyonu ayrıklaştırmanın yok ettiği yumuşaklığı korur.

π0.5 ve π0-FAST artımlı yükseltmeler. π0-FAST FAST tokenization'ı flow matching ile birleştirir.

### GR00T N1 — humanoid'ler için dual-system

NVIDIA'nın GR00T N1'i (Mart 2025) humanoid robotlar (>30 DOF, tam-vücut) için inşa edildi:

- System 2: sahne + instruction okuyan, ~1 Hz'de yüksek-seviye subgoal üreten büyük VLM.
- System 1: subgoal'lara koşullu düşük-seviye 50-100 Hz joint komutları üreten küçük action-head transformer.

Ayrım Kahneman'ın hızlı-ve-yavaş düşünmesine haritalanır: System 2 planlar, System 1 eyler. Faydalar: yavaş VLM-boyutu planlama hızlı kontrolü engellemez; System 1 latency için küçük kalır.

GR00T N1.7 (2025 sonları) veri ölçeklemesini iyileştiriyor. GR00T Omniverse'ten sim-to-real veriyle fine-tune ediyor.

### Open X-Embodiment

Eğitim verisi. RT-X (Ekim 2023) 22 robot boyunca 1M trajectory kapsayan 22 dataset'i birleştirdi. Open X-Embodiment herkesin kullandığı corpus:

- ALOHA / Bridge V2 / Droid / RT-2 Kitchen / Language Table.
- Her örnek: (robot durumu, kamera görünümleri, instruction, eylem dizisi).
- Eğitim hijyeni: eylem uzayını birleştir, joint aralıklarını normalize et, kameraları resize et.

OpenVLA ve π0 Open X-Embodiment'ta eğitiyor. Belirli bir robota domain farkı 100-1000 görev-spesifik demo üzerinde LoRA fine-tuning ile kapatılıyor.

### Co-fine-tuning vs yalnızca robot

Co-fine-tuning web VQA verisini robot trajectory'leri ile karıştırır. Oran önemli: çok fazla VQA ve model eylemleri unutur; çok fazla robot verisi ve model genel bilgiyi kaybeder.

RT-2'nin oranı: ~1:1. OpenVLA: ~0.5:1 web-to-robot. π0: benzer. Tam oran dataset boyutu başına tune edilecek bir hyperparameter.

Yalnızca robot eğitim out-of-distribution instruction'larda başarısız olan görev-spesifik modeller üretir. Co-fine-tuning "kırmızı küpü al (demo'da)" ile "soldan üçüncü en büyük nesneyi al (yeni ifade)" arasındaki fark.

### Güvenlik ve eylem limitleri

Her üretim VLA şunlarla gönderilir:

- Sert joint limitleri (spec'in ötesinde torque uygulayamaz).
- Velocity limitleri (soft clipping).
- Workspace sınırları (end-effector masadan ayrılamaz).
- Yeni görevler için human-in-the-loop onayı.

Bunlar VLA'nın dışında kontrol-katmanı kontrolleri olarak oturur. VLA'nın çıktısı bir öneri, komut değil.

## Kullan

`code/main.py`:

- 256-bin action tokenization ve de-tokenization uygular.
- DCT + quantization tabanlı bir FAST tokenizer çizer.
- (ayrık-bin, FAST, sürekli-flow) boyunca eylem adım başına token sayısını karşılaştırır.
- RT-2 → OpenVLA → π0 → GR00T'un bir soy özetini yazdırır.

## Yayınla

Bu ders `outputs/skill-vla-action-format-picker.md` üretir. Bir robot görevi (manipülasyon, navigasyon, humanoid tam-vücut) verildiğinde, ayrık-bin + RT-2, FAST + OpenVLA, flow-matching + π0 ya da dual-system + GR00T arasından seçer.

## Alıştırmalar

1. 30 Hz kontrol oranında 10-DOF kol. 256 bin'de ayrık-bin tokenization saniye başına kaç token yayar? 7B VLM ayak uydurabilir mi?

2. FAST tokenization 30 adımlık trajectory'leri ~10 token'a sıkıştırır. Trajectory yüksek-frekans hareket içeriyorsa (örn. davul çalmak) user neyi kaybeder?

3. π0'ın flow-matching head'i ~5 adımda denoise eder. Throughput'u OpenVLA'nın 4-5 Hz'deki autoregressive decode'una karşılaştır.

4. GR00T'un System 1 / System 2 bölünmesi Kahneman'a haritalanır. Bipedal yürümeye yardım edebilecek farklı bir bölünme (System 3?) öner.

5. Open X-Embodiment Bölüm 4'ü dataset curation üzerine oku. Domain leak'i engelleyen üç curation kuralını söyle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| VLA | "Vision-language-action" | Görsel + instruction alıp eylem komutları çıkaran model |
| Action tokenization | "Ayrık bin'ler" | Sürekli joint hedeflerini dim başına 256 bin'e kuantize et, her biri bir vocab ID |
| FAST tokenizer | "Frekans eylem token'ları" | 30 adımlık trajectory'leri ~10 token'a sıkıştırmak için DCT + quantize |
| Co-fine-tune | "Web + robot karıştır" | Genel bilgiyi korumak için robot demo'ları yanında web VQA verisi üzerinde eğit |
| Flow-matching action head | "π0 sürekli çıkış" | Rectified flow üzerinden 50 adımlık eylem dizisi çıkaran küçük transformer |
| System 1 / System 2 | "Dual-system kontrol" | Büyük VLM yavaş planlar, küçük action head hızlı eyler; GR00T kalıbı |
| Open X-Embodiment | "RT-X dataset" | 1M-trajectory cross-robot dataset; eğitim corpus'u |

## İleri Okuma

- [Brohan et al. — RT-2 (arXiv:2307.15818)](https://arxiv.org/abs/2307.15818)
- [Kim et al. — OpenVLA (arXiv:2406.09246)](https://arxiv.org/abs/2406.09246)
- [Black et al. — π0 (arXiv:2410.24164)](https://arxiv.org/abs/2410.24164)
- [NVIDIA — GR00T N1 (arXiv:2503.14734)](https://arxiv.org/abs/2503.14734)
- [Open X-Embodiment Collab — RT-X (arXiv:2310.08864)](https://arxiv.org/abs/2310.08864)
