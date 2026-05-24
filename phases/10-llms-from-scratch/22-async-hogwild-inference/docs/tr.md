# Async ve Hogwild! Inference

> Speculative decoding (Faz 10 · 15) bir sequence içindeki token'ları paralelleştirir. Multi-agent framework'ler tüm sequence'ler boyunca paralelleştirir ama açık koordinasyon (oylama, alt-görev bölme) zorlar. Hogwild! Inference (Rodionov et al., arXiv:2504.06261) başka bir şey yapar: PAYLAŞILAN bir key-value cache'e karşı aynı LLM'in N instance'ını paralel çalıştır. Her worker diğer her worker'ın ürettiği token'ı anında görür. Modern reasoning modeller — QwQ, DeepSeek-R1 — herhangi bir fine-tuning olmadan o paylaşılan cache üzerinden self-coordinate edebilir. Yaklaşım deneysel ama spec decode'a ortogonal oturan tamamen yeni bir çıkarım paralelliği ekseni açar. Bu ders stdlib Python'da iki-worker Hogwild! simülatörü implement eder ve paylaşılan-cache işbirliğinin mevcut modelin reasoning yeteneklerinden neden çıktığını açıklar.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 10 · 12 (inference optimization), Faz 10 · 15 (speculative decoding)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Üç yaygın parallel-LLM topolojisini (oylama, alt-görev, Hogwild!) tanımla ve her birinin hedeflediği problemleri adlandır.
- Çekirdek Hogwild! kurulumunu ifade et: birden fazla worker, bir paylaşılan KV cache, self-prompting yoluyla emergent koordinasyon.
- Worker sayısı `N`, görev-seviyesi paralellik `p` ve koordinasyon overhead'i `c` fonksiyonu olarak Hogwild!'ın wall-time hızlanmasını hesapla.
- Bir oyuncak problem üzerinde iki-worker Hogwild! simülatörü implement et ve emergent görev bölünmesini gözlemle.

## Sorun

Modern LLM'ler zor problemleri uzun reasoning zincirleri üreterek çözer — 5000 token adım-adım mantık yaygın, derin matematik problemlerinde on binlerce token olur. 70B modelde saniyede 35 token decode'da, 50k token 24 dakika. Etkileşimli değil.

Speculative decoding (Faz 10 · 15) bir sequence içinde paralelleştirerek 3-5x hızlanma sağlar. Bunun ötesinde autoregressive decoding'in sıralı bağımlılığı sert tavandır. Her yeni token her önceki token'a bağlıdır.

Bariz soru: sequence'ler boyunca paralelleştirebilir miyiz? Aynı modelin birden fazla kopyasını aynı problem üzerinde çalıştır, işbirliği yapmalarına izin ver, işi bölmelerini sağla?

