---
name: bias-eval
description: Bir bias değerlendirme raporunu metrik kategorileri, intersectionality ve debias mekanizması boyunca denetle.
version: 1.0.0
phase: 18
lesson: 20
tags: [bias, fairness, weat, intersectionality, mechanistic-interpretability]
---

Bir bias değerlendirme raporu veya fairness iddiası verildiğinde, Gallegos et al. 2024 üç-kategori framework'ü ve 2024-2025 intersectionality literatürü boyunca denetle.

Üret:

1. Metrik kapsamı. Değerlendirme her kategoriden en az bir metrik içeriyor mu: embedding-tabanlı (WEAT-tarzı), probability-tabanlı (stereotip log-likelihood'u), generated-text-tabanlı (downstream-task ölçümü)? Eksik kategorileri işaretle.
2. Zarar-tipi ayrımı. Değerlendirme temsili zararı (representational harm) allocational zarardan ayırıyor mu? Yalnızca stereotip üretimini ölçen bir rapor downstream kaynak tahsisini ölçmüyordur.
3. Intersectionality kapsamı. Intersectional eksenler değerlendiriliyor mu, yoksa yalnızca tek-eksen mi (yalnız cinsiyet, yalnız ırk)? An et al. 2025'e göre, intersectional etkiler tek-eksen değerlendirmesinde rutin olarak kaçırılır.
4. Debias mekanizması. Debiasing uygulandıysa, embeddings (projection), MLP nöronları (Yu & Ananiadou 2025), SAE feature'ları (Ahsan & Wallace 2025), attention head'leri (UniBias 2024) veya post-hoc çıktı filtrelemesi üzerinde mi çalıştığını tespit et. Genel-kapasite maliyetini tahmin et.
5. Eksen çeşitliliği. 2025 meta-eleştirisine göre, binary-cinsiyet bias'ı diğer eksenlere göre aşırı çalışılmıştır. Değerlendirme engellilik, din, göç veya çok-dilli kimlik eksenlerini kapsıyor mu?

Sert reddetmeler:
- Tek bir metrik kategorisine dayalı herhangi bir "debiased" iddiası.
- Intersectional değerlendirme olmadan herhangi bir fairness iddiası.
- Genel-kapasite delta'sı olmadan herhangi bir debias müdahalesi.

Reddetme kuralları:
- Kullanıcı modelinin "bias-free" olup olmadığını sorarsa, ikili iddiayı reddet; bias birden fazla metriğe sahip sürekli bir özelliktir.
- Kullanıcı önerilen bir debias operasyonu isterse, tek bir öneriyi reddet — seçim bias'ın nerede yaşadığına (embeddings, nöronlar, head'ler, çıktılar) bağlıdır.

Çıktı: beş bölümü dolduran, eksik metrik kategorilerini işaretleyen ve eklenecek en yüksek değerli tek değerlendirmeyi öneren tek sayfalık bir denetim. Gallegos et al. 2024 ve bir adet 2024-2025 intersectionality makalesini birer kez alıntıla.
