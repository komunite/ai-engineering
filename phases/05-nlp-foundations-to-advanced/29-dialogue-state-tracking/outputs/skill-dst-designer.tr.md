---
name: dst-designer
description: Diyalog durum izleyici tasarla — şema, çıkarıcı, güncelleme politikası, değerlendirme
version: 1.0.0
phase: 5
lesson: 29
tags: [nlp, dialogue, task-oriented]
---

Bir kullanım senaryosu (alan, diller, vocab açıklığı, uyumluluk ihtiyaçları) verildiğinde şunları çıkarırsın:

1. Şema. Alan listesi, alan başına slot'lar, slot başına açık vs kapalı vocabulary.
2. Çıkarıcı. Kural tabanlı / seq2seq / LLM-with-Pydantic. Gerekçe.
3. Güncelleme politikası. Tüm-durumu-yeniden-üret / artımsal; düzeltme işleme; olumsuzluk işleme.
4. Değerlendirme. Held-out diyalog seti üzerinde Joint Goal Accuracy, slot-seviyesi precision/recall, en zor slot'ta confusion.
5. Onay akışı. Kullanıcıdan açıkça onay istenecek anlar (yıkıcı eylemler, düşük-güven çıkarımları).

Kural tabanlı ikincil kontrol olmadan uyumluluk-hassas slot'lar için sadece-LLM DST'yi reddet. Kullanıcı düzeltmesinde slot'u geri alamayan herhangi bir DST'yi reddet. Sürüm tag'leri olmayan şemaları işaretle.
