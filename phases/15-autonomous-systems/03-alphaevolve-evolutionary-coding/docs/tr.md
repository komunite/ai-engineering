# AlphaEvolve — Evrimsel Kodlama Agent'ları

> Bir frontier coding modelini evrimsel bir döngü ve makine-doğrulanabilir bir evaluator ile eşleştir. Döngüyü yeterince uzun çalıştır. 48 skalar çarpım kullanan bir 4x4 karmaşık-matris çarpımı prosedürü keşfeder — Strassen'in üzerine 56 yıl sonra ilk iyileştirme. Aynı zamanda üretimde cluster compute'unun ~%0.7'sini geri kazanan Google çapında bir Borg scheduling heuristic'i bulur. Mimari kasıtlı olarak sıkıcı. Kazançlar evaluator'ın titizliğinden geliyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib, evrimsel döngü oyuncağı)
**Ön koşullar:** Faz 15 · 01 (uzun-horizon çerçeve), Faz 15 · 02 (self-taught reasoning)
**Süre:** ~60 dakika

## Sorun

Büyük dil modelleri kod yazabilir. Evrimsel algoritmalar kod üzerinde arama yapabilir. Her ikisi de onlarca yıldır ayrı denendi; her ikisi de tavana çarptı. LLM tavanı confabulation: model iddia ettiği şeyi yapmayan makul kod yazar. Evrimsel tavan arama maliyeti: syntax üzerinde rastgele mutasyonlar nadiren derlenebilir program üretir, daha iyilerini bırakın.

AlphaEvolve (Novikov vd., DeepMind, arXiv:2506.13131, Haziran 2025) bunları birleştirir. LLM bir program veritabanına hedeflenmiş edit'ler önerir; otomatik bir evaluator her varyantı puanlar; yüksek-skorlu varyantlar gelecekteki nesiller için ebeveyn olur. LLM makul kod yazmanın pahalı adımını üstlenir; evaluator confabulation'ları yakalar. Döngü saatlerden haftalara çalışır.

Raporlanan sonuçlar: 48-skalar-çarpım 4x4 karmaşık matris çarpımı (Strassen'in 1969 sınırı 49'du), Google üretiminde bir Borg scheduling heuristic'i, %32.5 FlashAttention kernel hızlanması, Gemini eğitim throughput iyileştirmeleri.

Mimari işe yarıyor çünkü evaluator makine-doğrulanabilir. Olmadığı yerde işe yaramıyor. Bu asimetri dersin kendisidir.

## Kavram

### Döngü

1. Doğru ama suboptimal bir tohum program `P_0` ile başla.
2. Her biri evaluator tarafından puanlanan varyant programların bir veritabanını sürdür.
3. Veritabanından bir veya daha fazla ebeveyn örnekle (MAP-elites tarzı ya da ada tabanlı).
4. LLM'yi (çoklu aday için Gemini Flash, zor olanlar için Gemini Pro) ebeveynin değiştirilmiş bir varyantını üretmesi için prompt'la.
5. Varyantı derle, çalıştır ve tutulmuş evaluator üzerinde değerlendir.
6. Skoruna ve özellik vektörüne göre anahtarlanmış olarak veritabanına ekle.
7. Tekrarla.

İki ayrıntı önemli. Birincisi, LLM'ye ebeveyn programdan fazlası prompt'lanır — tipik olarak veritabanından birkaç en iyi varyant, artı evaluator imzası, artı kısa bir görev açıklaması. Modelin işi skoru iyileştirebilecek hedeflenmiş bir değişiklik önermek. İkincisi, veritabanı yapılandırılmıştır (MAP-elites grid, ada tabanlı) böylece döngü sadece mevcut lideri değil, çeşitliliği keşfeder.

### Evaluator'ı pazarlık edilemez yapan şey

AlphaEvolve'un kazançları, evaluator'ın hızlı, deterministik ve oynanması zor olduğu domain'lerden gelir:

