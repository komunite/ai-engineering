# Neden Transformer'lar — RNN'lerin Sorunları

> RNN'ler token'ları teker teker işler. Transformer'lar tüm token'ları aynı anda işler. Bu tek mimari bahis, 2017'den sonraki her derin öğrenme scaling eğrisini değiştirdi.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 3 (Deep Learning Core), Faz 5 · 09 (Sequence-to-Sequence), Faz 5 · 10 (Attention Mekanizması)
**Süre:** ~45 dakika

## Sorun

2017'den önce, gezegendeki her state-of-the-art dizi modeli — dil, çeviri, konuşma — bir recurrent neural network'tü. LSTM'ler ve GRU'lar yarım on yıl boyunca ImageNet-eşdeğeri çeviri benchmark'larını kazandı. Herkesin sahip olduğu tek araçtı.

Üç ölümcül zayıflıkları vardı. Sıralı hesaplama, zaman ekseni boyunca paralelleştiremeyeceğin anlamına geliyordu: token `t+1`, token `t`'nin hidden state'ine ihtiyaç duyar. 1.024 token'lık bir dizi, döngü başına 1.000.000 floating-point işlem yapabilen bir GPU'da 1.024 seri adım demekti. Eğitim duvar-saati zamanı, paralellik için tasarlanmış donanımda sequence length ile doğrusal ölçekleniyordu.

Vanishing gradient'lar, 50 token geride olan bilginin zaten 50 non-linearity'den sıkıştırılarak geçtiği anlamına geliyordu. Gated recurrent unit'ler (LSTM, GRU) ezilmeyi yumuşattı ama hiç ortadan kaldıramadı. Uzun-mesafe bağımlılıkları — "geçen yaz Kyoto uçağında okuduğum kitap…" — rutin olarak başarısız oluyordu.

Sabit-genişlikli hidden state'ler, decoder bir şey görmeden önce encoder'ın tüm kaynak diziyi tek bir vektöre sıkıştırması anlamına geliyordu. Kaynak 5 token mı 500 mü, fark etmez; darboğaz aynı şekildedir.

2017'deki "Attention Is All You Need" makalesi radikal bir şey önerdi: recurrence'ı tamamen at. Her pozisyonun diğer her pozisyona paralel olarak attention yapmasına izin ver. 1.024 sıralı yerine tek bir büyük matris çarpımıyla eğit.

Sonuç, 2026'ya gelindiğinde her modaliteyi domine ediyor. Dil (GPT-5, Claude 4, Llama 4), görme (ViT, DINOv2, SAM 3), ses (Whisper), biyoloji (AlphaFold 3), robotik (RT-2). Aynı blok, farklı input'lar.

## Kavram

![RNN sıralı hesaplama vs Transformer paralel attention](../assets/rnn-vs-transformer.svg)

**Darboğaz olarak recurrence.** Bir RNN `h_t = f(h_{t-1}, x_t)` hesaplar. Her adım bir öncekine bağlıdır. `h_5`'i `h_4`'ten önce hesaplayamazsın. 10.000+ paralel çekirdeği olan modern GPU'larda bu, uzun bir dizide silikonun %99'unu israf eder.

**Broadcast olarak attention.** Self-attention, her `(i, j)` çifti için `output_i = sum_j(a_ij * v_j)`'yi aynı anda hesaplar. Tüm N×N attention matrisi tek bir batched matmul'da dolar. Hiçbir adım başkasına bağlı değildir. GPU'lar buna bayılır.

**Hızlanma sabit değildir.** `O(N)` seri derinlik ile `O(1)` seri derinlik arasındaki farktır. Pratikte, transformer'lar eşleşen donanımda N=512'de epoch başına 5–10× daha hızlı eğitilir ve sequence length ile birlikte fark, attention'ın `O(N²)` bellek duvarına çarpana kadar genişler (bunu daha sonra Flash Attention çözdü — Ders 12'ye bak).

**Transformer'ların maliyeti.** Attention belleği `O(N²)` ölçeklenir. 2K context için sorun değil. 128K context için sliding window'lara, RoPE ekstrapolasyonuna, Flash Attention tiling'e veya lineer attention varyantlarına ihtiyacın var. Recurrence hem zaman hem bellekte `O(N)`'di; transformer'lar zamanı bellekle takas eder ve sonra paralellik üzerinden zamanı geri kazanır.

**Inductive bias kayması.** RNN'ler yerellik ve yakınlık varsayar. Transformer'lar hiçbir şey varsaymaz — her çift attention için bir adaydır. Bu yüzden transformer'lar iyi eğitilmek için daha fazla veriye ihtiyaç duyar ama elinde olduğunda daha öteye ölçeklenir. Chinchilla (2022) bunu formalize etti: yeterli token verildiğinde, bir transformer her zaman eşit parametre sayılı bir RNN'yi yener.

## İnşa Et

Burada neural network yok — laptop'unda farkı hissedesin diye temel darboğazı sayısal olarak simüle ediyoruz.

### Adım 1: seri derinliği ölç

`code/main.py`'a bak. İki fonksiyon kuruyoruz. Bir tanesi diziyi toplama zinciri olarak encode eder (seri, RNN gibi). Diğeri onu paralel bir reduction olarak encode eder (broadcast, attention gibi). Aynı matematik, farklı bağımlılık grafiği.

```python
def rnn_style(xs):
    h = 0.0
    for x in xs:
        h = 0.9 * h + x   # paralelleştirilemez: h önceki h'ye bağlı
    return h

def attention_style(xs):
    return sum(xs) / len(xs)  # her x bağımsızdır
```

