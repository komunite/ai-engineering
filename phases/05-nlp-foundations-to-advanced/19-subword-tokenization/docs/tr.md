# Subword Tokenleştirme — BPE, WordPiece, Unigram, SentencePiece

> Kelime tokenleştiriciler görülmemiş kelimelerde tıkanır. Karakter tokenleştiricilerse dizi uzunluğunu patlatır. Subword tokenleştiriciler farkı böler. Her modern LLM bunlardan biriyle gönderilir.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 01 (Metin İşleme), Faz 5 · 04 (GloVe / FastText / Subword)
**Süre:** ~60 dakika

## Sorun

Vocabulary'nin 50,000 kelimesi var. Bir kullanıcı "untokenizable" yazıyor. Tokenleştiricin `[UNK]` döndürüyor. Model artık o kelime hakkında hiçbir sinyale sahip değil. Daha kötüsü: corpus'undaki 90'ıncı persentil belgenin 40 nadir kelimesi var, bu da belge başına 40 bit düşürülmüş bilgi anlamına geliyor.

Subword tokenleştirme bunu çözer. Yaygın kelimeler tek token kalır. Nadir kelimeler anlamlı parçalara ayrışır: `untokenizable` → `un`, `token`, `izable`. Eğitim verisi her şeyi kapsar çünkü herhangi bir string nihayetinde bir byte dizisidir.

2026'da her sınır LLM'i üç algoritmadan biriyle (BPE, Unigram, WordPiece), üç kütüphaneden birine sarmalanmış (tiktoken, SentencePiece, HF Tokenizers) gönderilir. Birini seçmeden bir dil modeli gönderemezsin.

## Kavram

![BPE vs Unigram vs WordPiece, karakter karakter](../assets/subword-tokenization.svg)

**BPE (Byte-Pair Encoding).** Karakter seviyesi bir vocabulary ile başla. Her komşu çifti say. En sık çifti yeni bir token'a birleştir. Hedef vocabulary boyutuna ulaşana kadar tekrarla. Baskın algoritma: GPT-2/3/4, Llama, Gemma, Qwen2, Mistral.

**Byte-level BPE.** Aynı algoritma ama Unicode karakterleri yerine ham byte'lar (256 base token) üzerinde. Sıfır `[UNK]` token garantisi — herhangi bir byte dizisi encode olur. GPT-2, 50,257 token kullanır (256 byte + 50,000 merge + 1 özel).

**Unigram.** Büyük bir vocabulary ile başla. Her token'a bir unigram olasılığı ata. Kaldırılması corpus log-olabilirliğini en az artıran token'ları yinelemeli olarak buda. Çıkarımda olasılıksal: tokenleştirmeleri örnekleyebilir (subword regularization yoluyla data augmentation için kullanışlı). T5, mBART, ALBERT, XLNet, Gemma tarafından kullanılır.

**WordPiece.** Ham frekanstan ziyade eğitim corpus'unun olabilirliğini maksimize eden çiftleri birleştir. BERT, DistilBERT, ELECTRA tarafından kullanılır.

**SentencePiece vs tiktoken.** SentencePiece, vocabulary'leri (BPE ya da Unigram) doğrudan ham Unicode metin üzerinde *eğiten* kütüphanedir, boşluğu `▁` olarak encode eder. tiktoken, OpenAI'nin önceden inşa edilmiş vocabulary'lere karşı hızlı *encoder*'ıdır; eğitmez.

Pratik kural:

- **Yeni bir vocabulary eğitmek:** SentencePiece (çok dilli, pre-tokenization yok) ya da HF Tokenizers.
- **GPT vocab'a karşı hızlı çıkarım:** tiktoken (cl100k_base, o200k_base).
- **İkisi de:** HF Tokenizers — tek kütüphane, eğitim + sunum.

## İnşa Et

### Adım 1: sıfırdan BPE

`code/main.py`'a bak. Döngü:

```python
def train_bpe(corpus, num_merges):
    vocab = {tuple(word) + ("</w>",): count for word, count in corpus.items()}
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for symbols, freq in vocab.items():
            for a, b in zip(symbols, symbols[1:]):
                pairs[(a, b)] += freq
        if not pairs:
            break
        best = pairs.most_common(1)[0][0]
        merges.append(best)
        vocab = apply_merge(vocab, best)
    return merges
```

Algoritmanın encode ettiği üç gerçek. `</w>` kelime sonunu işaretler, böylece "low" (sonek) ve "lower" (önek) farklı kalır. Frekans ağırlıklandırma yüksek frekanslı çiftlerin erken kazanmasını sağlar. Merge listesi sıralıdır — çıkarım merge'leri eğitim sırasında uygular.

### Adım 2: öğrenilmiş merge'lerle encode et

```python
def encode_bpe(word, merges):
    symbols = list(word) + ["</w>"]
    for a, b in merges:
        i = 0
        while i < len(symbols) - 1:
            if symbols[i] == a and symbols[i + 1] == b:
                symbols = symbols[:i] + [a + b] + symbols[i + 2:]
            else:
                i += 1
    return symbols
```

Naif O(n·|merges|). Üretim implementasyonları (tiktoken, HF Tokenizers) priority queue'larla merge-rank lookup kullanır ve neredeyse-lineer zamanda çalışır.

### Adım 3: pratikte SentencePiece

```python
import sentencepiece as spm

spm.SentencePieceTrainer.train(
    input="corpus.txt",
    model_prefix="my_tokenizer",
    vocab_size=8000,
    model_type="bpe",          # ya da "unigram"
    character_coverage=0.9995, # CJK için düşür (örn İngilizce için 0.9995, Japonca için 0.995)
    normalization_rule_name="nmt_nfkc",
)

sp = spm.SentencePieceProcessor(model_file="my_tokenizer.model")
print(sp.encode("untokenizable", out_type=str))
# ['▁un', 'token', 'izable']
```

Dikkat: pre-tokenization gerekmez, boşluk `▁` olarak encode edilir, `character_coverage` nadir karakterlerin ne kadar agresif korunacağını vs `<unk>`'a eşleneceğini kontrol eder.

### Adım 4: OpenAI uyumlu vocab'lar için tiktoken

```python
import tiktoken
enc = tiktoken.get_encoding("o200k_base")
print(enc.encode("untokenizable"))        # [127340, 101028]
print(len(enc.encode("Hello, world!")))   # 4
```

Yalnızca encoding. Hızlı (Rust arka uç). Byte sayma, maliyet tahmini, bağlam penceresi bütçelemesi için GPT-4/5 tokenleştirmesiyle tam eşleşme.

## 2026'da hâlâ gönderilen tuzaklar

- **Tokenleştirici kayması.** Vocab A üzerinde eğitim, vocab B'ye karşı deploy. Token ID'leri farklı; model çıktıları çöp. CI'da `tokenizer.json` hash'ini kontrol et.
- **Boşluk belirsizliği.** BPE'de "hello" vs " hello" farklı token'lar üretir. `add_special_tokens` ve `add_prefix_space`'i her zaman açıkça belirt.
- **Çok dilli yetersiz eğitim.** İngilizce ağırlıklı corpus'lar, Latin olmayan script'leri 5-10 kat daha fazla token'a bölen vocabulary'ler üretir. Aynı prompt GPT-3.5'te Japonca/Arapça'da 5-10 kat daha maliyetli. o200k_base bunu kısmen düzeltti.
- **Emoji split'leri.** Tek bir emoji 5 token alabilir. Bağlamı bütçelerken emoji ele alımını kontrol et.

## Kullan

2026 stack'i:

| Durum | Seç |
|-----------|------|
| Sıfırdan monolingual model eğitme | HF Tokenizers (BPE) |
| Çok dilli model eğitme | SentencePiece (Unigram, `character_coverage=0.9995`) |
| OpenAI uyumlu API sunma | tiktoken (GPT-4+ için `o200k_base`) |
| Alana özgü vocab (kod, matematik, protein) | Alan corpus'unda özel BPE eğit, base vocab ile birleştir |
| Edge çıkarım, küçük model | Unigram (küçük vocabulary'ler daha iyi çalışır) |

Vocabulary boyutu bir ölçeklendirme kararıdır, sabit değil. Kaba sezgi: <1B parametre için 32k, 1-10B için 50-100k, multilingual/frontier için 200k+.

## Yayınla

`outputs/skill-bpe-vs-wordpiece.md` olarak kaydet:

```markdown
---
name: tokenizer-picker
description: Pick tokenizer algorithm, vocab size, library for a given corpus and deployment target.
version: 1.0.0
phase: 5
lesson: 19
tags: [nlp, tokenization]
---

Given a corpus (size, languages, domain) and deployment target (training from scratch / fine-tuning / API-compatible inference), output:

1. Algorithm. BPE, Unigram, or WordPiece. One-sentence reason.
2. Library. SentencePiece, HF Tokenizers, or tiktoken. Reason.
3. Vocab size. Rounded to nearest 1k. Reason tied to model size and language coverage.
4. Coverage settings. `character_coverage`, `byte_fallback`, special-token list.
5. Validation plan. Average tokens-per-word on held-out set, OOV rate, compression ratio, round-trip decode equality.

Refuse to train a character-coverage <0.995 tokenizer on corpora with rare-script content. Refuse to ship a vocab without a frozen `tokenizer.json` hash check in CI. Flag any monolingual tokenizer under 16k vocab as likely under-spec.
```

## Alıştırmalar

1. **Kolay.** `code/main.py`'ın minik corpus'unda 500-merge BPE eğit. Üç held-out kelimeyi encode et. Kaçı tam 1 token vs >1 token üretti?
2. **Orta.** 100 İngilizce Wikipedia cümlesinde `cl100k_base`, `o200k_base` ve vocab=32k ile eğittiğin bir SentencePiece BPE arasında token sayımlarını karşılaştır. Her birinin sıkıştırma oranını raporla.
3. **Zor.** Aynı corpus'u BPE, Unigram ve WordPiece ile eğit. Küçük bir duygu sınıflandırıcısında her birini kullandığında downstream doğruluğu ölç. Seçim iğneyi 1 puan F1'den fazla hareket ettiriyor mu?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| BPE | Byte-Pair Encoding | Hedef vocab boyutuna ulaşana kadar en sık karakter çiftlerinin greedy birleştirilmesi. |
| Byte-level BPE | Asla bilinmeyen token yok | Ham 256 byte üzerinde BPE; GPT-2 / Llama bunu kullanır. |
| Unigram | Olasılıksal tokenleştirici | Log-olabilirlik kullanarak büyük bir aday setinden budar; T5, Gemma tarafından kullanılır. |
| SentencePiece | Boşluklu olan | BPE/Unigram'ı ham metin üzerinde eğiten kütüphane; boşluk `▁` olarak encode edilir. |
| tiktoken | Hızlı olan | OpenAI'nin önceden inşa edilmiş vocab'lar için Rust arkalı BPE encoder'ı. Eğitim yok. |
| Merge listesi | Sihirli sayılar | Sıralı `(a, b) → ab` merge listesi; çıkarım sırayla uygular. |
| Character coverage | Ne kadar nadirse çok? | Tokenleştiricinin kapsaması gereken eğitim corpus'undaki karakter oranı; ~0.9995 tipik. |

## İleri Okuma

- [Sennrich, Haddow, Birch (2015). Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — BPE makalesi.
- [Kudo (2018). Subword Regularization with Unigram Language Model](https://arxiv.org/abs/1804.10959) — Unigram makalesi.
- [Kudo, Richardson (2018). SentencePiece: A simple and language independent subword tokenizer](https://arxiv.org/abs/1808.06226) — kütüphane.
- [Hugging Face — Summary of the tokenizers](https://huggingface.co/docs/transformers/tokenizer_summary) — özlü referans.
- [OpenAI tiktoken repo](https://github.com/openai/tiktoken) — cookbook + encoding listesi.
