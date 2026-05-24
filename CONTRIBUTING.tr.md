# Katkı Rehberi

> 🌐 **English original:** [`CONTRIBUTING.md`](CONTRIBUTING.md) · **Upstream:** [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) (MIT)

Dersler, çeviriler, düzeltmeler, çıktılar — hepsi memnuniyetle karşılanır. Pull request başına tek katkı, review'ları hızlandırır ve katkıcı sayımlarının düzgün işlemesini sağlar.

> Bu repo `rohitg00/ai-engineering-from-scratch`'in Türkçe uyarlamasıdır. **İngilizce ders içeriği ile ilgili katkıları lütfen upstream'e gönderin** — upstream merge'leri sayesinde buraya yansıyacaktır. Türkçe çeviri, terim seçimi, web sitesi UX'i ve `ai-muhendisligi.komunite.com.tr` ile ilgili katkıları ise bu repoya gönderebilirsiniz.

## Önemli: README ve ROADMAP web sitesini besler

`site/build.js` `README.tr.md`, `ROADMAP.tr.md` ve `glossary/terms.md` (locale varyantlarıyla) dosyalarını parse ederek `site/data.js`'i üretir. Bu dosyalara dokunan herhangi bir pull request'te iki desen bozulmadan kalmalıdır:

- Faz başlıkları, ya `### Phase N: Name \`X lessons\`` formunda ya da `<details><summary><b>Phase N — Name</b> ... <code>X lessons</code> ... <em>Description</em></summary>` formunda.
- Ders tabloları `| # | Lesson | Type | Lang |` sütun şeklinde (capstone tablolarında `| # | Project | Combines | Lang |`). `Lang` sütunu düz metin (`Python, TypeScript`) ya da klasik emoji bayrakları (`🐍 🟦 🦀 🟣 ⚛️`) kabul eder; parser açısından eşdeğerdir.
- Faz başlıkları ve ders satırlarındaki ROADMAP durum glyph'leri (`✅`, `🚧`, `⬚`). Bunları metinle değiştirmeyin — parser tam karakter eşleşmesi yapıyor.

Bu dosyaları düzenledikten sonra `node site/build.js` çalıştırın; `git diff site/data.js` yalnızca timestamp değişimini göstermeli ise düzenlemeniz yapısal-güvenlidir.

## Katkı Yolları

### 1. Yeni Ders Ekle

