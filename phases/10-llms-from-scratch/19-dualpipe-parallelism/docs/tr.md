# DualPipe Parallelism

> DeepSeek-V3, MoE expert'leri node'lar arasında dağıtılmış 2.048 H800 GPU üzerinde eğitildi. Cross-node expert all-to-all iletişimi her 1 GPU-saat compute için 1 GPU-saat comm'a mal oluyordu. GPU'lar zamanın yarısında boştaydı. DualPipe (DeepSeek, Aralık 2024) forward ve backward hesaplamayı tetikledikleri all-to-all comm'larla overlap eden bidirectional bir pipeline'dır. Bubble'lar düşer, throughput tırmanır ve iki model-parametre kopyası tutmak (ismi veren "dual") Expert Parallelism zaten expert'leri rank'lere yaydığı için ucuzdur. Bu ders DualPipe'ın aslında ne yaptığının ve Sea AI Lab'ın DualPipeV iyileştirmesinin marjinal olarak daha sıkı bir bubble karşılığında neden 2x parametre maliyetini düşürdüğünün Öğrenim-tipi walkthrough'udur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, schedule simülatörü)
**Ön koşullar:** Faz 10 · 05 (distributed training, FSDP, DeepSpeed), Faz 10 · 14 (açık-model mimarileri ve MoE)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- DualPipe forward-backward chunk'ının dört bileşenini ve her birinin neden kendi overlap penceresini aldığını adlandır.
- Ölçekte pipeline bubble problemini ve pratikte vs pazarlamada "bubble-free"un ne anlama geldiğini açıkla.
- 8 PP rank ve 16 micro-batch için elle bir DualPipe schedule'ı izle ve forward ve reverse stream'lerin birbirinin boş slot'larını doldurduğunu doğrula.
- DualPipeV'in (Sea AI Lab, 2025) yaptığı tradeoff'u ifade et: Expert Parallelism inaktif olduğunda biraz daha büyük bir bubble maliyetiyle 2x parametre replikasyonunu düşürür.

## Sorun

2k H800 GPU üzerinde 671B MoE model eğitmek üç birleşen darboğaza koşar:

1. **Memory baskısı.** Her GPU modelin bir dilimini tutar. 128 head üzerinde 61 katman boyunca sequence 8k'da activation memory devasadır.
2. **Pipeline bubble'ları.** Geleneksel pipeline parallelism (GPipe, 1F1B) GPU'ları aşamasının input'unu veya gradient'ini beklerken boş bırakır. 8 aşamada, 1F1B scheduling ile bile GPU zamanının kabaca %12'si bubble olabilir.
3. **Cross-node all-to-all.** Expert parallelism ile MoE expert'leri node'lar arasına dağıtır. Her forward pass token'ları expert'lerine dispatch etmek için bir all-to-all ve birleştirmek için başka birini tetikler. 2k GPU'da bu kolayca 1:1 compute-to-comm oranı olur.

Bunların her birinin ayrı çözümleri var: memory için gradient checkpointing, pipeline bubble'ları için Zero Bubble (Sea AI Lab, 2023), all-to-all için expert-parallel comm kernel'leri. DualPipe'ın yaptığı onları birlikte oynatmak. Schedule compute ve comm'u tek bir forward-backward chunk içinde overlap eder, micro-batch'leri pipeline'ın her iki ucundan eşzamanlı enjekte eder ve sonuç schedule'ı tüm all-to-all'ı compute pencereleri içine gizlemek için kullanır.

Raporlanan sonuç: pipeline bubble'larının neredeyse-eliminasyonu, DeepSeek-V3'ün 14.8T-token eğitim koşusunda %95'in üzerinde GPU kullanımı.

## Kavram

### Pipeline Parallelism Tazeleme

N-katmanlı bir modeli P cihaz arasında böl. Cihaz `i` katmanları `i * N/P .. (i+1) * N/P - 1` tutar. Bir micro-batch cihaz 0'dan P-1'e forward akar, sonra P-1'den 0'a backward. Her cihaz sadece önceki cihaz output'unu gönderdiğinde forward aşamasını başlatabilir ve sadece downstream cihaz upstream gradient'i gönderdiğinde backward'ı başlatabilir.

GPipe (Huang et al., 2019) her seferinde bir micro-batch schedule eder, ki bu GPU zamanının çoğunu israf eder. 1F1B (Narayanan et al., 2021) birden fazla micro-batch için forward ve backward pass'leri interleave eder. Zero Bubble (Qi et al., 2023) backward pass'i iki parçaya böler — backward-for-input (B) ve backward-for-weights (W) — ve bubble'ı doldurmak için onları schedule eder. Zero Bubble'dan sonra, pipeline neredeyse sıkıdır.

