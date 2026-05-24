# Sıfırdan Tokenleştirici İnşa Etme

> Ders 01 sana bir oyuncak verdi. Bu ders sana bir silah veriyor.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 10, Ders 01 (Tokenleştiriciler: BPE, WordPiece, SentencePiece)
**Süre:** ~90 dakika

## Öğrenme Hedefleri

- Unicode, whitespace normalizasyonu ve özel token'ları halleden production-seviyeli bir BPE tokenleştirici inşa et
- Byte-level fallback implement et ki tokenleştirici, emoji, CJK ve kod dahil herhangi bir input'u bilinmeyen token üretmeden encode edebilsin
- BPE merge'lerini uygulamadan önce metni kelime sınırlarında bölen pre-tokenizasyon regex desenleri ekle
- Custom bir tokenleştiriciyi bir corpus üzerinde eğit ve çok dilli metin üzerinde tiktoken'a karşı sıkıştırma oranını değerlendir

## Sorun

Ders 01'deki BPE tokenleştiricin İngilizce metinde çalışıyor. Şimdi ona Japonca at. Veya emoji. Veya karışık tab ve boşluk olan Python kodu.

Bozulur.

BPE yanlış olduğu için değil — implementasyon eksik olduğu için. Production tokenleştirici herhangi bir encoding'teki ham byte'ları halleder, bölmeden önce Unicode'u normalize eder, asla merge edilmeyen özel token'ları yönetir, pre-tokenizasyonu subword bölmesiyle zincirler ve tüm bunları 15 trilyon token işleyen bir eğitim pipeline'ını darboğaza sokmayacak kadar hızlı yapar.

GPT-2'nin tokenleştiricisinin 50.257 token'ı var. Llama 3'ün 128.256. GPT-4'ün yaklaşık 100.000. Bunlar oyuncak rakamlar değil. O vocabulary'lerin arkasındaki merge tabloları yüzlerce gigabyte metin üzerinde eğitildi ve etrafındaki makine — normalizasyon, pre-tokenizasyon, özel token enjeksiyonu, chat template formatlaması — "hello world"u halleden bir tokenleştiriciyi tüm interneti hallederen bir tokenleştiriciden ayıran şey budur.

O makineyi inşa edeceksin.

## Kavram

### Tam Pipeline

Production tokenleştirici tek bir algoritma değildir. Her biri farklı bir problem çözen beş aşamalı bir pipeline'dır.

```mermaid
graph LR
    A[Ham Metin] --> B[Normalize]
    B --> C[Pre-Tokenize]
    C --> D[BPE Merge]
    D --> E[Özel Token'lar]
    E --> F[Token ID'leri]

    style A fill:#1a1a2e,stroke:#e94560,color:#fff
    style B fill:#1a1a2e,stroke:#e94560,color:#fff
    style C fill:#1a1a2e,stroke:#e94560,color:#fff
    style D fill:#1a1a2e,stroke:#e94560,color:#fff
    style E fill:#1a1a2e,stroke:#e94560,color:#fff
    style F fill:#1a1a2e,stroke:#e94560,color:#fff
```

Her aşamanın belirli bir görevi var:

| Aşama | Ne Yapıyor | Neden Önemli |
|-------|-------------|----------------|
| Normalize | NFKC Unicode, opsiyonel lowercase, opsiyonel aksan kaldırma | "fi" ligature (U+FB01) "fi" olur (iki karakter). Bunsuz, aynı kelime farklı token'lar alır. |
| Pre-Tokenize | Metni BPE'den önce parçalara böl | BPE'in kelime sınırları arasında merge etmesini önler. "the cat" asla "e c" token'ı üretmemeli. |
| BPE Merge | Öğrenilmiş merge kurallarını byte sequence'lerine uygula | Çekirdek sıkıştırma. Ham byte'ları subword token'larına çevirir. |
| Özel Token'lar | [BOS], [EOS], [PAD], chat template işaretleyicileri enjekte et | Bu token'ların sabit ID'leri var. Asla BPE merge'lerine katılmazlar. Model yapı için onlara ihtiyaç duyar. |
| ID Eşleme | Token string'lerini integer ID'lerine çevir | Model integer görür, string değil. |

### Byte-Level BPE

Ders 01'in tokenleştiricisi UTF-8 byte'ları üzerinde çalıştı. Bu doğru bir karardı. Ama önemli bir şeyi atladık: o byte'lar geçerli UTF-8 değilse ne olur?