> İngilizce ders eklemek istiyorsan, [upstream repoya](https://github.com/rohitg00/ai-engineering-from-scratch) PR aç — upstream merge'leri buraya da yansıyacaktır.

Her ders `phases/XX-faz-adi/NN-ders-adi/` altında şu yapıyla yaşar:

```
NN-ders-adi/
├── code/           En az bir çalıştırılabilir implementasyon
├── notebook/       Deneme için Jupyter notebook (opsiyonel)
├── docs/
│   ├── en.md       Ders dokümantasyonu (zorunlu — canonical)
│   └── tr.md       Türkçe çeviri (varsa)
└── outputs/        Bu dersin ürettiği prompt, skill ya da agent'lar (varsa)
```

**Ders dokümantasyon formatı** (`en.md` / `tr.md`):

```markdown
# Ders Başlığı

> Tek satırlık motto — temel fikri tek cümlede.

## Sorun

Bu neden önemli? Bu olmadan neyi yapamazsın?

## Kavram

Diyagram, görsel ve sezgiyle açıkla. Kod daha sonra geliyor.

## İnşa Et

Adım adım sıfırdan implementasyon.

## Kullan

Şimdi aynı şeyi gerçek bir framework ya da kütüphane ile yap.

## Yayınla

Bu dersin ürettiği prompt, skill, agent ya da tool.

## Alıştırmalar

1. Birinci alıştırma
2. İkinci alıştırma
3. Challenge alıştırma
```

### 2. Çeviri Ekle

Herhangi bir dersin `docs/` klasöründe yeni dosya oluştur:

```
docs/
├── en.md    (İngilizce — her zaman zorunlu, canonical)
├── tr.md    (Türkçe)
├── zh.md    (Çince)
├── ja.md    (Japonca)
├── es.md    (İspanyolca)
└── ...
```

İngilizce sürümle aynı yapıyı koru. İçeriği çevir, kodu değil.

**Türkçe çeviri konvansiyonları:** [`CLAUDE.md`](CLAUDE.md) içindeki "Çeviri Konvansiyonları" bölümünü oku — bölüm başlıkları için sabit eşleme tablosu, çevrilmeyen teknik terimler listesi (attention, transformer, gradient, vb.) ve tonalite kuralları orada.

### 3. Çıktı Ekle

Bir ders yeniden kullanılabilir bir prompt, skill, agent ya da MCP server üretiyorsa:

1. Dersin `outputs/` klasöründe oluştur
2. Üst seviye `outputs/` index'inde referans ekle

**Prompt formatı:**

```markdown
---
name: prompt-adi
description: Bu prompt ne yapar
phase: 14
lesson: 01
---

[Sistem prompt'u veya şablon burada]
```

**Skill formatı:**

```markdown
---
name: skill-adi
description: Bu skill ne öğretir
version: 1.0.0
phase: 14
lesson: 01
tags: [agents, loops]
---

[Skill içeriği burada]
```

### 4. Hata Düzelt veya Mevcut Dersleri İyileştir

- Çalışmayan kodu düzelt
- Açıklamaları iyileştir
- Daha iyi diyagramlar ekle
- Eskimiş bilgileri güncelle

> Türkçe çeviride hatalı/uyumsuz terimler için `glossary/terms.tr.md` kanonik kaynaktır.

### 5. Alıştırma veya Proje Ekle

Daha fazla alıştırma ve proje her zaman memnuniyetle karşılanır, özellikle birden fazla fazı birleştirenler.

## Kurallar

- **Kod çalışmalı.** Her kod dosyası listelenen bağımlılıklarla hatasız çalışmalı.
- **Kod içinde yorum yok.** Kod kendini açıklamalı. Açıklama için doc'u kullan.
- **İş için en iyi dil.** TypeScript ya da Rust daha iyi seçimken Python'u zorlamayın.
- **Önce sıfırdan inşa et.** Framework sürümünü göstermeden önce kavramı her zaman first-principles ile implemente et.
- **Pratik kal.** Teori pratiğe hizmet eder, tam tersi değil.
- **AI slop yok.** İnsan gibi yaz. Doğrudan ol. Dolguyu at.

### Türkçe çeviri için ek kurallar

- 2. tekil şahıs ("sen"), jargon-light, doğrudan ton
- Bölüm başlıkları için `CLAUDE.md`'deki sabit eşlemeyi kullan
- Çevrilmeyen teknik terimleri (transformer, attention, gradient, etc.) bozma
- Deyimleri birebir çevirme, uyarla
- Kod blokları, URL'ler, LaTeX ve frontmatter olduğu gibi korunur
- Quiz JSON dosyalarında `stage`, `correct` ve `options` sırasını **asla** değiştirme; yalnızca string alanları çevir
- `python3 -c "import json; json.load(open('FILE'))"` ile her quiz çevirisini doğrula

## Pull Request Süreci

1. Repo'yu fork'la
2. Bir feature branch oluştur (`git checkout -b add-lesson-phase3-gradient-descent`)
3. Değişikliklerini yap
4. Tüm kodun çalıştığından emin ol
5. Net açıklamalı bir pull request aç (bkz. [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md))

### Commit Mesajları

Bu repo [Conventional Commits](https://www.conventionalcommits.org/) standardını kullanır:

- `feat(<scope>): yeni özellik`
- `fix(<scope>): hata düzeltmesi`
- `docs(<scope>): dokümantasyon değişikliği`
- `i18n(<scope>): çeviri eklendi/güncellendi`
- `chore(<scope>): rutin bakım`

`<scope>` faz adı (`phase-04`), bileşen (`site`, `build`) ya da konvansiyon adı (`i18n`, `seo`) olabilir.

## Davranış Kuralları

Bkz. [`CODE_OF_CONDUCT.tr.md`](CODE_OF_CONDUCT.tr.md). Nazik ol, yardımsever ol, yapıcı ol.

## Üslup

- Doğrudan düzyazı. Dolguyu at. Manual'in tonunu yakala, pazarlama copy'sini değil.
- Başlıklarda dekoratif emoji yok. Lang sütununun emoji bayrakları tek istisna ve sadece parser onları eşlediği için.
- Kod, derste listelenen bağımlılıklarla olduğu gibi çalışır.
- Önce sıfırdan, sonra framework.
