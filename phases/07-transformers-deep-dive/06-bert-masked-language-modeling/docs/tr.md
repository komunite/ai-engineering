# BERT — Masked Language Modeling

> GPT bir sonraki kelimeyi tahmin eder. BERT eksik bir kelimeyi tahmin eder. Bir cümlelik fark — ve embedding biçimli her şeyin yarım on yılı.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 7 · 05 (Tam Transformer), Faz 5 · 02 (Text Representation)
**Süre:** ~45 dakika

## Sorun

2018'de her NLP görevi — duygu, NER, QA, entailment — kendi etiketli verisi üzerinde sıfırdan kendi modelini eğitiyordu. Fine-tune edebileceğin önceden eğitilmiş "İngilizce'yi anla" checkpoint'i yoktu. ELMo (2018) çift yönlü bir LSTM ile kontekstüel embedding'leri pretrain edebileceğini gösterdi; yardımcı oldu ama genelleşmedi.

BERT (Devlin et al. 2018) sordu: ya bir transformer encoder alıp internetteki her cümlede eğitsek ve onu iki taraftan da context'ten eksik kelimeleri tahmin etmeye zorlasak? Sonra downstream görevinde tek bir head'i fine-tune et. Parametre verimliliği bir vahiydi.

Sonuç: 18 ay içinde BERT ve varyantları (RoBERTa, ALBERT, ELECTRA) var olan her NLP leaderboard'ını domine etti. 2020'ye gelindiğinde, dünyadaki her arama motoru, içerik moderasyon pipeline'ı ve semantic-search sisteminin içinde bir BERT vardı.

2026'da encoder-only modeller hâlâ sınıflandırma, retrieval ve yapılandırılmış extraction için doğru araç — decoder'lardan token başına 5–10× daha hızlı çalışır ve embedding'leri her modern retrieval yığınının omurgasıdır. ModernBERT (Aralık 2024) mimariyi Flash Attention + RoPE + GeGLU ile 8K context'e itti.

## Kavram

