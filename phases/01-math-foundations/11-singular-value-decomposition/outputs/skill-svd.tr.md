---
name: skill-svd
description: SVD'yi sıkıştırma, gürültü temizleme, öneri sistemleri ve least-squares çözümleri gibi gerçek problemlere uygula
phase: 1
lesson: 11
---

Sen Singular Value Decomposition'ı pratik mühendislik problemlerine uygulamada uzmansın. Matris, veri sıkıştırma, gürültü, eksik veri ya da lineer sistem içeren bir görev verildiğinde, SVD'nin doğru araç olup olmadığını ve nasıl uygulanacağını belirle.

## Karar Çerçevesi

### Adım 1: Problem tipini belirle

- **Veri sıkıştırma / boyut indirgeme**: Truncated SVD kullan. En büyük k singular value'yu tut. k'yı enerji eşiği (yaygın hedef %95) ya da downstream görev performansına göre seç.
- **Gürültü azaltma**: Tam SVD hesapla. Singular value spektrumunda boşluk ara. Boşluğun altını kes. Boşluk sinyali gürültüden ayırır.
- **Eksik veri / öneri sistemleri**: Eksik girdileri doldur (satır ortalamaları ya da sıfırlar), SVD hesapla, düşük rank ile yeniden kur. Production'da eksik veriyi doğal olarak işleyen ALS ya da incremental SVD kullan.
- **Least-squares / pseudoinverse**: SVD hesapla. Sıfır olmayan singular value'ları tersine çevir. V Sigma+ U^T'yi hedef vektörle çarp. Normal denklemlerden daha kararlı.
- **Metin benzerliği / topic modeling**: Term-document matrisini kur. SVD uygula (bu LSA/LSI'dır). Belgeleri ve terimleri düşük rank uzaya projeksiyonla. Karşılaştırma için cosine similarity kullan.
- **Numerik rank belirleme**: SVD hesapla. En büyüğe oranla bir eşiğin üzerindeki singular value'ları say. Row reduction'dan daha güvenilir.
- **Matris normu hesabı**: Spectral norm = en büyük singular value. Frobenius normu = sqrt(singular value karelerinin toplamı). Nuclear norm = singular value'ların toplamı.
- **Condition number**: sigma_max / sigma_min. Sistemin pertürbasyonlara ne kadar duyarlı olduğunu söyler.

### Adım 2: Doğru varyantı seç

| Durum | Yöntem | Neden |
|-----------|--------|-----|
| Yoğun matris, tam ayrıştırma gerekli | `np.linalg.svd(A)` / Julia'da `svd(A)` | Standart algoritma, numerik olarak kararlı |
| Sadece en büyük k bileşen gerekli | `scipy.sparse.linalg.svds(A, k)` | k küçükken tam SVD'den hızlı |
| Sparse matris | `scipy.sparse.linalg.svds` | Sparse storage'ı verimli işler |
| Streaming veri | Incremental SVD / online SVD | Sıfırdan hesaplamadan ayrıştırmayı günceller |
| Eksik veri (öneri) | ALS, Funk SVD ya da NMF | Standart SVD eksiksiz matris ister |
| Çok büyük matris (milyonlarca satır) | Randomized SVD (`sklearn.utils.extmath.randomized_svd`) | O(mn min(m,n)) yerine O(mn log k) |
| Centered veride PCA | Centered veri matrisinin SVD'si | Covariance'ın eigendecomposition'ına eşdeğer, ama daha kararlı |

### Adım 3: k rank'ini seç

- **Enerji eşiği**: Kümülatif enerji = sum(sigma_1^2 ... sigma_k^2) / sum(tüm sigma^2). Enerji 0.95'i (ya da yüksek doğruluk için 0.99'u) aşınca dur.
- **Boşluk tespiti**: Singular value'ları çiz. Keskin bir düşüş ara. Boşluk sinyal ile gürültü sınırını gösterir.
- **Çapraz doğrulama**: Downstream görevler için k'yı tara ve held-out veride performans ölç.
- **Dirsek yöntemi**: Reconstruction error'a karşı k çiz. Dirsek, daha fazla bileşen eklemenin yardımcı olmadığı yerdir.
- **Domain bilgisi**: Verinin d altta yatan faktörü olduğunu biliyorsan, k = d kullan.

### Adım 4: Sonuçları doğrula

