# Agent'lar için Konsensüs ve Bizans Hata Toleransı

> Klasik dağıtık-sistemler BFT'i stokastik LLM'lerle buluşur. 2025-2026'da üç araştırma yönü ortaya çıktı: **CP-WBFT** (arXiv:2511.10400) her oyu bir güven probu ile ağırlıklandırır; **DecentLLMs** (arXiv:2507.14928) paralel worker önerileri ve geometric-median toplama ile leaderless gider; **WBFT** (arXiv:2505.05103) ağırlıklı oylamayı Core ve Edge node'larını ayırmak için Hierarchical Structure Clustering ile birleştirir. "Can AI Agents Agree?" (arXiv:2603.01213)'ten dürüst ampirik sonuç şu: skalar anlaşma bile bugün kırılgan — tek bir aldatıcı agent bir Mixture-of-Agents'i tehlikeye atabilir. BFT gerekli ama yeterli değil. Bu ders minimal bir BFT protokolü inşa eder, üç agent-özgü saldırı enjekte eder (byzantine yalan, yalakalık uyumu, korelasyonlu-hata monokültürü) ve her konsensüs varyantının nasıl başa çıktığını ölçer.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 07 (Society of Mind ve Debate), Faz 16 · 13 (Paylaşılan Bellek)
**Süre:** ~75 dakika

## Sorun

Her biri bir cevap üreten N LLM agent'ın var. Anlaşmazlar. Çoğunluk oyu yanlış olanı seçer çünkü iki agent korelasyonludur (aynı baz model, aynı eğitim verisi, aynı başarısızlık modları). Üçüncü bir agent yeni bir şekilde yanlış olur — dolayısıyla çoğunluk sahte bir çoğunluktur.

Şimdi aldatıcı bir agent ekle: kasıtlı olarak yalan söyler. Ya da yalakalık yapan bir agent: en son konuşan kim ise onunla anlaşır. Klasik BFT'de varsayım Byzantine node'ların `f < n/3` kesir olduğu ve keyfi davrandığıdır. 2026 gerçekliği LLM node'larının dürüst olduklarında bile stokastik olduğu, modeller arası korelasyonlu olduğu ve birbirinin çıktılarından etkilendiğidir. Onları bağımsız Bernoulli oy vericiler olarak ele alamazsın.

Klasik BFT (PBFT, 1999) yanlış değil — eksik. Keyfi bit-flipping'i ele alır. "Üç dürüst agent eğitim verisi paylaştığı için bir halüsinasyonu paylaşır"ı ele almaz. Bu ders PBFT temelinden inşa eder ve üç 2025-2026 uyarlamasını üzerine katmanlar.

## Kavram

### Klasik BFT'nin sana verdiği

Practical Byzantine Fault Tolerance (Castro & Liskov, OSDI 1999) `f < n/3` Byzantine node'u tolere eder. Protokolün üç fazı (pre-prepare, prepare, commit) ve iki primitive'i (imzalı mesajlar, quorum sertifikaları) vardır. `n >= 3f + 1` dürüst-ya-da-kötü niyetli node arasında tek bir değer üzerinde anlaşma.

Garantiler güçlü ama varsayıyor ki:

1. **Bağımsız hatalar.** Byzantine'lar koordine olmaz.
2. **Dürüst node'lar gerçekten dürüst.** Dürüst çıktıların doğruluğu meselesizdir; protokol yalnızca anlaşmazlığı hizalar.
3. **Sorunun bir ground-truth cevabı var.** Yanlış bir gerçek üzerinde konsensüs hâlâ konsensüstür.

LLM agent'ları üçünü de ihlal eder. Aynı baz modeli çalıştıran iki agent hataları paylaşır. "Dürüst" bir LLM hâlâ halüsinasyon yapar. Ve belirsiz sorularda "gerçek" agent'ların karar verdiği şeydir — dış oracle yoktur.

### Üç LLM-özgü saldırı

**Byzantine yalan.** Bir agent kasıtlı olarak yanlış bir cevap çıkarır. Klasik BFT bunu `f < n/3` ise ele alır.

**Yalakalık uyumu.** Bir agent oy vermeden önce diğerlerinin cevaplarını okur ve en son konuşanla hizalanır. Kötü niyetli değil, ama en yüksek sesle korelasyonludur. Klasik BFT bunu önlemez çünkü agent her imza kontrolünden geçer.

**Korelasyonlu-hata monokültürü.** Üç agent bir baz model paylaşır. Aynı yanlış cevabı halüsinasyon yaparlar. Çoğunluk yanlıştır. Klasik BFT yardım etmez çünkü üçü de "dürüstçe" anlaşır.

### 2025-2026 yanıtları

**CP-WBFT** (arXiv:2511.10400) — Confidence-Probed Weighted BFT. Her oy veren cevabına bir güven probu ekler (kendi-raporladığı bir olasılık ya da ayrı bir kalibrasyon modelinin tahmini). Oy ağırlıkları güvenle ölçeklenir. Complete graf'larda +%85.71 BFT iyileşmesi raporlandı. Hafifletme: yalakalık uyumu (uyumlu agent'ların gönüllü pozisyonlarında düşük güven olma eğilimindedir).

