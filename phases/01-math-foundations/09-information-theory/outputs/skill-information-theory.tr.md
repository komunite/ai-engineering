---
name: skill-information-theory
description: Bilgi teorisi kavramlarını ML loss fonksiyonlarına, model değerlendirmesine ve feature seçimine uygula
version: 1.0.0
phase: 1
lesson: 9
tags: [information-theory, entropy, loss-functions]
---

# ML için Bilgi Teorisi

Makine öğrenmesi sistemlerinde entropy, cross-entropy, KL divergence ve mutual information ne zaman kullanılır.

## Karar Kontrol Listesi

1. Tek bir dağılımdaki belirsizliği mi ölçüyorsun? **Entropy** kullan.
2. Bir modelin gerçek etiketlere ne kadar yaklaştığını mı ölçüyorsun? **Cross-entropy** kullan (bu senin sınıflandırma loss'un).
3. İki dağılım arasındaki mesafeyi mi ölçüyorsun? **KL divergence** kullan.
4. İki değişkenin ilişkili olup olmadığını mı kontrol ediyorsun? **Mutual information** kullan.
5. Dil modeli kalitesi mi raporluyorsun? **Perplexity** kullan (cross-entropy'nin üsteli).
6. Bir modeli başka bir modele mi distill ediyorsun? Öğretmenden öğrenciye **KL divergence**'i minimize et.

## Hangi ölçüyü ne zaman kullanmalı

| Ölçü | Formül | Kullanım | ML uygulaması |
|---|---|---|---|
| Entropy H(P) | -sum(p log p) | Bu dağılım ne kadar belirsiz? | Veri karmaşıklığı, maksimum entropi modelleri |
| Cross-entropy H(P,Q) | -sum(p log q) | Q modeli gerçek P'yi tahmin etmekte ne kadar iyi? | Sınıflandırma loss'u, dil modeli loss'u |
| KL divergence D(P\|\|Q) | sum(p log(p/q)) | P ve Q ne kadar farklı? | VAE loss'u (ELBO), knowledge distillation, RLHF |
| Mutual information I(X;Y) | H(X) - H(X\|Y) | Y, X hakkında ne kadar bilgi veriyor? | Feature seçimi, representation learning |
| Perplexity | exp(H(P,Q)) ya da 2^H | Model ne kadar kafası karışık? | Dil modeli değerlendirmesi |
| Şartlı entropi H(X\|Y) | -sum(p(x,y) log p(x\|y)) | Y bilindikten sonra X'teki kalan belirsizlik | Feature bilgilendiriciliği |

## Anahtar ilişkiler

```
Cross-entropy  = Entropy + KL divergence
H(P, Q)        = H(P)   + D_KL(P || Q)

H(P) eğitim boyunca sabit olduğundan:
  Cross-entropy minimize etmek = KL divergence minimize etmek

Mutual information = Entropy - Şartlı entropi
I(X; Y) = H(X) - H(X|Y) = H(Y) - H(Y|X)

Perplexity = exp(nats cinsinden cross-entropy)
           = 2^(bit cinsinden cross-entropy)
```

## Hızlı referans: formüller ve birimler

| Formül | Bit (log base 2) | Nat (log base e) |
|---|---|---|
| Bilgi: -log(p) | -log2(p) | -ln(p) |
| Entropy: -sum(p log p) | bit | nat |
| 1 nat = | 1.4427 bit | 1 nat |
| PyTorch default | -- | nat |
| Bilgi teorisi makaleleri | bit | -- |

## Değer yorumlaması

| Entropy değeri | Ne anlama gelir |
|---|---|
| 0 | Deterministik. Bir sonuç olasılığı 1. |
| log(n) | Maksimum belirsizlik. n çıktı üzerinde uniform dağılım. |
| Düşük | Dağılım sivri. Model emin. |
| Yüksek | Dağılım düz. Model emin değil. |

| Perplexity değeri | Dil modeli kalitesi |
|---|---|
| 1 | Mükemmel tahmin (pratikte asla olmaz) |
| 10 | Ortalama ~10 eşit olası token arasından seçim |
| 50 | Standart benchmarklarda GPT-2 seviyesi |
| < 10 | İyi temsil edilen domain'lerde state-of-the-art |

## Yaygın hatalar

- KL divergence'i hesaplayıp simetrik gibi muamele etmek. D_KL(P||Q) != D_KL(Q||P). Simetrik bir ölçü için Jensen-Shannon divergence kullan: JS = 0.5 * KL(P||M) + 0.5 * KL(Q||M), M = 0.5*(P+Q).
- One-hot etiketlerle cross-entropy'nin -log(p_true_class)'a sadeleştiğini unutmak. Gerçek dağılım one-hot iken tüm sınıflar üzerinde toplam almaya gerek yok.
- Kodda log base 2 kullanıp nat olarak raporlamak (ya da tersi). PyTorch default olarak doğal log kullanır. Nat'tan bit'e çevirmek için log2(e) = 1.4427 ile çarp.
- Boş ya da sıfır olasılıklı olayın entropy'sini hesaplamak. Kural: 0 * log(0) = 0, çünkü lim(p->0) p*log(p) = 0.
- Farklı kelime dağarcığı boyutlarında perplexity karşılaştırmak. Vocab size 50k ve perplexity 30 olan bir model, vocab size 10k ve perplexity 30 olanla doğrudan karşılaştırılamaz.

## Her kavramın production ML'de göründüğü yer

| Kavram | Nerede görürsün |
|---|---|
| Cross-entropy loss | Her sınıflandırma modelinde (nn.CrossEntropyLoss) |
| KL divergence | VAE ELBO, PPO clipping, knowledge distillation |
| Entropy regularization | RL'de keşif bonusu (yüksek entropy = daha fazla keşif) |
| Mutual information | Feature seçimi, InfoNCE loss (contrastive learning) |
| Perplexity | Dil modeli benchmark'ları (düşük = daha iyi) |
| Label smoothing | One-hot'u soft hedeflerle değiştirir, cross-entropy aşırı güvenini azaltır |
| Temperature scaling | Softmax öncesi logit'leri T'ye böler, çıktı entropy'sini kontrol eder |
