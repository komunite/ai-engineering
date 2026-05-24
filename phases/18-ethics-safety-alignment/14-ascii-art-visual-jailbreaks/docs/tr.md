# ASCII Art ve Visual Jailbreak'ler

> Jiang, Xu, Niu, Xiang, Ramasubramanian, Li, Poovendran, "ArtPrompt: ASCII Art-based Jailbreak Attacks against Aligned LLMs" (ACL 2024, arXiv:2402.11753). Zararlı bir istekteki safety-ilgili token'ları maskele, onları aynı harflerin ASCII-art render'larıyla değiştir ve gizlenmiş prompt'u gönder. GPT-3.5, GPT-4, Gemini, Claude, Llama-2 hepsi ASCII-art token'larını sağlam şekilde tanımakta başarısız oluyor. Saldırı PPL (perplexity filtreleri), Paraphrase savunmaları ve Retokenization'ı bypass eder. İlgili: ViTC benchmark'ı non-semantic visual prompt'ların tanınmasını ölçer; StructuralSleight bir kodlama saldırıları ailesi olarak Uncommon Text-Encoded Structure'lara (ağaçlar, grafikler, nested JSON) genelleştirir.

**Tür:** Yapım
**Diller:** Python (stdlib, ArtPrompt token-maskeleme harness'ı)
**Ön koşullar:** Faz 18 · 12 (PAIR), Faz 18 · 13 (MSJ)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- ArtPrompt saldırısını tarif et: kelime-tanımlama adımı, ASCII-art ikamesi, nihai gizlenmiş prompt.
- Standart savunmaların (PPL, Paraphrase, Retokenization) ArtPrompt üzerinde neden başarısız olduğunu açıkla.
- ViTC'yi tanımla ve neyi ölçtüğünü tarif et.
- StructuralSleight'ı keyfi Uncommon Text-Encoded Structure'lara bir genelleştirme olarak tarif et.

## Sorun

Paraphrase ve roleplay (Ders 12) ile ve uzun context (Ders 13) ile saldırılar text-seviyesi desende çalışır. ArtPrompt tanıma seviyesinde çalışır: model yasak token'ı parse etmez. Karakterlerde render edilmiş bir görüntüyü parse eder. Safety filtresi zararsız noktalama görür. Model bir kelime görür.

## Kavram

### ArtPrompt, iki adım

Adım 1. Word Identification. Bir zararlı istek verildiğinde, saldırgan safety-ilgili kelimeleri (örn. "bir bomba nasıl yapılır"da "bomba") tanımlamak için bir LLM kullanır.

Adım 2. Cloaked Prompt Generation. Tanımlanan her kelimeyi ASCII-art render'ıyla (harfin şeklini oluşturan karakterlerin 7x5 veya 7x7 bloku) değiştir. Model yeterince yetenekli bir modelin kelime olarak tanıyabileceği bir noktalama ve boşluk ızgarası alır; bir safety filtresi yalnızca ızgarayı görür.

Sonuç: GPT-4, Gemini, Claude, Llama-2, GPT-3.5 hepsi başarısız. Benchmark alt kümelerinde %75'in üzerinde attack success rate.

### Standart savunmalar neden başarısız

- **PPL (perplexity filter).** ASCII art yüksek perplexity'ye sahip — ama tüm yeni input da öyle. ArtPrompt'u bloklayan eşik seçimleri meşru yapılandırılmış input'u da bloklar.
- **Paraphrase.** Prompt'u paraphrase etmek ASCII art'ı yok eder. Pratikte, paraphrase LLM'leri sıklıkla art'ı korur veya yeniden inşa eder.
- **Retokenization.** Token'ları farklı şekilde bölmek modelin görüşünün harf şekillerini tanıdığı gerçeğini değiştirmez.

Altta yatan sorun safety filtrelerinin token- veya semantik-seviyede olmasıdır; ArtPrompt visual recognition seviyesinde çalışır.

### ViTC benchmark'ı

Non-semantic visual prompt'ların tanınması. Modelin ASCII-art, wingdings ve diğer non-text-semantik visual içeriği okuma yeteneğini ölçer. ArtPrompt'un etkinliği ViTC doğruluğuyla korele: model visual text'i ne kadar iyi okursa, ArtPrompt onda o kadar iyi çalışır. Bu bir capability-safety trade-off'udur.

### StructuralSleight

ArtPrompt'u genelleştirir: Uncommon Text-Encoded Structures (UTES). Ağaçlar, grafikler, nested JSON, JSON-içinde-CSV, diff-tarzı kod blokları. Bir yapı eğitim safety verisinde nadirse ama model tarafından parse edilebilirse, zararlı içeriği saklayabilir.

Savunma implikasyonu: safety modelin parse edebileceği yapılandırılmış temsiller arasında genelleşmeli. Set büyük ve büyüyor.

### Image-modality analog

Visual LLM'ler (GPT-5.2, Gemini 3 Pro, Claude Opus 4.5, Grok 4.1) saldırı yüzeyini genişletir. Gerçek görüntülerle ArtPrompt-tarzı saldırılar ASCII-art analoglarından daha güçlüdür çünkü image encoder'lar daha zengin sinyal üretir.

### Bu Faz 18'de nereye uyuyor

Dersler 12-14 üç ortogonal saldırı vektörünü tarif eder: iteratif refinement (PAIR), context uzunluğu (MSJ) ve kodlama (ArtPrompt/StructuralSleight). Ders 15 model-merkezli saldırılardan sistem-sınırı saldırılarına (indirect prompt injection) kayar. Ders 16 defansif araç tepkisini tarif eder.

## Kullan

`code/main.py` bir oyuncak ArtPrompt inşa eder. Bir zararlı sorgudaki spesifik kelimeleri ASCII-art glyph'lerle gizleyebilir, gizlenmiş string'in bir keyword filtresinden geçtiğini doğrulayabilir ve (opsiyonel olarak) gizlenmiş string'i basit bir tanıyıcı kullanarak geri decode edebilirsin.

## Yayınla

Bu ders `outputs/skill-encoding-audit.md` üretir. Bir jailbreak-savunma raporu verildiğinde, kapsanan kodlama saldırı ailelerini (ASCII art, base64, leet-speak, UTF-8 homoglyph, UTES) ve her birini yakalayan savunma katmanını sayar.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Gizlenmiş string'in basit bir keyword filtresinden geçtiğini doğrula. Gerekli karakter-seviyesi değişikliği raporla.

2. İkinci bir kodlama uygula: aynı hedef kelime için base64. Filtre-bypass oranını ArtPrompt'a karşı ve kurtarma zorluğunu karşılaştır.

3. Jiang vd. 2024 Bölüm 4.3'ü (beş-model sonuçları) oku. Aynı benchmark'ta Claude'un ArtPrompt-direncinin Gemini'ninkinden neden daha yüksek olduğu için bir sebep öner.

4. Prompt'ta ASCII-art-şekilli bölgeleri tespit eden bir pre-generation savunması tasarla. Meşru kod, tablolar ve matematiksel notasyon üzerinde false-positive oranını ölç.

5. StructuralSleight 10 kodlama yapısı listeler. 10'unu da işleyen genelleştirilmiş bir savunma çiz ve savunulan prompt başına compute maliyetini tahmin et.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| ArtPrompt | "ASCII-art saldırısı" | Safety kelimelerini ASCII-art render'larıyla maskeleyerek iki adımlı jailbreak |
| Cloaking | "kelimeyi sakla" | Yasak bir token'ı modelin okuduğu ama filtrenin okumadığı görsel bir temsille değiştir |
| UTES | "nadir yapı" | Uncommon Text-Encoded Structure — ağaç, grafik, nested JSON, vb. içerik kaçırmak için kullanılır |
| ViTC | "visual-text yeteneği" | Modelin non-semantic visual kodlamayı okuma yeteneği için benchmark |
| Perplexity filter | "PPL savunması" | Yüksek perplexity'li prompt'ları reddet; meşru yapılandırılmış input da yüksek puan aldığı için başarısız |
| Retokenization | "tokenizer shift savunması" | Prompt'u farklı bir tokenizer ile pre-process et; tanıma visual olduğu için başarısız |
| Homoglyph | "benzer karakterler" | Latin harflerine özdeş görünen Unicode karakterler; substring kontrollerini bypass eder |

## İleri Okuma

- [Jiang et al. — ArtPrompt (ACL 2024, arXiv:2402.11753)](https://arxiv.org/abs/2402.11753) — ASCII-art jailbreak makalesi
- [Li et al. — StructuralSleight (arXiv:2406.08754)](https://arxiv.org/abs/2406.08754) — UTES genelleştirmesi
- [Chao et al. — PAIR (Ders 12, arXiv:2310.08419)](https://arxiv.org/abs/2310.08419) — tamamlayıcı iteratif saldırı
- [Anil et al. — Many-shot Jailbreaking (Ders 13)](https://www.anthropic.com/research/many-shot-jailbreaking) — tamamlayıcı uzunluk saldırısı
