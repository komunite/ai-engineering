# CLAUDE.md

Bu dosya, Claude Code'un (claude.ai/code) bu repoda çalışırken referans alacağı talimatları içerir.

## Proje Bağlamı

**Sıfırdan Yapay Zeka Mühendisliği** — [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) MIT lisanslı curriculum'un Türkçe uyarlamasıdır. 20 faz, 435 ders. Statik site Vercel'de `ai-muhendisligi.komunite.com.tr` üzerinde yayımlanır.

TR canonical bir uyarlama: kök `README.md` doğrudan Türkçe; ders gövdeleri `docs/en.md` (upstream'den) + `docs/tr.md` (çeviri) olarak çift bulunur; outputs/quiz dosyaları `<base>.md` + `<base>.tr.md` sibling yapısındadır.

## Build & Geliştirme Komutları

```bash
# Türkçe build (varsayılan — site/build.js'de LOCALE || 'tr')
node site/build.js

# İngilizce build (en/ subdirectory'sini gerektirir — şu an mevcut değil, yalnızca TR canlı)
LOCALE=en node site/build.js

# Vercel build chain'inin tamamı (production ile birebir)
LOCALE=tr node site/build.js \
  && python3 scripts/build_sitemap.py \
  && python3 scripts/build_llms_txt.py \
  && rm -rf site/phases && cp -R phases site/phases \
  && python3 scripts/build_lesson_pages.py

# Yerel dev sunucusu (statik dosyalar)
cd site && python3 -m http.server 3001 --bind 127.0.0.1

# CI invariant kontrolleri (commit/push öncesi)
python3 scripts/audit_lessons.py
python3 scripts/build_catalog.py && git diff --exit-code catalog.json
python3 scripts/check_readme_counts.py
```

`build.js` `README.md`, `ROADMAP.md`, `glossary/terms.md` ve `phases/*/*/docs/<locale>.md` dosyalarını parse edip `site/data.js`'i üretir.

### Scripts envanteri

| Script | İş |
|---|---|
| `site/build.js` | Curriculum → `site/data.js` (locale-aware) |
| `scripts/audit_lessons.py` | Ders dizinleri için invariant denetimi (slug regex, quiz şeması, min doc boyutu) — **CI** |
| `scripts/build_catalog.py` | `catalog.json` (curriculum tree) üretir; ders yapısal değişikliklerinden sonra rebuild + commit zorunlu — **CI drift** |
| `scripts/check_readme_counts.py` | README'deki ders/skill/prompt sayıları catalog ile eşleşmeli — **CI drift** |
| `scripts/build_lesson_pages.py` | Her ders için crawler-friendly stub `index.html` (OG meta + JS redirect). Çıktılar `.gitignore`'da. |
| `scripts/build_sitemap.py` | `site/sitemap.xml` |
| `scripts/build_llms_txt.py` | `site/llms.txt` (llmstxt.org formatı) |
| `scripts/build_og.py` | OG görselleri (headless Chrome — aşağıdaki marka bölümü) |
| `scripts/scaffold-lesson.sh` | Yeni ders iskeleti (`LESSON_TEMPLATE.md`'den `docs/en.md`) |
| `scripts/install_skills.py` | `phases/**/outputs/{skill,prompt,agent}-*.md` artifact'larını harici target dizine kurar |
| `scripts/lesson_run.py` | Ders Python kodu için syntax / smoke check (`--execute` ile gerçek çalıştırma) |
| `scripts/link_check.py` | Markdown link doğrulaması |
| `scripts/scaffold_workbench.py` | Agent Workbench pack'i harici repo'ya kurar |
| `scripts/_lib.py` | Ortak Python yardımcıları |

### CI (`.github/workflows/curriculum.yml`)

`phases/**`, `catalog.json`, `README.md` veya ilgili scriptler değiştiğinde üç job çalışır:

1. **audit** — `audit_lessons.py`
2. **catalog-drift** — `build_catalog.py /tmp/catalog.fresh.json` üretip committed `catalog.json` ile diff
3. **readme-counts-drift** — `check_readme_counts.py`

Ders eklerken/değiştirirken **her zaman**: `python3 scripts/build_catalog.py` ile `catalog.json`'u yeniden üret ve commit'le. Aksi halde CI kırılır.

## Mimari

### Locale-aware fallback zinciri

Konvansiyon dosya tipine göre **farklı**:

| Dosya tipi | Pattern | Örnek |
|---|---|---|
| Kök `README` | TR canonical at root (sibling yok); diğer dil için `<locale>/README.md` veya `README.<locale>.md` | `README.md` (TR) |
| Diğer kök dokümanlar | EN canonical + TR sibling | `ROADMAP.md` + `ROADMAP.tr.md` |
| Ders gövdesi | Subdirectory locale dosyaları | `docs/en.md` + `docs/tr.md` |
| Quiz | Sibling | `quiz.json` (EN) + `quiz.tr.json` |
| Outputs (skill/prompt/agent) | Sibling | `skill-foo.md` + `skill-foo.tr.md` |
| Glossary | Sibling | `terms.md` + `terms.tr.md` |

`site/build.js` ve `site/lesson.html` her dosya için şu sırayı dener (dosya tipine göre adapte olur):

1. **Yerel locale**: `<base>.<LOCALE>.md` veya `docs/<LOCALE>.md`
2. **Yerel fallback**: canonical (`<base>.md` ya da `docs/en.md`)
3. **Upstream locale**: GitHub raw URL'inden locale dosyası
4. **Upstream fallback**: GitHub raw URL'inden canonical

Bu yapı kısmi çeviriye izin verir — eksik TR dosyaları otomatik EN'e düşer.

### Dizin yapısı

```
phases/<NN>-<slug>/                  Faz klasörü
├── README.md / README.tr.md         Faz girişi
├── <NN>-<lesson-slug>/              Ders dizini (slug regex: ^[0-9]{2}-[a-z0-9][a-z0-9-]*[a-z0-9]$)
│   ├── docs/en.md, docs/tr.md       Ders gövdesi (min 200 byte)
│   ├── code/                        Çalıştırılabilir örnekler (lesson_run.py syntax check'i)
│   ├── outputs/                     skill-*.md, prompt-*.md, agent-*.md (+ .tr.md sibling'leri)
│   ├── quiz.json, quiz.tr.json      Pre/check/post quiz soruları
│   └── index.html                   GENERATED — build_lesson_pages.py üretir; .gitignore'da
glossary/
├── terms.md / terms.tr.md           Sözlük (83 terim)
├── myths.md / README.md             Ek glossary materyalleri
outputs/                             Curriculum-wide installable artifact'lar
├── index.json                       Tüm skill/prompt/agent katalogu
├── skills/, prompts/, agents/, mcp-servers/
site/
├── *.html, *.js, style.css          Statik SPA (vanilla)
├── data.js                          build.js çıktısı (generated, manuel düzenlenmez)
├── sitemap.xml, llms.txt            build_sitemap.py / build_llms_txt.py çıktısı
├── og/                              OG görselleri (build_og.py — faz + statik)
├── assets/figures/                  Ders şekilleri
└── phases → ../phases               Yerel dev için symlink
scripts/                             Build/audit/install helper'ları (envanter yukarıda)
.github/workflows/curriculum.yml     audit + 2 drift check
.claude/skills/                      Project skill'leri (check-understanding, find-your-level)
catalog.json                         GENERATED (build_catalog.py); commit edilir, CI drift kontrol eder
vercel.json                          Build chain + cache header'ları + rewrite'lar
requirements.txt                     Ders kodları için Python deps (numpy, torch, transformers, anthropic…)
README.md                            TR canonical (sibling .tr.md YOK)
ROADMAP.md / ROADMAP.tr.md           Faz/ders ilerleme tablosu (build.js status emoji'lerini parse eder)
CHANGELOG.md / CHANGELOG.tr.md
CONTRIBUTING.md / CONTRIBUTING.tr.md
FORKING.md / FORKING.tr.md
LESSON_TEMPLATE.md / LESSON_TEMPLATE.tr.md   scaffold-lesson.sh bunu kopyalar
CODE_OF_CONDUCT.md / CODE_OF_CONDUCT.tr.md
```

**Not**: `.gitignore`'da `.claude/` var ama `.claude/skills/` klasörü **commit edilmiş** (iki project skill içerir). Bilerek hold-out: yeni `.claude/` çocukları default ignore olur, mevcut skill'ler korunur. `.claude/skills/*` eklerken `git add -f` gerekir.

### `site/phases` symlink'i

Yerel dev sunucusu sadece `site/` kökünü servis eder. `phases/` içeriğine browser'dan erişim sağlamak için `site/phases` → `../phases` symlink'i kullanılır. Bu sayede `lesson.html` `phases/<path>/docs/tr.md` adresinden TR markdown'ı doğrudan çekebilir.

Vercel build'inde symlink **silinip yerine gerçek kopya** konur (`rm -rf site/phases && cp -R phases site/phases`), çünkü `build_lesson_pages.py` her ders için `site/phases/<phase>/<lesson>/index.html` stub'ı yazıyor — symlink üzerinden yazsaydık source `phases/`'i kirletirdi. Kopya yapıldıktan sonra `phases/` ağacı tamamen `site/`'nin altında durur; lesson.html için upstream GitHub raw fetch fallback'ı yine devreye girebilir.

### Per-lesson generated stubs

`build_lesson_pages.py` her dersin yoluna `index.html` üretir. Bu stub:

- Doğru `<title>`, `<meta description>`, OG / Twitter card meta'ları, `canonical` link içerir
- `<noscript>` + meta refresh fallback
- JS ile `/lesson.html?path=phases/<phase>/<lesson>`'a redirect

Twitter/Slack/Facebook/Google crawler'ları redirect'i takip etmeden önce meta'ları okur → her paylaşım linki ders-özgü OG görseliyle gözükür. Stub'lar `.gitignore`'da; yalnızca Vercel build output'unda yaşar.

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

`vercel.json` `buildCommand`'ı 5 adımlık zincir çalıştırır (yukarıdaki "Vercel build chain"e bak). `LOCALE=tr` build komutuna hardcoded — env var set etmeye gerek yok. Cache header'ları statik asset'ler için 1 gün, HTML için 5 dakika (CDN'de 1 gün) olarak vercel.json'da tanımlı. Rewrite'lar: `/glossary`, `/catalog`, `/path`, `/roadmap` clean URL'leri.

## Yeni ders eklerken (workflow)

```bash
# 1. İskelet
scripts/scaffold-lesson.sh 05-nlp-foundations-to-advanced 03-tokenizers "Tokenizers from Scratch"

# 2. docs/en.md yaz, opsiyonel docs/tr.md ekle, quiz.json oluştur, code/ doldur

# 3. ROADMAP.md'de status emoji'sini güncelle (✅ / 🚧 / ⬚)

# 4. Catalog'u yeniden üret (CI drift kontrolü için ZORUNLU)
python3 scripts/build_catalog.py

# 5. README count'larını güncelle (gerekirse) ve audit'i çalıştır
python3 scripts/audit_lessons.py
python3 scripts/check_readme_counts.py

# 6. Commit (catalog.json dahil)
git add phases/05-nlp-foundations-to-advanced/03-tokenizers/ ROADMAP.md catalog.json
```

## Outputs & installable artifact'lar

Curriculum yalnızca ders metni değil, **kurulabilir agent skill / prompt / agent paketleri** de üretiyor:

- Her ders kendi `outputs/skill-*.md`, `prompt-*.md`, `agent-*.md` dosyalarını içerebilir (YAML frontmatter zorunlu)
- `outputs/index.json` curriculum-wide katalog
- `scripts/install_skills.py <target>` ile harici bir dizine kurulur (flat / by-phase / skills layout)
- `scripts/scaffold_workbench.py` Agent Workbench pack'ini (`AGENTS.md`, `schemas/`, `task_board.json` vb.) harici repo'ya iskeletler

Bunlara dokunurken artifact dosyalarının frontmatter şemasını bozma.

## Dikkat Edilecekler

- `data.js`, `catalog.json`, `site/sitemap.xml`, `site/llms.txt`, `site/phases/**/index.html` **hepsi build-generated**. Manuel düzenlenmez (catalog.json hariç — bu commit edilir ama scriptle üretilir).
- Site'ye yeni dil eklemek için: (1) `docs/<locale>.md` dosyalarını oluştur, (2) outputs/quiz için `.<locale>.md`/`.<locale>.json` sibling'leri, (3) `LOCALE=<xx> node site/build.js`. `build.js` ve `lesson.html` her ISO 639-1 iki harfli locale'i destekler.
- Quiz dosyalarında JSON yapısını bozma — `python3 -c "import json; json.load(open('FILE'))"` ile her zaman doğrula. `stage`, `correct`, `options` sırası asla değiştirilmez.
- Symlink (`site/phases`) Git'te commit edilir; Vercel build sırasında silinip kopya ile değiştirilir (`build_lesson_pages.py` stub'larının source ağacı kirletmemesi için).
- Lesson slug regex: `^[0-9]{2}-[a-z0-9][a-z0-9-]*[a-z0-9]$`. `audit_lessons.py` ihlalde fail eder.
- Ders kodları için Python deps `requirements.txt`'de (torch, transformers, anthropic, openai…). Build/script çalıştırmak için Python 3.10+ yeter (PEP 604 union types).

