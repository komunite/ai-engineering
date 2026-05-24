# T5, BART — Encoder-Decoder Modeller

> Encoder'lar anlar. Decoder'lar üretir. Onları bir araya geri getir ve input → output görevleri için tasarlanmış bir model elde edersin: çevir, özetle, yeniden yaz, transkribe et.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 7 · 05 (Tam Transformer), Faz 7 · 06 (BERT), Faz 7 · 07 (GPT)
**Süre:** ~45 dakika

## Sorun

Decoder-only GPT ve encoder-only BERT, 2017 mimarisini farklı hedefler için ayrı ayrı kırpar. Ama birçok görev doğal olarak input-output'tur:

- Çeviri: İngilizce → Fransızca.
- Özetleme: 5.000 token'lık makale → 200 token'lık özet.
- Konuşma tanıma: ses token'ları → metin token'ları.
- Yapılandırılmış extraction: prose → JSON.

Bunlar için, encoder-decoder en temiz uyumdur. Encoder kaynağın yoğun bir temsilini üretir. Decoder çıktıyı üretir, her adımda o temsile cross-attention yapar. Eğitim çıktı tarafında bir kaydırarak'tır. GPT ile aynı loss, sadece encoder çıktısına koşullandırılmış.

İki makale modern playbook'u tanımladı:

1. **T5** (Raffel et al. 2019). "Text-to-Text Transfer Transformer." Her NLP görevi metin-girdi, metin-çıktı olarak yeniden çerçevelendi. Tek mimari, tek vocabulary, tek loss. Mask'lenmiş span tahmininde pretrain edildi (input'taki span'ları boz, output'ta decode et).
2. **BART** (Lewis et al. 2019). "Bidirectional and Auto-Regressive Transformer." Denoising autoencoder: input'u birden fazla şekilde boz (karıştır, mask'le, sil, döndür), decoder'dan orijinali yeniden inşa etmesini iste.

2026'da encoder-decoder formatı input yapısının önemli olduğu yerlerde yaşıyor:

- Whisper (konuşma → metin).
- Google'ın çeviri yığını.
- Belirgin context-and-edit yapıları olan bazı kod-tamamlama / onarım modelleri.
- Yapılandırılmış akıl yürütme görevleri için Flan-T5 ve varyantları.

Decoder-only ışıkları çaldı, ama encoder-decoder hiç gitmedi.

## Kavram