Byte-level BPE bunu, olası her byte değerini (0-255) geçerli bir token olarak ele alarak çözer. Taban vocabulary'in tam olarak 256 girişten oluşur. Herhangi bir dosya — metin, binary, bozulmuş — bilinmeyen token üretmeden tokenleştirilebilir.

GPT-2 bir hile ekledi: vocabulary insan-okunabilir kalsın diye her byte'ı bir basılabilir Unicode karakterine eşle. Byte 0x20 (boşluk) onların eşlemesinde "G" karakteri olur. Bu sadece kozmetiktir. Algoritma umursamaz.

Asıl güç: byte-level BPE yeryüzündeki her dili halleder. Çince karakterler her biri 3 UTF-8 byte'tır. Japonca 3-4 byte olabilir. Arapça, Devanagari, emoji — hepsi sadece byte sequence'leri. BPE algoritması bu byte sequence'lerindeki desenleri, İngilizce ASCII byte'larındaki desenleri bulduğu şekilde tam olarak bulur.

### Pre-Tokenizasyon

BPE metnine dokunmadan önce, onu parçalara bölmen gerek. Bu, merge algoritmasının kelime sınırlarını aşan token'lar oluşturmasını önler.

GPT-2 metni bölmek için bir regex deseni kullanır:

```
'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+
```

Bu desen kısaltmalar ("don't" "don" + "'t" olur), opsiyonel önde boşluğu olan kelimeler, sayılar, noktalama ve whitespace üzerinde böler. Önde boşluk kelimeye ekli kalır — yani "the cat" şuna döner: [" the", " cat"], ["the", " ", "cat"] değil.

Llama, regex'i tamamen atlayan SentencePiece kullanır. Ham byte akışını uzun tek bir sequence olarak ele alır ve sınırları bulmayı BPE algoritmasına bırakır. Bu daha basit ama BPE'e kelimeler arası token oluşturma özgürlüğü daha fazla verir.

Seçim önemli. GPT-2'nin regex'i, tokenleştiricinin bir kelimenin sonundaki "the" ile bir sonraki kelimenin başındaki "the"'nin merge olması gerektiğini öğrenmesini önler. SentencePiece buna izin verir, bu da bazen daha verimli sıkıştırma üretir ama daha az yorumlanabilir token'lar üretir.

### Özel Token'lar

Her production tokenleştirici yapısal işaretler için token ID'leri ayırır:

| Token | Amaç | Kullanan |
|-------|---------|---------|
| `[BOS]` / `<s>` | Sequence başı | Llama 3, GPT |
| `[EOS]` / `</s>` | Sequence sonu | Tüm modeller |
| `[PAD]` | Batch hizalama için padding | BERT, T5 |
| `[UNK]` | Bilinmeyen token (byte-level BPE bunu ortadan kaldırır) | BERT, WordPiece |
| `<\|im_start\|>` | Chat mesajı sınırı başı | ChatGPT, Qwen |
| `<\|im_end\|>` | Chat mesajı sınırı sonu | ChatGPT, Qwen |
| `<\|user\|>` | Kullanıcı sırası işaretleyicisi | Llama 3 |
| `<\|assistant\|>` | Assistant sırası işaretleyicisi | Llama 3 |

Özel token'lar asla BPE tarafından bölünmez. Merge algoritması çalışmadan önce tam olarak eşleştirilir, sabit ID'leri ile değiştirilir ve çevredeki metin normal şekilde tokenleştirilir.

### Chat Template'leri

Çoğu insanın kafasının karıştığı ve çoğu implementasyonun bozulduğu yer burası.

Chat modeline mesaj gönderdiğinde, API bir mesaj listesi kabul eder:

```
[
  {"role": "system", "content": "You are helpful."},
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi there!"}
]
```

Model JSON görmez. Düz bir token sequence görür. Chat template, mesajları özel token'ları kullanarak o düz sequence'e çevirir. Her model bunu farklı yapar:

```
Llama 3:
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are helpful.<|eot_id|><|start_header_id|>user<|end_header_id|>

Hello<|eot_id|><|start_header_id|>assistant<|end_header_id|>

Hi there!<|eot_id|>

ChatGPT:
<|im_start|>system
You are helpful.<|im_end|>
<|im_start|>user
Hello<|im_end|>
<|im_start|>assistant
Hi there!<|im_end|>
```

