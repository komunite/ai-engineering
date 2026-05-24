# Norm'lar ve Uzaklıklar

> Uzaklık fonksiyonun "benzer"in ne anlama geldiğini tanımlar. Yanlış seç ve aşağı yöndeki her şey bozulur.

**Tür:** Yapım
**Dil:** Python
**Ön koşullar:** Faz 1, Ders 01 (Lineer Cebir Sezgisi), 02 (Vektörler, Matrisler ve İşlemler)
**Süre:** ~90 dakika

## Öğrenme Hedefleri

- L1, L2, kosinüs, Mahalanobis, Jaccard ve edit distance fonksiyonlarını sıfırdan implemente et
- Belirli bir ML görevi için uygun uzaklık metriğini seç ve alternatiflerin neden başarısız olduğunu açıkla
- L1 ve L2 norm'ları LASSO ve Ridge regularization'a ve onların geometrik kısıt bölgelerine bağla
- Aynı veri setinin farklı metrikler altında farklı en yakın komşular ürettiğini göster

## Sorun

İki vektörün var. Belki kelime embedding'leri. Belki kullanıcı profilleri. Belki piksel dizileri. Şunu bilmen lazım: ne kadar yakınlar?

Cevap tamamen hangi uzaklık fonksiyonunu seçtiğine bağlı. İki veri noktası bir metrik altında en yakın komşular olabilirken diğeri altında çok uzak olabilir. KNN sınıflandırıcın, öneri motorun, vektör veritabanın, kümeleme algoritman, loss fonksiyonun — hepsi bu seçime bağlı. Yanlış seç, modelin yanlış şey için optimize eder.

Evrensel olarak en iyi uzaklık yoktur. L2 mekansal veriler için çalışır. Kosinüs benzerliği NLP'de hakimdir. Jaccard kümeleri ele alır. Edit distance string'leri ele alır. Mahalanobis korelasyonları hesaba katar. Wasserstein olasılık kütlesini hareket ettirir. Her biri "benzer"in ne anlama geldiğine dair farklı bir varsayım kodlar.

Bu ders her büyük uzaklık fonksiyonunu sıfırdan inşa eder, her birinin ne zaman doğru araç olduğunu gösterir ve aynı verinin hangi metriği kullandığına bağlı olarak tamamen farklı en yakın komşular ürettiğini gösterir.

## Kavram

### Norm'lar: vektör büyüklüğünü ölçme

Bir norm bir vektörün "boyutunu" ölçer. İki vektör arasındaki her uzaklık fonksiyonu, farklarının normu olarak yazılabilir: d(a, b) = ||a - b||. Yani norm'ları anlamak uzaklıkları anlamaktır.

### L1 Norm (Manhattan uzaklığı)

L1 normu tüm bileşenlerin mutlak değerlerini toplar.

```
||x||_1 = |x_1| + |x_2| + ... + |x_n|
```

Buna Manhattan uzaklığı denir çünkü sadece eksenler boyunca hareket edebileceğin bir şehir ızgarasında ne kadar yürüdüğünü ölçer. Diyagonal yok.

```
Nokta A = (1, 1)
Nokta B = (4, 5)

L1 uzaklığı = |4-1| + |5-1| = 3 + 4 = 7

Bir ızgarada 3 blok doğuya ve 4 blok kuzeye yürürsün.
```

