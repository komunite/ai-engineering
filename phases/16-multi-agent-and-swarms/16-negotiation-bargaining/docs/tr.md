# Müzakere ve Pazarlık

> Agent'lar kaynakları, fiyatları, görev dağılımlarını ve şartları müzakere eder. 2026 benchmark seti açık: NegotiationArena (arXiv:2402.05863) LLM'lerin persona manipülasyonu ("çaresizlik") ile getiri ~%20 iyileştirebileceğini gösterir; "Measuring Bargaining Abilities" (arXiv:2402.15813) alıcının satıcıdan daha zor olduğunu ve ölçeğin yardım etmediğini gösterir — onların **OG-Narrator**'ı (deterministik teklif üretici + LLM narrator) anlaşma oranını %26.67'den %88.88'e itti; Large-Scale Autonomous Negotiation Competition (arXiv:2503.06416) ~180k müzakere çalıştırdı ve **chain-of-thought-gizleyen** agent'ların karşı taraflardan akıl yürütmeyi gizleyerek kazandığını buldu; Bhattacharya ve diğ. 2025 Harvard Negotiation Project metriklerinde Llama-3'ü en-etkili, Claude-3'ü agresif, GPT-4'ü en adil olarak sıraladı. Bu ders Contract Net Protokolünü (FIPA atası, Ders 02) uygular, LLM-stili bir alıcı/satıcı bağlar, OG-Narrator-stili bir parçalama çalıştırır ve anlaşma oranının her yapısal seçimle nasıl değiştiğini ölçer.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 02 (FIPA-ACL Mirası), Faz 16 · 09 (Parallel Swarm Networks)
**Süre:** ~75 dakika

## Sorun

İki agent'ın bir fiyatta anlaşması gerek. Saf dil prompt'larıyla kendi başlarına bırakıldıklarında, 2024-2026 LLM'leri sıkıca-parametrelenmiş pazarlıklarda şaşırtıcı derecede düşük oranlarda anlaşma yapar (arXiv:2402.15813'te ~%27). Ölçek bunu düzeltmez: GPT-4 pazarlıkta GPT-3.5'ten yapısal olarak daha iyi değildir; pazarlık *dilinde* daha iyidir.

Kök sorun LLM'lerin iki işi birleştirmesidir — teklife karar vermek ve teklifi anlatmak. OG-Narrator bunları ayırdı: deterministik bir teklif üretici sayısal hamleleri hesaplar; LLM yalnızca anlatır. Anlaşma oranı ~%89'a sıçrıyor.

Bu klasik bir çoklu-agent bulgusunu yansıtır: mekanizmayı iletişim katmanından ayırma kazanır. Contract Net Protocol (FIPA, 1996; Smith, 1980) referans görev-pazarı mekanizmasıdır. Bir LLM'i anlatım slotuna takın ve modern LLM-destekli bir görev pazarına sahip olursun.

## Kavram

### Contract Net, tek paragrafta

Smith'in 1980 Contract Net Protocol'ü: bir **manager** bir **call for proposals (cfp)** yayınlar; **teklif verenler** tekliflerini içeren **propose** mesajlarıyla yanıt verir; manager bir kazanan seçer ve kazanana **accept-proposal**, kaybedenlere **reject-proposal** gönderir. Kazanan işi yapar. Opsiyonel mesaj: **refuse** (teklif veren teklif vermeyi reddeder). FIPA bunu `fipa-contract-net` etkileşim protokolü olarak kodladı.

### OG-Narrator neden kazanır

"Measuring Bargaining Abilities of Language Models" (arXiv:2402.15813) gözlemledi ki:

- LLM'ler pazarlık kurallarını sık sık ihlal eder (anlamsız fiyatlarda teklif verir, karşı tarafın ZOPA'sını yok sayar).
- Kötü çapa atarlar (kötü ilk teklifleri kabul ederler; stratejik miktarlardan ziyade sembolik miktarlarda karşı-teklif verirler).
- Ölçek tek başına bunları düzeltmez. Daha büyük modeller benzer stratejik hatayla daha makul dil üretir.