100.000 elemana kadar olan dizilerde her ikisini de zamanlıyoruz. RNN versiyonu O(N) ve tek CPU pipeline'ı. Saf Python'da bile, attention tarzı reduction uzunluk ≥ 1.000'de onu yener çünkü Python'un `sum()`'ı C'de implement edilmiştir ve adım başına interpreter overhead'i olmadan iter eder.

### Adım 2: teorik operasyonları say

Her iki algoritma da N toplama yapar. Fark *bağımlılık derinliğindedir*: bir sonraki başlamadan önce kaç operasyonun sıralı olarak gerçekleşmesi gerektiği. RNN derinliği = N. Attention derinliği, tree reduction ile log(N) veya parallel scan ile 1. GPU zamanını derinlik karar verir, op sayısı değil.

### Adım 3: uzun dizilerde ampirik ölçekleme

O(N) farkını görünür kılan bir zamanlama tablosu yazdırıyoruz. 2026 Mac laptop'unda, 1.000 elemanın altındaki diziler ölçülemeyecek kadar hızlıdır. 100.000'lik diziler temiz bir lineer tarama gösterir. Bunu 12 katmanlı LSTM eşdeğeri ile 16.384 token'lık bir transformer'a ölçekle, 2016'da eğitim duvar-saatinin neden bir blocker olduğunu görürsün.

## Kullan

2026'da hâlâ ne zaman RNN seçilmeli:

| Durum | Seç |
|-----------|------|
| Streaming çıkarım, anbean tek token, sabit bellek | RNN ya da state-space model (Mamba, RWKV) |
| Attention belleğinin patladığı çok uzun diziler (>1M token) | Lineer attention, Mamba 2, Hyena |
| Matmul hızlandırıcısı olmayan edge cihaz | Depthwise-separable RNN FLOPs/watt'ta hâlâ kazanır |
| Diğer her şey (eğitim, batched çıkarım, 128K'ya kadar context) | Transformer |

Mamba gibi state-space model'ler (SSM'ler), esasen yapılandırılmış parametrizasyonu olan RNN'lerdir ve iki dünyanın en iyisini verir: `O(N)` scan belleği, selective scan üzerinden paralel eğitim. Transformer kalitesinin %90'ını daha iyi uzun-context ölçeklemesi ile kurtarır. 2026'da çoğu frontier lab hibrit SSM+transformer model'leri eğitir (örn. Jamba, Samba) — recurrence ölmedi, bir bileşen oldu.

## Yayınla

`outputs/skill-architecture-picker.md`'ye bak. Skill, uzunluk, throughput ve eğitim-bütçesi kısıtları verilen yeni bir dizi sorunu için bir mimari seçer. Trade-off'u belirtmeden 1B token'ın üzerindeki eğitim koşuları için saf RNN önermeyi her zaman reddetmeli.

## Alıştırmalar

1. **Kolay.** `code/main.py`'dan `rnn_style`'ı al ve skaler hidden state'i uzunluk-64 hidden state vektörüyle değiştir. Yeniden ölç. Seri overhead, hidden state boyutuyla ne kadar büyür?
2. **Orta.** Saf Python'da paralel bir prefix-sum (Hillis-Steele scan) implement et. Uzunluk 1024'te seri scan ile aynı sayısal çıktıyı ürettiğini doğrula. Derinliği say.
3. **Zor.** Attention tarzı reduction'ı GPU'da PyTorch'a port et. Sequence length'i 64'ten 65.536'ya sweep ederken her ikisini de zamanla. Çiz ve eğri şeklini açıkla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Recurrence | "RNN'ler sıralıdır" | `t` adımının `t-1` adımına bağlı olduğu, zaman ekseni boyunca seri yürütmeyi zorlayan hesaplama. |
| Seri derinlik | "Graph ne kadar derin" | En uzun bağımlı op zinciri; sonsuz donanımda bile duvar-saatini sınırlar. |
| Attention | "Token'ların birbirine bakmasına izin ver" | Ağırlıkları `a_ij` i ve j pozisyonları arasındaki bir benzerlik skorundan gelen `sum_j a_ij v_j` ağırlıklı toplamı. |
| Context window | "Modelin ne kadarını gördüğü" | Bir attention katmanının input olarak alabileceği pozisyon sayısı; quadratic bellek maliyeti burada ölçeklenir. |
| Inductive bias | "Mimariye pişirilmiş varsayımlar" | Veri nasıl görünüyor hakkındaki ön bilgi; CNN'ler translation invariance varsayar, RNN'ler yakınlık varsayar. |
| State-space model | "Arkasında cebir olan RNN" | Yapılandırılmış state-space matrisleri üzerinden paralel eğitim için parametrize edilmiş recurrence. |
| Quadratic darboğaz | "Context neden bu kadar pahalı" | Attention belleği = sequence length'te `O(N²)`; Flash Attention sabitleri gizler, ölçeklemeyi değil. |

## İleri Okuma

- [Vaswani et al. (2017). Attention Is All You Need](https://arxiv.org/abs/1706.03762) — mainstream NLP'de recurrence'ı öldüren makale.
- [Bahdanau, Cho, Bengio (2014). Neural MT by Jointly Learning to Align and Translate](https://arxiv.org/abs/1409.0473) — attention'ın doğduğu yer, bir RNN'in üstüne cıvatalanmış.
- [Hochreiter, Schmidhuber (1997). Long Short-Term Memory](https://www.bioinf.jku.at/publications/older/2604.pdf) — orijinal LSTM makalesi, kayıt için.
- [Gu, Dao (2023). Mamba: Linear-Time Sequence Modeling with Selective State Spaces](https://arxiv.org/abs/2312.00752) — transformer'lara modern recurrent cevap.