L1 ne zaman kullanılır:
- Yüksek boyutlu seyrek veri (metin feature'ları, one-hot encoding'ler)
- Aykırı değerlere karşı robust olmak istediğinde (tek bir büyük fark hakim olmaz)
- Feature seçimi problemleri (L1 regularization sparsity'yi destekler)

L1 regularization (Lasso) ile bağlantı: loss fonksiyonuna ||w||_1 eklemek mutlak weight değerlerinin toplamını cezalandırır. Bu küçük weight'leri tam olarak sıfıra iter, otomatik feature seçimi yapar. L1 cezası weight uzayında elmas şekilli kısıt bölgeleri oluşturur ve elmasların köşeleri eksenler üzerindedir, burada bazı weight'ler sıfırdır.

Loss fonksiyonlarına bağlantı: Mean Absolute Error (MAE), tahminler ve hedefler arasındaki ortalama L1 uzaklığıdır. Tüm hataları lineer olarak cezalandırır, MSE'ye kıyasla aykırı değerlere robust yapar.

### L2 Norm (Öklid uzaklığı)

L2 normu düz çizgi uzaklığıdır. Kare bileşenlerin toplamının karekökü.

```
||x||_2 = sqrt(x_1^2 + x_2^2 + ... + x_n^2)
```

Bu geometri dersinde öğrendiğin uzaklıktır. n boyutta Pisagor.

```
Nokta A = (1, 1)
Nokta B = (4, 5)

L2 uzaklığı = sqrt((4-1)^2 + (5-1)^2) = sqrt(9 + 16) = sqrt(25) = 5.0

Düz çizgi, ızgara boyunca diyagonal olarak keser.
```

L2 ne zaman kullanılır:
- Düşük-orta boyutlu sürekli veri
- Feature ölçekleri karşılaştırılabilir olduğunda
- Fiziksel uzaklıklar (mekansal veri, sensör okumaları)
- Piksel seviyesinde görüntü benzerliği

L2 regularization (Ridge) ile bağlantı: loss fonksiyonuna ||w||_2^2 eklemek büyük weight'leri cezalandırır. L1'in aksine, weight'leri sıfıra itmez. Tüm weight'leri orantılı olarak sıfıra doğru küçültür. L2 cezası dairesel kısıt bölgeleri oluşturur, dolayısıyla eksenler üzerinde köşe yoktur. Weight'ler küçülür ama nadiren tam sıfır olur.

Loss fonksiyonlarına bağlantı: Mean Squared Error (MSE) L2 uzaklıklarının karelerinin ortalamasıdır. Karelemek küçük hatalardan büyük hataları daha ağır cezalandırır.

```
MAE (L1 loss):  |y - y_hat|         Lineer ceza. Aykırı değerlere robust.
MSE (L2 loss):  (y - y_hat)^2       Quadratic ceza. Aykırı değerlere duyarlı.
```

### Lp Norm'lar: genel aile

L1 ve L2 Lp norm'unun özel durumlarıdır:

```
||x||_p = (|x_1|^p + |x_2|^p + ... + |x_n|^p)^(1/p)
```

p'nin farklı değerleri farklı şekilli "birim toplar" üretir (orijinden 1 uzaklıkta tüm noktaların kümesi):

```
p=1:    Elmas şekli       (köşeler eksenlerde)
p=2:    Çember/küre       (her zamanki yuvarlak top)
p=3:    Superelips        (yuvarlak kare)
p=inf:  Kare/hiperküp     (eksenler boyunca düz kenarlar)
```

### L-sonsuz Norm (Chebyshev uzaklığı)

p sonsuza yaklaştıkça, Lp normu maksimum mutlak bileşene yakınsar.

```
||x||_inf = max(|x_1|, |x_2|, ..., |x_n|)
```

İki nokta arasındaki uzaklık en çok farklı oldukları tek boyutla belirlenir. Diğer tüm boyutlar yok sayılır.

```
Nokta A = (1, 1)
Nokta B = (4, 5)

L-inf uzaklığı = max(|4-1|, |5-1|) = max(3, 4) = 4
```

L-sonsuz ne zaman kullanılır:
- Herhangi bir tek boyuttaki en kötü durum sapması önemli olduğunda
- Oyun tahtaları (satrançta kral L-sonsuzda hareket eder: herhangi bir yönde bir adım 1'e mal olur)
- Üretim toleransları (her boyut spec içinde olmalı)

### Kosinüs Benzerliği ve Kosinüs Uzaklığı

Kosinüs benzerliği iki vektör arasındaki açıyı ölçer, büyüklüklerini yok sayar.

```
cos_sim(a, b) = (a . b) / (||a||_2 * ||b||_2)
```

-1 (zıt yönler) ile +1 (aynı yön) arasındadır. Dik vektörlerin kosinüs benzerliği 0'dır.

Kosinüs uzaklığı bunu bir uzaklığa çevirir: cosine_distance = 1 - cosine_similarity. Bu 0 (özdeş yön) ile 2 (zıt yön) arasındadır.

```
a = (1, 0)    b = (1, 1)

cos_sim = (1*1 + 0*1) / (1 * sqrt(2)) = 1/sqrt(2) = 0.707
cos_dist = 1 - 0.707 = 0.293
```

Kosinüs neden NLP ve embedding'lere hakim: metinde, belge uzunluğu benzerliği etkilememeli. Kediler hakkında başka bir belgeden iki kat daha uzun olan kediler hakkındaki bir belge yine de "benzer" olmalıdır. Kosinüs benzerliği büyüklüğü (uzunluğu) yok sayar ve sadece yöne önem verir. Aynı kelime dağılımına sahip ama farklı uzunlukta iki belge aynı yöne işaret eder ve kosinüs benzerliği 1.0 alır.

Kosinüs benzerliği ne zaman kullanılır:
- Metin benzerliği (TF-IDF vektörleri, kelime embedding'leri, cümle embedding'leri)
- Büyüklüğün gürültü ve yönün sinyal olduğu herhangi bir alan
- Öneri sistemleri (kullanıcı tercih vektörleri)
- Embedding araması (vektör veritabanları neredeyse her zaman kosinüs veya dot product kullanır)

### Dot Product Benzerliği vs Kosinüs Benzerliği

İki vektörün dot product'ı:

```
a . b = a_1*b_1 + a_2*b_2 + ... + a_n*b_n
      = ||a|| * ||b|| * cos(açı)
```

Kosinüs benzerliği, dot product'ın her iki büyüklüğe bölünmesiyle normalize edilmiş halidir. Her iki vektör de zaten birim normalize edildiğinde (büyüklük = 1), dot product ve kosinüs benzerliği aynıdır.

```
Eğer ||a|| = 1 ve ||b|| = 1:
    a . b = cos(a ve b arasındaki açı)
```

Farklı oldukları durum: dot product büyüklük bilgisini içerir. Daha büyük büyüklüğü olan bir vektör daha yüksek dot product skoru alır. Bu, "popüler" öğelerin daha yüksek sıralanmasını istediğin bazı geri çağırma sistemlerinde önemlidir. Büyüklük örtük bir kalite veya önem sinyali görevi görür.

```
a = (3, 0)    b = (1, 0)    c = (0, 1)

dot(a, b) = 3     dot(a, c) = 0
cos(a, b) = 1.0   cos(a, c) = 0.0

İkisi de yön konusunda hemfikir, ama dot product büyüklüğü de yansıtır.
```

Pratikte:
- Saf yönsel benzerlik istediğinde kosinüs benzerliği kullan
- Büyüklükler anlamlı bilgi taşıdığında dot product kullan
- Birçok vektör veritabanı (Pinecone, Weaviate, Qdrant) ikisi arasında seçim yapmana izin verir
- Embedding'lerin L2-normalize ise, seçim önemli değildir

### Mahalanobis Uzaklığı

Öklid uzaklığı tüm boyutlara eşit davranır. Ama feature'ların ilişkiliyse veya farklı ölçeklerdeyse, L2 yanıltıcı sonuçlar verir.

Mahalanobis uzaklığı verinin kovaryans yapısını hesaba katar.

```
d_M(x, y) = sqrt((x - y)^T * S^(-1) * (x - y))
```

burada S verinin kovaryans matrisidir.

Sezgisel olarak: Mahalanobis uzaklığı önce veriyi de-correlate eder ve normalize eder (whitening), sonra o dönüştürülmüş uzayda L2 uzaklığını hesaplar. S birim matris ise (ilişkisiz, birim varyans feature'lar), Mahalanobis uzaklığı Öklid uzaklığına indirgenir.

```
Örnek: boy ve kilo ilişkilidir.
6'2" ve 180 lb birisi sıra dışı değildir.
5'0" ve 180 lb birisi sıra dışıdır.

Öklid uzaklığı ikisinin de ortalamadan eşit uzaklıkta olduğunu söyleyebilir.
Mahalanobis uzaklığı boy-kilo korelasyonunu hesaba katarak
ikincisini doğru şekilde bir aykırı değer olarak tanımlar.
```

Mahalanobis uzaklığı ne zaman kullanılır:
- Aykırı değer tespiti (ortalamadan büyük Mahalanobis uzaklığı olan noktalar aykırılardır)
- Feature'ların farklı ölçek ve korelasyonları olduğunda sınıflandırma
- Güvenilir bir kovaryans matrisi tahmin etmek için yeterli verin olduğunda
- Üretimde kalite kontrolü (çok değişkenli süreç izleme)

### Jaccard Benzerliği (kümeler için)

Jaccard benzerliği iki küme arasındaki örtüşmeyi ölçer.

```
J(A, B) = |A kesişim B| / |A birleşim B|
```

0 (örtüşme yok) ile 1 (özdeş kümeler) arasındadır. Jaccard uzaklığı = 1 - Jaccard benzerliği.

```
A = {kedi, köpek, balık}
B = {kedi, kuş, balık, yılan}

Kesişim = {kedi, balık}                  boyut = 2
Birleşim = {kedi, köpek, balık, kuş, yılan}  boyut = 5

Jaccard benzerliği = 2/5 = 0.4
Jaccard uzaklığı = 0.6
```

Jaccard ne zaman kullanılır:
- Etiket, kategori veya feature kümelerini karşılaştırma
- Kelime varlığına dayalı belge benzerliği (frekans değil)
- Yakın-duplicate tespiti (Jaccard'ın MinHash yaklaşımı)
- İkili feature vektörlerini karşılaştırma (varlık/yokluk verileri)
- Segmentasyon modellerini değerlendirme (Intersection over Union = Jaccard)

### Edit Distance (Levenshtein Uzaklığı)

Edit distance, bir string'i diğerine dönüştürmek için gereken minimum tek karakter işlemi sayısını sayar. İşlemler şunlardır: ekle, sil veya değiştir.

```
"kitten" -> "sitting"

kitten -> sitten  (k'yı s ile değiştir)
sitten -> sittin  (e'yi i ile değiştir)
sittin -> sitting (g ekle)

Edit distance = 3
```

Dinamik programlama kullanılarak hesaplanır. (i, j) girdisinin A string'inin ilk i karakteri ile B string'inin ilk j karakteri arasındaki edit distance'ı olduğu bir matris doldur.

```
        ""  s  i  t  t  i  n  g
    ""   0  1  2  3  4  5  6  7
    k    1  1  2  3  4  5  6  7
    i    2  2  1  2  3  4  5  6
    t    3  3  2  1  2  3  4  5
    t    4  4  3  2  1  2  3  4
    e    5  5  4  3  2  2  3  4
    n    6  6  5  4  3  3  2  3
```

Edit distance ne zaman kullanılır:
- Yazım kontrolü ve düzeltme
- DNA dizi hizalama (ağırlıklı işlemlerle)
- Bulanık string eşleştirme
- Düzensiz metin verisinin tekrar elenmesi

### KL Diverjansı (uzaklık değil ama öyle kullanılır)

KL diverjansı bir olasılık dağılımının diğerinden nasıl farklı olduğunu ölçer. Ders 09'da işlendi, ama insanların bunu uzaklık olmamasına rağmen "uzaklık" olarak kullandığı için bu tartışmaya aittir.

```
D_KL(P || Q) = sum(p(x) * log(p(x) / q(x)))
```

Kritik özellik: KL diverjansı simetrik DEĞİLDİR.

```
D_KL(P || Q) != D_KL(Q || P)
```

Bu, bir uzaklık metriğinin temel gereksinimini karşılamadığı anlamına gelir. Üçgen eşitsizliğini de karşılamaz. Bu bir diverjanstır, uzaklık değil.

İleri KL (D_KL(P || Q)) "ortalama-arayan"dır: Q, P'nin tüm modlarını kapsamaya çalışır.
Geri KL (D_KL(Q || P)) "mod-arayan"dır: Q, P'nin tek bir moduna odaklanır.

KL diverjansını gördüğünde:
- VAE'ler (ELBO'daki KL terimi latent dağılımı bir prior'a iter)
- Knowledge distillation (öğrenci öğretmenin dağılımını eşleştirmeye çalışır)
- RLHF (KL cezası fine-tune edilen modeli temel modele yakın tutar)
- Policy gradient yöntemleri (policy güncellemelerini kısıtlama)

### Wasserstein Uzaklığı (Earth Mover's Distance)

Wasserstein uzaklığı, bir olasılık dağılımını diğerine dönüştürmek için gereken minimum "iş"i ölçer. Şöyle düşün: bir dağılım bir toprak yığını ve diğeri bir çukursa, ne kadar toprağı ne kadar uzağa taşıman gerekir?

```
W(P, Q) = inf tüm taşıma planları gamma üzerinden E[d(x, y)]
```

1B dağılımlar için, kümülatif dağılım fonksiyonlarının mutlak farkının integraline indirgenir:

```
W_1(P, Q) = integral |CDF_P(x) - CDF_Q(x)| dx
```

Wasserstein neden önemli:
- Gerçek bir metriktir (simetrik, üçgen eşitsizliğini karşılar)
- Dağılımlar örtüşmediğinde bile gradyanlar sağlar (KL diverjansı sonsuza gider)
- Bu özellik onu Wasserstein GAN'larının (WGAN'lar) merkezine koydu, orijinal GAN'ların eğitim kararsızlığını çözdü

```
Örtüşmeyen dağılımlar:

P: [1, 0, 0, 0, 0]    Q: [0, 0, 0, 0, 1]

KL diverjansı: sonsuz (sıfırın log'u)
Wasserstein: 4 (tüm kütleyi 4 bin taşı)

Wasserstein anlamlı bir gradyan verir. KL vermez.
```

Wasserstein ne zaman kullanılır:
- GAN eğitimi (WGAN, WGAN-GP)
- Örtüşmeyebilen dağılımları karşılaştırma
- Optimal taşıma problemleri
- Görüntü geri çağırma (renk histogramlarını karşılaştırma)

### Neden Farklı Görevlerin Farklı Uzaklıklara İhtiyacı Var

| Görev | En iyi uzaklık | Neden |
|------|--------------|-----|
| Metin benzerliği | Kosinüs | Büyüklük gürültü, yön anlam |
| Görüntü piksel karşılaştırması | L2 | Mekansal ilişkiler önemli, feature'lar karşılaştırılabilir ölçek |
| Seyrek yüksek-boy feature'lar | L1 | Robust, nadir büyük farkları büyütmez |
| Küme örtüşmesi (etiketler, kategoriler) | Jaccard | Veri doğal olarak küme değerlidir, vektörel değil |
| String eşleştirme | Edit distance | İşlemler insan düzenleme sezgisine eşlenir |
| Aykırı değer tespiti | Mahalanobis | Feature korelasyonları ve ölçekleri hesaba katar |
| Dağılımları karşılaştırma | KL diverjansı | P yerine Q kullanarak kaybedilen bilgiyi ölçer |
| GAN eğitimi | Wasserstein | Dağılımlar örtüşmediğinde bile gradyanlar sağlar |
| Embedding'ler (vektör DB) | Kosinüs veya dot product | Embedding'ler anlamı yönde kodlayacak şekilde eğitilir |
| Öneri | Dot product | Büyüklük popülerlik veya güveni kodlayabilir |
| DNA dizileri | Ağırlıklı edit distance | Yer değiştirme maliyetleri nükleotid çiftine göre değişir |
| Üretim QC | L-sonsuz | Herhangi bir boyuttaki en kötü durum sapması önemli |

### Loss Fonksiyonlarına Bağlantı

Loss fonksiyonları, tahminler ve hedeflere uygulanan uzaklık fonksiyonlarıdır.

```
Loss fonksiyonu     Kullandığı uzaklık       Davranış
MSE                 L2 kare                  Büyük hataları ağır cezalandırır
MAE                 L1                       Tüm hataları eşit cezalandırır
Huber loss          Büyük hatalar için L1,   İkisinin en iyisi: aykırı değerlere robust,
                    küçük hatalar için L2    sıfır yakınında yumuşak gradyan
Cross-entropy       KL diverjansı            Dağılım uyumsuzluğunu ölçer
Hinge loss          max(0, margin - d)       Sadece margin altında cezalandırır
Triplet loss        L2 (tipik olarak)        Pozitifleri yakına çeker, negatifleri uzağa iter
Contrastive loss    L2                       Benzer çiftler yakın, benzer olmayanlar margin'in ötesinde
```

### Regularization'a Bağlantı

Regularization loss fonksiyonuna weight'ler üzerinde bir norm cezası ekler.

```
L1 regularization (Lasso):   loss + lambda * ||w||_1
  -> Seyrek weight'ler. Bazı weight'ler tam olarak sıfır olur.
  -> Otomatik feature seçimi.
  -> Çözümün köşeleri var (sıfırda diferansiye edilemez).

L2 regularization (Ridge):   loss + lambda * ||w||_2^2
  -> Küçük weight'ler. Tüm weight'ler sıfıra doğru küçülür.
  -> Feature seçimi yok (hiçbir şey tam sıfıra gitmez).
  -> Her yerde yumuşak çözüm.

Elastic Net:                  loss + lambda_1 * ||w||_1 + lambda_2 * ||w||_2^2
  -> L1'in sparsity'sini L2'nin kararlılığıyla birleştirir.
  -> İlişkili feature grupları birlikte tutulur veya bırakılır.
```

L1 neden sparsity üretir ama L2 üretmez: 2B weight uzayında kısıt bölgesini düşün. L1 bir elmas, L2 bir çember. Loss fonksiyonunun konturlarının (elipslerin) elmasa bir köşede, bir weight'in sıfır olduğu yerde dokunması en olasıdır. Çembere yumuşak bir noktada, her iki weight'in sıfır olmadığı yerde dokunurlar.

### En Yakın Komşu Araması

Her uzaklık fonksiyonu bir en yakın komşu arama problemi ima eder: bir sorgu noktası verildiğinde, veri setindeki en yakın noktaları bul.

Tam en yakın komşu araması, n nokta ve d boyutlu bir veri setinde sorgu başına O(n * d)'dir. Büyük veri setleri için bu çok yavaştır.

Approximate Nearest Neighbor (ANN) algoritmaları küçük miktarda doğruluğu masif hız kazanımları için takas eder:

```
Algoritma         Yaklaşım                      Kullanan
KD-tree'ler       Eksen hizalı uzay bölümü      scikit-learn (düşük boy)
Ball tree'ler     İç içe hiperküreler            scikit-learn (orta boy)
LSH               Rastgele hash projeksiyonlar   Yakın-duplicate tespiti
HNSW              Hiyerarşik gezilebilir         FAISS, Qdrant, Weaviate
                  küçük-dünya grafı
IVF               Küme tabanlı aramayla          FAISS (milyar ölçek)
                  ters dosya indeksi
Product quant.    Vektörleri sıkıştır, sıkışmış  FAISS (bellek-kısıtlı)
                  uzayda ara
```

HNSW (Hierarchical Navigable Small World) modern vektör veritabanlarında baskın algoritmadır. Her node'un yaklaşık en yakın komşularına bağlandığı çok katmanlı bir graf inşa eder. Arama en üst katmanda (seyrek, uzun atlamalar) başlar ve en alt katmana (yoğun, kısa atlamalar) iner.

## İnşa Et

### Adım 1: Tüm norm ve uzaklık fonksiyonları

Tam implementasyon için `code/distances.py`'a bak. Her fonksiyon sadece temel Python math kullanılarak sıfırdan inşa edilmiştir.

### Adım 2: Aynı veri, farklı uzaklıklar, farklı komşular

`distances.py`'daki demo bir veri seti oluşturur, bir sorgu noktası seçer ve en yakın komşunun uzaklık metriğine bağlı olarak nasıl değiştiğini gösterir. L1 altında "en yakın" olan nokta L2 veya kosinüs altında en yakın olmayabilir.

### Adım 3: Embedding benzerlik araması

Kod, kosinüs benzerliği vs L2 uzaklığı kullanarak bir sorgu için en benzer "belgeleri" bulan, sıralamaların farklı olabileceğini gösteren bir mock embedding benzerlik araması içerir.

## Kullan

En yaygın pratik kullanım: bir vektör veritabanında benzer öğeleri bulma.

```python
import numpy as np

def cosine_similarity_matrix(X):
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    X_normalized = X / norms
    return X_normalized @ X_normalized.T

embeddings = np.random.randn(1000, 768)

sim_matrix = cosine_similarity_matrix(embeddings)

query_idx = 0
similarities = sim_matrix[query_idx]
top_k = np.argsort(similarities)[::-1][1:6]
print(f"Öğe 0'a en benzer 5: {top_k}")
print(f"Benzerlikler: {similarities[top_k]}")
```

`model.encode(text)` çağırıp sonra bir vektör veritabanı aradığında, kaputun altında bu olur. Embedding modeli metni vektörlere eşler. Vektör veritabanı sorgu vektörün ile depolanan her vektör arasında kosinüs benzerliği (veya dot product) hesaplar, hepsini kontrol etmekten kaçınmak için ANN algoritmaları kullanır.

## Alıştırmalar

1. (1, 2, 3) ve (4, 0, 6) arasındaki L1, L2 ve L-sonsuz uzaklıklarını hesapla. Herhangi bir nokta çifti için L-inf <= L2 <= L1'in her zaman geçerli olduğunu doğrula. Bu sıralamanın neden garanti olduğunu kanıtla.

2. Kosinüs benzerliği yüksek (> 0.9) ama L2 uzaklığı büyük (> 10) olan iki vektör oluştur. Geometrik olarak ne olduğunu açıkla. Sonra kosinüs benzerliği düşük (< 0.3) ama L2 uzaklığı küçük (< 0.5) olan iki vektör oluştur.

3. Bir veri seti ve sorgu noktası alıp L1, L2, kosinüs ve Mahalanobis uzaklığı altında en yakın komşuyu döndüren bir fonksiyon implemente et. Dördünün de hangi noktanın en yakın olduğu konusunda anlaşmadığı bir veri seti bul.

4. CDF yöntemini kullanarak [0.5, 0.5, 0, 0] ve [0, 0, 0.5, 0.5] arasındaki Wasserstein uzaklığını elle hesapla. Sonra [0.25, 0.25, 0.25, 0.25] ve [0, 0, 0.5, 0.5] arasındakini hesapla. Hangisi daha büyük ve neden?

5. Yaklaşık Jaccard benzerliği için MinHash implemente et. 100 rastgele küme üret, tüm çiftler için tam Jaccard hesapla ve 50, 100 ve 200 hash fonksiyonu kullanan MinHash yaklaşımı ile karşılaştır. Yaklaşım hatasını çiz.

## Anahtar Terimler

| Terim | İnsanlar ne der | Aslında ne demek |
|------|----------------|----------------------|
| Norm | "Bir vektörün boyutu" | Bir vektörü negatif olmayan bir skalere eşleyen, üçgen eşitsizliğini, mutlak homojenliği ve sadece sıfır vektör için sıfırlığı karşılayan bir fonksiyon |
| L1 norm | "Manhattan uzaklığı" | Mutlak bileşen değerlerinin toplamı. Optimizasyonda sparsity üretir. Aykırı değerlere robust |
| L2 norm | "Öklid uzaklığı" | Kare bileşenlerin toplamının karekökü. Öklid uzayında düz çizgi uzaklığı |
| Lp norm | "Genelleştirilmiş norm" | Mutlak bileşenlerin p'inci kuvvetlerinin toplamının p'inci kökü. L1 ve L2 özel durumlar |
| L-sonsuz norm | "Max norm" veya "Chebyshev uzaklığı" | Maksimum mutlak bileşen değeri. Lp'nin p sonsuza yaklaşırken limiti |
| Kosinüs benzerliği | "Vektörler arasındaki açı" | Her iki büyüklüğe bölünerek normalize edilmiş dot product. -1 ile +1 arasında. Vektör uzunluğunu yok sayar |
| Kosinüs uzaklığı | "1 eksi kosinüs benzerliği" | Kosinüs benzerliğini bir uzaklığa çevirir. 0 ile 2 arasında |
| Dot product | "Normalleştirilmemiş kosinüs" | Bileşen bazlı çarpımların toplamı. Kosinüs benzerliği çarpı her iki büyüklüğe eşit |
| Mahalanobis uzaklığı | "Korelasyon-farkında uzaklık" | Veri kovaryans matrisi kullanılarak beyazlatılmış (de-correlate edilmiş ve normalize edilmiş) bir uzayda L2 uzaklığı |
| Jaccard benzerliği | "Küme örtüşmesi" | Kesişimin boyutu bölü birleşimin boyutu. Kümeler için, vektörler için değil |
| Edit distance | "Levenshtein uzaklığı" | Bir string'i diğerine dönüştürmek için minimum ekleme, silme ve değiştirme sayısı |
| KL diverjansı | "Dağılımlar arası uzaklık" | Gerçek bir uzaklık değil (simetrik değil). P'yi kodlamak için Q kullanmaktan ekstra bit'leri ölçer |
| Wasserstein uzaklığı | "Earth mover's distance" | Bir dağılımdan diğerine kütle taşımak için minimum iş. Gerçek bir metrik |
| Approximate nearest neighbor | "ANN araması" | Tam aramadan çok daha hızlı yaklaşık olarak en yakın noktaları bulan algoritmalar (HNSW, LSH, IVF) |
| HNSW | "Vektör DB algoritması" | Hierarchical Navigable Small World grafı. Hızlı yaklaşık en yakın komşu araması için çok katmanlı graf |
| L1 regularization | "Lasso" | Weight'lerin L1 normunu loss'a eklemek. Weight'leri sıfıra iter (sparsity) |
| L2 regularization | "Ridge" veya "weight decay" | Weight'lerin kareli L2 normunu loss'a eklemek. Sparsity olmadan weight'leri sıfıra doğru küçültür |
| Elastic Net | "L1 + L2" | L1 ve L2 regularization'ı birleştirir. İlişkili feature gruplarını her ikisinden daha iyi halleder |

## İleri Okuma

- [FAISS: A Library for Efficient Similarity Search](https://github.com/facebookresearch/faiss) - Meta'nın milyar ölçekli ANN araması için kütüphanesi
- [Wasserstein GAN (Arjovsky et al., 2017)](https://arxiv.org/abs/1701.07875) - Earth Mover's distance'ı GAN'lara tanıtan makale
- [Locality-Sensitive Hashing (Indyk & Motwani, 1998)](https://dl.acm.org/doi/10.1145/276698.276876) - temel ANN algoritması
- [Efficient Estimation of Word Representations (Mikolov et al., 2013)](https://arxiv.org/abs/1301.3781) - Word2Vec, embedding'ler için kosinüs benzerliğinin varsayılan olduğu yer
- [sklearn.neighbors documentation](https://scikit-learn.org/stable/modules/neighbors.html) - scikit-learn'de uzaklık metrikleri ve komşu algoritmaları için pratik rehber
