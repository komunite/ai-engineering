# Otonom Coding Agent Manzarası (2026)

> SWE-bench Verified üç yıldan kısa sürede %4'ten %80.9'a çıktı. Aynı Claude Sonnet 4.5, SWE-agent v1'de %43.2 ve Cline autonomous'ta %59.8 aldı — modelin etrafındaki iskele artık modelin kendisi kadar önemli. OpenHands (eski adıyla OpenDevin) en aktif MIT-lisanslı platform ve CodeAct döngüsü JSON tool çağrıları yerine doğrudan bir sandbox'ta Python aksiyonları yürütür. Manşet rakamlar metodolojik bir sorunu gizler: SWE-bench Verified'ın 500 görevinden 161'i yalnızca 1-2 satırlık bir değişiklik gerektiriyor ve SWE-bench Pro (10+ satırlık görevler) aynı frontier modeller için %23-59'da oturuyor.

**Tür:** Öğrenim
**Diller:** Python (stdlib, CodeAct vs JSON tool-çağrısı karşılaştırması)
**Ön koşullar:** Faz 14 · 07 (Tool kullanımı), Faz 15 · 01 (Uzun-horizon agent'lar)
**Süre:** ~45 dakika

## Sorun

"Hangi coding agent en iyi" yanlış soru. Doğru soru şu: işime uygun bir görev dağılımında, üretimde çalıştıracağım iskele ile, hangi uçtan uca güvenilirliği alıyorum?

2022 ile 2026 arasında alan, iskelenin — retrieval katmanı, planner, sandbox, edit-verify döngüsü, geri bildirim formatı — yük taşıdığını öğrendi. SWE-agent v1'de Claude Sonnet 4.5 SWE-bench Verified'da %43.2 aldı; Cline'ın otonom iskelesi içinde aynı model %59.8 aldı. 16.6 mutlak puan fark, aynı ağırlıklar. Base model bir bileşendir; döngü üründür.

Eşlik eden problem benchmark doygunluğunun regresyonları gizlemesidir. SWE-bench Verified doygunluğa yakındır ve kolay-görev kuyruğu (500'den 161 görev ≤2 satır gerektirir) üst skorları yukarı çeker. Gerçek dünya kalitesi, aynı liderlerin hâlâ %23-59'da oturduğu SWE-bench Pro (10+ satırlık değişiklikler) gibi dağılımlarda daha iyi ölçülür.

## Kavram

### SWE-bench, bir paragrafta

SWE-bench (Jimenez vd.) ground-truth patch'leri olan gerçek GitHub issue'larını alır ve bir agent'tan test suite'ini geçiren bir patch üretmesini ister. SWE-bench Verified (OpenAI, 2024), belirsiz ve bozuk görevler kaldırılmış insan-küratörlü 500-görev altkümesidir. SWE-bench Pro daha zor halefidir — 10+ satırlık değişiklik gerektiren görevler, mevcut frontier agent'lar %23-59'da oturur.

### 2022 → 2026 eğrisinin aslında gösterdiği

- **2022**: araştırma modelleri ham SWE-bench'te ~%4.
- **2024**: GPT-4 + Devin tarzı iskele ~%14'te; SWE-agent ~%12'de.
- **2025**: Aider ve SWE-agent içindeki Claude 3.5/3.7 Sonnet %40-55 aralığına girer.
- **2026**: Claude Sonnet 4.5 ve frontier rakipleri SWE-bench Verified'da %70-80+'da. Epoch AI'ın liderboard'u bunu canlı izler.

Eğim üç bileşik kaynak'tan geldi: daha iyi base modeller, daha iyi iskele (CodeAct, reflection, verifier döngüleri) ve daha iyi benchmark'lar (Verified gürültüyü kaldırarak).

### CodeAct vs JSON tool çağrıları

OpenHands (All-Hands-AI, arXiv:2407.16741, eski adıyla OpenDevin) belirli bir mimari bahis koydu: bir host'un decode edip yürüttüğü JSON tool çağrıları yayan model yerine, model Python kodu yayar ve Jupyter tarzı bir kernel bunu bir sandbox'ta çalıştırır. Agent dosyalar üzerinde döngü kurabilir, tool'ları zincirleyebilir ve tek bir aksiyon içinde kendi exception'larını yakalayabilir.

Trade-off:

- **JSON tool çağrıları**: her aksiyon bir tur; audit etmesi kolay; sınırlı kompozisyon; her çağrı açık bir validator'dan geçtiği için varsayılan olarak safe.
- **CodeAct**: bir aksiyon bir tüm program olabilir; kompozisyonel; sertleştirilmiş bir sandbox gerektirir (OpenHands Docker izolasyonu kullanır); failure mode'lar sandbox runtime'ının izin verdiği her şeyi içerir.

İki mimari de üretimde. CodeAct açık platformlarda baskındır (OpenHands, smolagents). JSON tool çağrıları sağlayıcının executor'ı kontrol ettiği yönetilen servislerde (Anthropic Managed Agents, OpenAI Assistants) baskın kalır.

### 2026 manzarasında iskeleler

| İskele | Lisans | Yürütme modeli | Dikkate değer özellik |
|---|---|---|---|
| OpenHands (OpenDevin) | MIT | Docker'da CodeAct | En aktif açık platform; event-stream replayable |
| SWE-agent | MIT | Agent-Computer Interface (ACI) | İlk uçtan uca SWE-bench iskelesi |
| Aider | Apache-2 | yerel repo'da diff ile edit | Minimal iskele, güçlü regresyon kararlılığı |
| Cline | Apache-2 | tool politikalı VS Code agent | Sonnet 4.5'te en yüksek skorlu açık iskele |
| Devin (Cognition) | Mülk | Yönetilen VM + planner | İlk "AI yazılım mühendisi" ürün kategorisi |
| Claude Code | Mülk | Permission mode'ları + routine'ler | Ders 10 agent döngüsünü detayda kapsar |

### İskele neden baskın

Bir coding koşusu uzun-horizon bir trajectory'dir (Ders 1). Güvenilirlik adımlar boyunca bileşik kazanır. İskelenin puan satın aldığı üç yer:

1. **Retrieval**: okunacak doğru dosyaları bulmak sessiz darboğazdır. SWE-agent'ın ACI'sı, OpenHands'in file-index'i ve Aider'ın repo-map'i hepsi buna saldırır.
2. **Verifier döngüsü**: test'leri çalıştırmak, stack trace'leri okumak ve yeniden denemek SWE-bench'te 10+ puanlık bir delta'dır.
3. **Failure containment**: hatada rollback yapan bir sandbox bileşik hasarı önler. Verifier döngüsü olan ve olmayan aynı model iki farklı ürün gibi görünür.

### Benchmark doygunluğu ve gerçek dağılım

OpenHands yazarları ve Epoch AI, SWE-bench Verified'ın kolay bir kuyruğa sahip olduğunu işaretliyor: 500 görevden 161'i yalnızca 1-2 satırlık bir değişiklik gerektiriyor. Yüksek skorlar kısmen bu kuyruk tarafından sürülüyor. SWE-bench Pro 10+ satırlık değişikliklere kısıtlar ve frontier sistemler için bile %23-59 aralığında skorlar döndürür. Üretim dağılımın neredeyse kesinlikle Verified'dan çok Pro'ya yakındır.

Bir agent seçmek için ima: kendi bug backlog'unun Pro benzeri bir altkümesini çalıştır. Önemli olan skor, gönderdiğin şeyi temsil eden görevlerdeki skordur.

## Kullan

`code/main.py` sabit bir mini-görev dağılımında iki oyuncak agent iskelesini karşılaştırır:

1. Tur başına bir aksiyon alan bir **JSON tool-çağrısı** iskelesi.
2. Aksiyon başına küçük bir Python snippet yayabilen bir **CodeAct** iskelesi.

Her ikisi de bir stub "model" (deterministik kurallar) kullanır, böylece karşılaştırma iskeleyi model kalitesinden izole eder. Çıktı, CodeAct iskelesinin daha fazla görevi daha az turda çözdüğünü, aksiyon başına daha büyük bir blast radius pahasına gösterir.

## Yayınla

`outputs/skill-scaffold-audit.md`, önerilen bir coding-agent iskelesini benimsenmeden önce audit etmene yardım eder: retrieval kalitesi, verifier varlığı, sandbox izolasyonu ve benchmark-dağılım uyumu.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Her iskele aynı görev setinde kaç tur alıyor? Her birinin aksiyon başına blast radius'u nedir?

2. OpenHands makalesini (arXiv:2407.16741) oku. Makale CodeAct'in karmaşık görevlerde JSON tool çağrılarını yendiğini savunur. Makalenin kabul ettiği bir failure mode'u belirle ve o mode'un üretimde ne zaman baskın olacağına dair bir cümle yaz.

3. Bug backlog'ından iki dosyada 10+ satırlık değişiklik gerektirecek bir görev seç. (a) JSON tool çağrıları ve (b) CodeAct altında bir frontier model için uçtan uca başarı olasılığını tahmin et. Farkı gerekçelendir.

4. SWE-bench Verified'ın 161 tek-dosya, 1-2 satırlık görevi var. Onları dışlayan bir skor oluştur. Liderboard nasıl karışıyor?

5. "Introducing SWE-bench Verified"ı (OpenAI) oku. Belirsiz görevleri kaldırmak için kullanılan belirli metodolojiyi açıkla ve küratörlüğün kaçıracağı bir kategori söyle.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| SWE-bench | "Coding benchmark'ı" | Ground-truth patch'leri ve test suite'leri olan gerçek GitHub issue'ları |
| SWE-bench Verified | "Temizlenmiş altküme" | 500 insan-küratörlü görev, kolay-kuyruk mevcut |
| SWE-bench Pro | "Daha zor altküme" | 10+ satırlık değişiklikler; frontier %23-59'da oturuyor |
| CodeAct | "Code-as-action" | Agent Python yayar; Jupyter tarzı kernel sandbox'ta yürütür |
| JSON tool çağrısı | "Function calling" | Her aksiyon yürütmeden önce doğrulanan yapılandırılmış bir JSON payload'u |
| İskele | "Agent framework'ü" | Base modelin etrafında retrieval + planner + executor + verifier döngüsü |
| ACI (Agent-Computer Interface) | "SWE-agent'ın formatı" | İnsan shell'leri için değil LLM ergonomisi için tasarlanmış komut seti |
| Verifier döngüsü | "Test-ve-retry" | Test'leri çalıştır, çıktıyı oku, patch'i revize et; en büyük model-dışı güvenilirlik kazancı |

## İleri Okuma

- [Jimenez et al. — SWE-bench](https://www.swebench.com/) — orijinal benchmark ve metodoloji.
- [OpenAI — Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) — küratörlü altkümenin nasıl kurulduğu.
- [Wang et al. — OpenHands: An Open Platform for AI Software Developers](https://arxiv.org/abs/2407.16741) — CodeAct mimarisi ve event-stream tasarımı.
- [Epoch AI — SWE-bench leaderboard](https://epoch.ai/benchmarks) — canlı izlenen skorlar.
- [Anthropic — Measuring agent autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) — uzun-horizon coding-agent güvenilirlik çerçevesi.
