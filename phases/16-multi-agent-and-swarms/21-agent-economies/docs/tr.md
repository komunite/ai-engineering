# Agent Ekonomileri, Token Teşvikleri, İtibar

> Uzun-vadeli otonom agent'lar (METR'in 1 saatten 8 saate iş eğrisi) ekonomik faillik gerektirir. Ortaya çıkan **5-katmanlı yığın**: **DePIN** (fiziksel compute) → **Identity** (W3C DID + reputation capital) → **Cognition** (RAG + MCP) → **Settlement** (account abstraction) → **Governance** (Agentic DAO'lar). Üretim agent-teşvik ağları arasında **Bittensor** (TAO subnet'leri görev-özgü modelleri ödüllendirir), **Fetch.ai / ASI Alliance** (ASI-1 Mini LLM + FET token) ve **Gonka** (verimli AI görevlerine compute'u yeniden dağıtan transformer-tabanlı PoW) bulunur. Akademik çalışma: AAMAS 2025'in merkeziyetsiz LaMAS'ı katkı veren agent'ları adil ödüllendirmek için **Shapley-value credit attribution** kullanır; Google Research "Mechanism design for large language models" monoton toplama altında second-price ödeme ile **token açık artırmalarını** önerir. Bu ders minimal bir agent pazaryeri inşa eder, Shapley-value credit attribution'ı bir çoklu-agent pipeline'ına uygular ve oyun-teori makinesinin somut olarak yerleşmesi için second-price token açık artırması çalıştırır.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 16 (Müzakere ve Pazarlık), Faz 16 · 09 (Parallel Swarm Networks)
**Süre:** ~75 dakika

## Sorun

Çoklu-agent sistemleri agent'lar değeri ortak ürettiğinde ama bireysel olarak ödüllendirilmesi gerektiğinde karmaşıklaşır. Klasik mekanizmalar — eşit bölüşüm, son-katkı-veren-hepsini-alır — adaletsiz ya da oynanabilirdir. Shapley değerleri yoluyla koalisyon-tabanlı ödüllendirme yapı gereği adildir ama hesaplaması pahalıdır. 2025-2026 literatürü yararlı yaklaşımları zorluyor: Shapley sampling, monoton toplama açık artırmaları ve onaylanmış katkılardan biriken zincir-üstü itibar.

Credit attribution'ın ötesinde alan gerçek ekonomik agent'lara döndü: Bittensor TAO subnet-özgü modelleri ince ayar yapmak için compute madenciliğini ödüllendirir, Fetch.ai/ASI ASI-1 Mini LLM kullanımını FET token ile ödüllendirir, Gonka transformer proof-of-work'ü verimli AI görevlerine yeniden dağıtır. Otonom olarak işlem yapan agent'lar bugün var; soru teşvikleri nasıl hizalanacağı.

Bu ders agent ekonomilerini belirli bir problem ailesi olarak ele alır — credit attribution, mechanism design ve itibar — ve fikirlerin yapışması için her birini minimal matematikle inşa eder.

## Kavram

### 5-katmanlı agent-ekonomi yığını

1. **DePIN (fiziksel compute).** GPU, depolama, bant genişliği kiralayan merkeziyetsiz altyapı. Bittensor subnet'leri, Render Network, Akash. Agent'a özgü değil; agent'lar kullanır.
2. **Identity.** W3C Decentralized Identifiers (DID'ler) her agent'a herhangi bir platformdan bağımsız dayanıklı bir ID verir. İtibar DID'e birikir. Agent Network Protocol (ANP) DID'i keşif katmanı olarak kullanır.
3. **Cognition.** Agent'ın akıl yürütme döngüsü: LLM + RAG + MCP. Bu diğer fazların inşa ettiğidir.
4. **Settlement.** Account abstraction (ERC-4337) agent'ların ETH tutmadan kendi bakiyelerinden gas ödemesine izin verir. Agent'lar hizmetler, birbirleri ya da compute için ödeyebilir.
5. **Governance.** Agentic DAO'lar: oy gücünün itibara bağlı olduğu, insanların *ve* agent'ların protokol değişikliklerinde oy verdiği yönetim yapıları.

Her üretim sistemi beşini kullanmaz. Bittensor 1, 2, kısmen 3, kısmen 4, hiçbir 5 kullanır. OpenAI agent'ları 3 hariç hiçbirini kullanmaz. Yığın bir referans haritasıdır, gereksinim değildir.

### Bittensor, Fetch.ai, Gonka — neler çalışıyor

**Bittensor (TAO).** Subnet'ler uzmanlaşmış görevlerdir (dil modelleme, görüntü üretimi, tahmin). Madenciler model çıktıları gönderir. Validator'lar onları sıralar; stake-ağırlıklı puanlama TAO ödüllerini dağıtır. Her subnet'in kendi değerlendirmesi vardır. Ekonomik ders: kullanılan compute için değil, görev-özgü çıktı kalitesi için öde.

**Fetch.ai / ASI Alliance.** ASI-1 Mini LLM Fetch.ai'nin ağında çalışır; kullanıcılar çıkarım için FET token öder. Burada agent'lar-peer'lar olarak anlatısı daha güçlüdür: Fetch'teki bir agent başka birini bir görev için çağırıp FET ile ödeyebilir.

**Gonka.** Transformer proof-of-work: "iş" bir transformer'ın forward pass'leridir. Madenciler bilinen doğru çıktılara (eğitim verilerinden) sahip çıkarım görevlerini çalıştırarak kazanır. Hash-tabanlı PoW yerine kaynak-verimli PoW.

Üçü de Nisan 2026 itibariyle üretim-grade'dir. Getiri dağılımı farklı. Bittensor subnet validator'larına göre kaliteyi ödüllendirir; Fetch ödeyen kullanıcılar tarafından ölçülen faydayı ödüllendirir; Gonka doğrulanabilir çıkarım işini ödüllendirir.

### Shapley-value credit attribution

Üç agent bir görev üzerinde iş birliği yapar. Çıktı 0.8 puan alır. Kim neye katkıda bulundu?

Shapley value: dört aksiyomu sağlayan tek kredi dağılımı (efficiency, symmetry, linearity, null). Agent `i` için:

```
shapley(i) = (1/N!) * tüm sıralamalar O üzerinde sum (v(S_i_O ∪ {i}) - v(S_i_O))
```

burada `S_i_O` sıralama `O`'da `i`'den önce olan agent kümesidir. Pratikte: tüm permütasyonları sırala, her permütasyonda her agent'ın marjinal katkısını kaydet, ortalama al.

N=3 agent için 6 permütasyon vardır. N=10 için 3.6M — pratikte sıralamaları enumerate etmek yerine örnekle.

### Toplama için second-price açık artırması

Google Research ("Mechanism design for large language models") LLM çıktılarını toplamak için second-price token açık artırmaları önerir. Kurulum: N agent'ın her biri bir tamamlama önerir; her birinin seçilmek için özel bir değeri vardır. Açık artırmacı en yüksek-değerli öneriyi seçer ve *ikinci-en-yüksek* değeri öder. Monoton toplama altında (değer kaç teklif edildiğine değil, hangi önerinin seçildiğine bağlıdır), bu doğru-anlatıcıdır — agent'lar gerçek değerlerini teklif eder.

LLM sistemleri için bu neden önemli: tamamlama görevlerini farklı fiyatlandırma ile birden çok agent'a outsource edebilirsin; açık artırma en iyiyi seçer + adil öder ve agent'ların yanlış raporlama için teşviki yoktur.

### Reputation capital

DID-bağlı bir itibar skoru onaylanmış katkılardan birikir. Basit bir güncelleme kuralı:

```
rep(i, t+1) = alpha * rep(i, t) + (1 - alpha) * contribution_quality(i, t)
```

Çürüme faktörü `alpha` 1'e yakın. İtibar:

- Yönlendirme kararları için okumak ucuzdur ("zor görevleri yüksek-rep agent'lara gönder").
- Sahte üretmek pahalıdır (zamanla birikir, DID'e bağlıdır).
- Slash'lanabilir: doğrulamayı geçemeyen katkılar çıkarır.

### AAMAS 2025 merkeziyetsiz LaMAS

LaMAS önerisi (AAMAS 2025) şunları birleştirir: DID kimliği, Shapley-value credit attribution ve basit bir açık artırma mekanizması. Temel iddia: credit attribution adımını merkeziyetsizleştirmek sistemi denetlenebilir yapar ve tek-nokta manipülasyonuna karşı bağışıklık verir.

### Ekonomiler nerede dağılır

- **Fiyat oracle manipülasyonu.** Credit fonksiyonu oynanabilirse, agent'lar onu oynar. Her mekanizmanın adversarial bir teste ihtiyacı vardır.
- **Sybil saldırıları.** Bir operatör kendi katkısını şişirmek için N sahte agent başlatır. DID'ler bunu yavaşlatır ama durdurmaz; itibar sahteleme maliyeti hafifletmedir.
- **Doğrulama maliyeti.** Credit attribution yalnızca verifier kadar adildir. Doğrulama ucuzsa (küçük LLM), oynanabilir; pahalı ise (insan paneli), sistem ölçeklenmez.
- **Düzenleyici sarkma.** Agent ekonomileri finansal düzenlemeyle kesişir. Bittensor, Fetch ve Gonka 2026 itibariyle bazı yargı bölgelerinde yasal gri alanlarda çalışır.

### Agent ekonomileri ne zaman mantıklı

- **Heterojen operatörlü açık ağlar.** Tek bir takım tüm agent'ları kontrol etmiyor.
- **Doğrulanabilir çıktılar.** Doğrulama olmadan credit attribution bir tahmindir.
- **Uzun-vadeli iş akışları.** Tek-atış görevler itibar birikiminden yararlanmaz.
- **Tokenize edilmiş ödemeler hukuksal olarak yargı bölgenizde uygulanabilir**.

Kapalı kurumsal sistemlerde ekonomi daha basit dağılıma yer verir (yöneticiler iş atar, metrikler içseldir). Ekonomi literatürü çoğunlukla açık ağlara uygulanır.

## İnşa Et

`code/main.py` şunları uygular:

- `shapley(value_fn, agents)` — küçük N için enumeration ile tam Shapley hesabı.
- `second_price_auction(bids)` — doğru-anlatıcı mekanizma; kazanan ikinci-en-yüksek öder.
- `Reputation` — üstel çürüme ve slashing ile DID-bağlı itibar.
- Demo 1: üç agent iş birliği yapar, tam Shapley krediyi atar.
- Demo 2: beş agent bir görev slot'u için teklif verir; second-price açık artırması kazanan + ödemeyi seçer.
- Demo 3: heterojen rep'li agent'lara 100 tur görev atama; rep-ağırlıklı yönlendirme rastgeleyi yener.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: her agent için Shapley değerleri; doğru-teklif dengesini gösteren açık artırma sonucu; ısınma sonrası rastgele üzerine %10-20 kalite kazanımı gösteren rep-ağırlıklı yönlendirme.

## Kullan

`outputs/skill-economy-designer.md` minimal bir agent ekonomisi tasarlar: kimlik katmanı seçimi, credit attribution mekanizması, ödeme mekanizması, itibar kuralı.

## Yayınla

2026'da bir agent ekonomisi çalıştırma:

- **Token'larla değil, itibarla başla.** İtibar uygulaması ucuz ve tek başına değerlidir; token'lar hukuksal ve ekonomik karmaşıklık ekler.
- **Ödüllendirmeden önce doğrula.** Bağımsız bir doğrulama adımı olmadan asla kredi dağıtma. Kendi-raporlanan kalite sybil oyunlarını biriktirir.
- **Shapley-örnek, Shapley-kesin değil.** 100-1000 sıralama örnekle; kesin enumeration ölçeklenmez.
- **Çürüme faktörünü sınırla ve itibarı tabanla.** Sınırsız çürüme meşru katkıda bulunanları siler; çok yavaş çürüme bayat yüksek-rep agent'ları ödüllendirir.
- **Mekanizmaları adversarial denetle.** Ağı açmadan önce kırmızı-takım senaryoları çalıştır. Her mekanizmanın bir oyun teorisi vardır; saldırganları değil, delikleri bulmak istersin.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Shapley değerlerinin toplam değere toplandığını doğrula (efficiency aksiyomu). Değer fonksiyonunu değiştir; Shapley dağılımları beklenen yönde değişiyor mu?
2. Shapley *sampling*'i uygula (K sıralama üzerinde Monte Carlo). K yaklaşım doğruluğunu nasıl etkiler? N=4 için kesin ile karşılaştır.
3. Açık artırmadan önce bir koalisyon oluşturma adımı uygula: agent'lar takımlara birleşip birim olarak teklif verebilir. Hangi koalisyonlar oluşur? Sonuç bireysel teklif vermekten Pareto-daha iyi mi?
4. Google Research mechanism-design yazısını oku. İhlal edilirse doğru-anlatıcılığı kıran bir varsayımı belirle. LLM ayarında o başarısızlık modu nasıl görünür?
5. AAMAS 2025 merkeziyetsiz LaMAS makalesini oku. Sentetik bir görev üzerinde 10 agent üzerinde Shapley adımlarını uygula. Kesin hesaplama ne kadar sürüyor? Sampling 100 çekim ile ne kadar yakına geliyor?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| DePIN | "Decentralized physical infrastructure" | Token-teşvikli compute/depolama/bant genişliği. Bittensor, Akash, Render. |
| DID | "Decentralized identifier" | Taşınabilir ID'ler için W3C spec'i. Agent itibarı platforma değil, DID'e bağlıdır. |
| ERC-4337 | "Account abstraction" | Gas sponsorluğu yapabilen ve agent ödemelerine olanak veren contract hesapları. |
| Shapley value | "Adil credit attribution" | Efficiency, symmetry, linearity, null'u sağlayan tek dağılım. |
| Second-price auction | "Vickrey açık artırması" | Doğru-anlatıcı mekanizma: kazanan ikinci-en-yüksek teklifi öder. Monoton toplama uyumlu. |
| Reputation capital | "Birikmiş kalite skoru" | Onaylanmış katkılardan DID-bağlı skor; zamanla çürür. |
| Agentic DAO | "Agent'lar + insanlar yönetir" | Agent oy verenlerin first-class olduğu, oy gücü itibara bağlı DAO. |
| TAO / FET / GPU credit | "Token denominasyonları" | Bittensor TAO, Fetch.ai FET, çeşitli DePIN token'ları. |

## İleri Okuma

- [The Agent Economy](https://arxiv.org/abs/2602.14219) — 5-katmanlı agent-ekonomi yığınının 2026 taraması
- [Google Research — Mechanism design for large language models](https://research.google/blog/mechanism-design-for-large-language-models/) — monoton toplamayla token açık artırmaları
- [AAMAS 2025 — decentralized LaMAS](https://www.ifaamas.org/Proceedings/aamas2025/pdfs/p2896.pdf) — Shapley-value credit attribution
- [Bittensor TAO documentation](https://docs.bittensor.com/) — subnet yapısı ve ödül dağılımı
- [Fetch.ai / ASI Alliance](https://fetch.ai/) — ASI-1 Mini LLM ve FET token
- [W3C Decentralized Identifiers (DIDs) spec](https://www.w3.org/TR/did-core/) — kimlik temeli
