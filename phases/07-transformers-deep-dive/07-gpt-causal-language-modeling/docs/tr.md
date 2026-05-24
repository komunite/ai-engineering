# GPT — Causal Language Modeling

> BERT iki tarafı da görür. GPT yalnız geçmişi görür. Üçgen mask modern yapay zekadaki en sonuç doğuran tek satır kod.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 02 (Self-Attention), Faz 7 · 05 (Tam Transformer), Faz 7 · 06 (BERT)
**Süre:** ~75 dakika

## Sorun

Bir dil modeli tek bir soru cevaplar: ilk `t-1` token verildiğinde, token `t` üzerindeki olasılık dağılımı nedir? Bu sinyalde — next-token prediction — eğit ve elde ettiğin bir model anbean bir token üzerinden keyfi metin üretebilir.

Tüm bir diziyi paralel olarak end-to-end eğitmek için, her pozisyonun tahmininin yalnızca önceki pozisyonlara bağlı olması gerekir. Aksi takdirde model basitçe cevaba bakarak hile yapar.

Causal mask bunu yapar. Softmax'tan önce attention skorlarına eklenen tek bir üst-üçgensel `-inf` değerleri matrisidir. Softmax'tan sonra, o pozisyonlar 0 olur. Her pozisyon yalnızca kendisine ve önceki pozisyonlara attention yapabilir. Ve bunu tüm diziye bir kere uyguladığın için, tek bir forward pass'te N paralel next-token tahmini elde edersin.

GPT-1 (2018), GPT-2 (2019), GPT-3 (2020), GPT-4 (2023), GPT-5 (2024), Claude, Llama, Qwen, Mistral, DeepSeek, Kimi — hepsi aynı çekirdek döngüye sahip decoder-only causal transformer'lardır. Sadece daha büyük, daha iyi veri ve daha iyi RLHF.

## Kavram

![Causal mask üçgensel bir attention matrisi yaratır](../assets/causal-attention.svg)

### Mask

`N` uzunluğunda bir dizi verildiğinde, `N × N` bir matris kur:

```
M[i, j] = 0       j <= i ise
M[i, j] = -inf    j > i ise
```

Softmax'tan önce `M`'yi ham attention skorlarına ekle. `exp(-inf) = 0`, dolayısıyla mask'li pozisyonlar sıfır ağırlık katkı sağlar. Attention matrisinin her satırı yalnızca önceki pozisyonlar üzerinde bir olasılık dağılımıdır.

Implementasyon maliyeti: tek bir `torch.tril()` çağrısı. Hesaplama süresi: nanosaniyeler. Alana etkisi: her şey.

### Paralel eğitim, seri çıkarım

Eğitim: tüm `(N, d_model)` diziyi bir kere forward-pass et, N cross-entropy loss hesapla (pozisyon başına bir), topla, backprop. Dizi boyunca paralel. GPT eğitiminin ölçeklenmesinin nedeni bu — tek bir GPU pass'inde batch içinde 1M token işliyorsun.

Çıkarım: token token üretirsin. `[t1, t2, t3]` ver, `t4`'ü al. `[t1, t2, t3, t4]` ver, `t5`'i al. `[t1, t2, t3, t4, t5]` ver, `t6`'yı al. KV cache (Ders 12), `t1…tn`'in hidden state'lerini kaydeder, böylece onları her adımda yeniden hesaplamazsın. Ama çıkarımda seri derinlik = çıktı uzunluğu. Autoregressive vergisi budur ve her LLM'in latency darboğazının decoding olmasının nedenidir.

### Loss — bir kaydırarak

`[t1, t2, t3, t4]` token'ları verildiğinde:

- Input: `[t1, t2, t3]`
- Hedefler: `[t2, t3, t4]`

Her pozisyon `i` için, `-log P(target_i | inputs[:i+1])` hesapla. Topla. Bu tüm dizinin cross-entropy'sidir.

Duyduğun her transformer LM bu loss'ta eğitilir. Pre-training, fine-tuning, SFT — aynı loss, farklı veri.

### Decoding stratejileri

Eğitimden sonra, örnekleme seçimleri insanların düşündüğünden daha çok önemli.

| Yöntem | Ne yapar | Ne zaman kullanılır |
|--------|--------------|-------------|
| Greedy | Her adımda argmax | Deterministik görevler, kod tamamlama |
| Temperature | Logit'leri T'ye böl, sample al | Yaratıcı görevler, daha yüksek T = daha fazla çeşitlilik |
| Top-k | Yalnız top-k token'dan sample al | Düşük-olasılıklı kuyrukları öldürür |
| Top-p (nucleus) | Kümülatif olasılık ≥ p olan en küçük setten sample al | 2020+ varsayılan; dağılım şekline adapte olur |
| Min-p | `p > min_p * max_p` olan token'ları tut | 2024+; uzun kuyrukları reddetmede top-p'den daha iyi |
| Speculative decoding | Draft model N token önerir, büyük model doğrular | Aynı kalitede 2–3× latency azalması |

2026'da min-p + temperature 0.7 açık-ağırlıklı modeller için makul bir varsayılandır. Speculative decoding her production çıkarım yığını için temel taştır.

### "GPT tarifi"nin işe yaramasını sağlayan