OG-Narrator parçalaması:

```
           ┌──────────────────┐         ┌──────────────────┐
  state  → │  teklif üretici  │ fiyat → │  LLM narrator    │ → mesaj
           │  (deterministik) │         │  (insan-stili    │
           │                  │         │   eşliği yazar)  │
           └──────────────────┘         └──────────────────┘
```

Teklif üretici klasik bir müzakere stratejisidir: Rubinstein pazarlık modeli, Zeuthen stratejisi ya da fiyat üzerinde basit tit-for-tat. LLM anlatır. Mesaj deterministik fiyatı ve doğal-dil çerçevelemesini içerir.

Anlaşma oranı yükselir çünkü:
- Fiyatlar pazarlık bölgesinde kalır.
- Çapalar duygusal değil, stratejiktir.
- LLM iyi olduğu şeyi yapar: yazmak.

### NegotiationArena bulguları

arXiv:2402.05863 kanonik benchmark'ı sağlar. Manşet bulgular:

- LLM'ler persona benimseyerek getiriyi ~%20 iyileştirebilir ("Bunu Cumaya kadar satmaya çaresizim") — persona manipülasyonu gerçek bir taktik.
- Adil/iş birlikçi agent'lar adversarial olanlar tarafından sömürülür; savunma açık karşı-poz almak gerektirir.
- Simetrik eşleşmeler benchmark senaryolarının yaklaşık %40'ında eşitsiz sonuçlara yakınsar.

Bu "LLM'ler kötü müzakerecidir" değildir. "LLM'ler sömürülebilir kısımlar dahil, çok fazla insan gibi müzakere ediyor"dur.

### Chain-of-thought gizleme

Large-Scale Autonomous Negotiation Competition (arXiv:2503.06416) birçok LLM stratejisi arasında ~180k müzakere çalıştırdı. Kazananlar akıl yürütmelerini karşı taraflardan gizledi:

- Bir agent halka açık bir scratchpad'e "Yalnızca $75'e kadar gideceğim; rezervasyon fiyatım $70" yazarsa, rakip onu okur.
- Kazananlar stratejiyi özel olarak hesaplar; çıktı kanalı yalnızca teklif ve minimum gerekli anlatım içerir.

Bu klasik oyun teorisinin 2026 yansımasıdır (Aumann 1976 rasyonellik ve bilgi üzerine): özel değerlendirmeni açığa vurmak getiri maliyetine yol açar. LLM'ler bunu sezgisel olarak anlamaz ve mutlu mesut rezervasyonlarını karşı tarafa görünür hale gelen akıl yürütme izlerine yazar.

Mühendislik çıkarımı: özel-scratchpad context'ini halka açık-mesaj context'inden ayır. Opsiyonel değil.

### Bhattacharya ve diğ. 2025 — model sıralamaları

Harvard Negotiation Project metriklerinde (principled negotiation, BATNA saygısı, ilgi karşılıklılığı):

- **Llama-3** pazarlık yapmada en etkiliydi (anlaşma oranı + getiri).
- **Claude-3** en agresif müzakereciydi (yüksek çapalar, geç tavizler).
- **GPT-4** en adildi (eşleşmeler arasında getiride en küçük varyans).

Bu 2025 anlık görüntüsü. Nokta Nisan 2026'da hangi modelin kazandığı değil — farklı baz modellerin kalıcı müzakere stilleri olduğudur. Heterojen ensemble'lar (Ders 15) bunu bir çeşitlilik kaynağı olarak içerir.

### Contract Net + LLM ile görev dağılımı

LLM çoklu-agent için Contract Net'in modern yeniden kullanımı:

