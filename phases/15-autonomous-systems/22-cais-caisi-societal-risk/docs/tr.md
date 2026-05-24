# CAIS, CAISI ve Societal-Scale Risk

> Center for AI Safety (CAIS, San Francisco, 2022'de Hendrycks ve Zhang tarafından kuruldu), dört-riskli framework'ü — malicious use, AI yarışları, organizational riskler, rogue AI'ler — ve yüzlerce profesör ve şirket lideri tarafından imzalanan Mayıs 2023 ekstinksiyon risk açıklamasını yayımlar. CAIS'ten 2026 yayınları: frontier-model değerlendirme için AI Dashboard, Remote Labor Index (Scale AI ile), Superintelligence Strategy Paper, AI Frontiers newsletter. Ayrı bir entity: NIST Center for AI Standards and Innovation (CAISI) — cyber, bio ve kimyasal-silah risklerine odaklı US-hükümeti yönelimli gönüllü anlaşmalar ve unclassified kapasite değerlendirmeleri. CAIS organizational riski dört üst-seviye riskten biri olarak işaretler: safety kültürü, titiz audit'ler, multi-layered savunmalar ve information security temeldir ama rutin olarak deployment hızına karşı trade-off yapılır. California SB-53, imzalanırsa, ilk US eyalet-seviyesi catastrophic-risk regülasyonu olur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, dört-risk envanteri ve azaltma matcher)
**Ön koşullar:** Faz 15 · 19 (RSP), Faz 15 · 20 (PF + FSF)
**Süre:** ~45 dakika

## Sorun

Ders 19 ve 20 lab-dahili scaling policy'lerini kapsadı. Ders 21 bağımsız kapasite değerlendirmesini kapsadı. Bu ders üçüncü perspektifi kapsar: catastrophic AI riski için kamuoyu tartışmasını ve düzenleyici baseline'ı şekillendiren sivil toplum ve hükümet kuruluşları.

İki ayrı entity önemlidir. CAIS, AI riski hakkında düşünmek için framework'ler yayımlayan ve halka açık açıklamaları koordine eden bir non-profit araştırma org'udur. CAISI, NIST içinde lab'lerle gönüllü anlaşmalar ve unclassified kapasite değerlendirmeleri yürüten bir US-hükümeti merkezidir. İsimler kafiyeli; misyonlar örtüşmüyor. Bir pratisyen ikisini de bilmelidir.

Pratik içerik: CAIS'in dört-riskli framework'ü literatürdeki en yaygın referans verilen societal-scale-risk taksonomisidir. Safety kültürü ve organizational risk bunlardan biridir ve bu, bir pratisyenin en doğrudan kontrolünde olandır. SB-53 (California), imzalanırsa ilk US eyalet-seviyesi catastrophic-risk regülasyonu olur; bill'in çerçevelemesi önemlidir çünkü eyalet-seviyesi regülasyon US tech politikasında tarihsel olarak federal aksiyonu yönetmiştir.

## Kavram

### CAIS — Center for AI Safety

- Kuruluş: 2022'de San Francisco'da, Dan Hendrycks ve meslektaşları tarafından ("Zhang" adı şu anki bir co-founder'ı değil erken bir collaborator'u ifade eder; güncel liderlik için CAIS website'sine bak).
- Status: 501(c)(3) non-profit.
- Dikkate değer 2023 çıktısı: yüzlerce araştırmacı ve CEO tarafından imzalanmış ekstinksiyon risk açıklaması. Belirtildi: "AI'den ekstinksiyon riskini azaltmak, pandemiler ve nükleer savaş gibi diğer societal-scale risklerin yanında küresel bir öncelik olmalıdır."
- 2026 çıktıları: frontier-model değerlendirme için AI Dashboard, Remote Labor Index (Scale AI ile ortak), Superintelligence Strategy Paper, AI Frontiers newsletter.

### Dört-riskli framework

CAIS'in framework'ü catastrophic AI riskini dört üst-seviye kategoriye gruplar:

1. **Malicious use**: kötü bir aktör zarara neden olmak için AI kullanır (bioweapons sentezi, dezenformasyon, siber saldırılar).
2. **AI yarışları**: lab'ler, şirketler veya uluslar arasındaki rekabetçi baskı deployment'ı safe olduğu noktanın ötesine iter.
3. **Organizational riskler**: dahili lab dinamikleri (safety-kültürü failure'ları, yetersiz audit, kaynaksız güvenlik) kötü bir deployment üretir.
4. **Rogue AI'ler**: yeterince yetenekli bir AI insan refahıyla çatışan hedefleri takip eder.

Bu tek taksonomi değildir; en çok alıntılanandır. Kategoriler karşılıklı dışlayıcı değildir — bir yarışta audit'i hızla takas eden bir kuruluşun ürettiği rogue bir AI dörtüdür de.

### Organizational risk nerede yaşar

Dört kategoriden, organizational risk pratisyenler için en actionable olandır. Bir lab'in safety kültürü, audit titizliği, savunma katmanlaması ve information security'si, modelinin Ders 10-18'in kontrolleri aslında yerinde olarak mı gönderildiğine yoksa o kontrollerin kimsenin doğrulamadığı checklist öğeleri mi olduğuna karar verir.

Somut organizational-risk levyeleri:

- **Safety kültürü**: takım üyeleri kariyer maliyeti olmadan bir endişeyi yükseltebileceklerini hissediyorlar mı? CAIS anketleri bunun diğer levyelerin güçlü bir öngöreni olduğunu bulur.
- **Titiz audit'ler**: harici ve dahili. Yalnızca-dahili audit'ler iyimser raporlar üretir.
- **Multi-layered savunmalar**: hiçbir tek katman yeterli değildir (Faz 15'in çalışan teması).
- **Information security**: model ağırlıklarının sızması, eval verilerinin sızması, monitor-bypass tekniklerinin sızması. Ders 19'daki RAND SL-4 belirli bir standarttır.

### CAISI — Center for AI Standards and Innovation

- NIST içinde çalışır.
- Frontier lab'lerle gönüllü anlaşmalar yürütür.
- Cyber, bio ve kimyasal-silah risklerine odaklı unclassified kapasite değerlendirmeleri yayımlar.
- CAIS'ten farklıdır; akronimler çakışır; hangisini okuduğunu doğrulamak için URL'yi (nist.gov) kontrol et.

CAISI'nin rolü, METR'in özel lab engagement'larına (Ders 21) kamuoyu, hükümet-yönelimli karşılığıdır. CAISI raporları unclassified'dır; METR raporları sıkça NDA-gate'lidir. İkisini de okuyan bir pratisyen daha tam bir resim alır.

### California SB-53

California Senate bill'i (2025-2026 oturumu) frontier modellerden catastrophic riski ele alır. Taslak haliyle anahtar hükümler:

- Eyalet-seviyesi yükümlülükleri tetikleyen belirli kapasite eşikleri.
- AI lab çalışanları için whistleblower koruması.
- Catastrophic failure'lar için olay raporlama gereksinimleri.

İmzalanırsa, ilk US eyalet-seviyesi catastrophic-risk regülasyonu olur. İmzalama durumundan bağımsız olarak, bill'in çerçevesi diğer eyalet yasamalarının probleme nasıl yaklaştığını şekillendirir. California'daki pratisyenler bill'in status'unu takip etmeli; başka yerdekiler US eyalet-seviyesi regülasyonun muhtemelen neye benzeyeceğini anlamak için onu okumalıdır.

### Societal-scale risk tek-katmanlı bir problem değildir

Faz 15'in çalışan teması — defense in depth — societal katmana da uygulanır. Hiçbir tek kuruluş, regülasyon veya framework catastrophic riski kapatmaz. Ekosistem yalnızca şu durumda çalışır:

- Lab'ler scaling policy'leri gönderir (Ders 19, 20).
- Harici değerlendiriciler ölçümler üretir (Ders 21).
- Sivil toplum izler ve halka duyurur (CAIS).
- Hükümet gönüllü programlar ve baseline regülasyon yürütür (CAISI, SB-53).
- Pratisyenler multi-layered kontroller inşa eder (Ders 10-18).

Bu faz için final sentez budur: önceki her ders, herhangi bir tek katmanın gücünden çok bütünlüğü önemli olan bir yığındaki bir katmandır.

## Kullan

`code/main.py` küçük bir risk-envanter aracı uygular. Önerilen bir deployment verildiğinde, deployment'ı dört-risk kategorilerine karşı etiketler ve bir azaltma checklist'i döner. Framework için bir okuma yardımcısıdır, insan yargısının yerine geçemez.

## Yayınla

`outputs/skill-societal-risk-review.md`, bir deployment'ı societal-scale-risk duruşu için inceler: dört kategoriden hangilerine dokunduğu, hangi azaltmaların yerinde olduğu, organizational-risk exposure'ının ne olduğu.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Farklı ölçeklerde üç sentetik deployment besle. Dört-risk etiketlerinin beklediğin ile eşleştiğini doğrula; aracın altı- veya üstü-etiketlediği bir vakayı belirle.

2. CAIS dört-riskli makalesini tam olarak oku. Bir risk kategorisi seç ve o kategoride 2026'da en önemli gelişmenin ne olduğuna inandığın hakkında iki paragraf yaz.

3. California SB-53'ün güncel taslağını oku. Catastrophic-risk duruşunu güçlendirdiğine inandığın bir hükmü ve zayıflattığına inandığın bir hükmü belirle. İkisini de gerekçelendir.

4. Bildiğin bir üretim AI deployment'ını seç (kendininki veya yayımlanmış bir tane). Onu organizational-risk alt-levyelere karşı puanla: safety kültürü, audit titizliği, multi-layered savunmalar, information security. Hangisi en zayıf? Onu par'a getirmek ne kadar maliyetli?

5. Bir yıl ek kapasite ve bir yıl ek deployment deneyimini yansıtan dört-riskli framework'ün 2028 versiyonunu taslak çıkar. Ne ekler, kaldırır veya yeniden gruplandırırsın?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| CAIS | "Center for AI Safety" | Non-profit; dört-riskli framework; 2023 ekstinksiyon açıklaması |
| CAISI | "US hükümeti AI safety" | NIST Center; gönüllü anlaşmalar; unclassified eval'ler |
| Dört-riskli framework | "CAIS'in taksonomisi" | malicious use, AI yarışları, organizational riskler, rogue AI'ler |
| Malicious use | "Kötü aktör AI kullanır" | Bioweapons, dezenformasyon, siber saldırılar |
| AI yarışları | "Rekabetçi baskı" | Lab'ler/şirketler/uluslar deployment'ı safety'nin ötesine iter |
| Organizational risk | "Lab dahili failure" | Safety kültürü, audit, savunmalar, infosec |
| Rogue AI | "Misaligned agent" | İnsan refahıyla çatışan hedefleri takip eden yetenekli AI |
| California SB-53 | "Eyalet-seviyesi regülasyon" | 2025-2026 bill; imzalanırsa ilk US eyalet catastrophic-risk regülasyonu |

## İleri Okuma

- [Center for AI Safety](https://safe.ai/) — dört-riskli framework'ün kurumsal evi.
- [CAIS — AI Risks that Could Lead to Catastrophe](https://safe.ai/ai-risk) — dört-riskli makale.
- [CAIS — May 2023 statement on extinction risk](https://safe.ai/statement-on-ai-risk) — kısa ortak açıklama.
- [NIST CAISI](https://www.nist.gov/caisi) — hükümet-yönelimli AI standartları ve innovation merkezi.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — lab-seviyesi taahhütleri societal-scale çerçeveye bağlar.