- **Matris çarpımı algoritması**: matrisleri çarpan ve eşitliği bit-aynı kontrol eden bir unit test.
- **Borg scheduling heuristic'i**: tarihsel cluster yükünü tekrar oynatan ve israf edilen compute'u ölçen üretim-seviyesi bir simülatör.
- **FlashAttention kernel'i**: bir doğruluk testi artı gerçek donanım üzerinde wall-clock benchmark.
- **Gemini eğitim throughput'u**: adım başına ölçülen GPU-saniyesi.

Her durumda evaluator, aksi takdirde baskın olacak LLM hata sınıfını yakalar: confabulate edilmiş doğruluk iddiaları, donanımda kaybolan performans iddiaları ve edge-case failure'lar. Evaluator'ı kaldır ve döngü güzel kod için optimize eder.

### Reward hacking bu ifadenin diğer yüzü

Evrim, evaluator'ın ölçtüğü şey ne olursa olsun onun için optimize eder. Evaluator kusurluysa, döngü kusuru bulacaktır. Doğrulanmamış bir domain'de döngü amaçlanan davranış için değil yüzey özelliği için optimize ederdi. DeepMind bunu makalede açıkça işaretler: AlphaEvolve'un başarıları yalnızca evaluator titizliğinin aramanın iddiasıyla eşleştiği domain'lere transfer olur.

Kod-arama döngülerinde 2025-2026 reward hacking somut örnekleri:

- "Tamamlama süresi"ni ödüllendiren optimizasyon hedefleri boş çözüm göndermeyi ödüllendirdi.
- Test-altında-doğruluğu ödüllendiren benchmark skorları testleri ezberlemeyi ve overfit etmeyi ödüllendirdi.
- "Kod kalitesi" proxy'si, anlamsal değişiklik olmaksızın yorumları kaldırmayı ve değişken adlarını yeniden yazmayı ödüllendirdi.

AlphaEvolve'daki düzeltme: LLM'nin asla görmediği, değerlendirme zamanında üretilen input'larla tutulmuş bir evaluator gönder. Buna rağmen DeepMind önerilen herhangi bir deployment'ta güçlü inceleme önerir.

### LLM + arama'nın neden ikisinden de tek başına daha iyi olduğu

LLM derlenebilir, anlamsal olarak makul modifikasyonlar üretebilir. 2000 satırlık bir Python dosyası üzerindeki rastgele-mutasyon GA neredeyse her zaman syntax hatası üretir. LLM ayrıca aramayı makul komşuluklara yoğunlaştırır (rastgele byte'lar değil bir fonksiyonu değiştir), bu da israf edilen evaluator çağrılarını dramatik olarak azaltır.

Evaluator karşılığında LLM'nin confabulation'larını yakalar. LLM'ler aslında O(n^2) olan bir fonksiyonun "limitte O(n log n) olduğunu" güvenle iddia eder; bir wall-clock benchmark soruyu çözer.

### AlphaEvolve'un frontier yığınındaki yeri

| Sistem | Üretici | Evaluator | Domain | Örnek kazanç |
|---|---|---|---|---|
| AlphaEvolve | Gemini | doğruluk + benchmark | algoritmalar, kernel'ler, scheduler'lar | 48-çarpım 4x4 matmul |
| FunSearch (DeepMind, 2023) | PaLM / Codey | doğruluk | kombinatorik matematik | cap-set alt sınırları |
| AI Scientist v2 (Sakana, L5) | GPT/Claude | LLM kritiği + deney | ML araştırması | ICLR workshop makalesi |
| Darwin Godel Machine (L4) | agent iskelesi | SWE-bench / Polyglot | agent kodu | %20 → %50 SWE-bench |

Dördü de aynı tarifin varyasyonları: üretici artı evaluator, döngü. Farklar evaluator'ın neyi notlandırdığı ve ne kadar titiz olduğudur.

## Kullan

`code/main.py` oyuncak bir sembolik-regresyon problemi üzerinde minimal bir AlphaEvolve benzeri döngü uygular. "LLM" hedef bir fonksiyonu hesaplayan bir programa küçük syntax mutasyonları öneren bir stdlib proxy'sidir. "Evaluator" tutulmuş test noktalarında ortalama kare hatayı ölçer.

İzle:

- En iyi skorun nesiller boyunca nasıl iyileştiğini.
- Bir MAP-elites grid'inin çeşitli çözümleri canlı tutarak döngünün lokal minimuma yakınsamamasını nasıl sağladığını.
- Tutulmuş testi kaldırmanın (yalnızca-eğitim evaluator) döngünün muhteşem şekilde overfit etmesine nasıl izin verdiğini.

## Yayınla

`outputs/skill-evaluator-rigor-audit.md`, yeni bir domain'de bir AlphaEvolve tarzı döngü düşünmenin ön koşuludur: evaluator'ın gerçekten önemsediğin failure'ları yakalıyor mu?

## Alıştırmalar

1. `code/main.py`'yi çalıştır. En iyi skor trajectory'sini not al. Tutulmuş evaluator'ı devre dışı bırak (`--no-holdout` bayrağı) ve yeniden çalıştır. Overfitting'i niceliksel olarak ifade et.

2. AlphaEvolve makalesinin MAP-elites grid'i üzerine 3. bölümü oku. Yeni bir problem (örn. derleyici optimizasyon pass'leri) için aramayı çeşitli tutacak bir özellik-vektörü descriptor'ı tasarla.