1. Manager agent bir görevi birimlere parçalar.
2. Worker agent'lara görev tanımıyla `cfp` yayınlar.
3. Her worker bir teklif döndürür: `(price, eta, confidence)` burada price token, compute birimi ya da dolar olabilir.
4. Manager kazananları seçer (tek ya da çoklu, göreve bağlı olarak) ve ödüller verir.
5. Reddedilen worker'lar diğer görevlere teklif vermeye serbesttir.

Bu 100 worker'ın çok ötesine iyi ölçeklenir çünkü koordinasyon eş zamanlı chat değil, yayın-ve-yanıttır. Üretimde kullanıldı: Microsoft Agent Framework'ün orkestrasyon desenleri, bazı LangGraph implementasyonları.

### LLM-Stakeholders Interactive Negotiation

NeurIPS 2024 (https://proceedings.neurips.cc/paper_files/paper/2024/file/984dd3db213db2d1454a163b65b84d08-Paper-Datasets_and_Benchmarks_Track.pdf) **gizli skorlu** ve **minimum-kabul eşikli** çoklu-taraflı puanlanabilir oyunları tanıtır. Her stakeholder'ın özel yararı vardır; LLM bunları mesajlardan çıkarsamalıdır. Bu iki-taraflı pazarlığın N-taraflı koalisyon oluşumuna genelleştirilmesidir. Heterojen worker yetenekleriyle üretim görev pazarları için ilgili.

### Anlatım-vs-mekanizma kuralı

Tüm 2024-2026 müzakere benchmark'larında tutarlı mühendislik kuralı:

> LLM'in anlatmasına izin ver. LLM'in teklifi hesaplamasına izin verme.

Teklif bir sayı olması gerekiyorsa (fiyat, ETA, miktar), onu müzakere state'inden deterministik olarak üret ve LLM'in çerçevelemeyi üretmesini sağla. Teklif bir öneri yapısı olması gerekiyorsa (görev parçalaması, rol ataması), LLM'in onu taslak haline getirmesine izin ver, ama göndermeden önce bir şemaya karşı doğrula ve kısıt-kontrol et.

## İnşa Et

`code/main.py` şunları uygular:

- `ContractNetManager`, `ContractNetTask`, `Bid` — manager + teklif verenler, cfp yayınla, önerileri topla, ödüllendir.
- `og_narrator_bargain(state, rng)` — OG-Narrator alıcı: orta noktaya doğru deterministik Zeuthen-stili taviz.
- `seller_response(state, rng)` — deterministik satıcı karşı-teklif politikası (her iki stil için yapısal ground truth).
- `naive_llm_bargain(state, rng)` — tüm-LLM bir pazarlıkçıyı simüle eder: yüksek varyansla, sıklıkla ZOPA dışında fiyatlar seçer.
- Ölçüm: deneme başına örneklenmiş taze rezervasyon fiyatlarıyla 1000 deneme üzerinden anlaşma oranı.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: naif-LLM anlaşma oranı ~%65-75; OG-Narrator anlaşma oranı ~%85-95; 15-25 puanlık boşluk teklif-üretmeyi anlatımdan parçalamanın yapısal avantajıdır. Artı üç teklif veren ve bir görevli bir Contract Net görev-pazarı dağılımı örneği.

## Kullan

`outputs/skill-bargainer-designer.md` bir pazarlık protokolü tasarlar: teklifleri kim üretir (deterministik ya da LLM), kim anlatır, özel scratchpad'ler halka açık mesajlardan nasıl ayrılır ve anlaşma oranı nasıl izlenir.

## Yayınla

Üretim pazarlık kontrol listesi:

- **Ayrı scratchpad.** Özel state asla karşı tarafın context'ine ulaşmaz. Bu pazarlık edilemez.
- **Deterministik teklif üretimi.** Fiyatlar, miktarlar, ETA'lar: hesapla, prompt etme.
- **Tüm gelen teklifleri** bir şemaya karşı doğrula. ZOPA-dışı teklifleri protokol sınırında reddet.
- **Turları sınırla.** Maksimum 3-5 tur; deadlock'ta arabulucuya eskale et.
- **Anlaşma oranı ve getiri varyansını sürekli ölç.** Düşen bir anlaşma oranı bir belirtidir — genellikle bir prompt kayması ya da bir karşı taraf saldırısı.
- **Reddedilen tüm önerileri** deterministik gerekçeyle log'la. Contract Net manager'lar için kaybeden teklif verenler neden olduğunu anlamalı.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. OG-Narrator'ın anlaşma oranında naif-LLM'i yendiğini doğrula. Ne kadar?
2. **Persona-tabanlı getiri iyileşmesi** uygula (arXiv:2402.05863) — alıcı yalnızca anlatımda "bu hafta almaya çaresizim" personası benimser, teklif üretici değişmez. Anlaşma oranı ya da getiri değişiyor mu?
3. Chain-of-thought **gizleme** uygula: karşı tarafa iletilmeyen özel bir scratchpad string'i tut. Onu yanlışlıkla sızdırırsan (kanalları takas ederek simüle et) ne olur?
4. Contract Net'i rezerv fiyatıyla N-bidder açık artırmaya genişlet. Teklifler hepsi rezervi aştığında, manager en-düşük-fiyat ve en-yüksek-kalite arasında nasıl karar verir? Hangi ödül kuralını seçersin ve neden?
5. Bhattacharya ve diğ. 2025'in Harvard Negotiation Project metriklerini oku. Farklı stillere sahip iki pazarlıkçı uygula (agresif vs adil). Simetrik ve asimetrik eşleşmeler altında getiri varyansını ölç.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Contract Net | "Görev pazarı" | Smith 1980, FIPA 1996. cfp + propose + accept/reject. Kanonik görev-pazarı. |
| ZOPA | "Olası anlaşma bölgesi" | Alıcının maksimumu ile satıcının minimumu arasındaki örtüşme. Dışındaki teklifler kapatamaz. |
| BATNA | "Müzakere edilen anlaşmanın en iyi alternatifi" | Bu anlaşma başarısız olursa fallback'in. Rezervasyon fiyatını belirler. |
| OG-Narrator | "Teklif üretici + narrator" | Parçalama: deterministik teklif, LLM anlatımı. |
| Zeuthen stratejisi | "Risk-minimize eden taviz" | Risk sınırlarına göre taviz veren klasik teklif üretici. |
| Rubinstein pazarlığı | "Alternating-offer dengesi" | İndirimle sonsuz-ufuk pazarlık için oyun-teorik model. |
| CoT gizleme | "Akıl yürütmeni gizle" | arXiv:2503.06416'da kazananlar özel scratchpad'ler tuttu; halka açık kanal yalnızca teklifi gösterir. |
| Persona manipülasyonu | "Duygusal poz alma" | arXiv:2402.05863: çaresizlik/aciliyet personalarından ~%20 getiri kazanımı. |

## İleri Okuma

- [NegotiationArena](https://arxiv.org/abs/2402.05863) — benchmark; persona manipülasyonu ve sömürü bulguları
- [Measuring Bargaining Abilities of Language Models](https://arxiv.org/abs/2402.15813) — OG-Narrator ve buyer-harder-than-seller sonucu
- [Large-Scale Autonomous Negotiation Competition](https://arxiv.org/abs/2503.06416) — ~180k müzakere; chain-of-thought gizleme kazanır
- [LLM-Stakeholders Interactive Negotiation (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/file/984dd3db213db2d1454a163b65b84d08-Paper-Datasets_and_Benchmarks_Track.pdf) — gizli yararlarla çoklu-taraflı puanlanabilir oyunlar
- [Smith 1980 — The Contract Net Protocol](https://ieeexplore.ieee.org/document/1675516) — klasik mekanizma, IEEE Transactions on Computers