DualPipe sonraki adım. Üstüne iki fikir ekler:

### Fikir 1: Chunk Ayrıştırma

Her forward chunk dört bileşene bölünür:

- **Attention.** Q/K/V projeksiyonları, attention, output projeksiyonu.
- **All-to-all dispatch.** Token'ları expert'lerine gönderen cross-node iletişimi.
- **MLP.** MoE expert hesaplaması.
- **All-to-all combine.** Expert output'larını geri getiren cross-node iletişimi.

Bir backward chunk bunların her birinin gradient versiyonlarını ekler. DualPipe bunları all-to-all dispatch sonraki chunk'ın attention compute'u ile paralel gerçekleşecek şekilde ve all-to-all combine takip eden chunk'ın MLP compute'u ile paralel gerçekleşecek şekilde schedule eder.

### Fikir 2: Bidirectional Scheduling

Çoğu pipeline schedule micro-batch'leri aşama 0'dan enjekte eder ve aşama P-1'e doğru akar. DualPipe micro-batch'leri HER İKİ uçtan enjekte eder. Aşama 0 oradan kaynaklanan forward micro-batch'leri görür; aşama P-1 oradan kaynaklanan forward micro-batch'leri de görür. İki stream ortada buluşur.

Bunun çalışması için, cihaz `i` HEM erken-pipeline katmanı `i`'yi HEM geç-pipeline katmanı `P - 1 - i`'yi tutmalı. Bu DualPipe'ın "dual" kısmı: her cihaz servis etmesi gereken model katmanlarının iki kopyasını tutar (her yön için bir tane). DeepSeek-V3 ölçeğinde, bu 2x parametre replikasyon maliyetidir. Expert Parallelism zaten MoE expert'lerini o kadar inceltir ki non-expert katmanlarını iki kez replicate etmek küçük patatestir.

Kritik olarak, bir yöndeki forward stream ve diğer yöndeki backward stream tam olarak tek-yön bir schedule'da bubble'ların olduğu yerde overlap eder. Bubble'lar kaybolur.

### Elle İzlenmiş Bir Schedule

P = 4 rank, 8 micro-batch, 4 forward / 4 reverse olarak bölünmüş düşün. Zaman soldan sağa hareket eder; satırlar cihaz rank'leridir.

```
           Zaman →
rank 0:  F1 F2 F3 F4  F5R F6R F7R F8R  B1 B2 B3 B4  ...
rank 1:     F1 F2 F3  F4/F5R F6R F7R   B1 B2 ...
rank 2:        F1 F2  F3/F5R F4/F6R    B1 ...
rank 3:           F1  F2/F5R F3/F6R    ...
```

"F4/F5R" notasyonunu okumak: rank 1 aynı zaman slot'unda micro-batch 4'ün forward'ını (pipeline'da soldan-sağa giden) VE micro-batch 5'in forward'ını (sağdan-sola giden) çalıştırıyor. Operasyonel olarak "bidirectional"in anlamı budur.

Rank 2'de çapraz stream'ler daha erken overlap eder, rank 0 ve P-1'de en geç overlap eder. Schedule'ın kararlı orta fazında, her rank Y-yönü-backward ile overlap edilmiş X-yönü-forward çalıştırır. Compute meşgul. Forward pass için all-to-all dispatch'ler backward compute içinde saklanır. All-to-all combine'lar forward compute içinde saklanır. Bubble'lar sıkıştırılır.

### Bubble Muhasebesi

Standart 1F1B pipeline bubble'ı (rank başına israf edilen zaman):

```
bubble_1F1B = (P - 1) * forward_chunk_time
```

Zero Bubble iyileştirmesi bunu aşağıya getirir ama sıfıra değil. DualPipe, kararlı fazda, micro-batch sayısı 2 katı pipeline derinliğine bölünebilirse sıfır bubble'a sahiptir. Kararlı fazın dışında (warmup ve cooldown), biraz bubble var ama micro-batch sayısıyla büyümez — makalenin vurguladığı bir anahtar özellik.

Pazarlama terimleriyle: "bubble-free". Teknik terimlerle: bubble'lar micro-batch sayısıyla büyümez. Sea AI Lab'ın takip analizi (DualPipeV / Cut-in-half) tam zero-bubble'ı sadece Expert Parallelism darboğaz olmadığında gösterir; EP-driven all-to-all ile, her zaman biraz scheduling tavizi vardır.