Önceki çalışma: oylama ensemble'ları (N model çalıştır, çoğunluk cevabını seç), tree-of-thought (reasoning yollarını dallandır ve birleştir) ve multi-agent framework'ler (her agent'a bir alt-görev ata, bir koordinatör kullan). Bunların hepsi spesifik görev alanlarında yardım eder. Hepsi de açık koordinasyon makinesi tanıtır — oylama kuralları, dal-budama mantığı, agent'tan-agent'a mesajlaşma protokolleri.

Hogwild! Inference farklı bir yaklaşım alır. N worker tek bir KV cache'i paylaşır. Her worker diğer her worker'ın ürettiği token'ları anında, sanki kendi context'iymiş gibi görür. Worker'lar — herhangi bir eğitim veya fine-tuning olmadan — işi nasıl böleceklerini çözer. Modern reasoning modelleri (QwQ, DeepSeek-R1, Claude-aile reasoning modu) paylaşılan cache'i okuyabilir ve "Worker 2'nin base case'i zaten hallettiğini görüyorum, dolayısıyla inductive adım üzerinde çalışacağım" gibi şeyler söyleyebilir.

Hızlanma iş yüküne bağlıdır ve Nisan 2026 itibarıyla deneyseldir. Ama fikir bilinmeye değer çünkü çıkarım paralelliğinde yeni bir eksen açar.

## Kavram

### Kurulum

N worker process initialize et, hepsi aynı LLM'i çalıştırıyor. Worker başına KV cache yerine, BİR paylaşılan cache koru. Worker `i` token `t_j` ürettiğinde, token paylaşılan cache'e bir sonraki pozisyona yazılır. Worker `k` bir sonraki adımını attığında, cache'in mevcut state'ini okur (tüm N worker'ın şu ana kadar ürettiği her şey dahil).

Adım zamanında, worker'lar token yazmak için yarışır. Worker başına pozisyon endeksi yok — cache tek büyüyen bir sequence. Sıra yazma varış zamanına göre belirlenir.

### Koordinasyon Neden Çıkar

Worker'lar bir prompt paylaşır. Tipik olarak "Bu problem üzerinde birlikte çalışan N instance'ından birisin. Her instance paylaşılan memory'i okur ve diğer instance'ların ne yazdığını görebilir. Gereksiz işten kaçın" gibi bir şey. Prompt artı paylaşılan cache yeterli. Reasoning modelleri cache'i okur, problemin hangi parçalarının zaten denendiğini fark eder ve (genellikle ama her zaman değil) keşfedilmemiş parçalara pivot eder.

Hogwild! makalesi (Rodionov et al., 2025) şu gözlemleri raporlar:

- Worker'lar planlar formüle eder ve cache üzerinden diğer worker'lara iletir.
- Worker'lar diğer worker'ların reasoning'indeki hataları fark eder ve dile getirir.
- Bir plan başarısız olduğunda worker'lar adapte olur ve alternatifler önerir.
- Redundancy kontrol etmesi prompt edildiğinde, worker'lar bunu tespit eder ve pivot eder.

Bunların hiçbiri fine-tuning gerektirmez. Emergent davranış modelin zaten sahip olduğu reasoning yeteneklerinden gelir.

### Adlandırma

Makalenin adı asenkron-güncelleme optimizer'ı olan Hogwild! SGD'ye (Recht et al., 2011) gönderme yapar. Analoji: SGD'nin asenkron worker'ları hepsi paylaşılan bir parametre vektörüne yazar; Hogwild! Inference'in worker'ları hepsi paylaşılan bir KV cache'e yazar. Her ikisi de senkronizasyon garantileri yerine empirik yakınsamaya güvenir.

### RoPE Bunu Tractable Yapar

Rotary Position Embeddings (RoPE, Su et al. 2021) Q ve K vektörlerindeki rotation yoluyla pozisyon bilgisini encode eder. Pozisyonlar rotation olduğu ve baked-in offset olmadığı için, bir token'ın pozisyonu KV cache girişini yeniden hesaplamadan kayabilir. Worker `i` paylaşılan cache'e pozisyon `p`'ye yazdığında, o pozisyonu okuyan diğer worker'lar cache'lenmiş girişi doğrudan kullanabilir — yeniden rotation gerekmez.

Öğrenilmiş-pozisyon veya absolute-pozisyon modelinde, Hogwild! her eşzamanlı yazımda cache invalidation gerektirirdi. RoPE cache'in kararlı kalmasına izin verir.

### Wall-Time Matematik

`T_serial` bir worker'ın problemi tek başına çözmesi için zaman olsun. `p` görev-seviyesi paralelleştirilebilir oran olsun. `c` adım başına koordinasyon overhead'i olsun (genişletilmiş cache'i okumak, ne yazılacağına karar vermek).

Tek-worker zamanı: `T_serial`.
Koordinasyon ücretsizse N-worker Hogwild! zamanı: `T_serial * ((1 - p) + p / N)`. Klasik Amdahl.
Koordinasyon overhead'i ile: `T_serial * ((1 - p) + p / N) + c * steps_per_worker`.

Bir worker'ın üretken olması için, `c` adım başına decode zamanına göre küçük olmalıdır. 5k+ token üreten reasoning modellerinde, worker'lar yüzlerce token koordinasyon overhead'ini karşılayabilir ve hala önde çıkabilir. Kısa chat görevlerinde, koordinasyon baskındır ve Hogwild! seriden daha kötüdür.

### Somut Örnek

Reasoning problemi: 10k token chain-of-thought. Problemin `p = 0.7` paralelleştirilebilir içerik (farklı kanıt stratejileri, farklı vaka analizleri) ve worker başına `c = 200` token koordinasyon overhead'i olduğunu varsay. `N = 4` worker ile:

- Seri zamanı: 10000 decode adımı.
- Hogwild! zamanı: 10000 * (0.3 + 0.7 / 4) + 200 * 4 = 10000 * 0.475 + 800 = 5550 decode adımı.
- Hızlanma: 10000 / 5550 = 1.8x.

Bu mütevazı. Ama daha uzun reasoning problemlerinde (50k token), koordinasyon overhead'i amortize olur ve hızlanma 2.5-3x'i iter. Hogwild! multi-threaded kodu doğal olarak yazmana izin veren bir dildeki thread-level paralelliğin çıkarım eşdeğeridir.

### Hogwild! İçin Ne Zaman Uzanmalı

- Görevin bağımsız alt-hedeflere paralelleştirilebildiği uzun reasoning problemleri (binlerce token).
- Adım adım düşünmeye eğitilmiş reasoning modelleri. Non-reasoning modelleri iyi self-coordinate etmez.
- Paylaşılan cache artı N worker process'i tutmak için yeterli VRAM'lı tek-node deployment'ları. Cache paylaşılır, ama her worker'ın kendi activation memory'si vardır.

### Ne Zaman Değil

- Kısa etkileşimli chat. Koordinasyon overhead'i baskındır.
- Paralelleşmeyen görevler (tek lineer kanıt, tek derleme). N=1 max.
- Non-reasoning modeller. Koordinasyon çıkmaz.
- Multi-node deployment'lar. Paylaşılan cache çok hızlı cross-worker senkronizasyon ister. Intra-node iyi; cross-node bir latency felaketi.

### Deneysel Statü

Nisan 2026 itibarıyla, Hogwild! açık kaynak PyTorch implementasyonu olan bir araştırma yöntemidir. Production benimsenmesi olmadı. Üç engelleyici:

1. Eşzamanlı process'ler arasında paylaşılan KV cache yönetimi non-trivial mühendislik.
2. Emergent koordinasyon göreve bağlı; benchmark'lar hala inşa ediliyor.
3. Hızlanmalar speculative decoding'in zaten sağladığıyla karşılaştırıldığında mütevazı ve ikisi birleştirilebilir ama birleşik mühendislik başka bir katman.

Bilmeye değer. Deneye değer. Henüz bir ürün üzerine bahse değmez.

## İnşa Et

`code/main.py` bir oyuncak Hogwild! simülatörü implement eder:

- İki worker process, her biri bilinen olasılıklarla birkaç token kategorisinden birini (work-token, observe-token, coordinate-token) üreten deterministik bir "LLM".
- Her iki worker'ın okuduğu ve yazdığı paylaşılan bir cache (sadece bir token listesi).
- Basit bir koordinasyon mantığı: bir worker diğerinin bir kategoride zaten yeterli work token ürettiğini gördüğünde, farklı bir kategori seçer.

Simülatör sabit bir adım bütçesi için çalışır ve şunları raporlar:

- Üretilen toplam work-token sayısı.
- Toplam wall time (worker adım sayısı).
- Tek worker üzerinde etkili hızlanma.
- Hangi worker'ın hangi token'ı yazdığının izi.

### Adım 1: Paylaşılan Cache

Her iki worker'ın eklediği bir liste. Gerçek implementasyonda basit lock'lama (Python `threading.Lock`); biz bir sayaçla simüle ediyoruz.

### Adım 2: Worker Döngüsü

Her worker, her adımda:

- Mevcut paylaşılan cache'i okur.
- Orada zaten ne olduğuna göre hangi kategoride token yazacağına karar verir.
- Bir token yazar.

### Adım 3: Koordinasyon Heuristiği

Kategori X'in cache'te zaten K token'ı varsa ve worker'ın amaçlanan kategorisi X ise, worker Y'ye geçer. Bu "bunun zaten kapsandığını fark et, onun yerine başka bir şey yap" reasoning-model davranışı için bir oyuncak yedeğidir.

### Adım 4: Ölçülen Hızlanma

Simülatörü N=1 worker ve N=2 worker ile, aynı toplam adım bütçesi ile çalıştır. Üretilen work-token'ları say. Koordinasyon-driven görev bölünmesi nedeniyle N=2 kabaca 1.5-1.8x daha fazla work-token üretmeli.

### Adım 5: Koordinasyonu Strese Sok

Koordinasyon heuristiğinin hassasiyetini azalt. Tekrar çalıştır. İyi koordinasyon olmadan, N=2'nin gereksiz olarak aynı token'ları ürettiğini ve hızlanmanın 1'in altına düştüğünü gözlemle. Bu makalenin gözlemiyle eşleşir: hile sadece worker'lar self-coordinate edecek reasoning kapasitesine sahipse çalışır.

## Kullan

Nisan 2026 itibarıyla production'da Hogwild! entegrasyonu araştırma-seviyesi. Yandex/HSE/IST'den referans implementasyon PyTorch-tabanlı ve DeepSeek-R1 ve QwQ modelleri üzerinde tek-node multi-process kurulumları hedefler.

Pragmatik benimseme yolu:

1. Reasoning-görev iş yükünü profil et. Keşif (birden fazla strateji, vaka analizleri, arama) vs lineer olan token'ların oranını ölç.
2. Keşif baskınsa, iki-worker bir Hogwild! deneyi çalıştır. Wall-time iyileştirmesini ölç.
3. İyileştirme 1.3x altındaysa, koordinasyon-baskın rejimdesin. Tek-worker'a geri dön.
4. İyileştirme 1.5x üzerindeyse, N=4'e it ve tekrar ölç. Azalan getiriler tipik olarak N=4-8 civarında vurur.

Speculative decoding ile birleştir: her Hogwild! worker'ı bağımsız olarak spec decode kullanabilir. İki hızlanma (kabaca) çarpılır, 3x spec decode ve 1.8x Hogwild!'ı naif tek-worker decoding üzerinde etkili 5.4x'a getirir.

## Yayınla

Bu ders `outputs/skill-parallel-inference-router.md` üretir. Bir reasoning iş yükü profili (token bütçesi, görev paralellik profili, model ailesi, deployment hedefi) verildiğinde, voting, tree-of-thought, multi-agent, Hogwild! ve speculative decoding stratejileri arasında route eder.

## Alıştırmalar

1. `code/main.py`'ı varsayılan ayarlarla çalıştır. N=2 Hogwild! konfigürasyonunun aynı wall time'da N=1 baseline'dan daha fazla work-token ürettiğini doğrula.

2. Koordinasyon heuristiğinin gücünü azalt (`coordination_weight=0.1` ayarla). Yeniden çalıştır. Hızlanmanın çöktüğünü göster. Neden olduğunu açıkla: worker'lar koordinasyon yapamadıklarında çaba duplicate eder.

3. `p=0.8, c=500` ve N=4 worker ile 50k-token reasoning görevi için beklenen Hogwild! hızlanmasını hesapla. Aynısını `p=0.3, c=200` ve N=4 ile 1k-token chat görevi için yap. Neden biri kazanım, diğeri kayıp?

4. Hogwild! makalesinin Bölüm 4'ünü (preliminary evaluation) oku. Yazarların raporladığı iki başarısızlık modunu tanımla. Daha iyi bir koordinasyon prompt'unun her birini nasıl mitige edebileceğini tanımla.

5. Oyuncakta Hogwild!'ı speculative decoding ile birleştir: her worker dahili olarak 2-token spec-decode kullansın. Çarpıcı hızlanmayı raporla. İki worker da aynı paylaşılan-cache prefix'ini uzatmak istediğinde hangi defter tutma problemi ortaya çıkar?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Hogwild! | "Paralel worker'lar, paylaşılan cache" | Aynı LLM'in bir paylaşılan KV cache ile eşzamanlı çalışan N instance'ı; self-prompting yoluyla emergent koordinasyon |
| Shared KV cache | "Koordinasyon mecrası" | Tüm worker'ların okuduğu ve yazdığı tek büyüyen KV buffer'ı; worker'lar arasında anında token görünürlüğünü sağlar |
| Emergent coordination | "Eğitim gerekmez" | Reasoning-yetenekli LLM'ler paylaşılan cache'i okuyabilir ve herhangi bir fine-tuning veya açık protokol olmadan işi bölebilir |
| Coordination overhead (c) | "Yönelmek için harcanan token" | Genişletilmiş cache'i okuyup ne yapılacağına karar verme worker başına maliyeti; toplam decode zamanına göre küçük kalmalı |
| Parallelizable fraction (p) | "Paralelde ne çalışabilir" | Görev-seviyesi paralellik: toplam işin intrinsically sıralı olmayan oranı |
| RoPE enables Hogwild! | "Rotary pozisyonlar shift-değişmez" | Pozisyonlar rotation olduğu için, paylaşılan cache'e yazmak önceki token'ları yeniden hesaplamayı gerektirmez |
| Voting ensemble | "N çalıştır, çoğunluğu seç" | En basit paralel çıkarım topolojisi; sınıflandırma için faydalı, uzun-form reasoning için daha az |
| Tree of thought | "Dallandır ve buda" | Birden fazla dalı keşfeden ve budayan reasoning stratejisi; açık koordinasyon mantığı |
| Multi-agent framework | "Alt-görevleri ata" | Her agent bir rol alır; bir koordinatör orkestre eder; ağır protokol overhead'i |

## İleri Okuma

- [Rodionov et al. -- Hogwild! Inference: Parallel LLM Generation via Concurrent Attention (arXiv:2504.06261)](https://arxiv.org/abs/2504.06261) -- Hogwild! makalesi, QwQ ve DeepSeek-R1 üzerinde preliminary evaluation
- [Recht, Re, Wright, Niu -- Hogwild!: A Lock-Free Approach to Parallelizing Stochastic Gradient Descent (arXiv:1106.5730, NeurIPS 2011)](https://arxiv.org/abs/1106.5730) -- orijinal Hogwild!, adlandırma kökeni
- [Su et al. -- RoFormer: Enhanced Transformer with Rotary Position Embedding (arXiv:2104.09864)](https://arxiv.org/abs/2104.09864) -- paylaşılan-cache çıkarımını tractable yapan özellik olan RoPE
- [Yao et al. -- Tree of Thoughts: Deliberate Problem Solving with Large Language Models (arXiv:2305.10601)](https://arxiv.org/abs/2305.10601) -- Hogwild!'ın ortogonal oturduğu tree-of-thought reasoning stratejisi
- [Leviathan et al. -- Fast Inference from Transformers via Speculative Decoding (arXiv:2211.17192)](https://arxiv.org/abs/2211.17192) -- Hogwild!'ın compose ettiği sequence-içi paralellik olan speculative decoding
- [Hogwild! reference PyTorch implementation](https://github.com/eqimp/hogwild_llm) -- makalenin deneyleri için tek doğruluk kaynağı
