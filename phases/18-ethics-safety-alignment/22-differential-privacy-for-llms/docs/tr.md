# LLM'ler için Differential Privacy

> DP-SGD standart olmaya devam ediyor — gürültü-enjekte edilmiş gradient güncellemeleri formel (epsilon, delta) garantileri sağlar. Compute, memory ve utility'deki overhead büyük; parametre-verimli DP fine-tuning (LoRA + DP-SGD) yaygın 2025 konfigürasyonudur (ACM 2025). Gerilim halindeki iki kanıt grubu: canary-tabanlı membership inference (Duan vd., 2024) dil modellerine karşı sınırlı başarı raporluyor; training-data extraction (Carlini vd., 2021; Nasr vd., 2025) önemli verbatim ezberleme kurtarıyor. Çözüm (arXiv:2503.06808, Mart 2025): boşluk neyin ölçüldüğündedir — eklenen canary'ler vs "en çıkarılabilir" veri. Yeni canary tasarımları shadow modeller olmadan loss-tabanlı MIA'yı mümkün kılar ve gerçekçi DP garantileriyle gerçek veri üzerinde eğitilmiş bir LLM'in ilk önemsiz olmayan DP audit'ini sağlar. Alternatifler: PMixED (arXiv:2403.15638) — next-token dağılımları üzerinde mixture of experts ile çıkarım zamanında private prediction; DP sentetik veri üretimi (Google Research 2024). Yükselen saldırı: LLM Feedback Üzerinden Differential Privacy Reversal — confidence-score sızıntısı.

**Tür:** Yapım
**Diller:** Python (stdlib, DP-SGD gürültü-enjeksiyonu ve ε-δ accountant gösterimi)
**Ön koşullar:** Faz 01 · 09 (information theory), Faz 10 · 01 (büyük-model eğitimi)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- (epsilon, delta)-differential privacy'yi tanımla ve DP-SGD reçetesini ifade et.
- 2024-2025 gerilimini açıkla: canary MIA vs training-data extraction farklı resimler veriyor.
- PMixED'i ve çıkarım-zamanı private prediction'ın DP eğitimine neden bir alternatif olduğunu tarif et.
- LLM Feedback Üzerinden Differential Privacy Reversal saldırısını tarif et.

## Sorun

LLM'ler ezberler. Carlini vd. 2021 üretim dil modellerinin talep üzerine verbatim eğitim metnini yeniden ürettiğini gösterdi. DP formel savunmadır: çıktının herhangi bir tek eğitim örneğine kanıtlanır şekilde duyarsız olacak şekilde eğit. 2024-2025 kanıtı DP-SGD'nin gerekli olduğunu ama deploy edilen ε değerlerinin tehdit modeliyle eşleşmeyebileceğini gösteriyor.

## Kavram

### (ε, δ)-differential privacy