Template'i yanlış yap ve model çöp üretir. Tek bir kesin format üzerinde eğitildi. Herhangi bir sapma — eksik bir newline, takas edilmiş bir token, fazladan bir boşluk — input'u eğitim dağılımının dışına atar.

### Hız

Python production tokenleştirmesi için çok yavaş.

tiktoken (OpenAI), Python binding'leri olan Rust'ta yazılmış. HuggingFace tokenizers da Rust. SentencePiece C++. Bunlar saf Python üzerinde 10-100x hızlanma elde eder.

Perspektif için: Llama 3 pretraining için 15 trilyon token'ı saniyede 1 milyon token'da (hızlı Python) tokenleştirmek 174 gün sürerdi. Saniyede 100 milyon token'da (Rust) 1.7 gün sürer.

Algoritmayı anlamak için Python'da inşa ediyorsun. Production'da derlenmiş implementasyon kullanır ve sadece Python wrapper'ına dokunursun.

## İnşa Et

### Adım 1: Byte-Level Encoding

Temel. Herhangi bir string'i byte sequence'ine çevir, görüntüleme için her byte'ı basılabilir bir karaktere eşle ve süreci tersine çevir.

```python
def bytes_to_tokens(text):
    return list(text.encode("utf-8"))

def tokens_to_text(token_bytes):
    return bytes(token_bytes).decode("utf-8", errors="replace")
```

Byte sayılarını görmek için çok dilli metinde test et:

```python
texts = [
    ("İngilizce", "hello"),
    ("Çince", "你好"),
    ("Emoji", "🔥"),
    ("Karışık", "hello你好🔥"),
]

for label, text in texts:
    b = bytes_to_tokens(text)
    print(f"{label}: {len(text)} karakter -> {len(b)} byte -> {b}")
```

"hello" 5 byte. "你好" 6 byte (karakter başına 3). Ateş emoji 4 byte. Byte-level tokenleştirici hangi dil olduğunu umursamaz. Byte byte'tır.

### Adım 2: Regex'li Pre-Tokenizer

Metni GPT-2 regex deseni kullanarak parçalara böl. Her parça BPE tarafından bağımsız tokenleştirilir.

```python
import re

try:
    import regex
    GPT2_PATTERN = regex.compile(
        r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    )
except ImportError:
    GPT2_PATTERN = re.compile(
        r"""'(?:[sdmt]|ll|ve|re)| ?[a-zA-Z]+| ?[0-9]+| ?[^\s\w]+|\s+(?!\S)|\s+"""
    )

def pre_tokenize(text):
    return [match.group() for match in GPT2_PATTERN.finditer(text)]
```

`regex` modülü Unicode property escape'lerini destekler (harfler için `\p{L}`, sayılar için `\p{N}`). Standart kütüphane `re` modülü desteklemez, bu yüzden ASCII karakter sınıflarına geri düşeriz. Production çok dilli tokenleştiriciler için `regex` kur.

Dene:

```python
print(pre_tokenize("Hello, world! Don't stop."))
# [' Hello', ',', ' world', '!', " Don", "'t", ' stop', '.']
```

Önde boşluk kelimeye ekli kalır. Kısaltmalar apostrofta bölünür. Noktalama kendi parçası olur. BPE bu sınırlar arasında token'ları asla merge etmez.

### Adım 3: Byte Sequence'lerinde BPE

Ders 01'den çekirdek algoritma, ama şimdi pre-tokenize edilmiş parçalar üzerinde bağımsız çalışır.

```python
from collections import Counter

def get_byte_pairs(chunks):
    pairs = Counter()
    for chunk in chunks:
        byte_seq = list(chunk.encode("utf-8"))
        for i in range(len(byte_seq) - 1):
            pairs[(byte_seq[i], byte_seq[i + 1])] += 1
    return pairs

def apply_merge(byte_seq, pair, new_id):
    merged = []
    i = 0
    while i < len(byte_seq):
        if i < len(byte_seq) - 1 and byte_seq[i] == pair[0] and byte_seq[i + 1] == pair[1]:
            merged.append(new_id)
            i += 2
        else:
            merged.append(byte_seq[i])
            i += 1
    return merged
```

### Adım 4: Özel Token İşleme

Özel token'lar tam eşleşme ve sabit ID gerektirir. BPE'yi tamamen atlarlar.

