# Makine Çevirisi

> Çeviri, otuz yıl boyunca NLP araştırmasını finanse eden ve şimdi de finanse etmeye devam eden görevdir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 5 · 10 (Attention Mekanizması), Faz 5 · 04 (GloVe, FastText, Subword)
**Süre:** ~75 dakika

## Sorun

Bir model bir dilde bir cümleyi okur ve başka bir dilde bir cümle üretir. Uzunluk değişir. Kelime sırası değişir. Bazı kaynak kelimeler birden fazla hedef kelimeye eşlenir ve tersi. Deyimler bire-bir eşlemeyi reddeder. Fransızca'da "I miss you" "tu me manques"tir — kelimesi kelimesine "sen bana eksiksin". Hiçbir kelime seviyesi hizalama bunu kurtaramaz.

Makine çevirisi NLP'yi encoder-decoder'ları, attention'ı, transformer'ları ve nihayetinde tüm LLM paradigmasını icat etmeye zorlayan görevdir. Her ileri adım, çeviri kalitesi ölçülebilir olduğu ve insan ile makine arasındaki açık inatçı olduğu için geldi.

Bu ders tarih dersini atlar ve 2026'nın çalışan pipeline'ını öğretir: önceden eğitilmiş çok dilli encoder-decoder (NLLB-200 ya da mBART), subword tokenleştirme, beam search, BLEU ve chrF değerlendirme ve hâlâ yakalanmadan üretime giden bir avuç başarısızlık modu.

## Kavram

![MT pipeline: tokenize → encode → attention ile decode → detokenize](../assets/mt-pipeline.svg)

Modern MT, paralel metin üzerinde eğitilmiş bir transformer encoder-decoder'dır. Encoder kaynağı kendi dilinin tokenleştirmesinde okur. Decoder hedefi, encoder'ın çıktısını cross-attention (ders 10) yoluyla kullanarak teker teker subword üretir. Decoding, greedy-decoding tuzağından kaçınmak için beam search kullanır. Çıktı detokenize edilir, detruecase edilir ve bir referansa karşı puanlanır.

Üç operasyonel seçim gerçek dünya MT kalitesini yönlendirir.

- **Tokenizer.** Karışık dilli bir corpus üzerinde eğitilmiş SentencePiece BPE. Diller arası paylaşılan vocabulary, NLLB'de zero-shot çiftleri mümkün kılan şeydir.
- **Model boyutu.** NLLB-200 distilled 600M bir laptop'a sığar. NLLB-200 3.3B yayınlanmış üretim varsayılanıdır. 54.5B araştırma tavanıdır.
- **Decoding.** Genel içerik için beam genişliği 4-5. Çok kısa çıktıdan kaçınmak için uzunluk cezası. Terminoloji tutarlılığına ihtiyaç duyduğunda kısıtlı decoding.

## İnşa Et

### Adım 1: önceden eğitilmiş bir MT çağrısı

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_id = "facebook/nllb-200-distilled-600M"
tok = AutoTokenizer.from_pretrained(model_id, src_lang="eng_Latn")
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

src = "The cats are running."
inputs = tok(src, return_tensors="pt")

out = model.generate(
    **inputs,
    forced_bos_token_id=tok.convert_tokens_to_ids("fra_Latn"),
    num_beams=5,
    length_penalty=1.0,
    max_new_tokens=64,
)
print(tok.batch_decode(out, skip_special_tokens=True)[0])
```

```text
Les chats courent.
```

Burada üç şey önemli. `src_lang`, tokenleştiriciye hangi script'i ve segmentasyonu uygulayacağını söyler. `forced_bos_token_id`, decoder'a hangi dili üreteceğini söyler. Her ikisi de NLLB'ye özgü numaralardır; mBART ve M2M-100 kendi konvansiyonlarını kullanır ve değiştirilemezler.

### Adım 2: BLEU ve chrF

BLEU, çıktı ve referans arasındaki n-gram örtüşmesini ölçer. Dört referans n-gram boyutu (1-4), precision'ların geometrik ortalaması, çok kısa çıktı için brevity penalty. Skor [0, 100] aralığındadır. Yaygın kullanılır. Yorumlanması can sıkıcıdır: 30 BLEU "kullanılabilir"; 40 "iyi"; 50 "olağanüstü"; 1 BLEU altındaki farklar gürültüdür.

chrF karakter seviyesi F-skoru ölçer. BLEU'nun eşleşmeleri eksik saydığı morfolojik olarak zengin dillere daha duyarlıdır. Sıklıkla BLEU'nun yanında raporlanır.

```python
import sacrebleu

hypotheses = ["Les chats courent."]
references = [["Les chats courent."]]