- **Reconstruction error**: ||A - A_k|| / ||A|| hesapla. Anlamlı truncation ise küçük olmalı.
- **Açıklanan varyans**: PCA/sıkıştırma için, yakalanan toplam varyans (enerji) oranını raporla.
- **Downstream görev performansı**: SVD bir ön işleme adımıysa uçtan uca metriği ölç.
- **Görsel inceleme**: Görüntüler için orijinal ve yeniden kurulmuş görüntüyü görsel karşılaştır. Öneriler için tahminleri bilinen rating'lerle karşılaştır.

## Yaygın Hatalar

- A^T A'nın eigendecomposition'ı üzerinden SVD hesaplamak. Bu, condition number'ı kareler ve numerik hassasiyeti kaybeder. Özel bir SVD rutini kullan.
- Sadece en büyük k bileşene ihtiyaç varken tam SVD kullanmak. Büyük matrisler için truncated ya da randomized SVD kullan.
- Eksik girdileri olan matrise doğrudan SVD uygulamak. Standart SVD eksiksiz matris ister. Bunun yerine matris tamamlama yöntemleri (ALS, Funk SVD) kullan.
- Centering'i unutmak. PCA için SVD'den önce veri centered (ortalama çıkarılmış) olmalı. Centering olmadan ilk bileşen varyansı değil ortalamayı yakalar.
- Aşırı truncate etmek. Çok az singular value tutarsan sinyali kaybedersin. Çok tutarsan gürültüyü tutarsın. Enerji eşikleri ya da çapraz doğrulama kullan.
- SVD'yi eigendecomposition ile karıştırmak. SVD herhangi bir matriste çalışır (her shape, her rank). Eigendecomposition tam eigenvector setine sahip kare matris ister. Simetrik pozitif yarı-tanımlı matrisler için aynıdırlar.

## Kod Kalıpları

### Hızlı sıkıştırma
```python
U, S, Vt = np.linalg.svd(A, full_matrices=False)
k = np.searchsorted(np.cumsum(S**2) / np.sum(S**2), 0.95) + 1
A_compressed = U[:, :k] @ np.diag(S[:k]) @ Vt[:k, :]
```

### Least-squares için pseudoinverse
```python
U, S, Vt = np.linalg.svd(A, full_matrices=False)
S_inv = np.array([1/s if s > 1e-10 else 0 for s in S])
x = Vt.T @ np.diag(S_inv) @ U.T @ b
```

### Gürültü temizleme
```python
U, S, Vt = np.linalg.svd(noisy_data, full_matrices=False)
k = find_gap(S)
clean_data = U[:, :k] @ np.diag(S[:k]) @ Vt[:k, :]
```

### Büyük ölçekli PCA
```python
from sklearn.utils.extmath import randomized_svd
U, S, Vt = randomized_svd(X_centered, n_components=50, random_state=42)
explained_variance = S**2 / (n_samples - 1)
```

## SVD'yi NE ZAMAN kullanmamalı

- Matris çok seyrek ve sadece birkaç bileşene ihtiyacın var. Doğrudan sparse eigensolver kullan.
- Negatif olmayan faktörlere ihtiyacın var (topic modeling, spectral unmixing). NMF kullan.
- Veri güçlü doğrusal olmayan yapıya sahip ve lineer yöntemler yakalayamaz. Autoencoder ya da manifold learning kullan.
- Streaming veride gerçek zamanlı güncellemeye ihtiyacın var ve matris sürekli değişiyor. Incremental/online SVD ya da yaklaşık yöntemler kullan.
- Matris belleğe sığıyor ama randomized SVD bile çok yavaş kalıyor. Sketching yöntemleri ya da örneklem tabanlı yaklaşımları düşün.

## Hesaplama Maliyeti

| Yöntem | Zaman | Bellek |
|--------|------|-------|
| m x n matrisin tam SVD'si | O(mn min(m,n)) | O(mn) |
| Truncated SVD (en büyük k) | O(mnk) | O((m+n)k) |
| Randomized SVD (en büyük k) | O(mn log k) | O((m+n)k) |
| Power iteration (1 vektör) | O(mn * iter) | O(m+n) |

10000 x 5000 matris için:
- Tam SVD: ~250 milyar işlem
- Truncated SVD (k=50): ~2.5 milyar işlem
- Randomized SVD (k=50): ~500 milyon işlem

Ölçek ve doğruluk gereksinimlerine uygun yöntemi seç.
