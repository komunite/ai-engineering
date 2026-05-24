# HTN ve Evrimsel Arama ile Planlama

> Sembolik planlama, planın kanıtlanabilir şekilde doğru olduğu durumları ele alır. Evrimsel kod araması, fitness fonksiyonunun makine-doğrulanabilir olduğu durumları ele alır. ChatHTN (2025) ve AlphaEvolve (2025) bir LLM ile eşleştirildiğinde her birinin neyi açtığını gösterir.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 02 (ReWOO ve Plan-and-Execute)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Hierarchical Task Network'leri açıkla: task'lar, method'lar, operatörler, precondition'lar, effect'ler.
- ChatHTN'nin hybrid döngüsünü açıkla — LLM fallback dekompozisyonu ile sembolik arama.
- AlphaEvolve'un evrimsel döngüsünü ve neden yalnızca programatik bir evaluator ile çalıştığını açıkla.
- Bir oyuncak HTN planner artı bir oyuncak evrimsel arama'yı stdlib'de uygula.

## Sorun

ReWOO (Ders 02), Plan-and-Execute ve ReAct çoğu agent planlamasını kapsar. İyi kapsamadıkları iki durum:

1. **Kanıtlanabilir doğruluklu planlar.** Çizelgeleme, uçuş yol bulma, compliance workflow'ları — plan yapısı gereği sound olmalı. Bazen bir adımı halüsine eden akıcı bir LLM planı kabul edilemez.
2. **Makine-doğrulanabilir fitness fonksiyonlu optimizasyonlar.** Matris çarpımı, çizelgeleme sezgileri, compiler pass'leri — hedef "doğru bir plan" değil, "en iyi plan."

HTN planlama ve AlphaEvolve iki farklı problemi çözer. Her ikisi de LLM'leri yedek olarak değil, amplifier olarak kullanır.

## Kavram

### Hierarchical Task Network'ler

Bir HTN:

- **Task'lar** — bileşik (dekompoze edilmek üzere) ve primitive (doğrudan yürütülebilir).
- **Method'lar** — precondition'larıyla bir bileşik task'ı alt-task'lara dekompoze etme yolları.
- **Operatörler** — precondition ve effect'li primitive aksiyonlar.
- **State** — bir olgular kümesi.

Planlama: bir hedef task ve initial state verildiğinde, precondition'ları sırayla karşılanan primitive operatörlere bir dekompozisyon bul.

HTN LLM'lerden eski ve kanıtlanabilir-doğru planlar için hâlâ referans.

### ChatHTN (Gopalakrishnan et al., 2025)

ChatHTN (arXiv:2505.11814) sembolik HTN'yi LLM sorgularıyla iç içe geçirir:

1. Mevcut method'larla mevcut bileşik task'ı dekompoze etmeyi dene.
2. Hiç method uygulanmazsa, LLM'e sor: "state `s`'de `task`'ı nasıl dekompoze edersin?"
3. LLM yanıtını aday alt-task'lara çevir.
4. Operator şemasına karşı doğrula; geçersiz dekompozisyonları reddet.
5. Recurse.

Makalenin merkezi iddiası: üretilen her plan kanıtlanabilir şekilde sound çünkü LLM önerileri yalnızca aday dekompozisyonlar olarak girer, hiçbir zaman doğrudan plan düzenlemeleri olarak değil. Sembolik katman doğruluğu sahiplenir; LLM method library'i genişletir.

Online method learning (OpenReview `gwYEDY9j2x`, 2025 takip) regresyon ile LLM-üretilmiş dekompozisyonları genelleştiren bir öğrenici ekler — LLM sorgu frekansını %75'e kadar keserek.

### AlphaEvolve (Novikov et al., 2025)

AlphaEvolve (arXiv:2506.13131, DeepMind, Haziran 2025) farklı bir canavar: Gemini 2.0 Flash/Pro ensemble tarafından orkestre edilen evrimsel kod araması.

Döngü:

1. Bir tohum program + programatik bir evaluator (bir fitness skoru döndürür) ile başla.
2. LLM ensemble mutasyonlar önerir.
3. Mutasyonları evaluator'den geçir.
4. En iyiyi tut; tekrar mutate et.

Yayınlanan kazançlar:

- 4x4 complex matris çarpımı için Strassen üzerine 56 yılda ilk iyileştirme (48 skaler çarpım).
- Bir Borg çizelgeleme sezgisi üzerinden %0.7 Google compute kurtarımı.
- Bir frontier workload üzerinde %32 FlashAttention hızlanması.

Sert kısıtlama: fitness fonksiyonu makine-doğrulanabilir olmalı. Düz yazı yanıtları üzerinde evrimsel arama yakınsamaz.

### Hangisini ne zaman kullanmalı