bleu = sacrebleu.corpus_bleu(hypotheses, references)
chrf = sacrebleu.corpus_chrf(hypotheses, references)
print(f"BLEU: {bleu.score:.1f}  chrF: {chrf.score:.1f}")
```

Her zaman `sacrebleu` kullan. Tokenleştirmeyi normalleştirir, böylece skorlar makaleler arasında karşılaştırılabilir. Kendi BLEU hesaplamanı yapmak, yanıltıcı benchmark'ların oluşma yoludur.

### Üç katmanlı değerlendirme hiyerarşisi (2026)

Modern MT değerlendirmesi üç tamamlayıcı metrik ailesi kullanır. En az ikisiyle gönder.

- **Heuristic** (BLEU, chrF). Hızlı, referans tabanlı, yorumlanabilir, paraphrase'e duyarsız. Eski karşılaştırma ve regresyon tespiti için kullan.
- **Öğrenilmiş** (COMET, BLEURT, BERTScore). İnsan yargısı üzerinde eğitilmiş sinirsel modeller; çevirinin kaynak ve referansa semantik benzerliğini karşılaştır. COMET, 2023'ten beri MT araştırmasıyla en yüksek ilişkilendirmeye sahiptir ve kalitenin önemli olduğu yerlerde 2026 üretim varsayılanıdır.
- **LLM-as-judge** (referanssız). Büyük bir modelden çevirileri akıcılık, yeterlilik, ton, kültürel uygunluk açısından puanlamasını iste. Rubric iyi tasarlandığında GPT-4-as-judge, insan anlaşmasıyla ~%80 oranında eşleşir. Referansın olmadığı açık uçlu içerik için kullan.

Pratik 2026 stack'i: BLEU ve chrF için `sacrebleu`, COMET için `unbabel-comet` ve nihai insan-yönelimli sinyal için bir prompt'lu LLM. Üretim verisinde güvenmeden önce her metriği 50-100 insan etiketli örneğe karşı kalibre et.

Referanssız metrikler (COMET-QE, BLEURT-QE, LLM-as-judge), referans çevirisi olmayan uzun kuyruk dil çiftleri için önemli olan, referanssız çeviri değerlendirmesi yapmana izin verir.

### Adım 3: üretimde ne bozulur

Yukarıdaki çalışan pipeline %80 oranında akıcı çeviri yapacak ve kalan %20'de sessizce başarısız olacaktır. Adı verilen başarısızlık modları:

- **Hallucination.** Model kaynakta olmayan içerik icat eder. Tanıdık olmayan alan vocabulary'sinde yaygındır. Semptom: çıktı akıcıdır ama kaynağın söylemediği gerçekleri iddia eder. Azaltım: alan terimleri üzerinde kısıtlı decoding, regule edilmiş içerikte insan incelemesi, girdiden çok daha uzun çıktı için izleme.
- **Off-target üretim.** Model yanlış dile çevirir. NLLB nadir dil çiftlerinde şaşırtıcı derecede buna eğilimlidir. Azaltım: `forced_bos_token_id`'yi doğrula ve her zaman çıktıda bir dil-ID model kontrolü ile decode et.
- **Terminoloji kayması.** "Sign up", doc 1'de "s'inscrire" ve doc 2'de "créer un compte" olur. UI metni ve kullanıcı yönelimli string'ler için, tutarlılık ham kaliteden daha önemlidir. Azaltım: sözlük kısıtlı decoding ya da post-edit sözlüğü.
- **Formality uyumsuzluğu.** Fransızca "tu" vs "vous", Japonca nezaket seviyeleri. Model eğitimde hangi form daha yaygınsa onu seçer. Müşteri yönelimli içerik için bu genellikle yanlıştır. Azaltım: model destekliyorsa bir formality token'ı ile prompt prefix, ya da yalnızca-formal corpus üzerinde küçük bir modeli fine-tune et.
- **Kısa girdide uzunluk patlaması.** Çok kısa girdi cümleleri sıklıkla aşırı uzun çeviriler üretir çünkü length penalty ~5 kaynak token altında uçurumdan düşer. Azaltım: kaynak uzunluğuyla orantılı sert max-length sınırı.

### Adım 4: bir alan için fine-tuning

Önceden eğitilmiş modeller generalist'tir. Hukuki, tıbbi ya da oyun-diyalog çevirisi alan paralel verisi üzerinde fine-tuning'den ölçülebilir biçimde fayda görür. Tarif egzotik değildir:

```python
from transformers import Trainer, TrainingArguments
from datasets import Dataset

pairs = [
    {"src": "The defendant pleaded guilty.", "tgt": "L'accusé a plaidé coupable."},
]

ds = Dataset.from_list(pairs)


def preprocess(ex):
    return tok(
        ex["src"],
        text_target=ex["tgt"],
        truncation=True,
        max_length=128,
        padding="max_length",
    )


ds = ds.map(preprocess, remove_columns=["src", "tgt"])

