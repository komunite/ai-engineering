# CLAUDE.md

Bu dosya, Claude Code'un (claude.ai/code) bu repoda çalışırken referans alacağı talimatları içerir.

## Proje Bağlamı

**Sıfırdan Yapay Zeka Mühendisliği** — [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) MIT lisanslı curriculum'un Türkçe uyarlamasıdır. 20 faz, 435 ders, 489 artifact. Statik site Vercel'de yayımlanır.

Upstream İngilizce içeriği canonical fallback olarak korunur; Türkçe içerikler sibling `.tr.md` / `.tr.json` dosyaları olarak eklenir. Locale-aware build sistemi her iki çıktıyı da üretebilir.

## Build & Geliştirme Komutları

```bash
# İngilizce build (varsayılan)
node site/build.js

# Türkçe build
LOCALE=tr node site/build.js

# Yerel dev sunucusu (statik dosyalar)
cd site && python3 -m http.server 3001 --bind 127.0.0.1
```

`build.js` `README.md`, `ROADMAP.md`, `glossary/terms.md` ve `phases/*/*/docs/<locale>.md` dosyalarını parse edip `site/data.js`'i üretir.

## Mimari

### Locale-aware fallback zinciri

`site/build.js` ve `site/lesson.html` her dosya için şu sırayı dener:

1. **Yerel locale**: `<base>.<LOCALE>.md` (örn. `README.tr.md`, `docs/tr.md`, `quiz.tr.json`)
2. **Yerel fallback**: `<base>.md` (canonical İngilizce)
3. **Upstream locale**: GitHub raw URL'inden `<base>.<LOCALE>.md`
4. **Upstream fallback**: GitHub raw URL'inden `<base>.md`

Bu yapı, herhangi bir fazın yalnızca kısmen çevrilmiş olmasına izin verir — eksik dosyalar otomatik İngilizce'ye düşer.

### Dizin yapısı

```
phases/<NN>-<slug>/                  Faz klasörü
├── README.md / README.tr.md         Faz girişi (kısa)
├── <NN>-<lesson-slug>/
│   ├── docs/en.md / docs/tr.md      Ders gövdesi
│   ├── outputs/skill-*.md / *.tr.md Skill/prompt artifact'ları
│   ├── quiz.json / quiz.tr.json     Quiz soruları
│   └── code/                        Çalıştırılabilir örnekler
glossary/
├── terms.md / terms.tr.md           Sözlük (83 terim)
site/
├── *.html / *.js                    Statik SPA (vanilla)
├── data.js                          build.js çıktısı (generated)
└── phases → ../phases               Yerel dev için symlink
README.md / README.tr.md             Kök katalog
ROADMAP.md / ROADMAP.tr.md           Faz/ders ilerleme tablosu
```

### `site/phases` symlink'i

Yerel dev sunucusu sadece `site/` kökünü servis eder. `phases/` içeriğine browser'dan erişim sağlamak için `site/phases` → `../phases` symlink'i kullanılır. Bu sayede `lesson.html` `phases/<path>/docs/tr.md` adresinden TR markdown'ı doğrudan çekebilir. Vercel deployment'ında bu rol upstream GitHub raw URL'i tarafından üstlenilir (lesson.html'in fetch fallback zinciri).

## Çeviri Konvansiyonları

### Bölüm başlıkları (sabit eşleme)

| EN | TR |
|---|---|
| `Learning Objectives` | `Öğrenme Hedefleri` |
| `The Problem` | `Sorun` |
| `The Concept` | `Kavram` |
| `Build It` | `İnşa Et` |
| `Use It` | `Kullan` |
| `Ship It` | `Yayınla` |
| `Exercises` | `Alıştırmalar` |
| `Step N: X` | `Adım N: X` |
| `Key Terms` | `Anahtar Terimler` |
| `Pitfalls` | `Tuzaklar` |
| `Further Reading` | `İleri Okuma` |
| `**Type:** Build` | `**Tür:** Yapım` |
| `**Type:** Learn` | `**Tür:** Öğrenim` |
| `**Type:** Capstone` | `**Tür:** Bitirme` |

### Çevrilmeyen teknik terimler (Türk ML topluluğu standardı)

