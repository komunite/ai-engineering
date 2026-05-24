---
name: text-encoder-picker
description: Verilen bir kısıt kümesi için metin encoder mimarisi seç
phase: 5
lesson: 08
---

Kısıtlar (görev, veri hacmi, gecikme bütçesi, deploy hedefi, hesaplama bütçesi) verildiğinde şunları çıkar:

1. Encoder mimarisi: TextCNN, BiLSTM, BiLSTM-CRF, transformer fine-tune ya da "donmuş encoder olarak pretrained transformer + küçük başlık".
2. Embedding girdisi: random init, donmuş GloVe ya da fastText veya bağlamsallaştırılmış transformer embeddings.
3. 5 satırlık eğitim tarifi: optimizer, learning rate, batch size, epoch sayısı, regularization.
4. Bir izleme sinyali. RNN/CNN modeller: uzun-bağımlılık başarısızlıkları için dizi-uzunluğu başına doğruluğu kontrol et. Transformer fine-tune'lar: LR çok yüksekse fine-tune çöküşünü izle; ilk 100 adımda train loss'a bak.

Kullanıcının ~500'den az etiketli örneği varsa TextCNN / BiLSTM baseline'ın platoya çıktığını göstermeden transformer fine-tune önermeyi reddet. Edge deploy'u (telefon, mikrokontrolcü, tarayıcı) her şeyden önce mimari kararı gerektirdiği şeklinde işaretle.