| Problem sınıfı | Kullan | Neden |
|---------------|-----|-----|
| Sert kısıtlamalı çizelgeleme | HTN + ChatHTN | Kanıtlanabilir soundness |
| Compiler optimizasyonu | AlphaEvolve | Makine-doğrulanabilir fitness |
| Çok-adımlı görev yürütme | ReAct / ReWOO | Döngüde LLM, formal garanti yok |
| Test'li kod iyileştirme | AlphaEvolve | Testler evaluator |
| Policy-bound otomasyon | HTN | Precondition'lar policy'yi kodlar |

### Bu desen nerede ters gider

- **Operatörsüz HTN.** Precondition/effect şemaları olmadan soundness iddiası çöker. ChatHTN'nin "LLM dekompozisyon önerir"i geçersiz hamleleri reddetmek için şemanın olmasını gerektirir.
- **Gerçek evaluator'sız AlphaEvolve.** "LLM'e kodun daha iyi olup olmadığını sor" bir fitness fonksiyonu değil. Evaluator deterministik ve hızlı olmalı.
- **Aşırı-mühendislik.** Çoğu agent görevi ikisine de ihtiyaç duymaz. Önce ReAct ya da ReWOO'ya uzan.

## İnşa Et

`code/main.py` iki oyuncak uyguluyor:

- Operatörler, method'lar, precondition'lar, effect'ler ve hiçbir method bir bileşik task'a uymadığında devreye giren bir `LLMFallback` ile stdlib bir HTN planner. "LLM" scripted bir decomposer, böylece planner çevrimdışı çalışır.
- Aritmetik programlar üzerinde stdlib evrimsel arama: çıktısı bir test seti üzerinde `|f(x) - target|`'i minimize eden ifadeler büyüt. Evaluator deterministik.

Çalıştır:

```
python3 code/main.py
```

Trace HTN planner'ının bir bileşik task'ı dekompoze ettiğini (plan-ortası LLM fallback ile) ve evrimsel döngünün hedef bir ifadede yakınsadığını gösteriyor.

## Kullan

- **HTN planner'lar** — `pyhop`, `SHOP3` ya da domain-spesifik policy enforcement için kendi planner'ını kur.
- **ChatHTN** — araştırma kodu; desen (sembolik + LLM fallback) herhangi bir HTN planner'a temiz şekilde port edilir.
- **AlphaEvolve** — DeepMind makalesi; desen (ensemble + evaluator) yeniden üretilebilir. OpenEvolve ve benzer açık kaynak fork'lar çıkıyor.
- **Agent framework'leri** — hiçbiri henüz birinci-sınıf HTN ya da AlphaEvolve yayınlamıyor. Bunu bir alt-agent ya da arka plan worker olarak inşa et.

## Yayınla

`outputs/skill-hybrid-planner.md` LLM rolü açıkça scope'lanmış hybrid planner iskelesi (HTN ya da evrimsel) üretir.

## Alıştırmalar

1. HTN planner'ı backtracking ile genişlet: bir operatörün postcondition'ı runtime'da başarısız olduğunda, geri al ve sonraki method'u dene.
2. ChatHTN'ye bir LLM-method cache'i ekle: LLM `T` task'ını state pattern `P`'de dekompoze ettiğinde, sonucu sakla. Sonraki çağrıda önce method library'i yeniden kontrol et.
3. Evrimsel arama evaluator'ünü gerçek bir test suite ile değiştir. 20 test case geçen bir sort fonksiyonu evolve et; yakınsamaya kadar nesilleri raporla.
4. AlphaEvolve'un evaluator tasarım notlarını oku. Önemsediğin bir domain için bir evaluator tasarla (SQL query optimizasyonu, test-suite minimizasyonu, deployment YAML).
5. Birleştir: bir bileşik task'ı alt-task'lara dekompoze etmek için HTN kullan, sonra her alt-task'ın primitive operatörü üzerinde evrimsel arama kullan. Nerede parlar, nerede aşırı-mühendislik olur?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| HTN | "Hiyerarşik planner" | Operatörler, precondition'lar, effect'lerle task dekompozisyonu |
| Method | "Dekompozisyon kuralı" | Bir bileşik task'ı alt-task'lara ayırma yolu |
| Operator | "Primitive aksiyon" | Precondition ve effect'li somut adım |
| ChatHTN | "LLM + HTN" | Hiçbir method uymadığında LLM'e soran sembolik planner |
| AlphaEvolve | "Evrimsel kod araması" | Ensemble LLM'ler kodu mutate eder; deterministik evaluator seçer |
| Fitness fonksiyonu | "Evaluator" | Çıktılar üzerinde deterministik, makine-doğrulanabilir skor |
| Online method learning | "Cache'lenmiş LLM dekompozisyonu" | Sorgu maliyetini kesmek için LLM planlarını sakla + genelleştir |

## İleri Okuma

- [Gopalakrishnan et al., ChatHTN (arXiv:2505.11814)](https://arxiv.org/abs/2505.11814) — sembolik + LLM hybrid planner
- [Novikov et al., AlphaEvolve (arXiv:2506.13131)](https://arxiv.org/abs/2506.13131) — LLM mutasyonlu evrimsel kod araması
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — planner'a vs basit döngüye ne zaman uzanmalı