1. **Decoder-only.** Encoder overhead'i yok. Katman başına bir attention + FFN pass'i.
2. **Ölçekleme.** 124M → 1.5B → 175B → trilyonlar. Chinchilla scaling laws (Ders 13) compute'u nasıl harcayacağını söyler.
3. **In-context learning.** 6B–13B civarında ortaya çıktı. Model fine-tuning olmadan few-shot örnekleri takip edebilir.
4. **RLHF.** İnsan tercihleri üzerinde post-training, ham pretrain edilmiş metni sohbet asistanlarına çevirdi.
5. **Pre-norm + RoPE + SwiGLU.** Ölçekte kararlı eğitim.

Çekirdek mimari GPT-2'den beri pek değişmedi. İlginç olan her şey veride, ölçekte ve post-training'de oldu.

## İnşa Et

### Adım 1: causal mask

`code/main.py`'a bak. Tek satır:

```python
def causal_mask(n):
    return [[0.0 if j <= i else float("-inf") for j in range(n)] for i in range(n)]
```

Softmax'tan önce attention skorlarına ekle. Mekanizmanın tamamı bu.

### Adım 2: 2 katmanlı GPT-vari bir model

İki decoder bloğu yığ (mask'lenmiş self-attention + FFN, cross-attention yok). Bir token embedding'i, bir positional encoding ve bir unembedding ekle (token embedding matrisine bağlı — GPT-2'den beri standart bir numara).

### Adım 3: next-token prediction, end-to-end

20 token'lık oyuncak bir vocab'ta, her pozisyonda logit'ler üret. Bir kaydırarak hedef'e karşı cross-entropy loss hesapla. Gradient yok — bu bir forward-pass sağlık kontrolüdür.

### Adım 4: örnekleme

Greedy, temperature, top-k, top-p, min-p implement et. Her birini sabit bir prompt'ta çalıştır ve çıktıları karşılaştır. Bir örnekleme fonksiyonu 10 satır.

## Kullan

PyTorch, 2026 deyimi:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")

prompt = "Attention is all you need because"
inputs = tok(prompt, return_tensors="pt")
out = model.generate(
    **inputs,
    max_new_tokens=64,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
)
print(tok.decode(out[0]))
```

Kaputun altında, `generate()` forward pass çalıştırır, son-pozisyon logit'lerini çeker, sonraki token'ı sample alır, ekler ve tekrar eder. Her production LLM çıkarım yığını (vLLM, TensorRT-LLM, llama.cpp, Ollama, MLX) aynı döngüyü ağır optimizasyonla implement eder — batched prefill, continuous batching, KV cache paging, speculative decoding.

**GPT vs BERT, her biri tek satır:** GPT `P(x_t | x_{<t})` tahmin eder. BERT `P(x_masked | x_unmasked)` tahmin eder. Loss, modelin generate edip edemeyeceğini belirler.

## Yayınla

`outputs/skill-sampling-tuner.md`'ye bak. Skill, yeni bir üretim görevi için örnekleme parametrelerini seçer ve deterministik decoding gerektiğinde flag'ler.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır ve softmax'tan sonra causal attention matrisinin alt-üçgensel olduğunu doğrula. Spot-check: satır 3 yalnızca sütun 0–3'te ağırlığa sahip olmalı.
2. **Orta.** Genişlik 4 için beam search implement et. 10 kısa prompt'ta beam-4 vs greedy perplexity'sini karşılaştır. Beam her zaman kazanır mı? (İpucu: genellikle çeviri için, açık-uçlu sohbet için değil.)
3. **Zor.** Speculative decoding implement et: draft olarak küçük bir 2 katmanlı model ve doğrulayıcı olarak 6 katmanlı bir model kullan. Uzunluk 64'ün 100 tamamlamasında duvar-saati hızlanmayı ölç. Çıktıların doğrulayıcının greedy'siyle eşleştiğini doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Causal mask | "Üçgen" | Pozisyon `i`'nin yalnızca `≤ i` pozisyonlarını görmesi için attention skorlarına eklenen üst-üçgensel `-inf` matris. |
| Next-token prediction | "Loss" | Her pozisyonda modelin dağılımının gerçek sonraki token'a karşı cross-entropy'si. |
| Autoregressive | "Anbean üret" | Çıktıyı input olarak geri besle; paralellik yalnız eğitimde, üretimde değil. |
| Logit'ler | "Pre-softmax skorlar" | Softmax'tan önce LM head'in ham çıktısı; örnekleme bunlar üzerinde olur. |
| Temperature | "Yaratıcılık düğmesi" | Logit'leri T'ye böl; T→0 = greedy, T→∞ = uniform. |
| Top-p | "Nucleus sampling" | Dağılımı toplamı ≥p olan en küçük sete kırp; kalandan sample al. |
| Min-p | "Top-p'den daha iyi" | `p ≥ min_p × max_p` olan token'ları tut; cutoff'u dağılımın keskinliğine adapte eder. |
| Speculative decoding | "Draft + doğrula" | Ucuz model N token önerir; büyük model paralel doğrular. |
| Teacher forcing | "Eğitim numarası" | Eğitim sırasında modelin tahminini değil, gerçek önceki token'ı besle. Her seq2seq LM için standart. |

## İleri Okuma

- [Radford et al. (2018). Improving Language Understanding by Generative Pre-Training](https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf) — GPT-1.
- [Radford et al. (2019). Language Models are Unsupervised Multitask Learners](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) — GPT-2.
- [Brown et al. (2020). Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165) — GPT-3 ve in-context learning.
- [Leviathan, Kalman, Matias (2023). Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) — spec decoding makalesi.
- [HuggingFace `modeling_llama.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py) — kanonik causal-LM referans kodu.
