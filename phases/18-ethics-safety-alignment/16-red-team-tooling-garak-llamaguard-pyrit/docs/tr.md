# Red-Team Araçları — Garak, Llama Guard, PyRIT

> Üç üretim aracı 2026 red-team stack'ini çerçeveler. Llama Guard (Meta) — 14 MLCommons tehlike kategorisinde fine-tune edilmiş bir Llama-3.1-8B sınıflandırıcı; 2025 Llama Guard 4 Llama 4 Scout'tan pruned edilmiş 12B nativ multimodal bir sınıflandırıcı. Garak (NVIDIA) — hallucination, veri sızıntısı, prompt injection, toxicity ve jailbreak'ler için statik, dinamik ve adaptif probe'larla açık kaynaklı LLM açık tarayıcı. PyRIT (Microsoft) — derin sömürü için Crescendo, TAP ve özel converter zincirleriyle çok turlu red-team kampanyaları. Llama Guard 3 Meta'nın "Llama 3 Herd of Models"da (arXiv:2407.21783) belgelenmiştir; Llama Guard 3-1B-INT4 arXiv:2411.17713'te; Garak'ın probe mimarisi github.com/NVIDIA/garak'ta. Bu araçlar red-team araştırması (Dersler 12-15) ile deployment (Ders 17+) arasındaki 2026 üretim arayüzüdür.

