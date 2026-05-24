# LLaVA-OneVision: Tek Görsel, Çoklu Görsel, Video Tek Modelde

> LLaVA-OneVision'dan önce (Li et al., Ağustos 2024) open-VLM dünyasının ayrı soyları vardı: tek görseller için LLaVA-1.5, Mantis ve VILA gibi çoklu görsel modelleri, Video-LLaVA ve Video-LLaMA gibi video modelleri. Her biri kendi benchmark'ını kazandı ve diğerlerinde başarısız oldu. LLaVA-OneVision tek bir müfredatın tek modeli üç senaryonun hepsine hakim olacak şekilde eğitebileceğini ve emergent görev-transferi etkilerinin (tek-görsel becerileri videoya aktarıldı, çoklu-görsel akıl yürütme tek görsele aktarıldı) uzmanların toplamını yendiğini savundu. Tarif aldatıcı şekilde basit: senaryolar boyunca sabit kalan bir görsel-token bütçesi, artı tek-görselden OneVision'a (çoklu görsel) videoya hareket eden açık bir müfredat. Bu ders bütçeyi, müfredatı ve emergent davranışları okur.

**Tür:** Yapım
**Diller:** Python (stdlib, token bütçe çözücü + müfredat planlayıcı)
**Ön koşullar:** Faz 12 · 05 (LLaVA), Faz 12 · 06 (any-resolution)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Tek görsel, çoklu görsel ve video input'ları boyunca sabit kalan bir görsel-token bütçesi tasarla.
- Becerileri tek görselden videoya catastrophic forgetting olmadan aktaran bir eğitim müfredatı sırala.
- Müfredat doğru yapıldığında tek modelin aynı parametre sayısında uzmanları neden yendiğini açıkla.
- LLaVA-OneVision'ın raporladığı üç emergent yeteneği söyle: multi-camera akıl yürütme, set-of-mark prompting, iPhone-ekran görüntüsü agent'ı.

## Sorun

Görsel, çoklu görsel ve video modeli farklı şekilde stresliyor.

Tek görsel OCR ve ince detayı yakalamak için yüksek-çözünürlüklü token'lar ister (AnyRes, ~2880 görsel token). Örnek başına bütçe: bir görsel, 2880 token.

Çoklu görsel orta çözünürlükte birkaç görsel ister (~576 token her biri) ki görseller arası akıl yürütme context'e sığsın. Örnek başına bütçe: 4-8 görsel, 576 her biri, 2300-4600 token.

Video temporal dinamikleri yakalamak için düşük çözünürlükte çok frame ister (pooling sonrası frame başına ~196 token). Örnek başına bütçe: 8-32 frame, 196 her biri, 1600-6200 token.

Ayrı modeller eğitirsen, bir bütçe seçersin. Tek model eğitirsen, bütçenin context'i patlatmadan senaryolar boyunca duyarlı şekilde ölçeklenmesi gerek.

OneVision-öncesi varsayılan cevap "bir senaryo eğit, diğerlerini görmezden gel" idi. Video-LLaVA ekstra eğitim aşamaları ile bir image modeline videoyu retrofit etti. LLaVA-NeXT tiling ile çoklu görsel desteği ekledi. Üçünü de temiz şekilde halleden olmadı.

## Kavram

### OneVision token bütçesi

LLaVA-OneVision örnek başına yaklaşık 3000-4000 token'lık birleştirilmiş bir görsel-token bütçesi seçer, senaryo başına farklı tahsis edilmiş:

- Tek görsel: AnyRes-9 (3x3 tile + thumbnail), her tile 384'te 729 patch ile, agresif bilinear pooling 2x2 → tile başına 182. Toplam: 9 * 182 + 182 = 1820 token. Ya da tile başına 729'da AnyRes-4 = 2916 + 729.
- Çoklu görsel: her görsel orta çözünürlükte (384, tiling yok), pooling olmadan 729 token. Bütçe 6 görsel → 4374 token.
- Video: 384 çözünürlükte 32 frame agresif 3x3 bilinear pool ile → frame başına 81 token. Toplam: 32 * 81 = 2592 token.

Tahsis kabaca sabit toplam token tutar. LLM hiç context'ini patlatan bir batch görmez. Encoder senaryo başına farklı geometri üretir, ama LLM aynı bütçeyi tüketir.

### Üç aşamalı müfredat

LLaVA-OneVision üç aşamada eğitir:

1. Tek görsel SFT (aşama SI). Tüm veri tek-görsel-artı-metin. Yüksek çözünürlüklü AnyRes input üzerinde eğit. Bu algı, OCR ve ince taneli anlamayı öğretir. LLaVA-NeXT verisi artı OneVision-spesifik tek görsel verisi kullanır.
2. OneVision SFT (aşama OV). Tek görsel + çoklu görsel + video (uniform örneklenmiş frame'ler) karıştır. Birleştirilmiş token bütçesi üzerinde eğit. Bu modele heterojen batch shape'lerini ele almayı öğretir. Ağırlık reset yok — aşama SI'dan devam eder.
3. Görev transferi (aşama TT). Ürüne bağlı olarak tipik olarak çoklu görsel ya da videoda daha ağır olan hedef görev karışımı ile devam et. Deployment için opsiyonel fine-tune.

Kritik: müfredat sırası önemli. Video-first ya da multi-image-first eğitim, aynı veri ile bile tek-görsel-first'ten daha kötü görsel performansı üretir. Makale bunu açıkça ablate ediyor.

### Müfredat neden çalışır

Tek görsel eğitimi algısal tabanı inşa eder. Patch token'ları ince taneli görsel feature taşır; LLM onları metinle entegre etmeyi öğrenir. Çoklu görsel ve video, güçlü algısal taban olmadan öğrenmesi zor yapısal zorluklar (hangi görsel hangisi, önce ne oldu) tanıtır.

Tüm senaryoları sıfırdan birlikte eğitirsen, model algıyı underfit eder (batch başına sınırlı tek görsel verisi) ve yapıyı overfit eder (çok sayıda çoklu görsel / video verisi). Sonuç: cross-image akıl yürütme kalıplarını takip eden ama görsel olarak sığ bir model.

Müfredat sıralaması sana aşama SI'dan algı gücünü, sonra aşama OV'dan compositional/temporal akıl yürütmeyi, ikisini de kaybetmeden verir.

### Emergent cross-senaryo becerileri

LLaVA-OneVision makalesi üç emergent yetenek raporluyor:

1. Multi-camera akıl yürütme. Çoklu görsel + video üzerinde ayrı ayrı eğitildi; çıkarımda multi-camera bir sürüş sahnesi hakkında akıl yürütmesi istendi. Model eğitimde o tam formatı hiç görmemesine rağmen görünümleri doğru entegre ediyor.
2. Set-of-mark prompting. User bir görseldeki nesneleri numaralı marker'larla annote ediyor; model "mark 3 mark 7'ye göre ne yapıyor" hakkında akıl yürütüyor. Ne marker'lar ne annotation üzerinde eğitildi; spatial grounding + multi-image referansının kombinasyonundan öğrendi.
3. iPhone-ekran görüntüsü agent'ı. User bir iPhone ekran görüntüsü sağlıyor ve bir sonraki click'i planlamasını istiyor. UI ekran görüntüleri, user workflow video'ları ve multi-image before/after çiftleri üzerinde eğitildi. Agent kullanım durumuna genelleşiyor.

Bunlar eğitilen görevler değil; müfredatın compositional yapısından emerge ediyorlar.

### Görsel-token pooling

Token bütçesi pooling gerektirir. OneVision 2D patch grid'inde bilinear interpolation kullanır: 24x24 = 576 patch 12x12 = 144 (2x faktör) ya da 8x8 = 64 (3x faktör) olur. Pooling locality'yi korumak için token uzayında değil, patch-grid uzayında yapılır.

Senaryo başına pooling faktörü seçimi başlı başına bir hyperparameter. Daha az pooling = daha çok token = daha zengin temsil. Daha çok pooling = daha az token = daha çok frame / görsel sığar.

### LLaVA-OneVision-1.5

2025 takibi (LLaVA-OneVision-1.5, arXiv 2509.23661) eğitim verisinde, model ağırlıklarında ve kodda "tamamen açık". Bazı benchmark'larda proprietary farkı eşler ve tarifi demokratikleştirir. Aynı müfredat, daha çok veri, daha iyi base LLM. Mimari değişiklik yok.

### Qwen2.5-VL ile karşıtlık

Qwen2.5-VL (Ders 12.09) farklı seçimler yapar. Sabit pooling yerine M-RoPE ve dinamik FPS kullanır. Bütçesi input ile ölçeklenir — 1 dakikalık video 5 saniyelik videodan daha çok token kullanır. LLaVA-OneVision bütçeyi sabitler ve pooling'i ölçekler. İkisi de çalışıyor; configurability'yi predictability ile takas ediyorlar.

## Kullan

`code/main.py` OneVision tarzı bir VLM için bir müfredat ve bütçe planlayıcısı. Örnek başına bir token bütçesi ve hedef senaryo karışımı (mesela %40 tek görsel, %30 çoklu görsel, %30 video) verildiğinde:

- Senaryo başına çözünürlük, pooling faktörü ve frame tahsis eder.
- Her senaryonun paylaşılan bütçeye sığdığını kontrol eder.
- Beklenen token sayısı, LLM FLOPs ve hangi senaryoların yetersiz tokenize edildiğini raporlar.
- Aşama-aşama eğitim programı yazdırır.

Bir OneVision fine-tune planlamak ya da bir VLM deployment'ının istek başına maliyetini sağlık kontrolü yapmak için kullan.

## Yayınla

Bu ders `outputs/skill-onevision-budget-planner.md` üretir. Hedef görev dağılımı ve örnek başına bütçe verildiğinde, AnyRes faktörünü, frame başına pooling'i, video frame sayısını ve müfredat aşama ağırlıklarını yayar. Birleştirilmiş-senaryo bir VLM eğittiğinde ya da fine-tune ettiğinde bunu kullan.

## Alıştırmalar

1. Ürünün %80 tek görsel, %10 çoklu görsel (2-4 görsel), %10 video (8-16 frame) destekliyor. Token bütçesini tasarla. Ağır çoklu görsel yapmadan tasarruf ettiğin ekstra bütçeyi nereye koyardın?

2. LLaVA-OneVision Bölüm 4.3'ü (emergent yetenekler) oku. Müfredatın muhtemelen açacağı ama makalenin raporlamadığı dördüncü bir emergent beceri öner.

3. Müfredat sırasını değiştir — önce çoklu görsel, sonra tek görsel, sonra video eğit. Hangi benchmark'ların bozulacağını ve neden olduğunu tahmin et.

4. Makale örnek başına yalnızca 8 frame'de eğitilen video benchmark'ları raporluyor. Bu çıkarımda 30 saniyelik videolara genelleşir mi? Önce ne kırılır — token bütçesi mi temporal akıl yürütme mi?

5. 24x24 patch'lerin 12x12'ye bilinear pooling'i her dim'de 4x azalmadır. Pooling'i stdlib Python'da uygula ve her 2x2 block üzerindeki ortalamanın bilinear çıktıya eşleştiğini doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| OneVision senaryosu | "Tek görsel, çoklu görsel ya da video" | Birleştirilmiş VLM'in ele aldığı üç input shape'inden biri; bütçe boyunca sabit kalır |
| Token bütçesi | "Örnek başına kaç token" | Eğitim / çıkarım örneği başına LLM'in gördüğü toplam görsel token, tipik olarak 3000-4000 |
| Müfredat | "Eğitim sırası" | Emergent transfer için seçilen aşama sıralaması (tek görsel → çoklu görsel → video) |
| Bilinear pooling | "Token küçültme" | Locality'yi korurken token sayısını azaltmak için patch grid'ine (2D) bilinear interpolation uygulamak |
| Emergent skill | "Eğitilmedi, yine de çalışıyor" | Müfredat kompozisyonu nedeniyle eşleşen eğitim verisi olmadan çıkarımda ortaya çıkan yetenek |
| AnyRes-k | "k-tile kurulum" | Sabit çözünürlüklü k alt-tile artı bir thumbnail, tipik k ∈ {4, 9} |
| Görev transferi | "Cross-senaryo genelleşmesi" | Paylaşılan backbone üzerinden videoya (ve tersi) uygulanan tek görselde öğrenilen beceriler |

## İleri Okuma

- [Li et al. — LLaVA-OneVision (arXiv:2408.03326)](https://arxiv.org/abs/2408.03326)
- [LLaVA-OneVision-1.5: Fully Open Framework (arXiv:2509.23661)](https://arxiv.org/abs/2509.23661)
- [Lin et al. — Video-LLaVA (arXiv:2311.10122)](https://arxiv.org/abs/2311.10122)
- [Lin et al. — VILA (arXiv:2312.07533)](https://arxiv.org/abs/2312.07533)
- [Wang et al. — Qwen2-VL (arXiv:2409.12191)](https://arxiv.org/abs/2409.12191)