![Masked language modeling: token seç, mask'le, orijinalleri tahmin et](../assets/bert-mlm.svg)

### Eğitim sinyali

Bir cümle al: `the quick brown fox jumps over the lazy dog`.

Rastgele %15 token'ı mask'le:

```
input:  the [MASK] brown fox jumps [MASK] the lazy dog
target: the  quick brown fox jumps  over  the lazy dog
```

Modeli mask'lenmiş pozisyonlarda orijinal token'ları tahmin etmek üzere eğit. Encoder çift yönlü olduğu için, pozisyon 1'deki `[MASK]`'i tahmin etmek pozisyon 2+'daki `brown fox jumps`'ı kullanabilir. GPT'nin yapamadığı şey budur.

### BERT mask kuralları

Tahmin için seçilen %15 token'dan:

- %80'i `[MASK]` ile değiştirilir.
- %10'u rastgele bir token ile değiştirilir.
- %10'u değişmeden bırakılır.

Neden her zaman `[MASK]` değil? Çünkü `[MASK]` çıkarımda asla görünmez. Modeli mask'lenmiş pozisyonların %100'ünde `[MASK]` beklemek üzere eğitmek pretraining ile fine-tuning arasında bir dağılım kayması yaratırdı. %10 rastgele + %10 değişmemiş modeli dürüst tutar.

### Next Sentence Prediction (NSP) — ve neden düşürüldü

Orijinal BERT NSP üzerinde de eğitildi: iki cümle A ve B verildiğinde, B'nin A'yı takip edip etmediğini tahmin et. RoBERTa (2019) onu ablate etti ve NSP'nin zarar verdiğini, yardım etmediğini gösterdi. Modern encoder'lar onu atlar.

### 2026'da değişen: ModernBERT

2024 ModernBERT makalesi bloğu 2026 ilkel'leriyle yeniden inşa etti:

| Bileşen | Orijinal BERT (2018) | ModernBERT (2024) |
|-----------|----------------------|-------------------|
| Positional | Learned absolute | RoPE |
| Activation | GELU | GeGLU |
| Normalization | LayerNorm | Pre-norm RMSNorm |
| Attention | Tam yoğun | Alternating local (128) + global |
| Context length | 512 | 8192 |
| Tokenizer | WordPiece | BPE |

Ve 2018 yığınından farklı olarak Flash-Attention-native. Çıkarım, daha iyi GLUE skorlarıyla sequence length 8K'da DeBERTa-v3'ten 2–3× daha hızlı.

### 2026'da hâlâ encoder seçen kullanım durumları

| Görev | Encoder neden decoder'ı yener |
|------|---------------------------|
| Retrieval / semantic search embedding'leri | Çift yönlü context = token başına daha iyi embedding kalitesi |
| Sınıflandırma (duygu, intent, toksisite) | Tek forward pass; üretim overhead'i yok |
| NER / token etiketleme | Pozisyon başına çıktı, doğal olarak çift yönlü |
| Zero-shot entailment (NLI) | Encoder'ın üzerinde sınıflandırıcı head |
| RAG için reranker | Cross-encoder skorlaması, LLM reranker'larından 10× daha hızlı |

## İnşa Et

### Adım 1: mask'leme mantığı

`code/main.py`'a bak. `create_mlm_batch` fonksiyonu, token ID listesi, vocab size ve bir mask olasılığı alır. Input ID'leri (mask'ler uygulanmış) ve etiketleri (yalnızca mask'lenmiş pozisyonlarda, başka yerlerde -100 — PyTorch'un ignore index konvansiyonu) döndürür.

```python
def create_mlm_batch(tokens, vocab_size, mask_prob=0.15, rng=None):
    input_ids = list(tokens)
    labels = [-100] * len(tokens)
    for i, t in enumerate(tokens):
        if rng.random() < mask_prob:
            labels[i] = t
            r = rng.random()
            if r < 0.8:
                input_ids[i] = MASK_ID
            elif r < 0.9:
                input_ids[i] = rng.randrange(vocab_size)
            # else: orijinali tut
    return input_ids, labels
```

### Adım 2: küçük bir corpus'ta MLM tahmini çalıştır

20 kelimelik bir vocab, 200 cümle üzerinde 2 katmanlı bir encoder + MLM head eğit. Gradient yok — forward-pass sağlık kontrolleri yapıyoruz. Tam eğitim PyTorch gerektirir.

### Adım 3: mask tiplerini karşılaştır

Üç yönlü kuralın modeli `[MASK]` olmadan kullanılabilir tuttuğunu göster. Mask'siz bir cümlede ve mask'li bir cümlede tahmin et. Her ikisi de makul token dağılımları üretmeli çünkü model eğitimde her iki pattern'i de gördü.

### Adım 4: fine-tune head

MLM head'i oyuncak bir duygu veri setinde bir sınıflandırma head'i ile değiştir. Yalnız head eğitilir; encoder donmuş. Bu, her BERT uygulamasının izlediği pattern'dir.

## Kullan

```python
from transformers import AutoModel, AutoTokenizer

tok = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
model = AutoModel.from_pretrained("answerdotai/ModernBERT-base")

text = "Attention is all you need."
inputs = tok(text, return_tensors="pt")
out = model(**inputs).last_hidden_state   # (1, N, 768)
```

**Embedding modelleri fine-tune edilmiş BERT'lerdir.** `all-MiniLM-L6-v2` gibi `sentence-transformers` modelleri, contrastive loss ile eğitilmiş BERT'lerdir. Encoder aynı. Loss değişti.

**Cross-encoder reranker'lar da fine-tune edilmiş BERT'lerdir.** `[CLS] query [SEP] doc [SEP]` üzerinde pair-classification. Query ve doc arasındaki çift yönlü attention, cross-encoder'lara biencoder'lar üzerinde kalite avantajı veren şey tam olarak budur.

**2026'da BERT seçilmemesi gereken zaman.** Generative her şey. Encoder'ın autoregressive olarak token üretmek için makul bir yolu yoktur. Ayrıca: küçük bir decoder'ın daha fazla esneklikle kaliteyi yakalayabildiği 1B parametre altındaki her şey (Phi-3-Mini, Qwen2-1.5B).

## Yayınla

`outputs/skill-bert-finetuner.md`'ye bak. Skill, yeni bir sınıflandırma veya extraction görevi için bir BERT fine-tune'unu (backbone seçimi, head spec, veri, eval, durdurma) kapsamlandırır.

## Alıştırmalar

1. **Kolay.** `code/main.py`'ı çalıştır ve 10.000 token boyunca mask dağılımını yazdır. ~%15'in seçildiğini ve bunların ~%80'inin `[MASK]` olduğunu doğrula.
2. **Orta.** Whole-word masking implement et: bir kelime subword'lere tokenize edildiyse, tüm subword'leri birlikte mask'le veya hiç mask'leme. Bunun 500 cümlelik bir corpus'ta MLM doğruluğunu iyileştirip iyileştirmediğini ölç.
3. **Zor.** Halka açık bir veri setinden 10.000 cümlede küçük (2 katman, d=64) bir BERT eğit. SST-2 duygu için `[CLS]` token'ını fine-tune et. Eşleşen parametrelerde decoder-only baseline'a karşı karşılaştır — kim kazanır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| MLM | "Masked language modeling" | Eğitim sinyali: rastgele %15 token'ı `[MASK]` ile değiştir, orijinalleri tahmin et. |
| Çift yönlü | "İki yönden bakar" | Encoder attention'ında causal mask yok — her pozisyon diğer her pozisyonu görür. |
| `[CLS]` | "Pooler token'ı" | Her dizinin başına eklenen özel token; son embedding'i cümle-seviyesi temsil olarak kullanılır. |
| `[SEP]` | "Segment ayırıcı" | Eşleşmiş dizileri ayırır (örn. query/doc, cümle A/B). |
| NSP | "Next sentence prediction" | BERT'in ikinci pretraining görevi; RoBERTa'da işe yaramaz gösterildi, 2019'dan sonra düşürüldü. |
| Fine-tuning | "Bir göreve adapte et" | Encoder'ı çoğunlukla donmuş tut; downstream görevi için üstte küçük bir head eğit. |
| Cross-encoder | "Bir reranker" | Hem query'i hem doc'u input olarak alan, alaka skoru çıkaran bir BERT. |
| ModernBERT | "2024 yenileme" | RoPE, RMSNorm, GeGLU, alternating local/global attention, 8K context ile yeniden inşa edilmiş encoder. |

## İleri Okuma

- [Devlin et al. (2018). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805) — orijinal makale.
- [Liu et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach](https://arxiv.org/abs/1907.11692) — BERT nasıl doğru eğitilir; NSP'yi öldürür.
- [Clark et al. (2020). ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators](https://arxiv.org/abs/2003.10555) — replaced-token detection eşleşen compute'ta MLM'yi yener.
- [Warner et al. (2024). Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder](https://arxiv.org/abs/2412.13663) — ModernBERT makalesi.
- [HuggingFace `modeling_bert.py`](https://github.com/huggingface/transformers/blob/main/src/transformers/models/bert/modeling_bert.py) — kanonik encoder referansı.
