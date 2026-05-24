# Fairness Kriterleri — Grup, Bireysel, Counterfactual

> Üç aile fairness literatürünü yapılandırır. Group fairness: demographic parity, equalized odds, conditional use accuracy equality — korunan gruplar arasında ortalama eşit oranlar. Individual fairness (Dwork vd. 2012): benzer bireyler benzer kararlar alır; karar haritasında Lipschitz koşulu. Counterfactual fairness (Kusner vd. 2017): hassas öznitelikler counterfactual olarak değiştirildiğinde değişmemişse bir karar bir bireye karşı fairdir. 2024 teorik sonuç (NeurIPS 2024): doğal bir CF-vs-accuracy trade-off vardır; bir model-agnostik yöntem optimal-ama-fair-olmayan bir tahmin ediciyi sınırlı doğruluk kaybıyla bir CF olana dönüştürür. Backtracking counterfactuals (arXiv:2401.13935, Ocak 2024): yasal olarak korunan özniteliklere müdahale gerektirmeyi atlatan yeni paradigma. Felsefi uzlaşma (ICLR Blogposts 2024): causal grafikle, belirli grup fairness ölçülerini karşılamak counterfactual fairness'ı gerektirir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, üç-kriter karşılaştırması)
**Ön koşullar:** Faz 18 · 20 (bias), Faz 02 (klasik ML)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Üç grup-fairness kriterini (demographic parity, equalized odds, conditional use accuracy equality) ve bir imkansızlık sonucunu ifade et.
- Dwork vd. 2012 Lipschitz formülasyonu üzerinden individual fairness'ı tarif et.
- Counterfactual fairness'ı ve causal-grafik bağımlılığını tarif et.
- Backtracking counterfactuals'ı ve korunan-öznitelik-üzerinde-müdahale problemini neden atlatdıklarını açıkla.

## Sorun

Ders 20 bias'ı ölçmekle ilgiliydi. Ders 21 ölçümün hizmet etmesi gereken fairness standardını tanımlamakla ilgili. Üç aile yapısal olarak farklı standartlar verir — bir model group-fair ve individual-unfair olabilir, counterfactually fair ve group-unfair olabilir. Bir standart seçmek bir policy kararıdır; hiçbir standart evrensel olarak optimal değildir.

## Kavram

### Group fairness