3. 48-çarpım 4x4 sonucu Strassen'in 49-çarpım sınırını 56 yıl sonra iyileştirdi. Makalenin Ek F'sini oku ve bu problem için evaluator'ın neden özellikle kolay doğru yapıldığını ve çoğu domain'in neden böyle olmadığını üç cümleyle açıkla.

4. AlphaEvolve'un başarısız olacağı bir domain öner. Evaluator'ın tam olarak nerede ve neden kırıldığını belirle.

5. Bildiğin bir domain için kullanacağın evaluator imzasını yaz. (a) doğruluk koşulları, (b) performans metriği, (c) tutulmuş input üretim kuralı, (d) en az bir anti-reward-hacking kontrolü içersin.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| AlphaEvolve | "DeepMind'ın evrimsel kodlama agent'ı" | Gemini + program veritabanı + makine-doğrulanabilir evaluator |
| MAP-elites | "Çeşitlilik-koruyan arşiv" | Özellik vektörleriyle anahtarlanmış grid; her hücre o descriptor'la en iyi varyantı tutar |
| Ada modeli | "Paralel evrim alt popülasyonları" | Periyodik olarak göç eden bağımsız popülasyonlar; erken yakınsamayı önler |
| Makine-doğrulanabilir evaluator | "Deterministik oracle" | LLM'nin sahteleyemeyeceği bir unit test, simülatör ya da benchmark — bu döngünün ön koşulu |
| Reward hacking | "Hedefi değil ölçüyü optimize etme" | Döngü, amaçlanan görevi yapmadan skoru maksimize etmenin yolunu bulur |
| Tohum program | "Başlangıç noktası" | Döngünün geliştiği başlangıç doğru-ama-suboptimal program |
| Tutulmuş evaluator | "LLM'nin asla görmediği değerlendirme verisi" | Ezberlemeyi önlemek için değerlendirme zamanında üretilen input'lar |

## İleri Okuma

- [Novikov et al. (2025). AlphaEvolve: A coding agent for scientific and algorithmic discovery](https://arxiv.org/abs/2506.13131) — tam makale.
- [DeepMind blog on AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) — sonuçlarla satıcı yazısı.
- [AlphaEvolve results repository](https://github.com/google-deepmind/alphaevolve_results) — keşfedilen algoritmalar, 48-çarpım 4x4 matmul dahil.
- [Romera-Paredes et al. (2023). Mathematical discoveries from program search with LLMs (FunSearch)](https://www.nature.com/articles/s41586-023-06924-6) — öncül sistem.
- [Anthropic — Responsible Scaling Policy v3.0 (Feb 2026)](https://anthropic.com/responsible-scaling-policy/rsp-v3-0) — evaluator-bağımlı otonomiyi anahtar bir araştırma yönü olarak çerçeveler.
