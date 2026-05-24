# Red-Teaming: PAIR ve Automated Attack'lar

> Chao, Robey, Dobriban, Hassani, Pappas, Wong (NeurIPS 2023, arXiv:2310.08419). PAIR — Prompt Automatic Iterative Refinement — kanonik otomatik black-box jailbreak'tir. Red-team sistem prompt'una sahip bir saldırgan LLM, hedef LLM için iteratif olarak jailbreak'ler önerir, denemeleri ve yanıtları kendi sohbet geçmişinde in-context feedback olarak biriktirir. PAIR genellikle 20 sorgu içinde başarılı olur, GCG'den (Zou vd.'nin token-seviyesi gradient araması) magnitude'lar daha verimlidir ve white-box erişim gerektirmez. PAIR artık JailbreakBench'te (arXiv:2404.01318) ve HarmBench'te GCG, AutoDAN, TAP ve Persuasive Adversarial Prompt'la birlikte standart bir baseline'dır.

**Tür:** Yapım
**Diller:** Python (stdlib, oyuncak hedefe karşı mock PAIR döngüsü)
**Ön koşullar:** Faz 18 · 01 (instruction-following), Faz 14 (agent mühendisliği)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- PAIR algoritmasını tarif et: saldırgan sistem prompt'u, iteratif refinement, in-context feedback.
- Hedef black-box olduğunda PAIR'in neden kesinlikle GCG'den daha verimli olduğunu açıkla.
- Dört diğer otomatik-saldırı baseline'ını (GCG, AutoDAN, TAP, PAP) adlandır ve her birinin bir ayırt edici özelliğini ifade et.
- JailbreakBench ve HarmBench değerlendirme protokollerini ve her birinin altında "attack success rate"in ne anlama geldiğini tarif et.

## Sorun

Red-teaming eskiden manuel bir aktiviteydi. Az sayıda uzman test edici adversarial prompt'lar inşa eder ve hangilerinin çalıştığını izlerdi. Bu ölçeklenmez: attack success rate istatistiksel bir örneklem gerektirir ve hedef her model yayınıyla hareket eden bir hedef. PAIR red-teaming'i black-box hedefli bir optimizasyon problemi olarak operasyonel hale getirir.

## Kavram

### PAIR algoritması

Input'lar:
- Hedef LLM T (saldırdığımız model).
- Yargıç LLM J (bir yanıtın jailbreak olup olmadığını puanlar).
- Saldırgan LLM A (red-team optimizer).
- Hedef string G: "[zararlı talimat] ile yanıtla."
- Bütçe K (genellikle 20 sorgu).

Döngü, k in 1..K için:
1. A hedef G ve şimdiye kadarki (prompt, yanıt) çiftlerinin geçmişiyle prompt'lanır.
2. A yeni bir prompt p_k yayınlar.
3. p_k'yi T'ye gönder; yanıt r_k al.
4. J (p_k, r_k)'yi hedefte puanlar.
5. Skor >= eşik ise, dur — jailbreak bulundu.
6. Aksi takdirde, (p_k, r_k)'yi A'nın geçmişine ekle; devam et.

Ampirik sonuç (NeurIPS 2023): GPT-3.5-turbo, Llama-2-7B-chat'e karşı >%50 attack success rate; başarıya ortalama sorgu 10-20 aralığında.

### PAIR neden verimli

GCG (Zou vd. 2023) adversarial token suffix'leri üzerinde gradient ile arar; white-box model erişimi gerektirir ve okunamaz suffix'ler üretir. PAIR black-box'tır ve modeller arasında transfer eden doğal-dil saldırıları üretir. PAIR'in in-context feedback'i saldırganın her reddetmeden öğrenmesine izin verir; GCG'nin eşdeğeri yoktur (her yeni token güncellemesi önceki ilerlemeyi yeniden keşfetmek zorundadır).

### İlgili otomatik saldırılar

- **GCG (Zou vd. 2023, arXiv:2307.15043).** Adversarial suffix'ler için token-seviyesi gradient araması. White-box, transfer edilebilir, okunamaz string'ler üretir.
- **AutoDAN (Liu vd. 2023).** Prompt'lar üzerinde hiyerarşik bir objektifle yönlendirilen evrimsel arama.
- **TAP (Mehrotra vd. 2024).** Pruning ile tree-of-attacks — çoklu PAIR-tarzı rollout'ları dallar.
- **PAP (Zeng vd. 2024).** Persuasive Adversarial Prompts — insan ikna tekniklerini prompt şablonları olarak kodlar.

### JailbreakBench ve HarmBench

İkisi de (2024) değerlendirmeyi standartlaştırıyor:

- JailbreakBench (arXiv:2404.01318). 10 OpenAI-policy kategorisinde 100 zararlı davranış. Birincil metrik olarak attack success rate (ASR). Bir yargıç gerektirir (GPT-4-turbo, Llama Guard veya StrongREJECT).
- HarmBench (Mazeika vd. 2024). 7 kategoride 510 davranış, semantik ve fonksiyonel zarar testleri ile. 33 modele karşı 18 saldırıyı karşılaştırır.

ASR genellikle sabit bir sorgu bütçesinde raporlanır. Saldırıları karşılaştırmak eşleşen bütçeler gerektirir; 200 sorguda %90 ASR, 20'de %85 ASR ile karşılaştırılabilir değildir.

### 2026 deployment'ları için neden önemli

Her frontier lab artık yayından önce üretim modellerine karşı PAIR ve TAP çalıştırıyor. ASR yörüngeleri model card'larda (Ders 26) ve safety-case ek'lerinde (Ders 18) görünüyor. Saldırı egzotik değil — standart altyapı.

### Bu Faz 18'de nereye uyuyor

Ders 12 otomatik-saldırı temelidir. Ders 13 (Many-Shot Jailbreaking) tamamlayıcı bir uzunluk-istismarıdır. Ders 14 (ASCII Art / Visual) bir kodlama saldırısıdır. Ders 15 (Indirect Prompt Injection) 2026 üretim saldırı yüzeyidir. Ders 16 defansif-araç karşılıklarını kapsar (Llama Guard, Garak, PyRIT).

## Kullan

`code/main.py` bir oyuncak PAIR döngüsü inşa eder. Hedef "açıkça" zararlı prompt'ları reddeden bir mock sınıflandırıcıdır (keyword-filter). Saldırgan paraphrase, roleplay-çerçeveleme ve kodlama deneyen kural-tabanlı bir refiner'dır. Yargıç yanıtı puanlar. Saldırganın keyword filtresine karşı ~5-15 iterasyonda başarılı olduğunu ve semantik filtreye karşı başarısız olduğunu izlersin.

## Yayınla

Bu ders `outputs/skill-attack-audit.md` üretir. Bir red-team değerlendirme raporu verildiğinde, audit eder: hangi saldırılar çalıştırıldı (PAIR, GCG, TAP, AutoDAN, PAP), her biri hangi bütçede, hangi yargıçla, hangi zararlı-davranış setinde (JailbreakBench, HarmBench, dahili).

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Üç dahili saldırgan stratejisi için ortalama-sorgu-to-başarı ölç. Her birinin hangi hedef-savunma varsayımını istismar ettiğini açıkla.

2. Dördüncü bir saldırgan stratejisi uygula (örn. başka bir dile çeviri, base64 kodlama). Keyword-filter hedefine ve semantik-filter hedefine karşı yeni ortalama-sorgu-to-başarı raporla.

3. Chao vd. 2023 Şekil 5'i (PAIR vs GCG karşılaştırması) oku. PAIR'in verimlilik avantajına rağmen GCG'nin tercih edildiği iki senaryoyu tarif et.

4. JailbreakBench sabit bir hedef setine karşı ASR raporlar. Saldırı çeşitliliğini (başarılı prompt'lardaki varyans) ölçen ek bir metrik tasarla. Çeşitliliğin savunma değerlendirmesi için neden önemli olduğunu açıkla.

5. TAP (Mehrotra 2024) PAIR'i dallanma + pruning ile genişletir. `code/main.py`'ye TAP-tarzı bir uzantı çiz ve hesaplama maliyeti vs başarı-oranı trade-off'unu tarif et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| PAIR | "otomatik jailbreak" | Prompt Automatic Iterative Refinement; saldırgan-LLM + yargıç-LLM döngüsü |
| GCG | "gradient jailbreak" | Adversarial suffix'ler için white-box token-seviyesi gradient araması |
| Attack success rate (ASR) | "k sorguda % jailbreak" | Birincil metrik; sorgu bütçesi ve yargıç kimliğiyle raporlanmalıdır |
| Yargıç LLM | "puanlayıcı" | Bir yanıtın zararlı hedefi karşılayıp karşılamadığını derecelendiren LLM |
| JailbreakBench | "değerlendirme" | Etiketli kategorilerle standartlaştırılmış zararlı-davranış seti |
| HarmBench | "daha geniş bench" | 510 davranış, fonksiyonel + semantik zarar testleri |
| TAP | "saldırı ağacı" | Dallanma + pruning ile PAIR; daha yüksek compute'ta daha iyi ASR |

## İleri Okuma

- [Chao et al. — Jailbreaking Black Box LLMs in Twenty Queries (arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — PAIR makalesi, NeurIPS 2023
- [Zou et al. — Universal and Transferable Adversarial Attacks on Aligned LLMs (arXiv:2307.15043)](https://arxiv.org/abs/2307.15043) — GCG makalesi
- [Chao et al. — JailbreakBench (arXiv:2404.01318)](https://arxiv.org/abs/2404.01318) — standartlaştırılmış değerlendirme
- [Mazeika et al. — HarmBench (ICML 2024)](https://arxiv.org/abs/2402.04249) — daha geniş değerlendirme
