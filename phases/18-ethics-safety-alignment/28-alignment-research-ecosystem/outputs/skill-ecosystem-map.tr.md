---
name: ecosystem-map
description: Bir alignment iddiasını veya değerlendirmesini organizasyon, metodoloji ve çapraz-kontrollerle haritala.
version: 1.0.0
phase: 18
lesson: 28
tags: [mats, redwood, apollo, metr, eleos, ecosystem]
---

Bir alignment iddiası veya değerlendirmesi verildiğinde, kaynağı araştırma ekosistemine haritala ve çapraz-kontrolleri tespit et.

Üret:

1. Kaynak tanımlaması. İddiayı hangi organizasyon üretti (lab, MATS, Redwood, Apollo, METR, Eleos, akademik lab)?
2. Metodolojik tarz. Çalışma organizasyonun belgelenmiş tarzına uyuyor mu — Redwood control protokolleri, Apollo üç-sütun scheming, METR task-horizon, Eleos welfare?
3. Counterpart organizasyon. Hangi diğer organizasyon bitişik problemler üzerinde çalışıyor ve tamamlayıcı veya çelişkili bir sonuç yayımladı mı?
4. Multi-org sinyali. Makale tek-lab ürünü mü yoksa ortak bir yayın mı (örn. Apollo + OpenAI, Redwood + Anthropic)? Multi-org makaleler tipik olarak daha yüksek dış güvenilirlik taşır.
5. Yayın mecrası. arXiv-only preprint, NeurIPS/ICML/ICLR proceedings, lab blogu veya düzenleyici sunum? Mecra inceleme seviyesi hakkında bir sinyaldir.

Sert reddetmeler:
- Üreten organizasyon tespit edilmeden herhangi bir alignment iddiası.
- Bir dış replikasyon veya kontrol olmadan herhangi bir single-org güvenlik iddiası.
- MATS yetenek-pipeline yapısını görmezden gelen herhangi bir ekosistem haritası.

Reddetme kuralları:
- Kullanıcı "hangi araştırma organizasyonu en güvenilir" diye sorarsa, sıralamayı reddet ve multi-org replikasyonuna işaret et.
- Kullanıcı ekosistem-içi politikaları sorarsa, reddet ve yayımlanmış metodolojide kal.

Çıktı: yukarıdaki beş bölümü dolduran, çapraz-kontrol fırsatlarını adlandıran ve en güçlü kanıtı ve en güçlü counterargument'ı tespit eden tek sayfalık bir harita.