attention, transformer, embedding, token, tokenizer, fine-tuning, prompt, agent, LLM, RAG, MCP, gradient, loss, batch, epoch, learning rate, weight decay, dropout, batch normalization, ReLU, GELU, softmax, KV cache, flash attention, MoE, LoRA, QLoRA, PPO, DPO, RLHF, SFT, scaling laws, perplexity, eigenvalue, eigenvector, tensor, scalar, norm, Jacobian, Hessian, CUDA, GPU, container, sandbox, observability, latency (kullanım bağlamında "gecikme" de geçer), throughput, baseline, guardrails, overfitting, underfitting, jailbreak, alignment, alignment faking, reward hacking, scheming, Constitutional AI, framework, pipeline, etc.

### Çevrilen kavramlar

| EN | TR |
|---|---|
| neural network | sinir ağı |
| weights | ağırlıklar |
| inference | çıkarım |
| training | eğitim |
| evaluation | değerlendirme |
| matrix | matris |
| vector | vektör |
| derivative | türev |
| gradient | gradyan |
| probability distribution | olasılık dağılımı |
| natural language processing | doğal dil işleme |
| computer vision | bilgisayarlı görü |
| speech recognition | konuşma tanıma |
| reinforcement learning | pekiştirmeli öğrenme |
| generative model | üretken model |
| multi-agent | çoklu-agent |
| autonomous | otonom |
| chain rule | zincir kuralı |
| activation function | aktivasyon fonksiyonu |
| loss function | loss fonksiyonu (kombine) |
| optimization | optimizasyon |
| convergence | yakınsama |

### Tonalite

- Doğrudan, jargon-light, 2. tekil şahıs ("sen")
- Deyimler birebir çevrilmez, uyarlanır
- Kod blokları, URL'ler, LaTeX, frontmatter olduğu gibi korunur
- Mermaid diyagramlarındaki prose label'ları çevrilir, identifier'lar korunur

## Quiz Yapısı

```json
{
  "questions": [
    {
      "stage": "pre" | "check" | "post",
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct": <0-3 integer>,
      "explanation": "..."
    }
  ]
}
```

`stage`, `correct` ve `options` sırası **asla** değiştirilmez. Sadece string alanlar çevrilir.

`lesson.html` üç quiz section'ı render eder: **Ders Öncesi Kontrol** (pre), **Ders Ortası Kontrol** (check), **Ders Sonrası Quiz** (post). Hardcoded "Anladığını Test Et" paneli (URL pattern match) sadece `quiz.json` yüklenemediğinde fallback olarak görünür.

## Deployment

```bash
# Vercel
vercel deploy --prod    # vercel.json zaten yapılandırılmış (output: site)
```

Vercel build komutu `node site/build.js` (varsayılan İngilizce). Türkçe deployment için `LOCALE=tr` env var Vercel project settings'inde set edilmelidir.

## Dikkat Edilecekler

- `data.js` build-generated; manuel düzenlenmemeli
- Site'ye yeni dil eklemek için: (1) `<base>.<locale>.md` dosyalarını oluştur, (2) `build.js` ve `lesson.html` zaten her ISO 639-1 iki harfli locale'i destekliyor, sadece `LOCALE=<xx>` ile build et
- Quiz dosyalarında JSON yapısını bozma — `python3 -c "import json; json.load(open('FILE'))"` ile her zaman doğrula
- Symlink (`site/phases`) Git'te commit edilir; clone sonrası Vercel ortamlarında `site/` deploy edildiğinden symlink ölü olur ama upstream fallback devreye girer

## Upstream İlişkisi

Upstream (`rohitg00/ai-engineering-from-scratch`) güncellemelerini almak için:

```bash
git remote add upstream https://github.com/rohitg00/ai-engineering-from-scratch.git
git fetch upstream
git merge upstream/main   # canonical EN içeriğini günceller; .tr.md dosyaları korunur
```

Canonical EN dosyaları upstream'den geldiği için, TR çevirileri ayrı dosyalar olarak yaşar ve merge conflict'ı çıkmaz. Tek istisna: kök `README.md` ve `ROADMAP.md` — bunlar TR varyantlarıyla (`README.tr.md`, `ROADMAP.tr.md`) ayrı dosyalardır, merge sorunsuz.