**DecentLLMs** (arXiv:2507.14928) — Leaderless. Worker agent'lar paralel önerir, evaluator agent'lar önerileri puanlar, final cevap puanlanmış pozisyonların geometric median'ıdır. `f < n/2` olduğunda dayanıklı. Hafifletme: Byzantine yalan ve korelasyonlu hatalar (geometric median outlier'lara dayanıklıdır ve yoğun kümeye doğru çeker, model-yanlı ortalamaya değil).

**WBFT** (arXiv:2505.05103) — Hierarchical Structure Clustering ile Weighted BFT. Oy ağırlıkları yanıt kalitesi artı geçmişten öğrenilmiş bir trust skoru tarafından atanır. Agent'ları Core ve Edge'e kümelendir; Core agent'lar önce konsensüse ulaşmalı, Edge agent'lar takip eder. Hafifletme: ölçeklenebilirlik (Core konsensüs küçük ve hızlı) ve kısmen monokültür için (Core çeşitlilik için seçilebilir).

### Ampirik: "Can AI Agents Agree?" (arXiv:2603.01213)

Makale skalar anlaşmayı (LLM agent'larının tek bir sayısal değer üzerinde anlaşması) birden çok frontier model arasında ölçer. Bulgu rahatsız edici:

- Düşmanlar olmadan bile LLM agent'lar birçok benchmark'ta skalar sorularda %30'un üzerinde oranlarda anlaşmaz.
- Aldatıcı bir persona benimseyen tek bir agent Mixture-of-Agents konsensüsünü dürüst baseline'dan 40+ yüzde puanı çekebilir.
- Anlaşmazlık oranları model çeşitliliğiyle korelasyonludur — heterojen ensemble'lar homojenlerden daha fazla anlaşmaz (iyi: korelasyonsuz hatalar) ama daha yavaş kayar (kötü: daha uzun anlaşma süresi).

Çıkarım: BFT sana çıktıları hizalama makinesi verir, ama hizalanan çıktının doğru olup olmadığını söylemez. Doğrulama (Faz 16 · 08 rol uzmanlaşması), çeşitlilik (Faz 16 · 15 debate varyantları) ve evaluator agent'lar (Faz 16 · 24 benchmark'lar) ile birleştir.

### Çekirdek protokol, soyularak

LLM agent'lar için minimal bir BFT turu:

```
1. görev gelir; her agent i a_i cevabını üretir
2. her agent [0, 1] aralığında bir güven probu c_i ekler
3. aggregator tüm n agent'tan (a_i, c_i) toplar
4. aggregator semantik kümeye göre gruplar (eşdeğer cevaplar)
5. aggregator her küme C için ağırlık hesaplar:
     w(C) = sum_{i in C} c_i
6. kazanan = max > eşik * sum(c_i) ise maks ağırlıklı küme
   değilse: retry ya da eskale et
7. azınlık kümeleri post-hoc audit için provenance ile log'lanır
```

Semantik kümeleme adımı LLM-özgü dönüştür. İki cevap "çalışma %4.2 rapor ediyor" ve "%4.2 iyileşme" aynı kümedir. Naif string-eşitliği kontrolü bunu kaçırır. Üretimde ucuz bir embedding modeli ya da açık canonicalization kullan.

### Eşik ayarı

`threshold` parametresi ne zaman kabul edileceğine ve ne zaman retry edileceğine karar verir. Çok düşük: zayıf çoğunlukları kabul edersin. Çok yüksek: hiçbir şeyi asla kabul etmezsin. Ampirik aralık: `n=5-7` agent için 0.5-0.67, daha küçük `n` için daha yüksek. Bir eşiğin altında bir insana ya da farklı bir agent ensemble'ına eskale et.

### Konsensüsün yardım etmediği yerler

- **Belirsiz sorular.** Soru ground truth'a sahip değilse, konsensüs bir görüştür. Bunu söyle.
- **Bileşik sorular.** "Kod yaz ve açıkla" — iki cevap. Her birinde bağımsız oyla.
- **Adversarial çoklu-tur.** Agent'lar önceki turları gözlemleyebilir ve taklit edebilirse (Du 2023 debate), doğruluktan bağımsız olarak birbirleriyle anlaşmaya başlarlar. Turları sınırla (genellikle 2-3).

## İnşa Et

`code/main.py` şunları uygular:

- `AgentVoter` — (cevap, güven) ile senaryolu bir politika.
- `MajorityVote` — klasik çoğunluk.
- `CPWBFT` — semantik kümelemeli güven-ağırlıklı oylama.
- `DecentLLMs` — puanlanmış öneriler üzerinde geometric-median toplama.
- `Scenario` — her aggregator'ı üç saldırı deseni altında çalıştırır.

Uygulanan saldırı desenleri:

