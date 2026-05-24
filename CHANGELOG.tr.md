# Changelog

> 🌐 **English original:** [`CHANGELOG.md`](CHANGELOG.md) · **Upstream:** [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) (MIT)

Curriculum'da neler değişti. En yeni girdi en üstte.

Format gevşek biçimde [Keep a Changelog](https://keepachangelog.com/) standardını takip eder. Her kayıt fazı, dersi ve neyin değiştiğini belirtir — böylece öğrenenler doğrudan farkı görebilir.

> Bu repo `rohitg00/ai-engineering-from-scratch` projesinin Türkçe uyarlamasıdır. Aşağıdaki upstream kayıtları orijinal projenin tarihçesini yansıtır; Türkçeleştirme ve Komünite uyarlaması kayıtları en altta listelenir.

## [Yayımlanmamış]

### Eklendi
- `scripts/scaffold-lesson.sh` — `phases/NN-faz/NN-ders/` altında klasör iskeletini ve `LESSON_TEMPLATE.tr.md`'den önceden doldurulmuş bir `docs/en.md` çatısı oluşturan scaffolder.
- `.github/PULL_REQUEST_TEMPLATE.md` — katkıcı checklist'i (kod çalışıyor, kod içinde yorum yok, önce sıfırdan inşa, ders başına atomik commit, ROADMAP satırı markdown link).
- `.github/ISSUE_TEMPLATE/bug_report.md` ve `new_lesson_proposal.md` — hata raporları ve ders önerileri için yapılandırılmış giriş formları.
- Bu `CHANGELOG.tr.md`.

## 2026-04 — Faz 4: Computer Vision tamamlandı

### Eklendi
- Faz 4'ün 28 dersinin tamamı; görüntü temellerinden çok-modlu görüye (VLM, 3D, video, self-supervised) kadar.
- Faz 4 satırları `ROADMAP.tr.md`'de ders klasörlerine markdown link olarak eklendi; böylece web sitesi bunları yüzeye çıkarıyor.

### Düzeltildi
- Faz 4'te 15+ derste hassasiyet geçişi:
  - `phase-4/02`: shape calculator, adaptive pool, flatten ve linear için RF/stride ele alımını belirtiyor.
  - `phase-4/03`: backbone seçici, kapsanan tüm aileleri listeliyor; OCR, medikal, endüstriyel için kafa rehberi eklendi.
  - `phase-4/04`: sınıflandırma teşhisi başarısızlık moduna göre nicel eşikler kullanıyor; tanımsız metrikler için `n/a` ilan ediliyor; 3'ten az sınıf için guard.
  - `phase-4/06`: detection metric reader `AP@0.5` kullanıyor (mAP@0.5 değil); sınıf başına recall opsiyonel olarak işaretlendi; anchor designer stride truncation ve seviye başına tek-anchor yolunu açıklıyor.
  - `phase-4/10`: sampler picker `unet_forward_ms`'i input olarak ilan ediyor; ControlNet guard'ı kural 0'a yükseltildi.
  - `phase-4/14`: ViT inspector refusal kuralıyla hizalandı — port denemeleri denetleniyor, onaylanmıyor.
  - `phase-4/24`: open-vocab stack picker'ın açık rule precedence'ı ve license-filter semantiği var; concept designer step-5/rule-80 çatışmasını çözüyor.
  - `phase-4/25`: VLM dokümanlarının `_merge`'i placeholder uyumsuzluğunda açıklayıcı `ValueError` fırlatıyor; CMER dahili olarak normalize ediyor.
  - `phase-4/27`: `synthetic_frames` GT box'larını frame H/W'ye clip ediyor.
  - `phase-4/28`: `rope_3d` dim split'i validate ediyor; DiT block örneğinden kullanılmayan `F` import'u kaldırıldı.

## 2026-Ç1 ve öncesi

### Eklendi
- Faz 0 (Kurulum & Araçlar): 12 dersin tamamı.
- Faz 1 (Matematik Temelleri): 22 dersin tamamı.
- Faz 2 (ML Temelleri): 18 dersin tamamı.
- Faz 3 (Derin Öğrenme Çekirdeği): perceptron, backprop, optimizer'lara kadar çekirdek dersler.
- Yerleşik Claude Code skill'leri: `find-your-level` (yerleştirme quiz'i) ve `check-understanding` (faz başına quiz).
- `aiengineeringfromscratch.com` web sitesi: katalog, ders başına sayfalar, roadmap, 277-terimlik sözlük.
- 20 fazın tamamı için ilk iskelet (`phases/00-*` → `phases/19-*`).
- `LESSON_TEMPLATE.tr.md`, `CONTRIBUTING.tr.md`, `ROADMAP.tr.md`, `README.tr.md`.

## Türkçe uyarlama — Komünite

> Aşağıdaki kayıtlar `komunite/ai-engineering` deposunun upstream'in üzerine eklediği değişiklikleri kapsar.

### 2026-05 — Tam Türkçeleştirme + statik site

#### Eklendi
- 20 fazın tamamı için Türkçe çeviri: 435 ders (`docs/tr.md`), 489 artifact (`outputs/*.tr.md`), 240 quiz (`quiz.tr.json`).
- 83 terimlik Türkçe sözlük (`glossary/terms.tr.md`).
- Türkçe kök içerikler: `README.tr.md`, `ROADMAP.tr.md`, faz başına `README.tr.md`'ler.
- `site/build.js`'e locale-aware fallback zinciri ve `LOCALE=tr` desteği.
- Ders başına 1200×630 OG görselleri (435 + 4 statik sayfa) ve `/phases/<faz>/<ders>/` pretty URL'leriyle stub HTML'ler (`scripts/build_og.py`, `scripts/build_lesson_pages.py`).
- `https://ai-muhendisligi.komunite.com.tr/` adresinde Vercel deployment.
- Hero altında atıf bandı — Rohit Ghumare ve Komünite kredisi, light/dark tema uyumlu.
- Katalog sayfasında kullanıcı ilerlemesi yansıması (`AIFSProgress` API), her ders sayfasının sonunda "Tamamlandı" CTA'sı.
- Türkçeleştirilmiş `.github/` template'leri (PR + 2 issue) ve TR sibling'leri (`CHANGELOG.tr.md`, `CODE_OF_CONDUCT.tr.md`, `CONTRIBUTING.tr.md`, `FORKING.tr.md`, `LESSON_TEMPLATE.tr.md`, `SPONSORS.tr.md`).

[Yayımlanmamış]: https://github.com/komunite/ai-engineering/compare/HEAD...HEAD
