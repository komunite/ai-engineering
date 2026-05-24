---
name: prompt-sft-data-curator
description: SFT için talimat veri setleri tasarla ve küratörlüğünü yap
version: 1.0.0
phase: 10
lesson: 6
tags: [sft, instruction-tuning, fine-tuning, data-curation, alignment]
---

# SFT Veri Küratörü

Spesifik bir yetenek (kod üretimi, matematik, sohbet, güvenlik) için instruction-tuning veri seti tasarlarken, veri toplama planlamak, kalite kriterleri tanımlamak ve eğitim pipeline'ını yapılandırmak için bu çerçeveyi kullan.

## Girdi Gereksinimleri

Şunu sağla:
- **Hedef yetenek** (örn. "Python kod üretimi", "tıbbi Q&A", "çok-turlu sohbet")
- **Base model** (örn. Llama 3 8B, Mistral 7B, Qwen 2.5 72B)
- **Bütçe** (annotation saati, sentetik üretim için API maliyetleri)
- **Format tercihi** (Alpaca, ShareGPT, ChatML)

## Adım 1: Veri Seti Tasarımı

### Boyut Yönergeleri

| Kalite Seviyesi | Gerekli Örnek | Beklenen Sonuç |
|--------------|----------------|------------------|
| Araştırma prototipi | 1,000-5,000 | LIMA kalitesi: örnekler uzman yazımıysa daha büyük veri setleriyle karşılaştırılabilir |
| Üretim v1 | 10,000-50,000 | Stanford Alpaca seviyesi: yaygın görevlerde sağlam talimat takibi |
| Üretim v2 | 50,000-200,000 | Vicuna/Llama 2 Chat seviyesi: sağlam çok-turlu, domain kapsama |

Kalite her zaman miktarı yener. 1000 uzman yazımı örnek (LIMA, Mayıs 2023) 50000+ örnek üzerinde eğitilen modellerle eşleşti. Öncelik ver:

1. **Çeşitlilik** -- hedef yeteneklerin tüm yelpazesini kapsa
2. **Doğruluk** -- her yanıt faktüel olarak doğru olmalı
3. **Açıklık** -- yanıtlar özlü ve iyi yapılandırılmış olmalı
4. **Zorluk gradyanı** -- kolay, orta ve zor örnekleri dahil et

### Çeşitlilik Kontrol Listesi

Genel amaçlı bir asistan için:
- Açık uçlu sorular (%20)
- Faktüel Q&A (%20)
- Yaratıcı yazım (%10)
- Kod üretimi (%15)
- Reasoning ve matematik (%15)
- Özetleme (%10)
- Kısıtlamalarla talimat takibi (%10)

Domain'e özgü modeller için yüzdeleri ayarla. Bir kodlama asistanı %60'ı kod üretimine, %20'yi kod açıklamasına ayırabilir.

## Adım 2: Veri Formatı

### Alpaca Formatı (single-turn)

```json
{
  "instruction": "Write a function that reverses a string in Python.",
  "input": "",
  "output": "def reverse_string(s):\n    return s[::-1]"
}
```

Ne zaman kullanılır: tek-turlu görevler, basit instruction-response çiftleri, hızlı prototipleme.

### ShareGPT Formatı (multi-turn)

```json
{
  "conversations": [
    {"from": "system", "value": "You are a Python expert."},
    {"from": "human", "value": "How do I reverse a string?"},
    {"from": "gpt", "value": "Use slicing: s[::-1]"},
    {"from": "human", "value": "What about for a list?"},
    {"from": "gpt", "value": "Same syntax works: my_list[::-1]"}
  ]
}
```

Ne zaman kullanılır: konuşmaya dayalı uygulamalar, çok-turlu context önemli olduğunda.

### ChatML Formatı (özel token'larla)

```
<|im_start|>system
You are a Python expert.<|im_end|>
<|im_start|>user
How do I reverse a string?<|im_end|>
<|im_start|>assistant
Use slicing: s[::-1]<|im_end|>
```

Ne zaman kullanılır: ChatML'yi native olarak kullanan modelleri hedeflerken (Qwen, Yi).

## Adım 3: Kalite Kriterleri

### Örnek Başına Kontroller

1. **Yanıt alaka düzeyi**: Yanıt gerçekten talimatı cevaplıyor mu?
2. **Faktüel doğruluk**: Tüm iddialar doğrulanabilir ve doğru mu?
3. **Bütünlük**: Yanıt talimatı tam olarak ele alıyor mu?
4. **Özlülük**: Aynı bilgi daha az kelime ile aktarılabilir mi?
5. **Format tutarlılığı**: Yanıt beklenen tarza uyuyor mu?

### Kırmızı Bayraklar (örneği reddet)

- Yanıt kendisiyle çelişiyor
- Yanıt zararlı içerik içeriyor reddetmeden
- Yanıt gerçekleri veya alıntıları halüsinasyon yapıyor
- Talimat belirsiz ve yanıt netleştirmiyor
- Yanıt talimatın yeniden ifade edilmiş kopyası

### Veri Seti Seviyesi Kontroller

- Tek bir kaynak/template'ten örneklerin %5'inden fazlası yok
- Yanıt token'larının en az %80'i anlamlı (dolgu değil)
- Ortalama yanıt uzunluğu 50-200 token (çok kısa veya çok uzun olmaktan kaçın)
- System prompt çeşitliliği: en az 10 farklı system prompt temsil edildi

## Adım 4: Eğitim Konfigürasyonu

| Parametre | Önerilen Aralık | Notlar |
|-----------|------------------|-------|
| Learning rate | 1e-5 - 5e-5 | Büyük modeller için düşük (70B için 1e-5, 7B için 5e-5) |
| Epoch | 1-3 | Validation loss'u izle, ilk artış belirtisinde dur |
| Batch boyutu | 32-128 | GPU sınırlıysa gradient accumulation ile ölçeklendir |
| Warmup | adımların %0-5'i | Pretraining'den daha az kritik |
| Weight decay | 0.0-0.1 | Kısa fine-tuning koşuları için opsiyonel |
| Loss maskeleme | Yalnızca response token'ları | Instruction ve system prompt token'larını maskele |
| Pretraining veri karışımı | %2-5 | Catastrophic forgetting'i önlemek için ham metin karıştır |

## Adım 5: Değerlendirme Protokolü

Eğitimden sonra şunlar üzerinde değerlendir:

1. **Talimat takibi oranı**: Modelin alakalı, tam yanıt ürettiği test promptlarının yüzdesi
2. **Forgetting skoru**: Tutulan genel metin corpus'unda base modele kıyasla perplexity
3. **Format uyumu**: Beklenen chat formatını takip eden yanıtların yüzdesi
4. **MT-Bench veya AlpacaEval**: Instruction-tuned modeller için standart benchmark'lar
5. **Domain'e özgü değerlendirme**: Hedef yeteneğin için özel değerlendirme

### Uyarı İşaretleri

- Epoch 1'den sonra validation loss artıyor: overfitting var, epoch'u azalt veya veriyi artır
- Forgetting skoru > %15 artıyor: learning rate fazla yüksek veya fazla epoch
- Model eğitim örneklerini birebir üretiyor: ciddi overfitting, daha çeşitli veri gerekir
- Model zararsız talimatları reddediyor: güvenlik verisi üzerinde aşırı eğitilmiş, veri setini dengele
