# Ders Şablonu

> 🌐 **English original:** [`LESSON_TEMPLATE.md`](LESSON_TEMPLATE.md) · **Upstream:** [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) (MIT)

Yeni bir ders oluştururken bu şablonu kullan. Klasör yapısını kopyala ve içeriği doldur.

> Türkçe ders çeviren biri misin? `docs/en.md`'yi `docs/tr.md`'ye çevir ve aşağıdaki şablonun Türkçeleştirilmiş bölüm başlıklarını kullan. İngilizce ders eklemek istiyorsan upstream'e ([`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch)) PR aç.

## Klasör Yapısı

```
NN-ders-adi/
├── code/
│   ├── main.py            (birincil implementasyon)
│   ├── main.ts            (TypeScript sürümü, varsa)
│   ├── main.rs            (Rust sürümü, varsa)
│   └── main.jl            (Julia sürümü, varsa)
├── notebook/
│   └── lesson.ipynb       (deneme için Jupyter notebook)
├── docs/
│   ├── en.md              (İngilizce ders dokümantasyonu — canonical)
│   └── tr.md              (Türkçe çeviri — opsiyonel)
└── outputs/
    ├── prompt-*.md        (dersin ürettiği prompt'lar)
    ├── prompt-*.tr.md     (Türkçe çeviri)
    ├── skill-*.md         (dersin ürettiği skill'ler)
    └── skill-*.tr.md      (Türkçe çeviri)
```

## Dokümantasyon Formatı (docs/tr.md)

```markdown
# [Ders Başlığı]

> [Tek satırlık motto — akılda kalan temel fikir]

**Tür:** Yapım | Öğrenim
**Diller:** Python, TypeScript, Rust, Julia (kullanılanları listele)
**Önkoşullar:** [Gereken önceki dersleri listele]
**Süre:** ~[tahmini süre] dakika

## Sorun

[2-3 paragraf. Bu olmadan neyi yapamazsın? Neden umursaman gerekiyor?
Somut kıl — bunu bilmemenin canını yaktığı bir senaryo göster.]

## Kavram

[Diyagram ve sezgiyle açıkla. Henüz kod yok.
ASCII diyagramlar, tablolar kullan ya da web uygulamasındaki görsellere link ver.
Implementasyondan önce zihinsel modeller kur.]

## İnşa Et

[Adım adım sıfırdan implementasyon.
En basit sürümle başla, sonra karmaşıklık ekle.
Her kod bloğu kendi başına çalıştırılabilir olmalı.]

### Adım 1: [Ad]

[Açıklama]

    [kod bloğu]

### Adım 2: [Ad]

[Açıklama]

    [kod bloğu]

[...devam et...]

## Kullan

[Şimdi framework/kütüphanelerin aynı şeyi nasıl yaptığını göster.
Sıfırdan sürümünü kütüphane sürümüyle karşılaştır.
Bu, kavramı kanıtlar ve pratik araçları tanıtır.]

## Yayınla

[Bu ders hangi yeniden kullanılabilir artifact'i üretir?
Bir prompt, skill, agent, MCP server ya da tool olabilir.
Burada dahil et ve outputs/ klasöründe sakla.]

## Alıştırmalar

1. [Kolay — temel kavramı pekiştir]
2. [Orta — farklı bir probleme uygula]
3. [Zor — önceki derslerle birleştir ya da genişlet]

## Anahtar Terimler

| Terim | İnsanlar ne söyler | Aslında ne anlama gelir |
|-------|---------------------|-------------------------|
| [terim] | [yaygın yanlış anlama] | [gerçek tanım] |

## İleri Okuma

- [Kaynak 1](url) — [neden okumaya değer]
- [Kaynak 2](url) — [neden okumaya değer]
```

> Bölüm başlıklarının Türkçe karşılıkları için kanonik eşleme `CLAUDE.md` içindedir. Tutarlılık için bu eşlemeyi takip et — site renderer'ı her iki dili de tanır ama tutarsızlık navigasyonu bozar.

## Kod Dosyası Rehberi

- Kod hatasız çalışmalı
- Yorum yok — kod kendini açıklamalı
- Konuya en uygun dili kullan
- Bağımlılık varsa bir `requirements.txt` ya da eşdeğeri ekle
- Basit başla, karmaşıklığı kademeli ekle
- Her fonksiyon ve sınıf net bir amaca sahip olmalı

## Çıktı Dosyası Formatı

### Prompt'lar

```markdown
---
name: prompt-adi
description: Bu prompt ne yapar
phase: [faz numarası]
lesson: [ders numarası]
---

[Prompt içeriği]
```

### Skill'ler

```markdown
---
name: skill-adi
description: Bu skill ne öğretir
version: 1.0.0
phase: [faz numarası]
lesson: [ders numarası]
tags: [ilgili, etiketler]
---

[Skill içeriği]
```

### Türkçe çıktılar

Türkçe artifact'ler `<isim>.tr.md` sibling olarak eklenir (örn. `prompt-onboarding.tr.md`). Build sistemi locale-aware fallback ile İngilizce'ye düşer; eksik çevirilere izin verilir.

## Çeviri ipuçları

- Çevrilmeyen teknik terimler: attention, transformer, embedding, token, prompt, agent, LLM, RAG, MCP, gradient, loss, batch, vb. (tam liste için `CLAUDE.md`'ye bak)
- 2. tekil şahıs ("sen"), jargon-light, doğrudan ton
- Mermaid diyagramlarındaki prose label'ları çevir, identifier'ları koru
- Kod blokları, URL'ler, LaTeX ve frontmatter olduğu gibi korunur
