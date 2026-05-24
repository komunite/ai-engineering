# Benchmark'lar: WebArena ve OSWorld

> WebArena dört self-hosted uygulamada web-agent yeteneğini test eder. OSWorld Ubuntu, Windows, macOS'ta desktop-agent yeteneğini test eder. Yayında (2023–2024) her ikisi de en-iyi-sınıf agent'lar ile insanlar arasında büyük bir uçurum gösterdi. Uçurum daralıyor; başarısızlık modları değişmedi.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 19 (SWE-bench, GAIA)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- WebArena'nın dört self-hosted uygulamasını ve execution-based evaluation'ın neden önemli olduğunu açıkla.
- OSWorld'ün neden accessibility API'leri yerine gerçek OS ekran görüntüleri kullandığını açıkla.
- İki birincil OSWorld başarısızlık modunu adlandır: GUI grounding ve operasyonel bilgi.
- OSWorld-G ve OSWorld-Human'ın temel benchmark üzerine neyi eklediğini özetle.

## Sorun

Generalist agent'lar tool çağırabilir. Bir tarayıcıyı 20 click boyunca sürerek bir alışveriş checkout'unu tamamlayabilirler mi? Yalnızca klavye ve fareyle bir Linux kutusunu yapılandırabilirler mi? WebArena ve OSWorld bu soruları yanıtlar.

## Kavram

### WebArena (Zhou et al., ICLR 2024)

- Dört self-hosted web uygulamasında 812 uzun-ufuk task: bir alışveriş sitesi, bir forum, GitLab-benzeri bir dev tool, business bir CMS.
- Artı utility'ler: harita, calculator, scratchpad.
- Değerlendirme gym API'leri üzerinden execution-based — sipariş verildi mi, issue kapatıldı mı, CMS sayfası güncellendi mi?
- Yayında: en iyi GPT-4 agent %14.41 başarıya vs insan %78.24.

Self-hosted çerçeveleme önemli — benchmark aksak değil çünkü hedef uygulamalar sabitlenmiş ve yeniden üretilebilir.

### Genişletmeler

- **VisualWebArena** — başarının görüntüleri yorumlamaya bağlı olduğu görsel-toprakla(n)mış task'lar (birinci-sınıf gözlem olarak ekran görüntüleri).
- **TheAgentCompany** (Aralık 2024) — terminal + kodlama ekler; gerçek remote-work ortamına daha çok benzer.

### OSWorld (Xie et al., NeurIPS 2024)

- Ubuntu, Windows, macOS'ta 369 gerçek bilgisayar task'ı.
- Gerçek uygulamaların free-form klavye ve fare kontrolü.
- Gözlem olarak 1920×1080 ekran görüntüleri.
- Yayında: en iyi model %12.24 vs insan %72.36.

### Birincil başarısızlık modları

1. **GUI grounding.** Pixel → element eşleştirme. Modeller 1920×1080'de UI elementlerini güvenilir şekilde lokalize etmekte zorlanır.
2. **Operasyonel bilgi.** Hangi menüde ayar, hangi keyboard shortcut, hangi preference pane. İnsanların yıllar içinde inşa ettiği bilgi kuyruğu.

### Takipler

- **OSWorld-G** — 564-örnek grounding suite + Jedi eğitim seti. Grounding'i planlamadan ayırır, böylece ayrı ölçebilirsin.
- **OSWorld-Human** — manuel küratörlü gold action trajectory'leri. En iyi agent'ların gerekenden 1.4-2.7x daha fazla adım kullandığını (trajectory-efficiency uçurumu) gösterir.

### Bu neden önemli

Claude computer use, OpenAI CUA, Gemini 2.5 Computer Use (Ders 21) hepsi WebArena ve OSWorld tarafından şekillendirilmiş workload'lar üzerinde eğitiliyor. Benchmark'lar hedef; üretim modelleri yayınlanan yanıt.

### Benchmark'lama nerede ters gider