args = TrainingArguments(output_dir="out", per_device_train_batch_size=4, num_train_epochs=3, learning_rate=3e-5)
Trainer(model=model, args=args, train_dataset=ds).train()
```

Birkaç bin yüksek kaliteli paralel örnek, birkaç yüz bin gürültülü web-kazınmış olanı yener. Eğitim verisinin kalitesi tek başına en büyük üretim koludur.

## Kullan

MT için 2026 üretim stack'i:

| Kullanım durumu | Önerilen başlangıç noktası |
|---------|---------------------------|
| Any-to-any, 200 dil | `facebook/nllb-200-distilled-600M` (laptop) ya da `nllb-200-3.3B` (üretim) |
| English-merkezli, yüksek kalite, 50 dil | `facebook/mbart-large-50-many-to-many-mmt` |
| Kısa koşular, ucuz çıkarım, İngilizce-Fransızca/Almanca/İspanyolca | Helsinki-NLP / Marian modelleri |
| Latency-kritik browser-side | ONNX-kuantize Marian (~50 MB) |
| Maksimum kalite, ödemeye razı | Çeviri prompt'larıyla GPT-4 / Claude / Gemini |

LLM'ler 2026 itibarıyla birkaç dil çiftinde özelleşmiş MT modellerini geçiyor, özellikle deyimsel içerik ve uzun bağlamda. Tradeoff, token başına maliyet ve latency. Bağlam uzunluğu, stilistik tutarlılık ya da prompting yoluyla alan adaptasyonu throughput'tan daha önemliyse bir LLM seç.

## Yayınla

`outputs/skill-mt-evaluator.md` olarak kaydet:

```markdown
---
name: mt-evaluator
description: Evaluate a machine translation output for shipping.
version: 1.0.0
phase: 5
lesson: 11
tags: [nlp, translation, evaluation]
---

Given a source text and a candidate translation, output:

1. Automatic score estimate. BLEU and chrF ranges you would expect. State whether a reference is available.
2. Five-point human-verifiable check list: (a) content preservation (no hallucinations), (b) correct language, (c) register / formality match, (d) terminology consistency with glossary if provided, (e) no truncation or length explosion.
3. One domain-specific issue to probe. E.g., for legal: named entities and statute citations. For medical: drug names and dosages. For UI: placeholder variables `{name}`.
4. Confidence flag. "Ship" / "Ship with review" / "Do not ship". Tie to the severity of issues found in step 2.

Refuse to ship a translation without a language-ID check on output. Refuse to evaluate without a reference unless the user explicitly opts in to reference-free scoring (COMET-QE, BLEURT-QE). Flag any content over 1000 tokens as likely needing chunked translation.
```

## Alıştırmalar

1. **Kolay.** `nllb-200-distilled-600M` kullanarak 5 cümlelik bir İngilizce paragrafı Fransızca'ya ve tekrar İngilizce'ye çevir. Gidiş-dönüşün orijinale ne kadar yakın olduğunu ölç. Kelime seçimi kaymasıyla semantik koruma görmelisin.
2. **Orta.** `fasttext lid.176` ya da `langdetect` kullanarak çeviri çıktıları üzerinde bir dil-ID kontrolü uygula. MT çağrısına entegre et, böylece off-target üretimler dönmeden önce yakalanır.
3. **Zor.** `nllb-200-distilled-600M`'ı kendi seçtiğin 5,000-çiftlik bir alan corpus'unda fine-tune et. Fine-tuning öncesi ve sonrası held-out sette BLEU ölç. Hangi tip cümlelerin iyileştiğini ve hangilerinin gerilediğini raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| BLEU | Çeviri skoru | Brevity penalty ile N-gram precision. [0, 100]. |
| chrF | Karakter F-skoru | Karakter seviyesi F-skoru. Morfolojik olarak zengin diller için daha duyarlı. |
| NMT | Sinirsel MT | Paralel metin üzerinde eğitilmiş transformer encoder-decoder. 2017+ varsayılanı. |
| NLLB | No Language Left Behind | Meta'nın 200 dilli MT model ailesi. |
| Kısıtlı decoding | Kontrollü çıktı | Çıktıda belirli token'ların ya da n-gram'ların geçmesini / geçmemesini zorla. |
| Hallucination | İcat edilmiş içerik | Kaynak tarafından desteklenmeyen model çıktısı. |

## İleri Okuma

- [Costa-jussà et al. (2022). No Language Left Behind: Scaling Human-Centered Machine Translation](https://arxiv.org/abs/2207.04672) — NLLB makalesi.
- [Post (2018). A Call for Clarity in Reporting BLEU Scores](https://aclanthology.org/W18-6319/) — BLEU skorlarını raporlamanın neden tek doğru yolu `sacrebleu` olduğu.
- [Popović (2015). chrF: character n-gram F-score for automatic MT evaluation](https://aclanthology.org/W15-3049/) — chrF makalesi.
- [Hugging Face MT guide](https://huggingface.co/docs/transformers/tasks/translation) — pratik fine-tuning gezintisi.