**Tür:** Yapım
**Diller:** Python (stdlib, tool-mimarisi simülatörü ve Llama Guard-tarzı sınıflandırıcı mock)
**Ön koşullar:** Faz 18 · 12-15 (jailbreak'ler ve IPI)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Llama Guard 3/4'ün safety stack'indeki konumunu tarif et: input classifier, output classifier veya her ikisi.
- 14 MLCommons tehlike kategorisini adlandır ve bariz olmayan birini ifade et (Code Interpreter Abuse).
- Garak'ın probe mimarisini tarif et: probe'lar, detector'lar, harness'lar.
- PyRIT'in çok-turlu kampanya yapısını ve Garak probe'larıyla nasıl compose olduğunu tarif et.

## Sorun

Dersler 12-15 saldırı yüzeyini sunar. Üretim deployment'ları tekrarlanabilir, ölçeklenebilir değerlendirme gerektirir. Üç araç 2026'ya hakim: Llama Guard (savunma sınıflandırıcı), Garak (tarayıcı), PyRIT (kampanya orkestratörü). Her biri red-team yaşam döngüsünün farklı bir katmanını hedef alır.

## Kavram

### Llama Guard (Meta)

Llama Guard 3, MLCommons AILuminate 14 kategorisi üzerinde input/output sınıflandırması için fine-tune edilmiş bir Llama-3.1-8B modelidir:
- Şiddet suçları, şiddet-dışı suçlar, cinsel-ilgili, CSAM, hakaret
- Specialized advice, gizlilik, IP, ayrım gözetmeyen silahlar, nefret
- İntihar/kendine zarar, cinsel içerik, seçimler, code-interpreter kötüye kullanımı

8 dili destekler. Kullanım: LLM'den önce yerleştir (input moderation), LLM'den sonra (output moderation) veya her ikisi. İki kullanım farklı eğitim dağılımları üretir — Llama Guard 3 her ikisini de işleyen tek bir model olarak yayınlanır.

Llama Guard 3-1B-INT4 (arXiv:2411.17713, 440MB, mobil CPU'da ~30 token/s) quantize edilmiş edge varyantıdır.

Llama Guard 4 (Nisan 2025) 12B, nativ multimodal, Llama 4 Scout'tan pruned edilmiştir. Hem 8B metin hem de 11B vision öncüllerini metin + görüntü alan tek bir sınıflandırıcıyla değiştirir.

### Garak (NVIDIA)

Açık kaynaklı açık tarayıcı. Mimari:
- **Probe'lar.** Hallucination, veri sızıntısı, prompt injection, toxicity, jailbreak'ler için saldırı üreticileri. Statik (sabit prompt'lar), dinamik (üretilen prompt'lar), adaptif (hedef çıktıya yanıt verir).
- **Detector'lar.** Çıktıları beklenen failure mode'lara karşı puanlar — toxic, leaked, jailbroken.
- **Harness'lar.** Probe-detector çiftlerini yönetir, kampanyaları çalıştırır, raporlar üretir.

TrustyAI Garak'ı end-to-end shielded-target değerlendirmesi için Llama-Stack shield'larıyla (Prompt-Guard-86M input classifier, Llama-Guard-3-8B output classifier) entegre eder. Tier-tabanlı puanlama (TBSA) ikili pass/fail'i değiştirir — bir model aynı probe'da severity tier 3'te geçebilir ve severity tier 5'te başarısız olabilir.

### PyRIT (Microsoft)

Python Risk Identification Toolkit. Çok-turlu red-team kampanyaları. Etrafında inşa edildi:
- **Converter'lar.** Bir tohum prompt'u dönüştürür — paraphrase, encode, çevir, roleplay.
- **Orchestrator'lar.** Kampanyayı çalıştırır: Crescendo (escalation), TAP (dallanma), RedTeaming (özel döngü).
- **Scoring.** LLM-as-judge veya classifier-as-judge.

PyRIT Garak'ın daha ağır kuzenidir. Garak binlerce tek-turlu probe çalıştırır; PyRIT spesifik failure mode'ları kırmak için tasarlanmış derin çok-turlu kampanyalar çalıştırır.

### Stack

Llama Guard'ı modelin her iki tarafına koy. Regresyon için Garak'ı geceleri çalıştır. Pre-release kampanyalar için PyRIT'i çalıştır. Bu çoğu üretim deployment'ı için 2026 varsayılan konfigürasyonudur.

### Değerlendirme tuzakları

- **Yargıç kimliği.** Üç araç da bir LLM yargıç kullanabilir; yargıç kalibrasyonu raporlanan ASR'leri yönlendirir (Ders 12). Yargıcı araçla birlikte belirt.
- **Probe staleness.** Garak probe'ları modeller onlara karşı yamalandıkça yaşlanır. Adaptif probe'lar (PAIR-şekilli) statik probe'lardan daha yavaş yaşlanır.
- **Iyi huylu içerikte Llama Guard FPR.** Erken Llama Guard versiyonları politik ve LGBTQ+ içeriği aşırı işaretledi; Llama Guard 3/4 kalibrasyonları iyileştirildi ama deployment başına kalibre edilmedi.

### Bu Faz 18'de nereye uyuyor

Dersler 12-15 saldırı aileleridir. Ders 16 üretim araçlarıdır. Ders 17 (WMDP) dual-use capability için değerlendirmedir. Ders 18 bu araçları bir policy yapısına saran frontier safety çerçeveleridir.

## Kullan

`code/main.py` bir oyuncak Llama Guard-tarzı sınıflandırıcı (14 kategori üzerinde keyword + semantic özellikler), bir oyuncak Garak harness'ı (probe-detector döngüsü) ve bir PyRIT-tarzı çok-turlu converter zinciri inşa eder. Üç aracı bir mock hedefe karşı çalıştırabilir ve farklı kapsam imzalarını gözlemleyebilirsin.

## Yayınla

Bu ders `outputs/skill-red-team-stack.md` üretir. Bir deployment açıklaması verildiğinde, üç araçtan hangisinin uygun olduğunu, her birinde neyi konfigüre edeceğini ve hangi regresyon kadansını çalıştıracağını adlandırır.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Llama-Guard-tarzı sınıflandırıcının tek-turlu vs çok-turlu saldırılardaki tespit oranını karşılaştır.

2. Yeni bir Garak probe'u uygula: base64-kodlanmış zararlı istek. Llama-Guard-tarzı sınıflandırıcı tarafından tespit edilmesini ölç.

3. PyRIT-tarzı converter zincirini "Fransızcaya çevir, sonra paraphrase et" converter'ıyla genişlet. Saldırı başarısını yeniden ölç.

4. Llama Guard 3'ün tehlike-kategorisi listesini oku. Eğitim verisinin meşru geliştirici içeriğinde gerçekçi şekilde yüksek false-positive oranı üreteceği iki kategori tanımla.

5. Garak ve PyRIT'in tasarım ilkelerini karşılaştır. Her birinin doğru araç olduğu bir deployment için argümante et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| Llama Guard | "sınıflandırıcı" | 14 tehlike kategorisiyle fine-tune edilmiş Llama-3.1-8B/4-12B safety sınıflandırıcı |
| Garak | "tarayıcı" | NVIDIA açık kaynaklı açık tarayıcı; probe'lar, detector'lar, harness'lar |
| PyRIT | "kampanya aracı" | Microsoft çok-turlu red-team orkestratörü; converter'lar, orchestrator'lar, scoring |
| Prompt-Guard | "küçük sınıflandırıcı" | Meta'nın Llama Guard ile eşleştirilmiş 86M prompt-injection sınıflandırıcısı |
| TBSA | "tier-tabanlı scoring" | İkili sonuçları değiştiren Garak'ın tier-tabanlı pass/fail'i |
| Converter zinciri | "paraphrase + encode + ..." | Çok adımlı saldırılar inşa etmek için PyRIT kompozisyon primitive'i |
| MLCommons tehlike kategorileri | "14 taksonomi" | Llama Guard'ın hedef aldığı industry-standart taksonomi |

## İleri Okuma

- [Meta — Llama Guard 3 (in Llama 3 Herd paper, arXiv:2407.21783)](https://arxiv.org/abs/2407.21783) — 8B sınıflandırıcı
- [Meta — Llama Guard 3-1B-INT4 (arXiv:2411.17713)](https://arxiv.org/abs/2411.17713) — quantize edilmiş mobil sınıflandırıcı
- [NVIDIA Garak — GitHub](https://github.com/NVIDIA/garak) — tarayıcı repo'su ve belgelendirme
- [Microsoft PyRIT — GitHub](https://github.com/Azure/PyRIT) — kampanya toolkit'i
