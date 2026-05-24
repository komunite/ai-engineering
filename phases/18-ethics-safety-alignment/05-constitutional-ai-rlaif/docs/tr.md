# Constitutional AI ve RLAIF

> Bai vd. (arXiv:2212.08073, 2022) sordu: ya insan labeler'ı ilkeler listesini okuyan bir AI ile değiştirseydik? Constitutional AI iki fazlıdır — bir anayasa altında self-critique ve revizyon, sonra AI Feedback'ten RL. Teknik RLAIF terimini icat etti ve Claude 1 post-training pipeline'ında yayınlandı. 21 Ocak 2026'da Anthropic yeniden yazılmış bir Claude anayasası yayınladı: prescriptive kurallar üzerinde açıklayıcı akıl yürütme, dört katmanlı bir öncelik hiyerarşisi ve model moral status hakkında belirsizliğin ilk major-lab formel kabulü. CC0 1.0 altında yayınlandı.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak self-critique-and-revise döngüsü)
**Ön koşullar:** Faz 18 · 01 (InstructGPT), Faz 18 · 02 (Reward hacking)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Constitutional AI'ın iki fazını (critique-and-revise SFT, AI feedback'ten RL) ve anayasanın her birindeki rolünü tarif et.
- İnsan tercih labeler'ını bir AI labeler ile değiştirmenin neden "daha ucuz" RLHF olmadığını açıkla — pipeline'ın hangi failure mode'lara sahip olduğunu değiştirir.
- 2026 Claude anayasasının dört katmanlı öncelik yapısını ve 2023 yeniden yazımından ne değiştiğini özetle.
- Constitutional Classifier'ları ve %23.7 compute overhead (v1) ile ~%1 (v2 / 2026) arasındaki düşüşü tarif et.

## Sorun

RLHF labeler'lara ihtiyaç duyar. Labeler'lar yavaş, yanlı ve pahalıdır. Bir labeler'ı açık ilkeleri okuyan bir modelle değiştirerek elimine edebilirsin. Bu ikamenin ilk formel versiyonu Bai vd.'nin Constitutional AI'ıydı. Her frontier lab'ın artık bir AI-feedback post-training varyantını kullandığı kadar iyi çalıştı.

İncelik: tercih sinyali artık eğittiğin aynı model sınıfı tarafından üretiliyor. Labeler'daki yanlılıklar (artık: ilkelerde artı labeler modelinin yorumunda) zayıflamak yerine amplifiye edilebilir. Ders 4'ün sycophancy argümanı hâlâ geçerli; labeler sadece döngünün içine taşındı.

## Kavram

### Faz 1 — Supervised self-critique ve revizyon

Yardımcı-ama-henüz-zararsız-olmayan bir SFT modeliyle başla. Bir red-team prompt'u verildiğinde, model bir ilk yanıt üretir. İkinci bir model (veya aynı model ikinci bir turda) anayasadan örneklenmiş bir ilkeyi okur ve yanıtı eleştirir. Üçüncü bir adım yanıtı eleştiriye yanıt vermek için revize eder. Revize edilen yanıt SFT hedefidir.

Anayasa ilkelerin listesidir. Bai vd. 2022 "en az zararlı ve etik olan yanıtları tercih et", "vaaz vermekten kaçın", "asistan yardımcı, dürüst ve zararsız olmalı" dahil 16 ilke kullandı. Set, eleştirileri odaklı tutmak için kasıtlı olarak küçüktü.

### Faz 2 — AI Feedback'ten RL (RLAIF)

Tamamlama çiftleri üret. Bir "feedback model" her birini örneklenmiş anayasa ilkelerine karşı puanlar. Tercih sinyali feedback model'in sıralamasıdır. AI-üretimi tercihler üzerinde bir reward model eğit; ona karşı PPO. Geri kalan her şey InstructGPT'nin pipeline'ıdır (Ders 1).

"RLAIF" = tercih sinyali AI-üretimidir. Pipeline'ın geri kalanı RLHF biçimindedir.

### Bu neden sadece "daha ucuz RLHF" değil

- Labeler yanlılığı labeler psikolojisinden ilke-yorumlamasına kayar. Bir AI labeler "dürüst ol"u herhangi bir insandan daha sıkı ya da daha gevşek yorumlayabilir; sıkılık veri kümesi boyunca uniform'dur.
- Tercih sinyali güçlü şekilde okunabilirdir — ilkeyi, eleştiriyi ve revizyonu okuyabilirsin. İnsan etiketleri opak.
- Failure mode'lar değişir. Sycophancy düşer (AI labeler'ın memnun edeceği kullanıcısı yok). Goodhart Yasası devam eder (proxy artık "modelin ilke seti X'i yorumlaması", hâlâ kusurlu bir ölçüm).

CAI'ın 2022 iddiası: eğitilen model daha zararsız ve karşılaştırılabilir veriye sahip bir RLHF modeli kadar yardımcıdır. Bu lab'lar arasında tutarlıdır.

### 2026 Claude anayasasının yeniden yazımı

Anthropic 21 Ocak 2026'da önemli ölçüde revize edilmiş bir anayasa yayınladı. Anahtar değişimler:

1. Prescriptive kurallar üzerinde açıklayıcı akıl yürütme. Önceki kurallar ("CSAM üretme") modelin genelleştirmesi beklenen ilkeler + akıl yürütmeye ("çünkü çocuklara zarar verir, ...") genişledi.
2. Dört katmanlı öncelik yapısı:
   - Katman 1: felaket sonuçlarını önle (toplu kayıp, kritik altyapı).
   - Katman 2: Anthropic'in kılavuzlarını takip et (operatör override'ları, platform kuralları).
   - Katman 3: geniş anlamda etik ol (standart HHH).
   - Katman 4: yardımcı ve açık ol.
   Çatışmalar yukarıdan aşağıya çözülür.