- **Yalnızca-ekran görüntüsü eval'ler.** OSWorld screenshot-driven; OSWorld'de DOM ya da accessibility API kullanan bir agent'ı değerlendirmek grounding zorluğunu kaçırır.
- **Trajectory uzunluğunu yoksaymak.** Yalnızca başarı-oranı puanlamak OSWorld-Human'ın yüzeye çıkardığı 1.4-2.7x adım verimsizliğini kaçırır.
- **Bayat self-hosted uygulamalar.** WebArena'nın uygulamaları belirli versiyonları sabitler; yeniden-küratörlemeden güncellemek karşılaştırılabilirliği bozar.

## İnşa Et

`code/main.py` oyuncak bir web-agent harness uyguluyor:

- Minimal bir "shopping app" state machine: list_items, add_to_cart, checkout.
- 3 task için gold trajectory'leri.
- Her task'ı denemeye çalışan scripted bir agent.
- Execution-based evaluator (state check) ve trajectory-efficiency metriği (gold'a karşı adımlar).

Çalıştır:

```
python3 code/main.py
```

Çıktı: task başına başarı oranı ve trajectory verimliliği, OSWorld-Human'ın metodolojisini yansıtarak.

## Kullan

- Sürekli değerlendirme için iç kümede self-hosted **WebArena Verified**.
- Desktop agent'lar için VM filosunda **OSWorld**.
- **Computer-use agent'lar** (Ders 21) — Claude, OpenAI CUA, Gemini — hepsi bunlar gibi workload'larda eğitildi.
- **Kendi ürün akışların** — en iyi 20 task'ın için gold trajectory'leri yakala; agent'ları haftalık onlara karşı çalıştır.

## Yayınla

`outputs/skill-web-desktop-harness.md` execution-based eval ve trajectory verimliliği metriğiyle bir web/desktop agent harness'ı kurar.

## Alıştırmalar

1. Oyuncak harness'ı ikinci bir uygulama (bir forum) ile genişlet. 3 task artı gold trajectory'leri yaz.
2. Task başına trajectory-verimliliği raporlaması ekle. Oyuncağında agent gold'un 1x, 2x ya da 3x üstünde mi?
3. Bir "distractor" tool uygula — gold trajectory'sinin asla kullanmadığı bir tane. Scripted agent baştan çıkar mı?
4. OSWorld-G'yi oku. Kendi eval'lerinde grounding başarısızlıklarını planning başarısızlıklarından nasıl ayırırsın?
5. WebArena'nın apps README'sini oku. Sabitlenmiş uygulama versiyonlarından birini yükselttiğinde ne bozulur?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| WebArena | "Web agent benchmark'ı" | 4 self-hosted uygulamada 812 task; gym-tarzı evaluation |
| VisualWebArena | "Visual WebArena" | Görsel-toprakla(n)mış WebArena; gözlemler ekran görüntüleri |
| OSWorld | "Desktop agent benchmark'ı" | Gerçek Ubuntu/Windows/macOS'ta 369 task |
| GUI grounding | "Pixel-to-element eşleştirme" | Model UI elementlerini 1920x1080'de lokalize ediyor |
| Operasyonel bilgi | "OS know-how" | Hangi menü, hangi shortcut, hangi preference pane |
| OSWorld-G | "Grounding suite" | 564 grounding-only örnek + eğitim seti |
| OSWorld-Human | "Gold trajectory'leri" | Verimliliği ölçmek için manuel uzman aksiyon dizileri |
| Trajectory verimliliği | "Gold üzerinde adımlar" | Agent adım sayısı bölü insan minimum |

## İleri Okuma

- [Zhou et al., WebArena (arXiv:2307.13854)](https://arxiv.org/abs/2307.13854) — dört-uygulamalı web benchmark
- [Xie et al., OSWorld (arXiv:2404.07972)](https://arxiv.org/abs/2404.07972) — cross-OS desktop benchmark
- [Anthropic, Introducing computer use](https://www.anthropic.com/news/3-5-models-and-computer-use) — Claude'un benchmark-şekilli yeteneği
- [OpenAI, Computer-Using Agent](https://openai.com/index/computer-using-agent/) — OSWorld ve WebArena sayıları