- **Demographic parity.** Tüm gruplar için P(Y=1 | A=a) = P(Y=1 | A=a'). Eşit kabul oranları.
- **Equalized odds.** P(Y=1 | Y*=y, A=a) = P(Y=1 | Y*=y, A=a'). Gruplar arasında eşit TPR ve FPR.
- **Conditional use accuracy equality.** P(Y*=y | Y=y, A=a) = P(Y*=y | Y=y, A=a'). Gruplar arasında eşit predictive value.

İmkansızlık (Chouldechova, Kleinberg-Mullainathan-Raghavan 2017): bu üçü eşit olmayan base rate'ler altında aynı anda karşılanamaz.

### Individual fairness

Dwork vd. 2012. Bir karar haritası f, görev-özgü bir benzerlik metriği d'ye göre individual fairdir eğer bazı Lipschitz sabiti L için |f(x) - f(x')| <= L * d(x, x'). Benzer bireyler benzer kararlar alır.

d'nin tanımlanmasını gerektirir. Policy sorusu, istatistiksel değil.

### Counterfactual fairness

Kusner vd. 2017. Bir karar bireye i'ye karşı counterfactually fairdir eğer popülasyonun bir causal modeli altında, i'nin hassas öznitelikleri counterfactually değiştirildiğinde karar değişmiyorsa.

Bir causal DAG gerektirir. DAG bir modelleme seçimidir. Counterfactual fairness yalnızca DAG kadar gerekçelidir.

### CF-vs-accuracy trade-off

NeurIPS 2024 teorik: counterfactual fairness ve tahmin doğruluğu arasında doğal bir trade-off vardır. Bir model-agnostik yöntem optimal-ama-fair-olmayan bir tahmin ediciyi sınırlı doğruluk maliyetinde bir CF olana dönüştürebilir. Doğruluk maliyeti optimal unfair tahmin edicideki hassas-öznitelik katsayısının büyüklüğüne bağlıdır.

### Backtracking counterfactuals

arXiv:2401.13935 (Ocak 2024). Geleneksel counterfactuals hassas öznitelik üzerinde müdahale gerektirir — "bu kişi farklı bir cinsiyette olsaydı karar değişir miydi". Yasal olarak, bu problemlidir: korunan öznitelikler sınıflandırma hukukunda müdahale edilemez.

Backtracking counterfactuals yönü çevirir: öznitelik üzerinde müdahale etmek yerine, bireyin gerçek özelliklerinin hangi kombinasyonu counterfactual sonucu üretirdi diye sorar. Bu yasal itirazı atlatır.

### Felsefi uzlaşma

ICLR Blogposts 2024. Elinde bir causal graph varken, belirli grup-fairness ölçülerini karşılamak counterfactual fairness'ı gerektirir. Üç aile ortogonal değildir; aynı altta yatan causal yapının farklı yönleridir.

Bu imkansızlık teoremlerini çözmez (eşit olmayan base rate'ler hâlâ aynı anda grup fairness'ı engeller). Ama "grup" ile "individual / counterfactual" arasındaki görünen karşıtlığın causal model hakkında açık olmamanın bir artefaktı olduğunu kısmen gösterir.

### Bu Faz 18'de nereye uyuyor

Ders 20 bias ölçümüdür. Ders 21 fairness tanımıdır. Ders 22 gizliliktir (differential privacy). Ders 23 watermarking'tir. Bunlar Ders 7-11'in deception-bitişik derslerini tamamlayan tahsisat-bitişik derslerdir.

## Kullan

`code/main.py` hassas öznitelik ve eşit olmayan base rate'lerle bir oyuncak ikili-sınıflandırma veri kümesi inşa eder. Basit bir sınıflandırıcıda demographic parity, equalized odds ve conditional use accuracy equality hesapla. Üç metriğin uyuşmadığını gözlemle. Demographic parity için bir re-weighting uygula ve diğer ikisindeki maliyetini gözlemle.

## Yayınla

Bu ders `outputs/skill-fairness-criterion.md` üretir. Bir fairness iddiası veya policy verildiğinde, hangi kriterin iddia edildiğini, iddia edilen eşit olmayan base rate'ler altında modelin kalan kriterleri karşılayıp karşılayamayacağını ve iddianın hangi causal DAG'a bağlı olduğunu tanımlar.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Varsayılan veride üç grup metriğini raporla. Demographic-parity-hedefli re-weighting'i uygula ve yeniden raporla.

2. Hassas-olmayan özellikler üzerinde L2 kullanarak Dwork vd. 2012 individual-fairness metriğini uygula. L=1 sabiti ile kaç çiftin Lipschitz ihlal ettiğini raporla.

3. Kusner vd. 2017'yi oku. Özgeçmiş puanlama için basit bir iki-özellik causal DAG inşa et ve ima ettiği counterfactual-fairness koşulunu tanımla.

4. 2024 backtracking-counterfactuals makalesi korunan öznitelikler üzerinde müdahaleden kaçınır. Bunun yasal uyum için önemli olduğu bir senaryo tarif et.

5. ICLR 2024 uzlaşması grup ve counterfactual fairness'ın aynı yapının yönleri olduğunu savunur. `code/main.py`'deki üç kriterden ikisini seç ve onları eşdeğer yapacak causal varsayımı ifade et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| Demographic parity | "eşit oranlar" | Gruplar arasında P(Y=1 | A=a) eşit |
| Equalized odds | "eşit TPR/FPR" | Gruplar arasında eşit true-positive ve false-positive oranları |
| Conditional use accuracy | "eşit PPV/NPV" | Gruplar arasında eşit predictive value'lar |
| Individual fairness | "Lipschitz koşulu" | Benzer bireyler benzer kararlar alır |
| Counterfactual fairness | "causal değişiklik invariance'ı" | Counterfactual öznitelik değişikliği altında karar değişmez |
| Backtracking counterfactual | "gerçeklikler üzerinden açıkla" | Counterfactual sonuçtan geriye doğru akıl yürütülür, öznitelikten ileriye doğru değil |
| İmkansızlık teoremi | "üçü çatışır" | Chouldechova / KMR 2017: eşit olmayan base rate'ler altında grup kriterleri karşılıklı olarak dışlayıcı |

## İleri Okuma

- [Dwork et al. — Fairness through Awareness (arXiv:1104.3913)](https://arxiv.org/abs/1104.3913) — individual fairness
- [Kusner, Loftus, Russell, Silva — Counterfactual Fairness (arXiv:1703.06856)](https://arxiv.org/abs/1703.06856) — counterfactual fairness
- [Chouldechova — Fair prediction with disparate impact (arXiv:1703.00056)](https://arxiv.org/abs/1703.00056) — imkansızlık
- [Backtracking Counterfactuals (arXiv:2401.13935)](https://arxiv.org/abs/2401.13935) — korunan-öznitelik müdahaleleri için yeni paradigma