![Cross-attention'lı encoder-decoder](../assets/encoder-decoder.svg)

### Forward döngüsü

```
kaynak token'ları ─▶ encoder ─▶ (N_src, d_model)  ──┐
                                                     │
hedef token'ları ─▶ decoder bloğu                    │
                 ├─▶ mask'lenmiş self-attention      │
                 ├─▶ cross-attention ◀───────────────┘
                 └─▶ FFN
                ↓
              sonraki-token logit'leri
```

Kritik şey, encoder input başına bir kere çalışır. Decoder autoregressive çalışır ama her adımda *aynı* encoder çıktısına cross-attention yapar. Encoder çıktısını cache'lemek uzun input'lar için bedava bir hızlanmadır.

### T5 pretraining — span corruption

Input'un rastgele span'larını seç (ortalama uzunluk 3 token, toplam %15). Her span'ı benzersiz bir sentinel ile değiştir: `<extra_id_0>`, `<extra_id_1>`, vs. Decoder yalnızca bozulmuş span'ları sentinel önekleriyle çıktılar:

```
kaynak: The quick <extra_id_0> fox jumps <extra_id_1> dog
hedef: <extra_id_0> brown <extra_id_1> over the lazy
```

Tüm diziyi tahmin etmekten daha ucuz sinyal. T5 makalesinin ablation'ında MLM (BERT) ve prefix-LM (UniLM) ile rekabetçi.

### BART pretraining — multi-noise denoising

BART beş gürültü fonksiyonu dener:

1. Token masking.
2. Token deletion.
3. Text infilling (bir span'ı mask'le, decoder doğru uzunluğu ekler).
4. Sentence permutation.
5. Document rotation.

Text infilling + sentence permutation kombinasyonu en iyi downstream sayıları üretti. Decoder her zaman orijinali yeniden inşa eder. BART'ın çıktısı tam dizidir, yalnız bozulmuş span'lar değil — bu yüzden pretraining compute'u T5'ten daha yüksektir.

### Çıkarım

GPT ile aynı autoregressive üretim. Greedy / beam / top-p örnekleme uygulanır. Beam search (genişlik 4–5) çeviri ve özetleme için standarttır çünkü çıktı dağılımı sohbete göre daha dardır.

### 2026'da her varyantı ne zaman seçmeli

| Görev | Encoder-decoder? | Neden |
|------|------------------|-----|
| Çeviri | Evet, genelde | Net kaynak dizi; sabit çıktı dağılımı; beam search çalışır |
| Speech-to-text | Evet (Whisper) | Input modalitesi çıktıdan farklı; encoder ses özelliklerini şekillendirir |
| Sohbet / akıl yürütme | Hayır, decoder-only | Kalıcı bir "input" yok — konuşma dizidir |
| Kod tamamlama | Genelde hayır | Uzun context'li decoder-only kazanır; Qwen 2.5 Coder gibi kod modelleri decoder-only |
| Özetleme | İkisi de çalışır | BART, PEGASUS önceki decoder-only baseline'ları yendi; modern decoder-only LLM'ler onları eşleştirir |
| Yapılandırılmış extraction | İkisi de | T5 temizdir çünkü "text → text" herhangi bir çıktı formatını emer |

~2022'den beri trend: decoder-only, encoder-decoder'ın sahip olduğu görevleri ele geçiriyor çünkü (a) instruction-tuned decoder-only LLM'ler prompting üzerinden her şeye genelleşir, (b) tek mimari iki mimariden daha kolay ölçeklenir, (c) RLHF bir decoder varsayar. Encoder-decoder, input modalitesinin farklı olduğu (konuşma, görüntü) veya beam search kalitesinin önemli olduğu yerlerde tutunuyor.

## İnşa Et

`code/main.py`'a bak. Oyuncak bir corpus için T5 tarzı span corruption implement ediyoruz — bu dersin en faydalı tek parçası çünkü o zamandan beri her encoder-decoder pretraining tarifinde görünüyor.

### Adım 1: span corruption

```python
def corrupt_spans(tokens, mask_rate=0.15, mean_span=3.0, rng=None):
    """Toplamı ~mask_rate token olan span'lar seç. (corrupted_input, target) döndür."""
    n = len(tokens)
    n_mask = max(1, int(n * mask_rate))
    n_spans = max(1, int(round(n_mask / mean_span)))
    ...
```

Hedef formatı T5 konvansiyonudur: `<sent0> span0 <sent1> span1 ...`. Bozulmuş input span konumlarında değişmemiş token'ları sentinel token'larla iç içe geçirir.

### Adım 2: round-trip doğrula

Bozulmuş input ve hedef verildiğinde, orijinal cümleyi yeniden inşa et. Bozman tersine çevrilebilirse, forward pass iyi tanımlıdır. Bu bir sağlık kontrolüdür — gerçek eğitim asla bunu yapmaz, ama test ucuzdur ve span muhasebende off-by-one bug'ları yakalar.

### Adım 3: BART gürültülemesi

Beş fonksiyon: `token_mask`, `token_delete`, `text_infill`, `sentence_permute`, `document_rotate`. İkisini kompoze et ve sonucu göster.

## Kullan

HuggingFace referansı:

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer
tok = T5Tokenizer.from_pretrained("google/flan-t5-base")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")

inputs = tok("translate English to French: Attention is all you need.", return_tensors="pt")
out = model.generate(**inputs, max_new_tokens=32)
print(tok.decode(out[0], skip_special_tokens=True))
```

T5 numarası: görev adı input metnine gider. Aynı model onlarca görevi ele alır çünkü her görev metin-girdi, metin-çıktıdır. 2026'da bu pattern instruction-tuned decoder-only modeller tarafından genelleştirildi, ama T5 bunu önce kodlaştırdı.

## Yayınla

`outputs/skill-seq2seq-picker.md`'ye bak. Skill, input-output yapısı, latency ve kalite hedefleri verilen yeni bir görev için encoder-decoder ile decoder-only arasında seçim yapar.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır, 30 token'lık bir cümleye span corruption uygula, sentinel olmayan kaynak token'larını decode edilmiş hedef span'larla birleştirmenin orijinali yeniden ürettiğini doğrula.
2. **Orta.** BART'ın `text_infill` gürültüsünü implement et: rastgele span'ları tek bir `<mask>` token ile değiştir, decoder doğru span uzunluğunu artı içeriği çıkarmalı. Bir örnek göster.
3. **Zor.** Küçük bir İngilizce → pig-Latin corpus'unda (200 çift) `flan-t5-small`'u fine-tune et. Tutulan 50 çiftlik bir sette BLEU ölç. Aynı veriyle aynı compute'ta `Llama-3.2-1B`'i fine-tune etmeyle karşılaştır.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Encoder-decoder | "Seq2seq transformer" | İki yığın: input için çift yönlü encoder, çıktı için cross-attention'lı causal decoder. |
| Cross-attention | "Kaynağın hedefle konuştuğu yer" | Decoder'ın Q × encoder'ın K/V'si. Encoder bilgisinin decoder'a girdiği tek yer. |
| Span corruption | "T5'in pretraining numarası" | Rastgele span'ları sentinel token'larla değiştir; decoder span'ları çıktılar. |
| Denoising objective | "BART'ın oyunu" | Input'a bir gürültü fonksiyonu uygula, decoder'ı temiz diziyi yeniden inşa etmeye eğit. |
| Sentinel token | "`<extra_id_N>` placeholder" | Kaynaktaki bozulmuş span'ları etiketleyen ve hedefte yeniden etiketleyen özel token'lar. |
| Flan | "Instruction-tuned T5" | >1.800 görevde fine-tune edilmiş T5; encoder-decoder'ı instruction-following'de rekabetçi kıldı. |
| Beam search | "Decoding stratejisi" | Her adımda top-k kısmi diziyi tut; çeviri/özetleme için standart. |
| Teacher forcing | "Eğitim zamanı input'u" | Eğitim sırasında decoder'a sample'lanmış olan değil, gerçek önceki çıktı token'ını besle. |

## İleri Okuma

- [Raffel et al. (2019). Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://arxiv.org/abs/1910.10683) — T5.
- [Lewis et al. (2019). BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension](https://arxiv.org/abs/1910.13461) — BART.
- [Chung et al. (2022). Scaling Instruction-Finetuned Language Models](https://arxiv.org/abs/2210.11416) — Flan-T5.
- [Radford et al. (2022). Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper, kanonik 2026 encoder-decoder.
- [HuggingFace `modeling_t5.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/t5/modeling_t5.py) — referans implementasyonu.
