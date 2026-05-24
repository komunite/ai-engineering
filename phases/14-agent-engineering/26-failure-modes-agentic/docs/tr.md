# Başarısızlık Modları: Agent'lar Neden Bozulur

> MASFT (Berkeley, 2025) 14 çoklu-agent başarısızlık modunu 3 kategoride kataloglar. Microsoft'un Taxonomy'si mevcut AI başarısızlıklarının agentic ortamlarda nasıl güçlendiğini dokümante eder. Endüstri saha verisi beş yinelenen modda yakınsar: halüsine edilmiş aksiyonlar, scope creep, kademeli hatalar, context loss, tool misuse.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 05 (Self-Refine ve CRITIC), Faz 14 · 24 (Observability)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- MASFT'ın üç başarısızlık kategorisini ve her birinde en az dört spesifik modu adlandır.
- Agentic başarısızlığın mevcut AI başarısızlık modlarını (bias, halüsinasyon) neden güçlendirdiğini açıkla.
- Beş endüstri-yinelenen modu ve hafifletmelerini açıkla.
- Agent trace'lerini başarısızlık-modu etiketleriyle etiketleyen bir stdlib detector uygula.

## Sorun

Ekipler trace'lerin %90'ında çalışan agent'lar yayınlıyor. %10 başarısızlık rastgele gürültü değil — küçük sayıda yinelenen kategoriye düşerler. Onları adlandırabildiğinde, onlar için monitor edebilir ve onları düzeltebilirsin.

## Kavram

### MASFT (Berkeley, arXiv:2503.13657)

Multi-Agent System Failure Taxonomy. 3 kategoride cluster'lanmış 14 başarısızlık modu. Inter-annotator Cohen's Kappa 0.88 — kategoriler güvenilir şekilde ayırt edilebilir.

Merkezi iddia: başarısızlıklar çoklu-agent sistemlerinde temel tasarım kusurları, daha iyi base model'lerle düzeltilecek LLM sınırlamaları değil.

### Microsoft Taxonomy of Failure Mode in Agentic AI Systems

- Mevcut AI başarısızlıkları (bias, halüsinasyon, data leakage) agentic ortamlarda güçlenir.
- Yeni başarısızlıklar otonomiden çıkar: ölçekte istenmeyen aksiyon, tool misuse, mission drift.
- Beyaz kağıt agentic ürünler için risk register'ı.

### Characterizing Faults in Agentic AI (arXiv:2603.06847)

- Başarısızlıklar orchestration, iç state evrimi ve ortam etkileşiminden çıkar.
- Yalnızca "kötü kod" ya da "kötü model çıktısı" değil.

### LLM Agent Hallucinations Survey (arXiv:2509.18970)

İki birincil manifestasyon:

1. **Instruction-following Deviation** — agent system prompt'u takip etmiyor.
2. **Long-range Contextual Misuse** — agent önceki turlardan gelen bağlamı unutuyor ya da yanlış uyguluyor.

Sub-intention hataları: Omission (kaçırılan adım), Redundancy (tekrarlanan adım), Disorder (sıra-dışı adımlar).

### Beş endüstri-yinelenen mod

Arize, Galileo, NimbleBrain 2024-2026 saha analizleri şunlarda yakınsar:

