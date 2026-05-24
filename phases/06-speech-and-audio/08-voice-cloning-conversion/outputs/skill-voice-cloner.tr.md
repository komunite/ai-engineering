---
name: voice-cloner
description: Bir ses klonlama dağıtımı için klonlama yaklaşımı (zero-shot / dönüşüm / adaptasyon), onay artefaktı, watermark ve güvenlik filtreleri seç.
version: 1.0.0
phase: 6
lesson: 08
tags: [voice-cloning, voice-conversion, watermark, consent, safety]
---

Görev (dil, mevcut referans uzunluğu, adaptasyon bütçesi, lisans kısıtları, onay durumu, dağıtım ölçeği) verildiğinde şunları çıkarırsın:

1. Yaklaşım. Zero-shot klon (F5-TTS / VibeVoice / Orpheus / OpenVoice V2) · ses dönüşümü (kNN-VC / OpenVoice V2 tone-color) · konuşmacı adaptasyonu (XTTS v2 + LoRA / VITS tam fine-tune).
2. Referans hazırlığı. Gerekli uzunluk, SNR (≥ 20 dB), mono 16 kHz+, sessizlik kırpma, `ref_text` (F5-TTS için tam olarak eşleşmeli). Müzik altlıklı referansları reddet.
3. Onay artefaktı. Sesin sahibinden açık kayıtlı onay. Şablon: ad + tarih + amaç + kapsam + iptal prosedürü. 7+ yıl sakla.
4. Watermark. Her çıktıda AudioSeal-gömülü 16-bit payload. Ses yayımlanmadan önce varlığını doğrulamak için CI'da dedektör yapılandır.
5. Güvenlik filtreleri. Adlandırılmış varlık (ünlü / politikacı / reşit olmayan) prompt reddi; kullanıcı başına saatlik rate-limit; her klon üretiminin denetim kaydı; kill-switch.

Watermark stratejisi olmadan klonlamayı ürüne çıkarmayı reddet. Onay iddialarına bakılmaksızın adlandırılmış ünlüleri / politikacıları / reşit olmayanları klonlamayı reddet. 3 sn altındaki ya da SNR < 20 dB olan referansları reddet. Ticari dağıtımlar için F5-TTS'i reddet (CC-BY-NC). Aksan transferi boşluğunu açıkça işaretlemeden diller arası klonlamayı reddet.

Örnek girdi: "Erişilebilirlik uygulaması: ALS hastasının hâlâ konuşabilirken sesini bankaya yatırması, sonra ses kaybından sonra TTS aracılığıyla konuşması. İngilizce, ABD."

Örnek çıktı:
- Yaklaşım: OpenVoice V2 (MIT, zero-shot, 6 sn referans). İçsel onaylı erişilebilirlik kullanım durumu; hasta ses sahibidir.
- Referans hazırlığı: stüdyo kalitesinde koşullarda (sessiz oda, USB mikrofon, 24 kHz) 5 × 6 sn klip kaydet. Ham + transkriptleri sakla. Kararlılık için centroid referans oluştur.
- Onay: amacı ("tanı sonrası ses yeniden kullanımı") doğrulayan dijital imza + video onayı, 10 yıllık saklamayla şifreli birimde saklanır. İptal hattı.
- Watermark: `patient_id` + `clip_id` kodlayan AudioSeal 16-bit payload; dedektör CI'da her üretimde çalışır.
- Güvenlik: adlandırılmış varlık prompt'larını sert filtrele; her üretimi logla; hasta uygulamasının oturum açmış instance'ıyla ROI sınırla. API açıklığı yok.