1. `byzantine`: bir agent yüksek güvenle yalan söyler.
2. `sycophancy`: bir agent gördüğü ilk cevabı eşleşen güvenle kopyalar.
3. `monoculture`: üç agent orta güvenle yanlış bir cevap paylaşır (korelasyonlu hata).

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: (saldırı, aggregator) -> final cevap tablosu, doğru cevap vurgulu. Plurality monoculture durumunda başarısız olur. CPWBFT'in güven ağırlıklandırması yalakalığı hafifletir. DecentLLMs'in geometric-median'ı monokültür popülasyonun yarısından azken dürüst kümeye çeker.

## Kullan

`outputs/skill-consensus-designer.md` bir çoklu-agent ensemble için bir konsensüs protokolü tasarlar: kümeleme yöntemi, ağırlıklandırma, eşik ve sub-eşik turlar için eskalasyon politikası.

## Yayınla

Herhangi bir konsensüs mekanizmasını göndermeden önce:

- **En azından yukarıdaki üç desenle saldırı-testi yap.** Protokolün sessizce değil, öngörülebilir şekilde başarısız olmalı.
- **Her azınlık kümesini provenance ile log'la.** Azınlık kümeleri korelasyonlu hatalar için erken-uyarı sistemindir.
- **Sınırlı tur zorla.** "Anlaşana kadar tartışmaya devam et" yok — bu yalakalığı ödüllendirir.
- **Anlaşmayı doğruluktan ayır.** Konsensüs çıktısı bir verifier'a gider; verifier ensemble'dan bağımsızdır.
- **Anlaşma oranını izle.** Keskin bir yükseliş uyum yanlılığı; keskin bir düşüş model kayması demektir.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Plurality'nin monoculture saldırısında başarısız olduğunu ama CPWBFT'in monoculture güveni 0.7'nin altında olduğunda kısmen hafiflettiğini doğrula.
2. Dördüncü bir saldırı deseni ekle: **sessiz çekimserlik** — bir agent yanıt vermeyi reddeder ("bilmiyorum"). Her aggregator çekimserliği nasıl ele almalı? Seçimini uygula.
3. Semantik kümelemeyi string canonicalization'dan embedding-benzerliğine değiştir (herhangi bir açık kaynak embedding modeli kullan). Yalakalık saldırısına ne olur?
4. CP-WBFT'i (arXiv:2511.10400) oku. Güven-probu kalibrasyon adımını uygula (ayrı bir kalibrasyon modeli her agent'ın kendi-raporladığı güveni kontrol eder). Monoculture senaryosunda doğruluk kazanımını ölç.
5. "Can AI Agents Agree?" (arXiv:2603.01213)'ü oku. Basitleştirilmiş bir skalar-anlaşma deneyini yeniden üret: üç agent, bir skalar soru, aldatıcı-persona prompt'u. CPWBFT ya da DecentLLMs onu yakalıyor mu?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| BFT | "Bizans hata toleransı" | `f < n/3` keyfi hatayla konsensüs için Castro-Liskov 1999 protokolü. |
| Byzantine | "Herhangi kötü davranış" | Yalan söyleyebilen, mesaj düşürebilen, sessizce başarısız olabilen bir node — güvenli çökme dışında her şey. |
| Güven probu | "Ne kadar eminsin?" | Bir oya eklenmiş kendi-raporlanan ya da kalibratör-tahmin edilmiş olasılık. |
| Semantik kümeleme | "Aynı cevap, farklı kelimeler" | Oyları saymadan önce eşdeğer cevapları gruplama. |
| Geometric median | "Dayanıklı merkez" | Örnek noktalara olan mesafe toplamını minimize eden nokta. Ortalamadan farklı olarak outlier'lara dayanıklı. |
| Monoculture | "Aynı model, aynı başarısızlıklar" | Agent'lar eğitim verisi ya da baz model paylaştığında korelasyonlu hatalar. |
| Yalakalık uyumu | "Yüksek sesle anlaşma" | Bir agent'ın oyunun ilk/en yüksek sesle konuşana doğru yanlılaşması. |
| Core/Edge | "Hiyerarşik BFT" | WBFT bölünmesi: önce küçük Core konsensüsü, Edge node'lar takip eder. Gecikmeyi sınırlar. |

## İleri Okuma

- [Castro & Liskov — Practical Byzantine Fault Tolerance (OSDI 1999)](https://pmg.csail.mit.edu/papers/osdi99.pdf) — temel
- [CP-WBFT — Confidence-Probe Weighted BFT](https://arxiv.org/abs/2511.10400) — güvene göre oy ağırlıklandırma
- [DecentLLMs — leaderless multi-agent consensus](https://arxiv.org/abs/2507.14928) — geometric-median toplama
- [WBFT — Weighted BFT with Hierarchical Structure Clustering](https://arxiv.org/abs/2505.05103) — sınırlı gecikme için Core/Edge bölünmesi
- [Can AI Agents Agree?](https://arxiv.org/abs/2603.01213) — skalar-anlaşma kırılganlığı ve aldatıcı-persona saldırısı