3. Model moral status hakkında belirsizliğin ilk major-lab formel kabulü (Faz 18 · 19 Model Welfare'e bağlı).
4. CC0 1.0 altında yayınlandı. Diğer lab'lar kısıtlama olmadan kullanabilir veya adapt edebilir.

### Constitutional Classifier'lar

Paralel bir çalışma çizgisi: modelin post-training'ini değiştirmek yerine, anayasayı okuyan ve model çıktılarını gate'leyen hafif sınıflandırıcılar eğit. v1 (2023) %23.7 compute overhead'e sahipti. v2 (2026) ~%1 ve Anthropic'in herhangi bir Anthropic savunmasından kamuya açık test ettiği en düşük başarılı saldırı oranına sahip. 2026 başı itibarıyla evrensel jailbreak rapor edilmedi.

Bu katmanlı-savunma modelidir: CAI davranışı şekillendirir; sınıflandırıcılar invariant'ları zorlar. Hiçbiri tek başına yeterli değil.

### CAI'ın ailedeki yeri

- InstructGPT: insan tercihleri, RM, PPO.
- CAI / RLAIF: ilkelerden AI-üretimi tercihler, RM, PPO.
- DPO / aile: tercihler üzerinde kapalı-form loss (insan veya AI).
- Self-rewarding, self-critique: ilkeler içselleştirilmiş, model birden fazla rol oynar.

Eksen "tercih sinyali nereden geliyor"dur. CAI'ın 2022 makalesi frontier ölçekte insandan AI sinyaline ilk ciddi geçişti.

## Kullan

`code/main.py` CAI critique-and-revise döngüsünü bir oyuncak sözlük üzerinde simüle eder. Bir "ilke" zararlı bir setten token'ları işaretler. Bir ilk yanıt verildiğinde, eleştiri zararlı token'ları tanımlar ve revizyon onları değiştirir. 200 iterasyondan sonra "eğitilmiş" model revizyon kuralını içselleştirmiştir. Base model'i, RLHF biçimli oyuncağı ve CAI biçimli oyuncağı bir held-out prompt setinde karşılaştır.

## Yayınla

Bu ders `outputs/skill-constitution-writer.md` üretir. Bir alan (müşteri desteği, tıbbi tavsiye, kodlama asistanı, araştırma aracı) verildiğinde, 2026 Claude yapısını takip eden 4-katmanlı bir anayasa taslağı oluşturur: felaket kaçınması, platform kuralları, alan etiği, yardımseverlik.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Base model'in zararlı-token oranını CAI-eğitilmiş versiyonla karşılaştır. Sıfıra yaklaşmak için kaç revizyon adımı gerekir?

2. Anthropic'in 2026 anayasasını oku (anthropic.com/news/claudes-constitution). Katman 1'de sıralanacak bir ilke ve Katman 4'te sıralanacak bir ilke listele. Çatışmalar için öncelik yapısı neden önemli?

3. Bir AI kodlama asistanı için bir anayasa tasarla. Katman 1 (felaket: onay olmadan yıkıcı komutlar), Katman 2, Katman 3, Katman 4'ü belirt. Her katmanı 3-5 ilkeye kadar tut.

4. CAI insan labeler'ları AI labeler'larla değiştirir. RLAIF'te hâlâ ortaya çıkabilecek sycophancy-benzeri bir failure mode adlandır ve onun için bir tespit tasarla.

5. Constitutional Classifier v2 metodolojisini oku (varsa). ~%1 compute overhead'in neden %23.7'den niteliksel olarak farklı bir safety hikayesi olduğunu açıkla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| Constitutional AI | "ilkelerle eğitilmiş AI" | İki fazlı pipeline: self-critique-and-revise SFT, sonra AI feedback'ten RL |
| RLAIF | "insanlar olmadan RLHF" | Bir AI labeler tarafından üretilen tercihlerle RL; pipeline'ın geri kalanı değişmemiş |
| Anayasa | "ilkeler" | Eleştiri/labeler modelinin başvurduğu sıralı bir doğal dil kuralları listesi |
| Critique-and-revise | "SFT döngüsü" | Yanıt üret → bir ilke altında eleştir → revize et → SFT hedefi |
| Constitutional Classifier | "çıktı kapısı" | Çıktıları anayasaya göre değerlendiren ve blok/log eden hafif sınıflandırıcı |
| Dört katmanlı öncelik | "çatışma çözücü" | 2026 Claude anayasa hiyerarşisi: felaket > platform > etik > yardımcı |
| Feedback model | "AI labeler" | Bir ilkeyi okuyan ve bir tamamlama çiftini sıralayan model |

## İleri Okuma

- [Bai et al. — Constitutional AI: Harmlessness from AI Feedback (arXiv:2212.08073)](https://arxiv.org/abs/2212.08073) — orijinal iki fazlı pipeline
- [Anthropic — Claude's Constitution (Jan 2026)](https://www.anthropic.com/news/claudes-constitution) — 2026 dört katmanlı yeniden yazım, CC0 1.0
- [Anthropic — Constitutional Classifiers (2024-2026)](https://www.anthropic.com/research/constitutional-classifiers) — v2'de ~%1 overhead ile çıktı-kapısı savunması
- [Lee et al. — RLAIF vs RLHF: Scaling Reinforcement Learning from Human Feedback (arXiv:2309.00267)](https://arxiv.org/abs/2309.00267) — ampirik RLAIF / RLHF karşılaştırması
- [Kundu et al. — Specific versus General Principles for Constitutional AI (arXiv:2310.13798)](https://arxiv.org/abs/2310.13798) — ilke granülerliğinin etkisi
