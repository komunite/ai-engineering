---
name: skill-concept-prompt-designer
description: Kullanıcı söylemlerini bölme, disambiguation ve fallback'lerle iyi formlu SAM 3 concept prompt'larına çevir
version: 1.0.0
phase: 4
lesson: 24
tags: [sam3, open-vocab, prompt-engineering, segmentation]
---

# Concept Prompt Designer

SAM 3'ün accuracy'si concept prompt'unun nasıl ifade edildiğine yoğun şekilde bağlı. Bu skill serbest form kullanıcı söylemlerini SAM 3'ün iyi handle ettiği prompt'lara normalize eder.

## Ne zaman kullan

- Doğal dilli nesne sorguları kabul eden bir UI inşa ederken.
- Üst akış çağıranların cümle gönderdiği bir API üzerinden SAM 3'ü açığa çıkarırken.
- Kötü SAM 3 eşleşmelerini ayıklarken — sık sık prompt bozuk, model değil.

## Girdiler

- `utterance`: ham kullanıcı string'i.
- `context`: opsiyonel domain ipucu (örn. "surveillance", "medical", "retail").
- `max_concepts`: söylem başına çıkarılacak maksimum konsept; varsayılan 5.

## SAM 3'ün tercih ettiği kurallar

- **Cümleler değil, kısa isim öbekleri.** `"cat"` `"there is a cat"`'i yener.
- **Somut isimler.** `"skateboard"` `"thing to ride on"`'ı yener.
- **Modifier'lar ismin hemen öncesinde.** `"red car"` `"car that is red"`'ı yener.
- **Küçük harf.** SAM 3 sağlam ama empirik olarak küçük harf girdilerde biraz daha iyi.
- **Tekil ya da çoğul.** İkisi de çalışır; birden çok instance bekleniyorsa çoğul yardımcı olur.

## Adımlar

1. **Yaygın ayırıcılarla tokenize et** — virgül, noktalı virgül, "and", "or", "&".
2. **Filler ön ekleri düşür** — "find", "show me", "segment", "detect", "locate", "a", "an", "the".
3. **Prepositional modifier'ları yalnızca görsel** ise tut — `"striped red umbrella"` evet, `"umbrella from yesterday"` hayır (`"from yesterday"` görüntüde değil).
4. Opsiyonel `context` kullanarak **çakışmaları çöz**:
   - surveillance bağlamında `"window"` -> `"building window"`.
   - medical bağlamında `"window"` -> genellikle hata; kullanıcının netleştirmesini öner.
5. Bölme sıfır konsept üretiyorsa **ve** söylem en az bir somut isim içeriyorsa tam string'e **fallback**. Hiçbir somut isim çıkarılamıyorsa, konsept çıkarma — sadece uyarılar döndür ve kullanıcıdan netleştirme iste (bkz. Kurallar).
6. **`max_concepts`'te kap.** İstenenden fazla konsept çıkarıldıysa, söylem sırasına göre ilk `max_concepts`'i tut ve geri kalanı `dropped`'a `"exceeded max_concepts"` nedeniyle ekle. Bu, kullanıcı uzun bir enumeration yapıştırdığında latency'yi sınırlı tutar.

## Çıktı formatı

```
[designed prompts]
  utterance:    <original>
  concepts:     ["concept_1", "concept_2", ...]
  dropped:      ["filler_1", ...]
  warnings:     ["concept too abstract", "may match many classes", ...]

[sam3 calls]
  Her konsept için çalıştır: sam3.detect(image, concept)
  Çıktıları tespit başına farklı konsept etiketleriyle merge et.
```

## Örnekler

```
in:  "can you find me a cat or two dogs?"
out: ["cat", "dogs"]
dropped: ["can you find me", "a", "or two", "?"]
note: "dogs" çoğul tutuldu çünkü söylem "two dogs" diyor — çoğul ipucu korundu.

in:  "segment the big red truck and the blue sedan"
out: ["big red truck", "blue sedan"]
dropped: ["segment", "the", "and"]

in:  "thing near the door"
out: ["door"]
warnings: ["'thing' SAM 3 için fazla soyut; 'door'a düşürüldü"]

in:  "striped red umbrella, green hat, pink balloon"
out: ["striped red umbrella", "green hat", "pink balloon"]
```

## Kurallar

- 8 kelimeden uzun cümleleri SAM 3'e asla geçirme — bunun üstünde accuracy düşer.
- Bir söylem çıkarılabilir somut isim içermiyorsa, SAM 3'ü çalıştırma; uyarıları döndür ve netleştirme iste.
- Tırnak içindeki noktalama üzerinde bölme; `"black and white cat"` tırnaklıysa tek konsept olarak koru.
- Production debug için orijinal söylemi ve türetilen konseptleri her zaman logla.
