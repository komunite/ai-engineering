# Watermarking — SynthID, Stable Signature, C2PA

> Üç teknoloji 2026 AI-üretimli-içerik provenance'ını yapılandırır. SynthID (Google DeepMind) — Ağustos 2023'te başlatılan image watermarking, Mayıs 2024'te text+video (Gemini + Veo), Ekim 2024'te Responsible GenAI Toolkit üzerinden text open-source, Kasım 2025'te Gemini 3 Pro ile birlikte birleşik multi-media detector. Text watermarking next-token örnekleme olasılıklarını fark edilmeyecek şekilde ayarlar; image/video watermark'lar sıkıştırma, kırpma, filtreler, frame-rate değişikliklerinde hayatta kalır. Stable Signature (Fernandez vd., ICCV 2023, arXiv:2303.15435) — her çıktının sabit bir mesaj içermesi için latent diffusion decoder'ı fine-tune eder; kırpılmış (içeriğin %10'u) üretilen görüntüler FPR<1e-6'da >%90 tespit edildi. Takip "Stable Signature is Unstable" (arXiv:2405.07145, Mayıs 2024) — fine-tuning kaliteyi korurken watermark'ı kaldırır. C2PA — kriptografik olarak imzalanmış, kurcalamaya açık metadata standardı (C2PA 2.2 Explainer 2025). Watermarking ve C2PA tamamlayıcıdır: metadata strip edilebilir ama daha zengin provenance taşır; watermark'lar transcoding boyunca devam eder ama daha az bilgi taşır.

**Tür:** Yapım
**Diller:** Python (stdlib, token-watermark embed + detect)
**Ön koşullar:** Faz 10 · 04 (sampling), Faz 01 · 09 (information theory)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Token-seviyesi watermarking'i (SynthID-text tarzı) ve onu tespit edilebilir yapan mekanizmayı tarif et.
- Stable Signature'ı ve onu kıran 2024 kaldırma saldırısını tarif et.
- C2PA'nın rolünü ve watermarking ile neden tamamlayıcı olduğunu ifade et.
- Anahtar limitleri tarif et: model-özgü sinyal, paraphrase altında sağlamlık ve anlamı koruyan saldırılar (arXiv:2508.20228).

## Sorun

2023-2024 deepfake'lerin ve AI-üretimli içeriğin politik ve tüketici bağlamlarına ölçekte girdiğini gördü. Watermarking önerilen teknik provenance sinyalidir: üretimleri oluşturma zamanında işaretle, sonra tespit et. 2025 kanıtı: hiçbir watermark koşulsuz olarak sağlam değil, ama C2PA metadata ile katmanlı, kombinasyon kullanılabilir bir provenance hikayesi sağlıyor.

## Kavram

### Text watermarking (SynthID-text tarzı)

Google tarafından üretime alınan Kirchenbauer vd. 2023 mekanizması:

1. Her decoding adımında, vocabulary'nin "yeşil" ve "kırmızı" setlere bir pseudorandom partition'ını üretmek için önceki K token'ı hash'le.
2. Yeşil logit'lere δ ekleyerek örneklemeyi yeşil sete doğru yanlandır.
3. Üretim şansın üretebileceğinden daha fazla yeşil token içerir.

Tespit: her prefix'i yeniden hash'le, üretimdeki yeşil token'ları say, bir z-score hesapla. z-score watermark'lı metin için >0, insan metni için ~0'dır.

Özellikler:
- Okuyuculara fark edilemez (δ kalite kaybı küçük olacak kadar küçüktür).
- Vocabulary partition fonksiyonuna erişimle tespit edilebilir.
- Paraphrase'e karşı sağlam değil — metni yeniden yazmak sinyali yok eder.

SynthID-text Ekim 2024'te Google'ın Responsible GenAI Toolkit'i üzerinden open-source.

### Stable Signature (image)

