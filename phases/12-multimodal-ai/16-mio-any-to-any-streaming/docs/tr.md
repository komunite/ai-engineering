# MIO ve Any-to-Any Streaming Multimodal Modeller

> GPT-4o açık modellerin çoğunun çoğaltamayacağı bir ürün gönderiyor: gerçek zamanlı sesi duyan, videoyu gören ve geri konuşan bir agent. 2024 sonlarında açık-ekosistem cevabı MIO (Wang et al., Eylül 2024) idi. MIO metin, görsel, konuşma ve müziği tokenize eder, interleaved diziler üzerinde tek causal transformer eğitir ve herhangi modaliteden herhangi modaliteye üretir. AnyGPT (Zhan et al., Şubat 2024) kavram kanıtıydı; MIO ölçek-büyütmesi; Unified-IO 2 (Allen AI, Aralık 2023) vision + action grounding ile kuzeni. Bu ders any-to-any kalıbını okur — dört tokenizer, tek transformer, streaming-dostu decode.

**Tür:** Öğrenim
**Diller:** Python (stdlib, dört-modalite token allocator + streaming decode döngüsü)
**Ön koşullar:** Faz 12 · 11 (Chameleon), Faz 6 (Konuşma ve Ses)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- Çarpışma olmadan metin, görsel, konuşma ve müzik token'larını barındıran paylaşılan bir sözcük tasarla.
- SEED-Tokenizer'ı (görseller) ve SpeechTokenizer residual-VQ'yu (konuşma) sıkıştırma + yeniden inşa trade-off'larında karşılaştır.
- Any-to-any üretimi inşa eden dört aşamalı müfredatı açıkla.
- Üç açık any-to-any tarifini ve ana trade-off'larını söyle: MIO, AnyGPT, Unified-IO 2.

## Sorun

Birleştirilmiş bir multimodal model iddia etmesi kolay, ölçekte inşa etmesi zor. 2024'e kadar çoğu "any-to-any" sistem pipeline'lıydı: vision modeli → metin temsili → konuşma modeli → ses. Her hop bilgi kaybeder, latency ekler ve eğitimi karmaşıklaştırır. GPT-4o'nun demo videosu saniye-altı yanıtla tek-model alternatifi gösterdi; açık sistemler aylarca geride kaldı.

Mühendislik zorlukları:

- Her modalite için tokenizer'lar var olmalı, yeniden inşa için yeterince kayıpsız sıkıştırmalı ve token'ları transformer'ın tüketebileceği hızda üretmeli.
- Tek bir sözcük metin (32k+), görsel (16k+), konuşma (4k+), müzik (8k+) için uzay tahsis etmeli. Kırk-bin-artı giriş minimum.
- Eğitim verisi her input-output çiftini (metin→görsel, görsel→konuşma, konuşma→görsel, vs.) kapsamalı ya da model compose etmeli.
- Çıkarım output token'larını conversational latency için yeterince hızlı stream etmeli (<500ms time-to-first-audio-byte).

## Kavram

### Dört modalite için dört tokenizer

MIO'nun tokenizer yığını:

- Metin: standart BPE, vocab ~32000.
- Görsel: SEED-Tokenizer (2023) — ayrık codebook ile kuantize edilmiş VAE, 4096 giriş, görsel başına 32x32 token.
- Konuşma: SpeechTokenizer residual-VQ (2023) — 16kHz waveform'u 8 hiyerarşik codebook'a kodlar; ilk seviye kaba içerik, sonraki seviyeler prosody ve speaker identity ekler.
- Müzik: benzer residual-VQ (Meta'nın MusicGen / Encodec ailesi), 4-8 codebook.

Her modalite integer token üretir. Token'lar paylaşılan sözcükte ayrık ID aralıkları alır:

```
text:   0..31999
image:  32000..36095  (4096 image token)
speech: 36096..40191  (4096 speech base token, artı residual katmanlar)
music:  40192..48383  (8192 music token)
sep:    48384..48390  (<image>, <speech>, <music>, </...>, vs.)
```

Toplam: ~48k sözcük. Input embedding ve output projeksiyonu hepsini kapsar.

### Streaming decode

Konuşma üretimi residual-VQ kullanır. Transformer base (katman 0) konuşma token'larını tahmin eder; paralel-decoded residual quantizer sonraki katmanları tahmin eder. Her katman 0 token'ı 16kHz'de kabaca 50ms ses.

Streaming kalıbı:

1. User mikrofona konuşur; gerçek zamanlı ses tokenizer her 50ms bir konuşma token'ı yayar.
2. MIO geldikçe token'ları tüketir (prompt prefill + artımlı forward).
3. Output token'lar üretildikçe stream eder; paralel konuşma decoder onları ~50-150ms latency ile ses örneklerine dönüştürür.
4. Time-to-first-audio-byte: MIO makalesinde ~300-500ms, GPT-4o'nun ~250ms'sine yaklaşıyor.

Mini-Omni (arXiv:2408.16725), GLM-4-Voice (arXiv:2412.02612) ve Moshi (arXiv:2410.00037) tamamlayıcı streaming konuşma-LLM tasarımları. Özellikle Moshi tek GPU'da 160ms gidiş-dönüş elde ediyor.

### Dört aşamalı müfredat

MIO'nun eğitim müfredatı:

1. Aşama 1 — hizalama. Büyük ölçekli modalite-çift corpus'ları: text-image, text-speech, text-music. Her çift kendi token sözcüğü segmentini kullanır. Paylaşılan sözcüğü eğitir.
2. Aşama 2 — interleaved. Çok modaliteli interleaved belgeler (görseller + video ile bloglar, transcript'li podcast'ler, vb.). Cross-modality context'i eğitir.
3. Aşama 3 — konuşma-iyileştirilmiş. Metin yeteneğini kaybetmeden konuşma kalitesini yükseltmek için ekstra ses verisi.
4. Aşama 4 — SFT. Modaliteler arası instruction tuning: VQA, captioning, narration, konuşma-konuşma diyalog.

Bir aşamayı kaçırmak belirli yetenekleri bozar: aşama 2'yi atla ve model cross-modality context'i kaybeder; aşama 3'ü atla ve konuşma zayıf olur.

### Chain-of-visual-thought

MIO chain-of-visual-thought'u tanıtıyor: model ara görsel token'ları akıl yürütme adımı olarak yayar. "Kedi ağaca tırmanıyor mu?" için model:

1. Sahneyi render eden `<image>` token'ları yayar (input görselden ya da bir skeçten).
2. Skeçi analiz eden metin yayar.
3. Son cevabı yayar.

Render edilen ara görsel scratchpad gibi çalışır. Spatial-akıl yürütme görevlerinde benchmark'lar iyileşir. Fikir metin akıl yürütmesi için chain-of-thought'u yansıtıyor.

### Any-to-any rakipler

- AnyGPT (arXiv:2402.12226): 4 modalite (metin, görsel, konuşma, müzik), benzer tasarım.
- Unified-IO 2 (arXiv:2312.17172): vision action çıkışları, derinlik, normaller ekler. Daha çok görev çeşitliliği, daha küçük ölçek.
- NExT-GPT (arXiv:2309.05519): LLM + modalite-spesifik diffusion decoder'ları. Tek-model yaklaşımı değil.
- CoDi (arXiv:2305.11846): composable diffusion; paylaşılan latent üzerinden any-to-any.

MIO saf-token any-to-any'ye en yakın. AnyGPT kavramsal atası.

### Latency bütçesi

Conversational ürün için her bileşenin latency'si önemli:

- Mikrofon → ses token: ~50ms.
- Prefill (ses token'ları + geçmiş): 8B modelde ~100ms.
- İlk output token: ~50ms.
- Paralel residual-VQ + konuşma decoder: ~100-150ms.

Toplam time-to-first-audio-byte: ~300ms minimum. GPT-4o ~250ms iddia ediyor. Moshi 160ms. MIO/AnyGPT kamuya açık benchmark'lara göre 400-600ms aralığında.

### Any-to-any neden zor kalmaya devam ediyor

2026'da bile açık any-to-any modeller kapalı olanların iki eksende gerisinde:

- Konuşma kalitesi. Residual-VQ tokenizer kayıplı; conversational konuşma ElevenLabs sınıfı seslere kıyasla robotik geliyor.
- Cross-modality akıl yürütme. Modele "gördüğün hakkında şarkı söyle" sormak hâlâ saf-görü görevlerden daha sık başarısız.

Bunlar açık araştırma problemleri. Qwen3-Omni (Ders 12.20) 2025'te en gelişmiş açık deneme.

## Kullan

`code/main.py`:

- Dört-modalite sözcük tahsisini tanımlar ve yazdırır.
- Multimodal input listesini (metin, görsel, ses klibi, müzik) tokenizer router üzerinden yönlendirir.
- Latency sayımı ile text-to-speech yanıtı için streaming decode'u simüle eder.
- Encoder, prefill ve decoder latency'leri verildiğinde beklenen time-to-first-audio-byte'ı hesaplar.

## Yayınla

Bu ders `outputs/skill-any-to-any-pipeline-auditor.md` üretir. Conversational ürün spec'i (modaliteler girer, modaliteler çıkar, latency hedefi) verildiğinde, MIO-family tasarım seçimlerini denetler ve latency bütçesini hesaplar.

## Alıştırmalar

1. Ürünün konuşma input alıyor ve konuşma output döndürüyor. Uçtan uca latency bütçe hedefi nedir? Zaman harcayan bileşenleri listele.

2. SpeechTokenizer residual-VQ 8 codebook kullanır. Residual seviyeleri paralel-decode etmenin neden gerekli olduğunu (sequential vs) ve hangi latency tasarrufu getirdiğini öner.

3. Sözcüğün 32k metin + 4k görsel + 4k konuşma var. 8k müzik ve ~10 ayırıcı ekle. Hidden dim 4096'da embedding-matris parametre maliyeti nedir?

4. Chain-of-visual-thought ara bir görsel yayar. Hangi tür sorular fayda görür? Hangi türler ekstra token'larla zarar görür?

5. Moshi'yi (arXiv:2410.00037) oku. "Inner monologue" tekniğini betimle ve MIO'nun chain-of-visual-thought ile karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Any-to-any | "Multimodal girer/çıkar" | Metin, görsel, konuşma ve müziği herhangi yönde kabul eden ve yayan tek model |
| Residual-VQ | "Konuşma tokenizer yığını" | Her katmanın bilgi eklediği çoklu codebook tokenization'ı; base katman içerik, sonraki katmanlar prosody |
| SEED-Tokenizer | "Görsel kodları" | MIO tarafından kullanılan 4096-girişli codebook'lu ayrık görsel tokenizer'ı |
| Chain-of-visual-thought | "Görsel scratchpad" | Model son cevabından önce akıl yürütme adımı olarak ara görsel üretir |
| Time-to-first-audio-byte | "TTFAB" | User sesinden ilk ses çıktısına latency; conversational his için <500ms |
| Dört aşamalı müfredat | "Eğitim tarifi" | Hizalama -> interleaved -> konuşma-iyileştirilmiş -> SFT, bu sırayla |

## İleri Okuma

- [Wang et al. — MIO (arXiv:2409.17692)](https://arxiv.org/abs/2409.17692)
- [Zhan et al. — AnyGPT (arXiv:2402.12226)](https://arxiv.org/abs/2402.12226)
- [Lu et al. — Unified-IO 2 (arXiv:2312.17172)](https://arxiv.org/abs/2312.17172)
- [Wu et al. — NExT-GPT (arXiv:2309.05519)](https://arxiv.org/abs/2309.05519)
- [Tang et al. — CoDi (arXiv:2305.11846)](https://arxiv.org/abs/2305.11846)