## Upstream İlişkisi

Upstream (`rohitg00/ai-engineering-from-scratch`) güncellemelerini almak için:

```bash
git remote add upstream https://github.com/rohitg00/ai-engineering-from-scratch.git
git fetch upstream
git merge upstream/main   # canonical EN içeriğini günceller; .tr.md dosyaları korunur
```

Canonical EN dosyaları upstream'den geldiği için, TR çevirileri ayrı dosyalar olarak yaşar ve merge conflict'ı çıkmaz. Tek istisna: kök `README.md` ve `ROADMAP.md` — bunlar TR varyantlarıyla (`README.tr.md`, `ROADMAP.tr.md`) ayrı dosyalardır, merge sorunsuz.

## Marka & Tasarım — DEĞİŞMEZ Kurallar

Bu repo'da görsel üretirken (OG image, banner, README görseli, sosyal kart, vb.) **aşağıdaki tipografi kuralları değiştirilemez**. Bir görsel "homepage hero ile aynı görünmüyor"sa, sorunun ilk yeri burası.

### Ana başlık (hero / H1) fontu — VT323

Web sitesinin hero başlığı (`site/index.html` içindeki `.manual-title` H1) **VT323**'tür. Tüm yan görseller (OG images, banner.svg, social previews) ana başlık için **AYNEN bu fontu** kullanmalı:

```css
/* site/style.css içindeki tek doğru değer */
--font-display: 'VT323', ui-monospace, 'JetBrains Mono', monospace;

/* Tüm h1-h4: */
font-family: var(--font-display);
color: var(--blueprint);   /* #3553ff */
text-transform: uppercase;
font-weight: 400;
letter-spacing: 0.02em;
```

**Yanlış kullanımlar (geçmişte yapıldı, tekrar yapma):**
- ❌ `Source Serif 4` / serif font ile hero başlık → yan görsel artık siteyle eşleşmez
- ❌ Renksiz / siyah hero başlık → blueprint mavi (`#3553ff`) zorunlu
- ❌ Karışık casing → uppercase + letter-spacing 0.02em zorunlu

### Headless Chrome ile OG render ederken — FOUT tuzağı

`scripts/build_og.py` görselleri Chrome `--screenshot` ile alır. Google Fonts varsayılan `display=swap` ile gelir ve **Chrome, font yüklenmeden ekran görüntüsü alabilir** → VT323 fallback'e (system mono, smooth sans-serif) düşer ve hero başlık homepage'le eşleşmez.

Bu yüzden OG template'lerinde (`og_template.html`, `og_template_static.html`) **zorunlu**:

1. Google Fonts URL'sinde `&display=block` (swap değil) → tarayıcı font yüklenene kadar render'ı bloklar.
2. Template head'inde `document.fonts.ready` script'i — fonts hazır olunca işaret koysun.
3. `build_og.py` Chrome komutunda **`--virtual-time-budget=4000`** ve `--run-all-compositor-stages-before-draw` flag'leri → Chrome screenshot'tan önce font yüklemesine zaman verir.

Bu üçü olmadan **görsel sessizce yanlış üretir**, fark etmek için göze bakmak gerekir.

### Kontrol listesi (yeni görsel oluştururken)

- [ ] Hero başlık VT323 mi? (pixelated/8-bit görünmesi gerek, smooth sans-serif değil)
- [ ] Renk `#3553ff` (blueprint) mi?
- [ ] Uppercase + `letter-spacing: 0.02em` uygulanmış mı?
- [ ] OG template ise `display=block` + virtual-time-budget kullanıldı mı?
- [ ] Lokalde render edip son görseli **gözle kontrol** ettin mi? (CSS doğru ama font yüklenmediği için yanlış görünebilir)
