---
name: ner-picker
description: Verilen bir çıkarım görevi için doğru NER yaklaşımını seç
version: 1.0.0
phase: 5
lesson: 06
tags: [nlp, ner, extraction]
---

Bir görev tanımı (alan, etiket kümesi, dil, gecikme, veri hacmi) verildiğinde şunları çıkar:

1. Yaklaşım. Kural tabanlı + gazetteer, CRF, BiLSTM-CRF ya da transformer fine-tune.
2. Başlangıç modeli. Adlandır (`en_core_web_sm` / `en_core_web_trf` gibi spaCy model ID'leri, `dslim/bert-base-NER` gibi Hugging Face checkpoint ID'leri ya da "özel, sıfırdan eğitilmiş").
3. Etiketleme stratejisi. BIO, BILOU ya da span-bazlı. Tek cümleyle gerekçelendir.
4. Değerlendirme. `seqeval` kullan. Daima entity-level F1 raporla, asla token-level değil.

500'den az etiketli örnekte transformer fine-tune önermeyi reddet — kullanıcının zaten pretrained alan modeli (örn. tıbbi için BioBERT) yoksa. İç içe geçmiş entity'leri span-bazlı ya da çok-geçişli modeller gerektirdiği şeklinde işaretle. Kullanıcı kutudan-çıkmış CoNLL-2003 etiketleri kullanırken "üretim ölçeği" derse gazetteer denetimi şart koş.
