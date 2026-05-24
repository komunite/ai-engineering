---
name: skill-fine-tuning-guide
description: LoRA ve QLoRA ile LLM'leri ne zaman ve nasıl fine-tune edeceğine dair karar ağacı
version: 1.0.0
phase: 11
lesson: 8
tags: [fine-tuning, lora, qlora, peft, llm-engineering]
---

# Fine-Tuning Karar Kılavuzu

Fine-tuning'den önce şunları sırayla dene:

```
1. Prompt engineering (dakikalar, $0)
2. Prompt içinde few-shot örnekleri (dakikalar, $0)
3. Bilgi retrieval'ı için RAG (günler, $10-100/ay)
4. LoRA/QLoRA ile fine-tuning (günler, deney başına $5-50)
5. Full fine-tuning (haftalar, çalışma başına $100-10.000)
```

Sadece bir önceki adım ölçülebilir şekilde yetersizse bir sonraki adıma geç.

## Ne zaman fine-tune et

- Model, prompt'lamanın başaramadığı tutarlı bir çıktı stili veya formatına ihtiyaç duyuyor
- Daha büyük bir modeli damıtıyorsun (8B modelden GPT-4 kalitesi)
- Gecikme önemli ve few-shot örnekleri çok fazla token ekliyor
- Modelin karmaşık bir muhakeme pattern'ini güvenilir şekilde takip etmesi gerekiyor
- İstenen input-output davranışından 1.000+ yüksek kaliteli örneğin var

## Ne zaman fine-tune ETME

- Model, doğru prompt ile istediğini zaten yapıyor
- Modelin gerçekleri bilmesi gerekiyor (yerine RAG kullan)
- 500'den az eğitim örneğin var (overfitting muhtemel)
- Görev sık değişiyor (yeniden eğitim pahalı)
- Belirli bir çıktıyı hangi verinin etkilediğini denetlemen gerekiyor (fine-tuning bir kara kutudur)

## Yöntem seçimi

| GPU VRAM | 7B model | 13B model | 70B model |
|----------|----------|-----------|-----------|
| 16GB (T4) | QLoRA | Uygulanabilir değil | Uygulanabilir değil |
| 24GB (3090/4090) | QLoRA veya LoRA | QLoRA | Uygulanabilir değil |
| 40GB (A100) | LoRA veya Full | QLoRA veya LoRA | QLoRA |
| 80GB (A100/H100) | Full | LoRA veya Full | QLoRA veya LoRA |

## LoRA konfigürasyon checklist

1. r=16, alpha=32 ile başla (çoğu görev için güvenli varsayılan)
2. Önce q_proj ve v_proj'u hedefle (minimum geçerli LoRA)
3. QLoRA için learning rate 2e-4, LoRA fp16 için 5e-5 kullan
4. lora_dropout=0.05 ayarla
5. 1-3 epoch eğit (daha fazlası overfitting riski)
6. Held-out set üzerinde her 100 adımda değerlendir
7. Checkpoint'leri sakla ve en iyiyi eval loss'a göre seç

## Sık yapılan hatalar

- Çok fazla epoch için eğitmek (küçük veri setlerinde epoch 2-3'ten sonra overfitting)
- Full fine-tuning ile aynı learning rate'i kullanmak (LoRA daha yüksek LR'ye ihtiyaç duyar)
- Pad token'ı ayarlamayı unutmak (Llama modelleriyle NaN loss'a neden olur)
- Base modeli dondurmamak (LoRA'nın amacını boşa çıkarır)
- Sadece eğitim verisinde değerlendirmek (her zaman değerlendirme için %10-20 ayır)
- Prompt engineering baseline'ını atlamak (prompt'lamanın zaten çözdüğü problemi fine-tune etmek)

## Kalite doğrulaması

Eğitimden sonra 200+ held-out örnekte karşılaştır:
1. En iyi prompt'la base model (baseline)
2. LoRA adapter ile base model (fine-tune edilmiş modelin)
3. Aynı prompt'la GPT-4 veya Claude (tavan)

LoRA modeli prompt'lu baseline'ı yenmiyorsa, daha çok compute değil, eğitim verisi veya konfigürasyon iyileştirilmesi gerekiyor.

## Adapter yönetimi

- Multi-task serving için adapter'ları ayrı tut (istek başına adapter değiştir)
- Tek görev deployment için adapter'ları base ağırlıklara birleştir
- Adapter'ları Hugging Face Hub'da sakla (10-100MB, versiyonlama ve paylaşımı kolay)
- Deploy etmeden önce birleştirilmiş model çıktılarının birleştirilmemişle eşleştiğini test et
- Birden fazla adapter'ı bir araya getirmek için TIES-Merging veya DARE kullan

## Eğitim hata ayıklama

Loss düşmüyorsa:
1. Learning rate'i kontrol et (LoRA için çok düşük, 2e-4 dene)
2. LoRA katmanlarının gerçekten gradyan aldığını doğrula
3. Base model ağırlıklarının dondurulduğunu teyit et
4. Veri formatını kontrol et (tokenizer modelin beklediği formatla eşleşmeli)

Loss düşüyor ama eval kalitesi kötüyse:
1. Eğitim verisi kalite sorunu (çöp girer, çöp çıkar)
2. Overfitting (epoch'u azalt, dropout'u artır, daha çok veri ekle)
3. Yanlış target modüller (karmaşık görevler için MLP katmanları ekle)
4. Rank çok düşük (r=32 veya r=64 dene)