1. **Halüsine edilmiş aksiyonlar.** Agent var olmayan bir tool invoke eder ya da argümanlar uydurur.
2. **Scope creep.** Agent görevi kullanıcının istediğinin ötesine genişletir (ekstra PR'lar oluşturur, ekstra e-postalar gönderir).
3. **Kademeli hatalar.** Bir yanlış çağrı downstream etkileri tetikler. Bir hayalet SKU halüsinasyonu dört API çağrısı tetikler — bir çoklu-sistem olayı.
4. **Context loss.** Uzun-ufuk görevleri erken-tur kısıtlamalarını unutur.
5. **Tool misuse.** Doğru tool'u yanlış argümanlarla ya da tamamen yanlış tool'u çağırır.

Kademeli olan katil. Agent'lar "başarısız oldum"u "görev imkansız"dan ayırt edemez ve döngüyü kapatmak için 400 hatalarında sıklıkla bir başarı mesajı halüsine eder.

### Hafifletme: her adımda kapılar

Bir akıl yürütme zincirinin her adımında otomatik doğrulama kapıları, factual topraklamayı ortam state'ine karşı kontrol eder. Somut olarak:

- Per-step safety classifier (Ders 21).
- Tool-call argüman doğrulama (Ders 06).
- Getirilen içeriği bilinen olgulara karşı cross-check (Ders 05, CRITIC).
- State'i yeniden probe ederek success halüsinasyonu tespit et (dosya gerçekten oluştu mu?).

### Başarısızlık izleme nerede ters gider

- **Yalnızca crash etiketleme.** Çoğu agent başarısızlığı geçerli-görünen çıktı üretir. İçerik-seviyesi check'ler gerek.
- **Baseline yok.** Drift tespiti son-bilinen-iyi gerektirir; o olmadan "bu kötüleşiyor" diyemezsin.
- **Aşırı-alarm.** Her başarısızlık bir page üretir. Cluster ve rate-limit et.

## İnşa Et

`code/main.py` bir stdlib başarısızlık-modu etiketleyici uyguluyor:

- Beş modu kapsayan sentetik bir trace dataset.
- Mod başına detector fonksiyonları (tool çağrılarında imza desenleri, çıktılar, tekrar aksiyonlar).
- Her trace'i etiketleyen ve mod dağılımını raporlayan bir etiketleyici.

Çalıştır:

```
python3 code/main.py
```

Çıktı: trace başına etiketler + agregat dağılım, Phoenix'in trace clustering'inin yüzeye çıkardığının ucuz bir kopyası.

## Kullan

- **Phoenix** üretim drift clustering için (Ders 24).
- **Langfuse** session replay + annotation için.
- **Custom** observability platformunun tespit edemediği domain-spesifik imzalar için.

## Yayınla

`outputs/skill-failure-detector.md` domain'ine göre özelleştirilmiş, bir trace store'a kablolanmış başarısızlık-modu detector'ları üretir.

## Alıştırmalar

1. "Success hallucination" için bir detector ekle: agent başarı döndürür ama hedef state değişmemiş.
2. Kurduğun bir üründen 100 gerçek trace etiketle. Hangi mod baskın? Onu düzeltmenin maliyeti ne?
3. Bir "cascade radius" metriği uygula: N adımındaki bir başarısızlık verildiğinde, kaç downstream adımı etkiledi?
4. MASFT'ın 14 başarısızlık modunu oku. Ürününe uygulanan üçü seç. Detector yaz.
5. Bir detector'ı bir CI işine kablola: trace'lerin >=%5'i bir modu etiketlerse build'i başarısız et.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| MASFT | "Çoklu-agent başarısızlık taksonomisi" | Berkeley 14-mod kategorilemesi |
| Kademeli hata | "Ripple başarısızlık" | Bir erken hata N adım boyunca propagate eder |
| Context loss | "Kısıtlamayı unuttu" | Uzun-ufuk tur erken-tur olgularını düşürür |
| Tool misuse | "Yanlış tool / yanlış args" | Geçerli çağrı, yanlış invocation |
| Success hallucination | "Sahte tamamlama" | Agent 400'de başarı iddia eder; state değişmemiş |
| Scope creep | "Aşırıya kaçma" | Agent istenenden fazlasını yapar |
| Instruction-following deviation | "İtaatsizlik" | System prompt'u ya da kullanıcı kısıtlamasını yoksayar |
| Sub-intention hataları | "Plan bug'ları" | Plan yürütmesinde omission, redundancy, disorder |

## İleri Okuma

- [Cemri et al., MASFT (arXiv:2503.13657)](https://arxiv.org/abs/2503.13657) — 14 başarısızlık modu, 3 kategori
- [Microsoft, Taxonomy of Failure Mode in Agentic AI Systems](https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/final/en-us/microsoft-brand/documents/Taxonomy-of-Failure-Mode-in-Agentic-AI-Systems-Whitepaper.pdf) — risk register'ı
- [Arize Phoenix](https://docs.arize.com/phoenix) — pratikte drift clustering
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — daha basit desenler modları tamamen ne zaman önler