```python
class SpecialTokenHandler:
    def __init__(self):
        self.special_tokens = {}
        self.pattern = None

    def add_token(self, token_str, token_id):
        self.special_tokens[token_str] = token_id
        escaped = [re.escape(t) for t in sorted(self.special_tokens.keys(), key=len, reverse=True)]
        self.pattern = re.compile("|".join(escaped))

    def split_with_specials(self, text):
        if not self.pattern:
            return [(text, False)]
        parts = []
        last_end = 0
        for match in self.pattern.finditer(text):
            if match.start() > last_end:
                parts.append((text[last_end:match.start()], False))
            parts.append((match.group(), True))
            last_end = match.end()
        if last_end < len(text):
            parts.append((text[last_end:], False))
        return parts
```

### Adım 5: Tam Tokenleştirici Sınıfı

Her şeyi zincirle: normalize et, özel token'larda böl, pre-tokenize et, BPE merge et, ID'lere eşle.

```python
import unicodedata

class ProductionTokenizer:
    def __init__(self):
        self.merges = {}
        self.vocab = {i: bytes([i]) for i in range(256)}
        self.special_handler = SpecialTokenHandler()
        self.next_id = 256

    def normalize(self, text):
        return unicodedata.normalize("NFKC", text)

    def train(self, text, num_merges):
        text = self.normalize(text)
        chunks = pre_tokenize(text)
        chunk_bytes = [list(chunk.encode("utf-8")) for chunk in chunks]

        for i in range(num_merges):
            pairs = Counter()
            for seq in chunk_bytes:
                for j in range(len(seq) - 1):
                    pairs[(seq[j], seq[j + 1])] += 1
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            new_id = self.next_id
            self.next_id += 1
            self.merges[best] = new_id
            self.vocab[new_id] = self.vocab[best[0]] + self.vocab[best[1]]
            chunk_bytes = [apply_merge(seq, best, new_id) for seq in chunk_bytes]

    def add_special_token(self, token_str):
        token_id = self.next_id
        self.next_id += 1
        self.special_handler.add_token(token_str, token_id)
        self.vocab[token_id] = token_str.encode("utf-8")
        return token_id

    def encode(self, text):
        text = self.normalize(text)
        parts = self.special_handler.split_with_specials(text)
        all_ids = []
        for part_text, is_special in parts:
            if is_special:
                all_ids.append(self.special_handler.special_tokens[part_text])
            else:
                for chunk in pre_tokenize(part_text):
                    byte_seq = list(chunk.encode("utf-8"))
                    for pair, new_id in self.merges.items():
                        byte_seq = apply_merge(byte_seq, pair, new_id)
                    all_ids.extend(byte_seq)
        return all_ids

    def decode(self, ids):
        byte_parts = []
        for token_id in ids:
            if token_id in self.vocab:
                byte_parts.append(self.vocab[token_id])
        return b"".join(byte_parts).decode("utf-8", errors="replace")

    def vocab_size(self):
        return len(self.vocab)
```

### Adım 6: Çok Dilli Test

Gerçek test. İngilizce, Çince, emoji ve kod at.

```python
corpus = (
    "The quick brown fox jumps over the lazy dog. "
    "The quick brown fox runs through the forest. "
    "Machine learning models process natural language. "
    "Deep learning transforms how we build software. "
    "def train(model, data): return model.fit(data) "
    "def predict(model, x): return model(x) "
)

tok = ProductionTokenizer()
tok.train(corpus, num_merges=50)

bos = tok.add_special_token("<|begin|>")
eos = tok.add_special_token("<|end|>")

test_texts = [
    "The quick brown fox.",
    "你好世界",
    "Hello 🌍 World",
    "def foo(x): return x + 1",
    f"<|begin|>Hello<|end|>",
]

for text in test_texts:
    ids = tok.encode(text)
    decoded = tok.decode(ids)
    print(f"Input:   {text}")
    print(f"Token:   {len(ids)} id")
    print(f"Decoded: {decoded}")
    print()
```

Çince karakterler her biri 3 byte üretir. Emoji 4 byte üretir. Bunların hiçbiri tokenleştiriciyi çökertmez. Hiçbiri bilinmeyen token üretmez. Byte-level BPE'in gücü budur.

## Kullan

### Gerçek Tokenleştiricileri Karşılaştırma

Llama 3, GPT-4 ve Mistral'ın gerçek tokenleştiricilerini yükle. Her birinin aynı çok dilli paragrafı nasıl ele aldığını gör.

