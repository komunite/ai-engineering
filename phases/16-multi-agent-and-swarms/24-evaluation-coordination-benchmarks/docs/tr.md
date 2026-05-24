# Değerlendirme ve Koordinasyon Benchmark'ları

> Beş 2025-2026 benchmark'ı çoklu-agent değerlendirme uzayını kapsar. **MultiAgentBench / MARBLE** (ACL 2025, arXiv:2503.01935) milestone KPI'larıyla star/chain/tree/graph topolojilerini değerlendirir; **graph araştırma için en iyi**, cognitive planning ~%3 milestone başarısı ekler. **COMMA** multimodal asimetrik-bilgi koordinasyonunu değerlendirir; GPT-4o dahil state-of-the-art modeller rastgele baseline'ı yenmede zorlanır. **MedAgentBoard** (arXiv:2505.12371) dört tıbbi görev kategorisini kapsar ve sıklıkla çoklu-agent'ın tek-LLM'i baskınlaştırmadığını bulur. **AgentArch** (arXiv:2509.10769) tool-use + bellek + orkestrasyonu birleştiren kurumsal agent mimarilerini benchmark'lar. **SWE-bench Pro** ([arXiv:2509.16941](https://arxiv.org/abs/2509.16941)) iş uygulamaları, B2B hizmetleri ve geliştirici tool'larını kapsayan 41 repo'da 1865 problem'a sahiptir; frontier modeller Pro'da ~%23 puan alır vs Verified'da %70+ — kontaminasyon üzerinde gerçeklik kontrolü. Claude Opus 4.7 (Nisan 2026) açık agent-takım koordinasyonuyla Pro'da **%64.3** rapor edildi (henüz yayınlanmış Anthropic birincil kaynak yok — ön sonuç olarak ele al); Verdent (agent scaffold) Verified'da **%76.1 pass@1** vurur ([Verdent technical report](https://www.verdent.ai/blog/swe-bench-verified-technical-report)). **AAAI 2026 Bridge Program WMAC** (https://multiagents.org/2026/) 2026 topluluk odak noktasıdır. Bu ders MARBLE'ın metriklerine inşa eder, topoloji-vs-metrik bir sweep çalıştırır ve "yalnızca SWE-bench Verified'ı geçmek genelleme kanıtı değildir" kuralını sabitler.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 15 (Voting ve Debate Topology), Faz 16 · 23 (Başarısızlık Modları)
**Süre:** ~75 dakika

## Sorun

Bir makale "çoklu-agent sistemimiz daha iyi" iddia ettiğinde soru şu: neyden daha iyi, neyde, nasıl ölçülmüş? 2023-2024 çoklu-agent değerlendirme dönemi kaostu — herkes kendi metriklerini, kendi baseline'larını ve kendi görev setlerini seçti. 2025-2026 benchmark'ları yapı dayattı.

Paylaşılan benchmark'lar olmadan iki çoklu-agent sistemini anlamlı şekilde karşılaştıramazsın. Daha da kötüsü, hold-out benchmark'lar olmadan frontier modeller kontaminasyon yapabilir. SWE-bench Verified 2025 ortasında eğitim corpus'larında kısmen kontamine oldu; frontier skorları şişti; Pro kontamine olmamış bir gerçeklik kontrolü olarak tasarlandı.

Bu ders beş kanonik 2026 benchmark'ını sıralar, her birinin neyi ölçtüğünü isimlendirir ve sana benchmark iddialarını şüpheyle okumayı öğretir.

## Kavram

### MultiAgentBench (MARBLE) — ACL 2025

arXiv:2503.01935. Araştırma, kodlama ve planlama görevlerinde dört koordinasyon topolojisini (star, chain, tree, graph) değerlendirir. Milestone-tabanlı KPI'lar yalnızca final başarıyı değil, kısmi ilerlemeyi izler.

Ölçülen sonuçlar:

- **Graph** topoloji araştırma senaryoları için en iyi; any-to-any eleştiriyi destekler.
- **Chain** adım adım iyileştirme kodlamada en iyi.
- **Star** hızlı-faktüel konsolidasyonda en iyi.
- **Coordination tax** graph'ta ~4 agent'tan sonra görünür.
- **Cognitive planning** topolojiler arası ~%3 milestone başarısı ekler.

Şu durumda kullan: koordinasyon topolojilerini elma-elmaya karşılaştırmak istiyorsun. MARBLE repo'su (https://github.com/ulab-uiuc/MARBLE) değerlendiriciyi sağlar.

### COMMA — multimodal asimetrik bilgi

Agent'ların farklı gözlem modalitelerine sahip olduğu ve tam bilgi paylaşımı olmadan koordine olması gereken görevleri kapsar. Raporlanan sonuç rahatsız edici: GPT-4o dahil frontier modeller COMMA'da agent-agent iş birliğinde **rastgele baseline'ı** yenmede zorlanır. Sinyal şu: çoklu-agent modaliteler az-eğitilmiş ve az-değerlendirilmiştir — LLM'ler tek-modalite iş birliğini makul şekilde ele alır; çoklu-modalite koordinasyonu çöker.

Şu durumda kullan: sistemin multimodal ya da asimetrik-bilgi koordinasyonuna sahip. COMMA'nın null sonucu iddia etmeden önce ölçmek için bir uyarıdır.

### MedAgentBoard — alan stres testi

arXiv:2505.12371. Dört tıbbi görev kategorisi: tanı, tedavi planlama, rapor üretimi, hasta iletişimi. Çoklu-agent vs tek-LLM vs geleneksel kural-tabanlı sistemleri karşılaştırır.

Bulgu: çoklu-agent çoğu kategoride tek-LLM'i baskınlaştır**maz**. Çoklu-agent avantajı dardır — görev parçalaması alt görevler net şekilde ayrılabildiğinde yardım eder (tanı + tedavi); koordinasyon yükü uzmanlaşma kazanımını aştığında zarar verir (rapor üretimi).

Şu durumda kullan: alanın net tek-LLM baseline'larına sahip. MedAgentBoard'un dersi genelleşirse, önerilen çoklu-agent sistemlerinin çoğu aşırı-mühendisliklenmiştir.

### AgentArch — kurumsal mimariler

arXiv:2509.10769. Tool kullanımı, bellek ve orkestrasyonun birlikte katmanlandığı kurumsal ayarlar. Benchmark her katmanın katkısını izole eder: tool eklemek ne kadar yardım eder? Bellek eklemek? Çoklu-agent orkestrasyonu eklemek?

Şu durumda kullan: bir kurumsal agent yığını tasarlıyorsun ve her katmanı gerekçelendirmen gerekiyor. AgentArch değerini ölçemeyeceğin özellikleri satın almaktan kaçınmana yardım eder.

### SWE-bench Pro — gerçeklik kontrolü

arXiv:2509.16941. İş uygulamaları, B2B hizmetleri ve geliştirici tool'larını kapsayan 41 repo'da 1865 problem. Daha sonraki eğitim kesimleriyle **kontamine olmayacak** şekilde tasarlandı. Frontier modeller Pro'da ~%23 puan alır vs Verified'da %70+. Boşluk kontaminasyon sinyalidir.

Nisan 2026 skorları:
- Claude Opus 4.7 Pro'da: **%64.3** (açık agent-takım koordinasyonuyla raporlandı; henüz yayınlanmış Anthropic birincil kaynak yok — ön sonuç olarak ele al).
- Verdent (agent scaffold) Verified'da: **%76.1 pass@1** ([teknik rapor](https://www.verdent.ai/blog/swe-bench-verified-technical-report)).
- Agent scaffolding olmadan Pro'da frontier ham skorları: ~%23-35 ([SWE-bench Pro makalesi](https://arxiv.org/abs/2509.16941)).

Çıkarım: "SWE-bench Verified'ı yendik" artık yetenek kanıtı değil. Pro mevcut gating test'tir. Agent-takım scaffolding'i Pro'da ölçülebilir kazanımlar üretir (~30-40 puan delta), bu 2026'da çoklu-agent koordinasyonu için en güçlü ampirik argümanlardan biridir.

### AAAI 2026 WMAC

AAAI 2026 Bridge Program — Workshop on Multi-Agent Coordination (https://multiagents.org/2026/). Çoklu-agent AI araştırması için 2026 topluluk odak noktası. Kabul edilen makaleler ve workshop proceedings yeni yöntemleri değerlendirmek için kanonik mekandır; üretim kararları için WMAC-kabul iddialarını arXiv preprint'lerine erteleme.

### Benchmark iddialarını şüpheyle oku — 2026 kontrol listesi

Biri bir çoklu-agent sonucu iddia ettiğinde:

1. **Hangi benchmark, hangi split?** SWE-bench Verified vs Pro çok önemli. Yanlış split'te raporlanan bir sayı değersizdir.
2. **Kontaminasyon kontrolü.** Benchmark modelin eğitim kesiminden sonra mı yayınlandı? Değilse, dikkatle ele al.
3. **Baseline karşılaştırması.** Tek-LLM baseline vs, rastgele vs, önceki çoklu-agent çalışması vs. "aynı sistemin ayarlanmamış versiyonu vs" değil.
4. **İstatistiksel anlamlılık.** N deneme, p-değer, güven aralığı. Frontier modeller yüksek-varyanstır; tek çalıştırmalar yanıltır.
5. **Görev çeşitliliği.** Tek görev mi çok mu? Genelleme üretim için önemlidir.
6. **Maliyet açıklaması.** Görev başına token, duvar-saati. 20× maliyette %90 çözüm bir iş kararıdır, yetenek iddiası değildir.

### Hiçbir benchmark'ın iyi ölçmediği şeyler

- **Uzun-vadeli koordinasyon.** Günlerce duvar-saati etkileşim. Tüm mevcut benchmark'lar kısa çalışır.
- **Adversarial direnç.** Bir agent kötü niyetli ya da tehlikeye atıldığında ne olur?
- **Dağıtım altında drift.** Benchmark'lar statiktir; üretim dağılımları kayar.
- **Maliyet-normalize edilmiş performans.** Çoğu benchmark dolar başına doğruluğu değil, ham doğruluğu raporlar.

Gerçekten önemsediğin eksen için kendi iç benchmark'ını inşa etmek çoğu zaman doğru hamledir.

## İnşa Et

`code/main.py` etkileşimsiz bir gezintidir:

- Bir oyuncak görev üzerinde 3 çoklu-agent sistemi simüle eder.
- Her biri için MARBLE-stili milestone metrikleri hesaplar.
- Bir "eğitim" setinden görevleri tutarak bir kontaminasyon kontrolü çalıştırır.
- Rastgele bir baseline'a açıkça karşılaştırır.
- Bir benchmark-iddiaları scorecard'ı yazdırır.

Çalıştır:

```bash
python3 code/main.py
```

Beklenen çıktı: ham doğruluk, milestone başarısı, görev başına maliyet, vs-rastgele baseline delta ve bir kontaminasyon-kontrolü notu ile sistem scorecard'ı.

## Kullan

`outputs/skill-benchmark-reader.md` herhangi bir çoklu-agent benchmark iddiasını okur ve scrutiny kontrol listesini uygular. Çıktı: bir not ve uyarılar.

## Yayınla

Üretim değerlendirme disiplini:

- **Bir iç benchmark inşa et** ki gerçek üretim dağılımını yansıtsın. Halka açık benchmark'lar bilgilendirir ama yerine geçmez.
- **Her karşılaştırmaya bir rastgele baseline ekle.** Bir koordinasyon görevinde rastgeleyi büyük marjla yenemiyorsan, görev kötü-konulmuş olabilir.
- **Doğruluğun yanında maliyet raporla.** Token maliyeti ve duvar-saati. Ops takımları ikisine de ihtiyaç duyar.
- **Benchmark'ı çeyrek başına yeniden inşa et.** Üretim dağılımı kayar; bayat benchmark'lar yanıltır.
- **Yayınlanmış-benchmark overfitting'inden kaçın.** Takımın özellikle SWE-bench Pro sayılarına optimize ediyorsa, üretimde gerileyeceksin.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Üç simüle edilmiş sistemden hangisinin en iyi maliyet-başına-milestone'a sahip olduğunu belirle. En yüksek ham-doğruluk sistemiyle eşleşiyor mu?
2. MultiAgentBench'i (arXiv:2503.01935) oku. Kendi görev alanın için MARBLE'ın dört topolojiden hangisini öneriyor olacağına karar ver. Makalenin sonuçlarından gerekçelendir.
3. SWE-bench Pro makalesini oku. Onu kontaminasyon-dirençli kılan özellikle ne? Aynı teknik önemsediğin diğer benchmark'lara uygulanabilir mi?
4. COMMA'nın multimodal koordinasyon bulgusunu oku. İç benchmark'ına ekleyebileceğin basit bir multimodal koordinasyon görevi tasarla. Yararlı bir sinyal olarak ne sayılacak?
5. Benchmark-iddiaları kontrol listesini son bir çoklu-agent makalesinin manşet sonucuna uygula. İddiaya hangi notu verirdin?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| MARBLE | "MultiAgentBench" | ACL 2025; milestone KPI'larıyla star/chain/tree/graph topolojiler. |
| COMMA | "Multimodal benchmark" | Multimodal asimetrik-info koordinasyon; frontier modeller rastgeleye karşı zorlanır. |
| MedAgentBoard | "Alan stres testi" | Dört tıbbi kategori; sıklıkla çoklu-agent'ın tek-LLM'i baskınlaştırmadığını bulur. |
| AgentArch | "Kurumsal benchmark" | Tool'lar + bellek + orkestrasyon katmanlanmış. |
| SWE-bench Pro | "Kontaminasyon-dirençli" | 1865 problem, 41 repo; ~%23 vs Verified'da %70+ (kontaminasyon sinyali). |
| Milestone başarısı | "Kısmi kredi" | Yalnızca final başarıyı değil, ilerlemeyi ödüllendiren benchmark'lar. |
| Kontaminasyon | "Benchmark eğitime sızdı" | Yayın sonrası, benchmark'lar eğitim corpus'larına kayar; skorlar şişer. |
| WMAC | "AAAI 2026 Bridge Program" | Workshop on Multi-Agent Coordination; topluluk odak noktası. |

## İleri Okuma

- [MultiAgentBench / MARBLE](https://arxiv.org/abs/2503.01935) — milestone KPI'lı topoloji benchmark'ı
- [MARBLE repository](https://github.com/ulab-uiuc/MARBLE) — referans implementasyon
- [MedAgentBoard](https://arxiv.org/abs/2505.12371) — alan stres testi; çoklu-agent sıklıkla baskınlaştırmaz
- [AgentArch](https://arxiv.org/abs/2509.10769) — kurumsal agent mimarileri
- [SWE-bench leaderboards](https://www.swebench.com/) — frontier modeller için Verified ve Pro skorları
- [AAAI 2026 WMAC](https://multiagents.org/2026/) — 2026 topluluk odak noktası