### DualPipeV — İyileştirme

Sea AI Lab (2025) EP comm overlap'in nokta olmadığında 2x parametre replikasyonun israfta olduğunu gözlemledi. DualPipeV schedule'ları bidirectional enjeksiyonu tek bir parametre kopyası üzerinde çalışan bir "V-şekli" schedule'a katlar. Bubble DualPipe'ınkinden biraz daha büyüktür, ama memory tasarrufu önemlidir. DeepSeek açık kaynak DualPipe implementasyonlarında DualPipeV'i bir EP-off modu olarak benimsedi.

Tradeoff:

| Özellik | DualPipe | DualPipeV | 1F1B | Zero Bubble |
|---------|---------|-----------|------|------------|
| Cihaz başına param kopyası | 2 | 1 | 1 | 1 |
| Micro-batch'lere karşı bubble | sabit | küçük büyüme | büyür | büyür |
| Compute-comm overlap | tam | kısmi | minimal | kısmi |
| Ne zaman kullan | EP-ağır MoE | dense veya EP-hafif | baseline | herhangi bir pipeline |

### 14.8T-Token Bir Koşu İçin Ne Anlama Geliyor

DeepSeek-V3'ün pretraining'i 2.048 H800 GPU üzerinde kabaca 2.8M GPU-saat içinde 14.8T token tüketti. Naif 1F1B ile, bunun %12-15'ini pipeline bubble'larına kaybederlerdi — 340-420K GPU-saat, tam bir 70B model eğitmek için yeterli. DualPipe çoğunu kurtardı. Katkıyı iç loglar olmadan doğrudan sayısallaştırmak zor, ama makaledeki iddia eğitim boyunca ortalama %95'in üzerinde GPU kullanımı.

Daha küçük koşular için (1k GPU altı), DualPipe overkill — pipeline bubble'ları toplam maliyete göre daha küçüktür ve dense-model eğitimi nadiren all-to-all darboğazına vurur. Çok-bin GPU ölçeğinde frontier MoE eğitimi için, etkili olarak gereklidir.

### Stack'te Nerede Oturur

- **FSDP**'ye tamamlayıcı (Faz 10 · 05). FSDP model parametrelerini rank'lere shard eder; DualPipe compute'u rank'ler arasında schedule eder. Birleşirler.
- **ZeRO-3** gradient sharding ile uyumlu. İki-kopya replikasyonun defter tutması ZeRO'nun sharded gradient'leriyle işbirliği yapmak zorundadır.
- Spesifik cluster topolojisine ayarlanmış **custom all-to-all kernel'ler** gerektirir. DeepSeek'in açık kaynak kernel'leri referans implementasyondur.

## Kullan

`code/main.py` bir pipeline schedule simülatörüdür. `(P, n_micro_batches, schedule)` alır ve 1F1B, Zero Bubble, DualPipe ve DualPipeV'in her biri için kararlı-faz kullanımını yazdırır. Bu bir öğretim aracı — sayılar makalelerdeki nitel iddialarla eşleşir, production ölçülen hızlanma hakkında bir iddia değildir.

Simülatörün değeri: farklı P ve micro-batch sayılarıyla çalıştır ve 1F1B için bubble oranının nasıl büyüdüğünü ama DualPipe için büyümediğini izle.

Gerçek bir eğitim koşusu için entegrasyon değerlendirmeleri:

- Micro-batch sayına temiz bölünen bir pipeline-parallel derinliği seç.
- Expert-parallel mesh'in bidirectional all-to-all'ı desteklediğinden emin ol. DeepSeek'in kernel'leri referanstır.
- İlk seferinde schedule'ın kendisi üzerinde bir haftalık debugging zamanı yakmayı bekle. Defter tutması karmaşık.
- Sadece toplam değil, rank başına GPU kullanımını izle. DualPipe'ın faydası straggler'ları sıkıştırmaktan gelir.

## Yayınla

Bu ders `outputs/skill-dualpipe-planner.md` üretir. Bir eğitim cluster spesifikasyonu (GPU sayısı, topoloji, interconnect, model şekli) verildiğinde, bir pipeline parallelism stratejisi, kullanılacak scheduling algoritması ve hedef ölçekte beklenen bubble oranını önerir.

## Alıştırmalar