```python
import tiktoken

gpt4_enc = tiktoken.get_encoding("cl100k_base")

test_paragraph = "Machine learning is powerful. 机器学习很强大。 L'apprentissage automatique est puissant. 🤖💪"

tokens = gpt4_enc.encode(test_paragraph)
pieces = [gpt4_enc.decode([t]) for t in tokens]
print(f"GPT-4 ({len(tokens)} token): {pieces}")
```

```python
from transformers import AutoTokenizer

llama_tok = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
mistral_tok = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")

for name, tok in [("Llama 3", llama_tok), ("Mistral", mistral_tok)]:
    tokens = tok.encode(test_paragraph)
    pieces = tok.convert_ids_to_tokens(tokens)
    print(f"{name} ({len(tokens)} token): {pieces[:20]}...")
```

Aynı metin için farklı token sayıları göreceksin. 128K vocabulary'li Llama 3 yaygın desenleri merge etmede daha agresif. 100K ile GPT-4 ortada oturur. 32K ile Mistral daha fazla token üretir ama daha küçük bir embedding katmanı vardır.

Tradeoff hep aynı: daha büyük vocabulary daha kısa sequence ama daha fazla parametre demek.

## Yayınla

Bu ders production tokenleştirici inşa etme ve debug etme için bir prompt üretir. `outputs/prompt-tokenizer-builder.md`'a bak.

## Alıştırmalar

1. **Kolay:** Herhangi bir token ID'si için ham byte'ları gösteren bir `get_token_bytes(id)` metodu ekle. En yaygın merge edilmiş token'larının aslında neyi temsil ettiğini incele.
2. **Orta:** Whitespace ve rakamlarda bölen ama önde boşlukları koruyan Llama-tarzı pre-tokenizer'ı implement et. Vocabulary'sini aynı corpus üzerinde GPT-2 regex yaklaşımıyla karşılaştır.
3. **Zor:** Bir `{"role": ..., "content": ...}` mesaj listesi alan ve Llama 3 chat formatı için doğru token sequence'ini üreten bir chat template metodu ekle. HuggingFace implementasyonuna karşı test et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| Byte-level BPE | "Byte'lar üzerinde çalışan tokenleştirici" | 256 byte değerlik taban vocabulary ile BPE — bilinmeyen token olmadan herhangi bir input'u halleder |
| Pre-tokenizasyon | "BPE'den önce bölme" | BPE'nin kelime sınırları arasında merge etmesini önleyen regex veya kural-tabanlı bölme |
| NFKC normalizasyonu | "Unicode temizliği" | Canonical decomposition ardından compatibility composition — "fi" ligature "fi" olur, fullwidth "A" "A" olur |
| Chat template | "Mesajların token'a dönüşümü" | role/content mesaj listesini düz token sequence'ine çevirme tam formatı — modele özgü ve eğitim formatına uymalı |
| Özel token'lar | "Kontrol token'ları" | BPE'i atlayan ayrılmış token ID'leri — [BOS], [EOS], [PAD], chat işaretçileri — merge'den önce tam eşleştirilir |
| Fertility | "Kelime başına token" | Output token / input kelime oranı — GPT-4'te İngilizce için 1.3, Korece için 2-3, daha yüksek = daha çok context israfı |
| tiktoken | "OpenAI tokenleştiricisi" | Python binding'leri olan Rust BPE implementasyonu — saf Python'dan 10-100x daha hızlı |
| Merge tablosu | "Vocabulary" | Eğitim sırasında öğrenilen byte-pair merge'lerinin sıralı listesi — bu tokenleştiricinin öğrenilmiş bilgisinin KENDİSİDİR |

## İleri Okuma

- [OpenAI tiktoken source](https://github.com/openai/tiktoken) -- GPT-3.5/4 tarafından kullanılan Rust BPE implementasyonu
- [HuggingFace tokenizers](https://github.com/huggingface/tokenizers) -- BPE, WordPiece, Unigram destekleyen Rust tokenleştirici kütüphanesi
- [Llama 3 paper (Meta, 2024)](https://arxiv.org/abs/2407.21783) -- 128K vocabulary ve tokenleştirici eğitimi hakkında detaylar
- [SentencePiece (Kudo & Richardson, 2018)](https://arxiv.org/abs/1808.06226) -- dil-agnostik tokenleştirme
- [GPT-2 tokenizer source](https://github.com/openai/gpt-2/blob/master/src/encoder.py) -- orijinal byte-to-Unicode eşlemesi