Fernandez vd. ICCV 2023. Her üretilen görüntünün latent temsil içine gömülmüş sabit bir ikili mesaj içermesi için latent diffusion decoder'ı fine-tune et. Tespit bir neural decoder ile latent'tan decode edilir. Kırpılmış (içeriğin %10'una) görüntüler FPR<1e-6'da >%90 tespit edildi.

Mayıs 2024 "Stable Signature is Unstable" (arXiv:2405.07145): decoder'ı fine-tune etmek image kalitesini korurken watermark'ı kaldırır. Adversarial post-generation fine-tuning ucuzdur; watermark'ın adversarial sağlamlığı sınırlıdır.

### SynthID birleşik detector (Kasım 2025)

Gemini 3 Pro ile birlikte: tek bir API'de text, image, audio ve video'dan SynthID sinyalleri okuyan bir multi-media detector. Google provenance stack'ini birleştirir.

### C2PA

Coalition for Content Provenance and Authenticity. Kriptografik olarak imzalanmış kurcalamaya açık metadata standardı. C2PA 2.2 Explainer (2025). Bir C2PA manifest provenance iddialarını (kim oluşturdu, ne zaman, hangi dönüşümler) yaratıcının anahtarıyla imzalanmış olarak kaydeder.

Watermarking'e tamamlayıcı:
- Metadata strip edilebilir; watermark'lar (kolayca) edilemez.
- Metadata zengindir (tam provenance zinciri); watermark'lar bit taşır.
- C2PA platform benimsemesine bağlıdır; watermark'lar otomatik olarak gömer.

Google ikisini de Search, Ads ve "About this image"da entegre eder.

### Limitler

- **Model-özgü.** SynthID watermark'lar SynthID-etkin modellerden üretimleri işaretler. SynthID'siz bir modelden bir üretim watermark'lı değildir, bu yüzden "SynthID sinyali yok" özgünlük kanıtı değildir.
- **Paraphrase.** Text watermark'ları anlamı koruyan paraphrase'i hayatta kalmaz.
- **Dönüşüm saldırıları.** arXiv:2508.20228 (2025) hem text watermark'larını hem de birçok image watermark'ı yok eden anlamı koruyan saldırılar gösterir.
- **Fine-tune kaldırma.** "Stable Signature is Unstable"a göre, post-generation fine-tuning gömülü watermark'ları kaldırır.

### EU AI Act Madde 50

AI-üretimli içerik etiketleme için Transparency Code (ilk taslak Aralık 2025, ikinci taslak Mart 2026, [European Commission status sayfasına](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content) göre beklenen final Haziran 2026). Code Nisan 2026 itibarıyla taslak halinde kalmaya devam ediyor ve zaman çizelgesi değişebilir. Teknik katmanı gerektiren düzenleyici katmandır. Deepfake'ler etiketlenmelidir.

### Bu Faz 18'de nereye uyuyor

Dersler 22-23 modelin ne yaydığıyla ilgilidir (özel veri, provenance sinyali). Ders 27 training-data yönetişimini kapsar. Ders 24 bu teknik önlemleri gerektiren düzenleyici çerçevedir.

## Kullan

`code/main.py` bir oyuncak text watermark'ı inşa eder. Token'lar 0..N-1 tam sayılarıdır; watermark'lı örnekleme hash-tanımlı yeşil set'e doğru yanlanır. Bir detector yeşil-token z-score'unu hesaplar. 1000-token üretimlerde tespiti gözlemleyebilir, paraphrase'in sinyali yok ettiğini izleyebilir ve insan metninde false-positive oranını ölçebilirsin.

## Yayınla

Bu ders `outputs/skill-provenance-audit.md` üretir. Provenance iddiasıyla bir content deployment'ı verildiğinde, audit eder: watermark mekanizması (varsa), C2PA imzalama zinciri (varsa), her birinin adversarial sağlamlığı ve modality-başına kapsam.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Watermark'lı 1000-token üretim vs insan-yazılı metin için z-score'ları raporla. %95 güven eşiğinde false-positive oranını tanımla.

2. Token'ların %30'unu eş anlamlılarla değiştiren bir paraphrase saldırısı uygula. z-score'u yeniden ölç.

3. Kirchenbauer vd. 2023 Bölüm 6'yı sağlamlık üzerine oku. Text watermark'ları neden paraphrase altında başarısız olur ama image watermark'ları kırpmayı hayatta kalır?

4. SynthID-text + C2PA metadata kullanan bir deployment tasarla. Tüketicinin gördüğü provenance zincirini tarif et. Her bileşenin bir failure mode'unu tanımla.

5. 2024 "Stable Signature is Unstable" sonucu fine-tuning'in image watermark'ı kaldırdığını gösterir. Bu saldırıyı sınırlayan bir deployment kontrolü tasarla — örneğin, fine-tune edilmiş checkpoint'lerin imzalı yayınlarını gerektir.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| SynthID | "Google'ın watermark'ı" | Cross-modal provenance sinyali; text, image, audio, video |
| Token watermark | "Kirchenbauer-tarzı" | Yeşil-token z-score üzerinden tespit edilebilir biased-sampling text watermark'ı |
| Stable Signature | "image watermark'ı" | Fine-tune-decoder watermark'ı; ICCV 2023 |
| C2PA | "metadata standardı" | Kriptografik olarak imzalanmış kurcalamaya açık provenance metadata |
| Paraphrase sağlamlığı | "yeniden ifadelendirme onu bozar mı" | Text watermark özelliği; şu anda sınırlı |
| Fine-tune kaldırma | "adversarial unwatermark" | Decoder fine-tuning üzerinden image watermark'ı kaldıran saldırı |
| Cross-modal detector | "birleşik SynthID" | Modaliteler arası Kasım 2025 birleşik API |

## İleri Okuma

- [Kirchenbauer et al. — A Watermark for Large Language Models (ICML 2023, arXiv:2301.10226)](https://arxiv.org/abs/2301.10226) — token-watermark mekanizması
- [Fernandez et al. — Stable Signature (ICCV 2023, arXiv:2303.15435)](https://arxiv.org/abs/2303.15435) — image watermark makalesi
- ["Stable Signature is Unstable" (arXiv:2405.07145)](https://arxiv.org/abs/2405.07145) — kaldırma saldırısı
- [Google DeepMind — SynthID](https://deepmind.google/models/synthid/) — cross-modal watermark
- [C2PA 2.2 Explainer (2025)](https://c2pa.org/specifications/specifications/2.2/explainer/Explainer.html) — metadata standardı