1. `code/main.py`'ı `(P=8, micro_batches=16, schedule=dualpipe)` ve `(P=8, micro_batches=16, schedule=1f1b)` üzerinde çalıştır. GPU kullanım farkını hesapla ve eğitimin milyon token'ı başına kurtarılan GPU-saat olarak ifade et.

2. `(P=4, micro_batches=8, schedule=dualpipe)` için schedule tablosunu elle çiz. Her zaman slot'unu micro-batch ID ve yönle işaretle. Bubble'ların olmadığı ilk zaman slot'unu tanımla.

3. DeepSeek-V3 teknik raporunun Şekil 5'ini oku (arXiv:2412.19437). Bir DualPipe forward chunk içinde all-to-all dispatch için overlap penceresini tanımla. Compute schedule'ın onu nasıl sakladığını açıkla.

4. P=8 pipeline aşamalı 70B dense model ve P=16 pipeline aşamalı 671B MoE model için DualPipe'ın 2x parametre overhead'ini hesapla. MoE durumunun overhead'inin neden oransal olarak daha küçük olduğunu göster (çoğu parametre büyük EP grubu boyunca shardlı expert'lerdir).

5. DualPipe'ı Chimera (2021'den rakip bir bidirectional scheduler) ile karşılaştır. Makalenin Bölüm 3.4'ünü referans olarak kullanarak DualPipe'ın eklediği ama Chimera'nın sahip olmadığı iki spesifik özelliği tanımla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Pipeline bubble | "Rank başına boş zaman" | Pipeline aşamasının input'unu veya gradient'ini beklediği için israf edilen GPU döngüleri |
| 1F1B | "Varsayılan pipeline schedule" | Birbirine geçmiş bir forward / bir backward scheduling; DualPipe'ın yendiği baseline |
| Zero Bubble | "Sea AI Lab 2023" | Backward'ı B'ye (input gradient) ve W'ye (weight gradient) böler; pipeline'ı neredeyse tam sıkıştırır |
| DualPipe | "DeepSeek-V3 schedule" | Bidirectional pipeline + compute-comm overlap; bubble'lar micro-batch sayısıyla büyümez |
| DualPipeV | "Cut-in-half" | 2x parametre replikasyonunu biraz daha büyük bubble'lar pahasına düşüren V-şekli iyileştirme |
| Chunk | "Pipeline iş birimi" | Bir pipeline aşaması boyunca bir micro-batch'in forward veya backward pass'i |
| All-to-all dispatch | "Token'ları expert'lere gönder" | Token'ları atanmış MoE expert'lerine yönlendiren cross-node comm |
| All-to-all combine | "Expert output'larını geri getir" | MLP sonrası expert output'larını toplayan cross-node comm |
| Expert Parallelism (EP) | "GPU'lar arası expert'ler" | MoE expert'lerini rank'lere shard eder, böylece farklı GPU'lar farklı expert'leri tutar |
| Pipeline Parallelism (PP) | "GPU'lar arası katmanlar" | Model katmanlarını rank'lere shard eder; DualPipe'ın schedule ettiği boyut |
| Bubble fraction | "İsraf edilen GPU zamanı" | (bubble_time / total_time); DualPipe'ın sıfıra ittiği oran |

## İleri Okuma

- [DeepSeek-AI -- DeepSeek-V3 Technical Report (arXiv:2412.19437), Bölüm 3.3.2 ve Şekil 5](https://arxiv.org/abs/2412.19437) -- birincil DualPipe referansı
- [DeepSeek -- DualPipe GitHub repository](https://github.com/deepseek-ai/DualPipe) -- DualPipeV (Cut-in-half) modu dahil açık kaynak referans implementasyon
- [Qi et al. -- Zero Bubble Pipeline Parallelism (arXiv:2401.10241, Sea AI Lab 2023)](https://arxiv.org/abs/2401.10241) -- Zero Bubble öncüsü
- [Sea AI Lab -- DualPipe could be better without the Dual](https://sail.sea.com/blog/articles/63) -- DeepSeek'in EP-off modunu bilgilendiren DualPipeV analizi
- [Narayanan et al. -- PipeDream / 1F1B (arXiv:1806.03377, 2018-2021)](https://arxiv.org/abs/1806.03377) -- DualPipe'ın karşılaştırdığı 1F1B schedule
- [Huang et al. -- GPipe (arXiv:1811.06965, 2018)](https://arxiv.org/abs/1811.06965) -- orijinal pipeline parallelism makalesi ve bubble problemi