Bir rastlanmış algoritma M, bir örnekte farklı olan herhangi iki veri kümesi ve herhangi bir olay S için aşağıdaki sağlanırsa (ε, δ)-DP'dir:
P(M(D) in S) <= e^ε * P(M(D') in S) + δ.

Yorum: çıktı dağılımı yeterince yakındır (ε ile parametrize edilir) ki herhangi bir tek bireyin katkısı δ olasılığı dışında güvenilir şekilde çıkarılamaz.

### DP-SGD

Abadi vd. 2016. Standart reçete:
1. Bir mini-batch örnekle.
2. Örnek-başına gradient'leri hesapla.
3. Her örnek-başına gradient'i bir C eşiğine clip et.
4. Clip edilmiş gradient'leri topla ve σ * C std'li Gaussian gürültü ekle.
5. Parametreleri güncellemek için gürültülü toplamı kullan.

Gizlilik maliyeti bir accountant tarafından izlenir (Moments Accountant, Rényi DP accountant). LLM literatüründe raporlanan ε değerleri tehdit modeline, veri hassasiyetine ve utility hedefine göre büyük ölçüde değişir; evrensel "güvenli" varsayılan ε yoktur. Yayınlanan örnekler bazı LLM eğitim ayarlarında kabaca ε ≈ 1–10 arasında değişir, ama bunlar açıklayıcıdır — önerilen varsayılanlar değil. Daha düşük ε genellikle daha fazla gürültü gerektirir ve utility kaybını artırabilir.

### LoRA + DP-SGD

Bir frontier modelinin tam DP-SGD'si yasaklayıcıdır. LoRA (Hu vd. 2022) gradient güncellemelerini küçük bir adapter'a sınırlar, örnek-başına gradient depolamayı azaltır. LoRA + DP-SGD yaygın 2025 konfigürasyonudur. DP garantileri adapter'a uygulanır; base model sabit tutulur.

### 2024-2025 gerilimi

İki kanıt çizgisi:

- **Canary MIA (Duan vd. 2024).** Eğitim verisine eşsiz canary'ler ekle, bir membership-inference saldırganının onları tanımlayıp tanımlayamayacağını ölç. Dil modellerinde sınırlı başarı raporluyor. MIA'nın zor olduğunu öneriyor.
- **Training-data extraction (Carlini 2021, Nasr vd. 2025).** Modeli bir prefix ile prompt'la; eğitimden verbatim metin kurtarıp kurtarmadığını ölç. Önemli ezberleme raporluyor. İlgili anlamda MIA'nın kolay olduğunu öneriyor.

Mart 2025 çözümü (arXiv:2503.06808): ikisi farklı şeyleri ölçer. MIA "örnek e D'de mi?" diye eklenmiş canary'lerde sorar. Extraction "D'den ne kurtarabilirim?" sorar. "En çıkarılabilir" örnek gizlilik için önemlidir; canary'ler bunu az raporlar çünkü çıkarılabilir olmak için optimize edilmemişlerdir.

Yeni canary tasarımları. Shadow modeller olmadan loss-tabanlı MIA. Gerçekçi DP garantileriyle gerçek veri üzerinde bir LLM'in ilk önemsiz olmayan DP audit'i.

### DP eğitimine alternatifler

- **PMixED (arXiv:2403.15638).** Çıkarım zamanında private prediction. Next-token dağılımları üzerinde mixture of experts; her uzman eğitim verisinin bir shard'ını görür; aggregation DP için gürültü ekler. DP eğitimini tamamen atlatır.
- **DP sentetik veri üretimi (Google Research 2024).** DP-SGD ile LoRA-fine-tune, sentetik veri örnekle, downstream sınıflandırıcıyı sentetik veri üzerinde eğit.

İkisi de tam DP eğitiminin utility maliyetini farklı bir tehdit modeli pahasına atlatır.

### LLM Feedback Üzerinden Differential Privacy Reversal

Yükselen 2025 saldırı. Bireyleri yeniden tanımlamak için bir DP-eğitilmiş modelin confidence skorlarını bir oracle olarak kullan. Çıktılar sızdırmasa bile, confidence dağılımları sızdırabilir.

Savunma: confidence'ları ifşa etme veya ifşadan önce truncate/quantize et. Bu (ε, δ)-DP eğitiminin ötesinde ek bir gerekliliktir.

### Bu Faz 18'de nereye uyuyor

Dersler 20-21 bias/fairness'tır. Ders 22 gizliliktir. Ders 23 watermarking üzerinden provenance'tır. Ders 27 düzenleyici veri-provenance katmanını kapsar.

## Kullan

`code/main.py` bir oyuncak ikili-sınıflandırma veri kümesi üzerinde DP-SGD simüle eder. Gürültü çarpanı σ'yı ve clipping normu C'yi tarayabilir ve (ε, δ) bütçesini ve doğruluk maliyetini izleyebilirsin. Bir "canary saldırısı" eşsiz bir eğitim örneği ekler ve DP'den önce ve sonra bir log-loss testinin onu tespit edip edemediğini ölçer.

## Yayınla

Bu ders `outputs/skill-dp-audit.md` üretir. Bir dil modeli deployment'ında bir DP iddiası verildiğinde, audit eder: (ε, δ) değerleri, kullanılan accountant, MIA değerlendirme protokolü ve confidence-exposure vektörlerinin değerlendirilip değerlendirilmediği.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. σ'yı {0.5, 1.0, 2.0}'de tara ve (ε, δ)-doğruluk trade-off'unu raporla. Utility'nin çöktüğü noktayı tanımla.

2. Bir canary insertion ve bir log-loss testi uygula. σ = 1.0'da DP-SGD'den önce ve sonra tespit oranını ölç.

3. Nasr vd. 2025'i training-data extraction üzerine oku. Extraction başarısı orta ε altında neden çökmüyor? Bu MIA-as-evaluation hakkında ne ima ediyor?

4. Tamamen çıkarım zamanında çalışan PMixED (arXiv:2403.15638) kullanan bir deployment tasarla. PMixED'nin ele aldığı ve DP-SGD'nin almadığı tehdit modeli nedir?

5. LLM Feedback Üzerinden DP Reversal saldırısını çiz. Confidence-score sızıntısını sınırlayan bir önlem tasarla ve deployment maliyetini tahmin et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| DP | "(ε, δ)-differential privacy" | Formel gizlilik: komşu-veri-kümesi değişimi altında çıktı dağılımı yakın |
| DP-SGD | "gürültü-enjekte SGD" | Gradient clipping + Gaussian gürültü eklenmesi; standart DP eğitimi |
| LoRA + DP-SGD | "verimli private fine-tune" | Low-rank adapter'larda DP-SGD; standart 2025 konfigürasyonu |
| MIA | "membership inference" | Bir örneğin eğitim verisinde olup olmadığını belirleyen saldırı |
| Canary | "eklenen watermark örneği" | DP sızıntısını ölçmek için kullanılan eşsiz eğitim örneği |
| PMixED | "private inference mixture" | Next-token dağılımları üzerinde mixture-of-experts üzerinden çıkarım-zamanı DP |
| DP Reversal | "confidence sızıntı saldırısı" | Bir modelin confidence'ını yeniden tanımlama için oracle olarak kullanan saldırı |

## İleri Okuma

- [Abadi et al. — DP-SGD (arXiv:1607.00133)](https://arxiv.org/abs/1607.00133) — standart DP eğitim algoritması
- [Carlini et al. — Extracting Training Data (arXiv:2012.07805)](https://arxiv.org/abs/2012.07805) — kanonik extraction makalesi
- [Duan et al. — Canary MIA on LLMs (arXiv:2402.07841, 2024)](https://arxiv.org/abs/2402.07841) — sınırlı-başarılı MIA
- [Kowalczyk et al. — Auditing DP for LLMs (arXiv:2503.06808, Mart 2025)](https://arxiv.org/abs/2503.06808) — gerilim çözümü
- [PMixED (arXiv:2403.15638)](https://arxiv.org/abs/2403.15638) — çıkarım-zamanı private prediction
