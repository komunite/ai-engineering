# CLIP'ten BLIP-2'ye — Modalite Köprüsü Olarak Q-Former

> CLIP görsel ve metni hizalar ama caption üretemez, soru cevaplayamaz ya da konuşma sürdüremez. BLIP-2 (Salesforce, 2023) bunu küçük bir eğitilebilir köprü ile çözdü: 32 öğrenilebilir query vektörü cross-attention ile donmuş bir ViT'in feature'larına attend eder, sonra doğrudan donmuş bir LLM'in input akışına oturur. Bir 11B LLM'i bir ViT-g/14'e bağlayan 188M parametrelik köprü. 2026'ya kadar her adapter tabanlı VLM — MiniGPT-4, InstructBLIP, LLaVA'nın kuzenleri — bir descendant. Bu ders Q-Former'ın mimarisini okuyor, iki aşamalı eğitimini açıklıyor ve donmuş bir text decoder'a görsel token'lar besleyen oyuncak bir versiyonu inşa ediyor.

**Tür:** Yapım
**Diller:** Python (stdlib, cross-attention + öğrenilebilir-query demosu)
**Ön koşullar:** Faz 12 · 02 (CLIP), Faz 7 (Transformer'lar)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Donmuş bir vision encoder ile donmuş LLM arasındaki eğitilebilir bottleneck'in maliyet ve kararlılıkta uçtan uca fine-tuning'i neden yendiğini açıkla.
- Sabit bir öğrenilebilir query setinin dış görsel feature'lara attend ettiği bir cross-attention block uygula.
- BLIP-2'nin iki aşamalı pretraining'inden geç: representation (ITC + ITM + ITG) sonra generative (donmuş decoder ile LM loss).
- Q-Former'ı LLaVA'da kullanılan daha basit MLP projector ile karşılaştır ve her seçimin ne zaman kazandığını savun.

## Sorun

Görsel başına 1408 boyutlu 256 patch token üreten donmuş bir ViT'in var. 4096 boyutlu token embedding bekleyen donmuş bir 7B LLM'in var. Aşikar köprü — 1408'den 4096'ya bir lineer katman — çalışır, ama tüm 256 patch token'ı LLM'in context'ine beslemek görsel başına 256 ekstra token'a mal olur. 32 görsellik bir batch boyunca bu yalnızca görsel modalitesi tarafından tüketilen 8192 token.

BLIP-2 sorusu: 256-token görsel temsilini çok daha az token'a (mesela 32) sıkıştırabilir misin, LLM'in görsel hakkında caption yazması, soru cevaplaması ve akıl yürütmesi için yeterli bilgiyi korurken? Ve bu köprüyü donmuş backbone'lara dokunmadan eğitebilir misin, eğitim maliyetini sadece köprünün parametrelerine tutarak?

Cevap: bir Q-Former. ViT'in patch token'larına cross-attend eden 32 öğrenilebilir "query" vektörü, LLM'in tükettiği 32-token görsel özet üretir. Toplam 188M parametre. LLM'e hiç dokunmadan önce contrastive, matching ve generative objective'ler ile eğitildi.

## Kavram

### Öğrenilebilir query'ler

Q-Former'ın çekirdek hilesi: LLM'in metin token'larının görsel patch'lere attend etmesine izin vermek yerine, 32 öğrenilebilir query vektörünün `Q` yeni setini tanıt ve *onların* görsel patch'lere attend etmesine izin ver. Query'ler modelin parametreleri — eğitim sırasında öğrenilir ve aynı 32 query her görsel için kullanılır.

Cross-attention sonrası her query görselin sıkıştırılmış bir özetini tutar — "ana nesneyi betimle", "arka planı betimle", "nesneleri say", vb. Query'ler tam anlamıyla semantik etiketlerde uzmanlaşmaz; aşağı akış loss'larının düşmesini sağlayan ne kodlamayı öğrenirler.

### Mimari

Q-Former iki yollu küçük bir transformer (12 katman, ~100M param):

1. Query yolu: 32 query vektörü self-attention'dan (kendi aralarında), sonra donmuş ViT'in patch token'ları üzerinde cross-attention'dan, sonra FFN'den akar.
2. Text yolu: BERT benzeri text encoder self-attention ve FFN ağırlıklarını query yolu ile paylaşır. Text yolu için cross-attention devre dışı.

Eğitim zamanında her iki yol da çalışır. Query'ler ve metin paylaşılan self-attention üzerinden etkileşir, bu da query'lerin onu gerektiren görevler için metne koşullanabileceği anlamına gelir (ITM, ITG). Çıkarım zamanında VLM handoff için yalnızca query'ler akar, 32 görsel token üretir.

### İki aşamalı eğitim

BLIP-2 iki aşamada pretrain eder:

Aşama 1: representation learning (LLM yok). Üç loss:
- ITC (image-text contrastive): pooled query token'ları ile text CLS token'ı arasında CLIP tarzı contrastive.
- ITM (image-text matching): ikili sınıflandırıcı — bu image-text çifti eşleşme mi? Hard-negative mined.
- ITG (image-grounded text generation): metin üzerinde causal LM head, query'lere koşullu. Query'leri metin üretilebilir içerik kodlamaya zorlar.

Yalnızca Q-Former eğitilir. ViT donmuş. LLM dahil değil.

Aşama 2: generative learning. Donmuş bir LLM tak (OPT-2.7B ya da Flan-T5-XL, vb.). 32 query çıktısını küçük bir lineer katman ile LLM'in embedding dim'ine projekte et. Metin prompt'una baştan ekle. Birleştirilmiş prompt + görsel + caption dizisi üzerinde LM loss ile yalnızca lineer projeksiyonu ve Q-Former'ı eğit.

Aşama 2 sonrası, Q-Former + projeksiyon tam görsel adapter. Çıkarımda: görsel → ViT → Q-Former → linear proj → metine baştan eklenir → donmuş LLM çıktı yayar.

### Parametre ekonomisi

ViT-g/14 (1.1B, donmuş) + OPT-6.7B (6.7B, donmuş) + Q-Former (188M, eğitilmiş) ile BLIP-2 = toplam 8B, 188M eğitilmiş. Yalnız Q-Former tüm yığının parametrelerinin ~%2.4'ü. Eğitim maliyeti bunu yansıtır: bir avuç A100'de günler, uçtan uca için haftalar yerine.

Kalite: BLIP-2 zero-shot VQA'da Flamingo-80B'yi eşler ya da yener, 50 kat daha küçükken. Köprü çalışıyor.

### InstructBLIP ve instruction-aware Q-Former

InstructBLIP (2023), Q-Former'ı ekstra bir input ile genişletir: instruction text'in kendisi. Cross-attention zamanında query'ler artık hem görsel patch'lere hem instruction'a erişebilir. Query'ler tek sabit özet öğrenmek yerine instruction başına ("arabaları say", "ruhu betimle") uzmanlaşabilir. Held-out görevlerde benchmark kazanımları.

### MiniGPT-4 ve projector-only yaklaşım

MiniGPT-4 Q-Former'ı tuttu ama her şeyi donmuş bırakırken yalnızca çıkış lineer projeksiyonunu eğitti. Ucuz, ama maliyeti kalite — query'ler BLIP-2'nindi, seninkiler değil. Hızlı iterasyon için iyi, en iyi mimari değil.

### LLaVA neden daha basite gitti

LLaVA (2023, Ders 12.05) Q-Former'ı 24x24 grid için her ViT patch token'ını LLM uzayına projekte eden düz bir 2 katmanlı MLP ile değiştirdi — görsel başına 576 token, hepsi LLM'e beslenir. Daha kötü sıkıştırma ama LLM'in ham patch'ler üzerinde attend etmesine izin verir. O zamanlar bu tartışmalıydı; 2023'ün sonlarında baskındı çünkü görsel instruction verisi (LLaVA-Instruct-150k) MLP'nin yeterli sinyali korumak üzere eğitilebileceğini kanıtladı. Trade-off: LLaVA'nın context'i daha hızlı dolar, ama doğal olarak çok-görsel ve videoya ölçeklenir.

2026'ya gelindiğinde alan bölündü: Q-Former token bütçesi önemli olduğu yerde (uzun video, çok görsel) hayatta kalır; MLP projector token başına ham kalitenin öncelik olduğu yerde baskın.

### Gated cross-attention: Flamingo, ata

Flamingo (Ders 12.04) BLIP-2'den önce geldi ve aynı cross-attention fikrini kullandı ama tek bir köprü olarak değil, her donmuş LLM katmanında. BLIP-2 yalnızca input katmana sıkıştırmanın hâlâ çalıştığını gösterdi. Gemini ve Idefics ikisini birleştirir: interleaved input token'ları artı in-context few-shot için opsiyonel gated cross-attention.

### 2026 descendant'ları

- Q-Former: token bütçesi nedeniyle BLIP-2, InstructBLIP, MiniGPT-4 ve çoğu video-language modeli.
- Perceiver resampler: Flamingo'nun varyantı (Ders 12.04); Idefics ailesi, Eagle, OmniMAE.
- MLP projector: LLaVA, LLaVA-NeXT, LLaVA-OneVision, Cambrian-1.
- Attention pool: VILA, PaliGemma.

Dördü de geçerli. Karar verdirici soru token bütçesi mi yoksa token başına kalite üzerinde mi kısıtlı olduğun.

## Kullan

`code/main.py` stdlib bir Q-Former tarzı cross-attention inşa eder:

1. 256 görsel patch token'ı (dim 128) simüle et.
2. 32 öğrenilebilir query (dim 128) instantiate et.
3. Scaled-dot-product cross-attention çalıştır (query'lerden Q, patch'lerden K/V).
4. Bir lineer katman ile LLM-dim'e (512) projekte et.
5. 32 LLM-ready görsel token çıktıla.

Tüm matematik saf Python'da (vektörler üzerinde iç içe döngüler). Oyuncak ama doğru shape. Attention-weight matrisi yazdırılır, böylece her query'nin hangi patch'lerden çektiğini görebilirsin.

## Yayınla

Bu ders `outputs/skill-modality-bridge-picker.md` üretir. Hedef VLM konfigürasyonu (vision encoder token sayısı, LLM context bütçesi, deployment kısıtları, kalite hedefi) verildiğinde, her köprü için kısa bir gerekçe ve parametre sayısı tahmini ile Q-Former vs MLP vs Perceiver resampler önerir.

## Alıştırmalar

1. PyTorch'ta cross-attention block'unu uygula. 32 query ve 256 key/value ile attention-weight matrisinin 32 x 256 olduğunu ve her satırın softmax sonrası 1'e toplandığını doğrula.

2. BLIP-2 aşama 1'de Q-Former eş zamanlı üç loss çalıştırır: ITC, ITM, ITG. Her birinin forward imzasını sahte-kodla yaz. Hangisi text encoder yolunun aktif olmasını gerektiriyor?

3. Parametre sayılarını karşılaştır: Q-Former (12 katman, 768 hidden) vs 2 katmanlı MLP projector (1408 → 4096, iki katman). Hangi LLM ölçeğinde 188M Q-Former maliyeti eğitim verimliliği olarak geri öder?

4. BLIP-2 makalesinin (arXiv:2301.12597) Q-Former'ın nasıl initialize edildiğine dair Bölüm 3.2'sini oku. BERT-base'den initialize etmenin (random değil) yakınsamayı neden hızlandırdığını açıkla.

5. 60 frame'e örneklenmiş 10 dakikalık 1 FPS bir video için (Q-Former → frame başına 32 token) vs (MLP projector → frame başına 576 token) frame başına token maliyetini hesapla. Hangisi 128k-token LLM context penceresine sığar?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Q-Former | "Querying transformer" | Donmuş ViT feature'larına cross-attend eden 32 öğrenilebilir query vektörlü küçük transformer |
| Öğrenilebilir query'ler | "Görü için soft prompt" | Cross-attention'ın query tarafı olarak hizmet eden sabit parametre seti; model başına öğrenilir, tüm input'lar arasında paylaşılır |
| Cross-attention | "Q buradan, K/V şuradan" | Query, key ve value'nun farklı kaynaklardan geldiği attention; query'lerin ViT patch'lerinden nasıl çektiği |
| ITC | "Image-text contrastive" | Q-Former pooled query'leri vs text CLS'e uygulanan CLIP tarzı loss |
| ITM | "Image-text matching" | Hard-negative mined çiftler üzerinde ikili sınıflandırıcı; query'leri ince taneli uyumsuzlukları ayırmaya zorlar |
| ITG | "Image-grounded text generation" | Metnin query'lere koşullu üretildiği causal LM loss; query'leri metin-decode edilebilir içerik kodlamaya zorlar |
| İki aşamalı pretraining | "Representation sonra generative" | Aşama 1 Q-Former'ı tek başına eğitir (ITC/ITM/ITG); Aşama 2 donmuş LLM takar ve yalnızca projeksiyon + Q-Former eğitir |
| Donmuş backbone | "Fine-tune etme" | Vision encoder ve LLM ağırlıkları sabit; yalnızca köprü eğitilir |
| Projection head | "LLM dim'e lineer" | Q-Former çıktısını LLM'in embedding boyutuna eşleyen son lineer katman |
| Perceiver resampler | "Flamingo'nun versiyonu" | Benzer öğrenilebilir-query cross-attention, Flamingo tarafından tek köprü yerine her katmanda kullanılır |

## İleri Okuma

- [Li et al. — BLIP-2 (arXiv:2301.12597)](https://arxiv.org/abs/2301.12597) — çekirdek makale.
- [Li et al. — BLIP (arXiv:2201.12086)](https://arxiv.org/abs/2201.12086) — ITC/ITM/ITG üçlüsü ile selefi.
- [Li et al. — ALBEF (arXiv:2107.07651)](https://arxiv.org/abs/2107.07651) — "align before fuse" — aşama 1 eğitiminin kavramsal atası.
- [Dai et al. — InstructBLIP (arXiv:2305.06500)](https://arxiv.org/abs/2305.06500) — instruction-aware Q-Former.
- [Zhu et al. — MiniGPT-4 (arXiv:2304.10592)](https://arxiv.org/abs/2304.10592) — projector-only yaklaşım.
- [Jaegle et al. — Perceiver IO (arXiv:2107.14795)](https://arxiv.org/abs/2107.14795) — öğrenilebilir-query cross-attention için genel mimari.
