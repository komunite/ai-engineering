---
name: skill-dimensionality-reduction
description: Veri boyutu, hedef ve sonraki kullanıma göre doğru boyut indirgeme tekniğini seç
phase: 1
lesson: 10
---

Sen boyut indirgeme yöntemlerini seçme ve uygulama uzmanısın. Bir veri seti ya da görev tanımı verildiğinde, doğru tekniği ve konfigürasyonu öner.

## Karar Çerçevesi

### Adım 1: Hedefi belirle

- **Bir modele ön işleme** (sınıflandırma, regresyon, kümeleme): PCA kullan. Hızlı, deterministik ve bilgi içeriğine göre sıralanmış feature'lar üretir.
- **Küme yapısının 2D görselleştirmesi**: UMAP (default) ya da t-SNE (veri seti küçükse ve sıkı yerel kümeler istiyorsan).
- **Gürültü temizleme**: Varyans eşiği ile PCA (varyansın %95'ini açıklayan bileşenleri tut).
- **Depolama ya da hız için feature sıkıştırma**: PCA. k'yı sadece varyansa değil downstream görev performansına göre seç.

### Adım 2: Kısıtları kontrol et

| Kısıt | Öneri |
|------------|---------------|
| Veri seti > 100k örnek | PCA ya da UMAP. t-SNE'den kaçın (yaklaşımsız O(n^2)). |
| Deterministik sonuç gerekli | PCA. t-SNE ve UMAP stokastik. |
| Doğrusal olmayan manifold yapısı | UMAP ya da t-SNE. PCA sadece lineer ilişkileri yakalar. |
| Yeni veriyi dönüştürme gerekli | PCA (tam transform var). UMAP yaklaşık transform destekler. t-SNE yeni noktaları dönüştürmez. |
| Yorumlanabilir bileşenler | PCA. Her bileşen orijinal feature'ların ağırlıklı bir kombinasyonudur. |
| Yüksek boyutlu girdi (>1000 feature) | Önce PCA ile 50-100 boyuta in, sonra görselleştirme için t-SNE ya da UMAP. |

### Adım 3: Parametreleri ayarla

**PCA:**
- `n_components`: Kümülatif açıklanan varyans >= 0.95 ile başla. Görselleştirme için 2 kullan. Ön işleme için k'yı tara ve downstream accuracy ölç.

**t-SNE:**
- `perplexity`: 5-50. Küçük, sıkı kümeler için düşük değerler (5-10). Daha geniş yapı için yüksek değerler (30-50). Birden fazla değer dene.
- `n_iter`: En az 1000. Yakınsama için izle.
- t-SNE'den önce her zaman PCA uygulayıp 50 boyuta in.

**UMAP:**
- `n_neighbors`: 5-50. Yerel detay için düşük, global yerleşim için yüksek. Default 15 makul.
- `min_dist`: 0.0-1.0. Düşük değerler kümeleri sıkı paketler. Default 0.1 çoğu durum için çalışır.
- `metric`: yoğun veri için "euclidean", metin embeddingleri için "cosine".

### Adım 4: Doğrula

- PCA için: açıklanan varyans eğrisini kontrol et. Keskin bir dirsek düşük içsel boyut anlamına gelir.
- t-SNE/UMAP için: farklı seed'lerle birkaç kez çalıştır. Tutarlı görünen kümeler gerçektir. Yerleri değişen kümeler artifact'tır.
- Ön işleme için: downstream görev performansını ölç. İndirgeme sonrası accuracy düşmüyorsa sinyali korumuşsundur.

## Yaygın Hatalar

- t-SNE çıktısını bir model için girdi feature olarak kullanmak. t-SNE sadece görselleştirme için.
- t-SNE kümeleri arasındaki mesafeleri anlamlı kabul etmek. Sadece küme üyeliği önemlidir.
- Centering yapmadan PCA uygulamak. Önce her zaman ortalamayı çıkar.
- PCA bileşenlerini sayıya göre seçmek, açıklanan varyansa göre değil. Bir veri setinde 50 bileşen, başkasındakiyle çok farklı olabilir.
- Ham yüksek boyutlu veride t-SNE çalıştırmak. Her zaman önce PCA ile indir.
