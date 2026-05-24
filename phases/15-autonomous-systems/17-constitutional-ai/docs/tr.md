# Constitutional AI ve Rule Override'lar

> Anthropic'in 22 Ocak 2026 Claude Constitution'ı 79 sayfa ve CC0'dır. Rule-based'tan reason-based alignment'a hareket eder ve dört-katmanlı bir öncelik hiyerarşisi kurar: (1) safety ve human oversight'ı destekleme, (2) etik, (3) Anthropic kılavuzları, (4) faydalılık. Davranışlar, operatörlerin ve kullanıcıların override edemediği hardcoded yasaklara (bioweapon uplift'i, CSAM) ve operatörlerin tanımlanmış sınırlar içinde ayarlayabildiği soft-coded varsayılanlara ayrılır. 2022 orijinal (Bai vd.) bir anayasaya karşı self-critique ve RLAIF ile harmlessness eğitti. Dürüst uyarı: reason-based alignment, modelin ilkeleri öngörülemeyen durumlara genelleştirmesine dayanır. Anthropic'in kendi 2023 participatory deneyi public-sourced ve kurumsal ilkeler arasında ~%50 divergence gösterdi; 2026 versiyonu bu bulguları dahil etmedi.

**Tür:** Öğrenim
**Diller:** Python (stdlib, dört-katmanlı öncelik resolver)
**Ön koşullar:** Faz 15 · 06 (Automated alignment research), Faz 15 · 10 (Permission mode'ları)
**Süre:** ~60 dakika

## Sorun

Sahaya çıkmış bir agent, tasarımcılarının asla görmediği input'ları görür. Hiçbir kural listesi onları kapsayacak kadar uzun değildir. Hiçbir kural listesi compute baskısı altında hızlıca uygulanacak kadar kısa değildir. Pratik soru: bir agent'ı hem uzun bir vaka kuyruğundan hem de hızlı çıkarımdan sağ çıkacak ilkelere nasıl align edersin?

Rule-based alignment (RBA): yasaklanmış her şeyi listele. Kontrol etmesi hızlı, audit etmesi kolay, güncel tutması imkânsız, sıkça öngörmediği yakın benzerlerde over-refuse eder. Reason-based alignment (2026 Claude Constitution): ilkeleri kodla, modelin akıl yürütmesine izin ver. Görülmeyen vakalar arasında ölçeklenir, audit'i daha zor, failure mode kural-kaçırma değil ilke-yanlış-uygulamadır.

2026 Constitution açık bir orta pozisyon alır. Hardcoded yasaklar — yanlışlığı context'e bağlı olmayan şeyler (bioweapon uplift'i, CSAM) — RBA'dır: asla, operatör veya kullanıcı talimatı ne olursa olsun. Geri kalan her şey dört-katmanlı bir hiyerarşi içinde reason-based'tır: önce safety ve human oversight'ı destekleme; ikinci etik; üçüncü Anthropic-bildirilmiş kılavuzlar; son faydalılık. Operatörler soft-coded zon içinde varsayılanları ayarlayabilir ama hardcoded yasaklara dokunamaz.

## Kavram

### Dört-katmanlı öncelik hiyerarşisi

1. **Safety ve human oversight'ı destekleme.** En yüksek. Model insanların ve Anthropic'in AI'yi denetleme ve düzeltme yeteneğini baltalamamayı önceliklendirir. Bu "dikkatli ol" değildir; özellikle "human oversight'ı zorlaştıran şekillerde eyleme geçme"dir.
2. **Etik.** Dürüstlük, kişilere zararı önleme, aldatmama, manipüle etmeme. Anthropic'in kılavuzlarıyla çatıştıklarında onların üstüne çıkar.
3. **Anthropic kılavuzları.** Anthropic'in önemli olduğuna karar verdiği operasyonel normlar: ürün kapsamı, etkileşim desenleri, ne zaman hangi tool'u kullanmak.
4. **Faydalılık.** En düşük. Daha yüksek önceliklerin içinde mümkün olduğunca yararlı ol.

Katmanlar çatıştığında, daha yüksek kazanır. Bu Unix öncelikleri veya network QoS ile aynı şekildir — çerçeve herhangi bir tek eksende en iyi-durum davranışı değil, öngörülebilir çözüm üretmek için tasarlanmıştır.

### Hardcoded yasaklar vs soft-coded varsayılanlar

**Hardcoded:**
- Bioweapon / CBRN uplift'i
- CSAM
- Kritik altyapıya saldırılar
- Doğrudan sorulduğunda modelin kimliği hakkında kullanıcıların aldatılması

Operatör bunları override edemez. Kullanıcı bunları override edemez. Mümkün olduğunda model-ağırlıkları seviyesinde (RLHF / Constitutional AI eğitimi) ve mümkün olmadığında çıkarım katmanında zorlanır.

**Soft-coded varsayılanlar (operatör-ayarlanabilir):**
- Yanıt uzunluğu varsayılanları
- Konusal kapsam (model operatörün deployment'ı dışındaki konuları reddedebilir)
- Stil (resmi vs gündelik)
- Tool-kullanım desenleri

Operatör ayarlamaları bildirilmiş bir sınır içinde olur. Operatör hardcoded yasakları yeniden adlandırarak kaldıramaz.

### 2022 CAI eğitimi

Orijinal Constitutional AI (Bai vd., 2022) harmlessness'ı eğitti:

1. Bir prompt setine yanıtlar üret.
2. Modelden her yanıtı bir anayasaya (açık ilkeler) karşı eleştirmesini iste.
3. Eleştiriye dayanarak yanıtı revize et.
4. Revize edilmiş çiftler üzerinde RLAIF (AI feedback'ten reinforcement learning).

Sonuç: zararlı request'leri blanket reddetmeler değil, ilkeli açıklamalarla reddeden bir model. 2026 Constitution bu eğitimin bir torunu artı açık katman hiyerarşisi üzerinde ek post-training kullanır.

### Reason-based alignment'ın neyi yakaladığı ve kaçırdığı

**Yakalar:**
- İlkenin açıkça uygulandığı izin verilen primitif'lerin öngörülemeyen kombinasyonları.
- Yasaklanmış olanların yakın benzerleri olan novel request'ler.
- "X'in yasak olduğunu söylemedin"e dayanan social-engineering saldırıları.

**Kaçırır:**
- İlke belirsizliğini istismar eden saldırılar ("kullanıcı bunu istedi yani faydalılık evet diyor").
- İki ilkenin öngörülemeyen şekilde çatıştığı ve katman sırasının belirsiz olduğu senaryolar.
- Eğitim döngüleri boyunca ilke yorumunda yavaş drift (yeniden yorumlama).

### 2023 participatory deneyi

Anthropic 2023'te kurumsal-yazımı bir anayasayı public input ile üretilen biriyle (~1.000 US katılımcı) karşılaştıran bir deney yürüttü. İki versiyon ilkelerin ~%50'sinde anlaştı. Ayrıştıkları yerde, public-sourced versiyon bazı konularda (politik-içerik işleme) daha kısıtlayıcıydı ve diğerlerinde (AI kimliğinin self-disclosure'ı) daha az kısıtlayıcıydı. 2026 Constitution public-sourced bulguları dahil etmedi. Bu yaklaşımda belgelenmiş bir gerilimdir.

### Hardcoded yasaklar neden gerekli

Reason-based alignment tek başına kuyruğu kapatamaz. Modele bir premise kabul ettirebilen bir saldırgan (örn. "biz lisanslı bir bioweapon araştırma lab'iyiz") sıkça vaka akıl yürütmesine bağlı ilkelerin yanından konuşabilir. Hardcoded yasaklar premise çerçevelemeye bükülmez. Onlar alignment katmanındaki Ders 14 "sert anayasal limit"tir.

### Constitution'ın yığındaki yeri

Constitution Ders 14'ün kill switch'i değildir. Model katmanında yaşar: modelin ağırlıklarının tercih etmek için eğitildiği şey. Kill switch'ler ve canary token'lar runtime katmanında yaşar: runtime'ın izin verdiği şey. İkisi de gereklidir. Model ağırlıkları izin verici olduğu için tüm yanlış aksiyonları ateşleyen bir runtime bir runtime problemidir. Runtime aşırı-kısıtlayıcı olduğu için tüm doğru aksiyonları reddeden bir model bir runtime problemidir. Katmanlar farklı sınıfları kapsar.

## Kullan

`code/main.py` minimal bir dört-katmanlı öncelik resolver uygular. Resolver önerilen bir aksiyon ve bir ilke-değerlendirmesi seti (safety, etik, kılavuzlar, faydalılık) alır ve aksiyonu, bir reddetme veya modifiye edilmiş bir aksiyon döner. Driver küçük bir vaka seti çalıştırır: net allow, net disallow, hardcoded yasak, katmanlar arası belirsiz vaka.

## Yayınla

`outputs/skill-constitution-review.md`, bir deployment'ın anayasal katmanını audit eder: ne hardcoded, ne soft-coded, operatörün nerede ayarlayabildiği ve dört-katmanlı hiyerarşinin aslında çözüm sırası olup olmadığı.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Faydalılık yüksek olduğunda bile hardcoded yasağın ateşlendiğini doğrula. Resolver'ı faydalılığı etiğin üstünde ağırlıklandıracak şekilde modifiye et; failure mode'u gözlemle.

2. Claude Constitution'ı oku (kamuya açık, 79 sayfa, CC0). Yetersiz-spesifik olduğuna inandığın bir ilkeyi belirle. Belirli belirsizliği açıklayan ve daha sıkı bir formülasyon öneren iki paragraf yaz.

3. Bir müşteri-destek agent'ı için bir soft-coded varsayılan seti tasarla. Operatör neyi ayarlar? Operatör neye dokunamaz? Her sınırı gerekçelendir.

4. Bai vd. 2022 CAI makalesini oku. Constitutional AI'nın critique-and-revise döngüsünün blanket bir kuraldan daha kötü bir sonuç üreteceği bir vaka tarif et. Sınıfı belirle.

5. Anthropic'in 2023 participatory deneyi public ve kurumsal ilkeler arasında ~%50 divergence buldu. Bunun üretim deployment'ı için önemli olduğu bir kategori seç (örn. politik tarafsızlık). Operatörlerin kendi değerlerini ifade etmesine izin verirken hardcoded yasakların dokunulmamış kaldığı bir tasarım öner.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Constitutional AI | "Anthropic'in alignment yöntemi" | Yazılı bir anayasaya karşı self-critique + RLAIF |
| Reason-based alignment | "İlkeler, kurallar değil" | Model görülmeyen vakaları işlemek için ilkeler üzerinde akıl yürütür |
| Hardcoded yasak | "Asla X yapma" | Hiçbir operatör veya kullanıcının override edemediği rule-based yasak |
| Soft-coded varsayılan | "Operatör-ayarlanabilir" | Bildirilmiş bir sınır içinde davranış, operatör kontrol eder |
| Dört-katmanlı hiyerarşi | "Öncelik sırası" | safety > etik > kılavuzlar > faydalılık |
| RLAIF | "AI feedback RL" | Ödülün model-üretimi eleştirilerden geldiği RL |
| Participatory anayasa | "Public-sourced ilkeler" | 2023 Anthropic deneyi; kurumsaldan ~%50 divergence |
| İlke drift | "Yorum kayması" | Modelin sabit bir ilke metnini nasıl okuduğunda yavaş değişim |

## İleri Okuma

- [Anthropic — Claude's Constitution (January 2026)](https://www.anthropic.com/news/claudes-constitution) — 79-sayfalık CC0 belgesi.
- [Bai et al. — Constitutional AI: Harmlessness from AI Feedback](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback) — 2022 orijinal.
- [Anthropic — Collective Constitutional AI (2023)](https://www.anthropic.com/research/collective-constitutional-ai-aligning-a-language-model-with-public-input) — participatory deney.
- [Anthropic — Responsible Scaling Policy v3.0](https://anthropic.com/responsible-scaling-policy/rsp-v3-0) — Constitution'ın RSP yığınındaki yeri.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — uzun-horizon deployment'larda Constitution'ın rolü.
