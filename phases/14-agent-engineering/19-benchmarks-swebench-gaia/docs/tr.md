# Benchmark'lar: SWE-bench, GAIA, AgentBench

> Üç benchmark 2026'da agent değerlendirmesinin demir attığı yerler. SWE-bench kod patch'lemeyi test eder. GAIA generalist tool use'u test eder. AgentBench multi-environment akıl yürütmeyi test eder. Kompozisyonlarını, kontaminasyon hikayelerini ve neyi ölçmediklerini bil.

**Tür:** Öğrenim
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 06 (Tool Use)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- SWE-bench'in test harness'ını (FAIL_TO_PASS) adlandır ve neden unit testlere kapı koyduğunu açıkla.
- SWE-bench Verified'ın (OpenAI, 500 task) neden var olduğunu ve neyi çıkardığını açıkla.
- GAIA'nın tasarımını açıkla: insanlar için basit, AI için zor; üç zorluk seviyesi.
- AgentBench'in sekiz ortamını ve açık kaynak LLM'ler için birincil engelini adlandır.
- SWE-bench+ kontaminasyon bulgusunu ve sonuçlarını özetle.

## Sorun

Leaderboard'lar bir benchmark'ta hangi modelin kazandığını söyler. Şunları söylemez:

- Benchmark'ın kontamine olup olmadığını (eğitim verisinde çözümler, test sızıntısı).
- Benchmark'ın önemsediğin şeyi ölçüp ölçmediğini (kod vs browsing vs generalist).
- Evaluator'ın sağlam olup olmadığını (AST eşleştirme, state checks, insan inceleme).

Bir sayıyı alıntılamadan önce üç demir-atan benchmark'ı ve başarısızlık modlarını bil.

## Kavram

### SWE-bench (Jimenez et al., ICLR 2024 oral)

- 12 popüler Python repo'sundan 2,294 gerçek GitHub issue.
- Agent şunu alır: pre-fix commit'teki codebase + doğal-dil issue açıklaması.
- Agent şunu üretir: bir patch.
- Evaluator: patch'i uygula, repo'nun test suite'ini çalıştır. Patch FAIL_TO_PASS testlerini (önceden başarısız, şimdi başarılı) PASS_TO_PASS testlerini bozmadan çevirmeli.

SWE-agent (Yang et al., 2024) agent-computer arayüzlerini (file editor komutları, modelin anladığı arama syntax'ı) vurgulayarak yayında %12.5'e vurdu.

### SWE-bench Verified

OpenAI, Ağustos 2024. İnsan-küratörlü 500-task alt küme. Belirsiz issue'ları, güvenilmez testleri ve fix'in net olmadığı task'ları kaldırır. "Agent'ın gerçek patch yayar mı?" için birincil benchmark.

### Kontaminasyon

- SWE-bench issue'larının %94'ten fazlası çoğu model cutoff'undan önce.
- **SWE-bench+** başarılı patch'lerin %32.67'sinin issue text'inde çözüm sızdırdığını (model description'da fix'i gördü), %31.08'inin zayıf test kapsamı nedeniyle şüpheli olduğunu buldu.
- Verified daha temiz ama kontaminasyon-free değil.

Pratik sonuç: SWE-bench'te %50 puan alan bir model SWE-bench+'ta %35 puan alabilir. SWE-bench performansı iddia ediyorsan her zaman ikisini raporla.

### GAIA (Mialon et al., Kasım 2023)

- 466 soru; özel leaderboard için huggingface.co/gaia-benchmark'ta 300 alıkonuldu.
- Tasarım felsefesi: "insanlar için kavramsal olarak basit (%92) ama AI için zor (plugin'li GPT-4: %15)."
- Akıl yürütme, multi-modality, web, tool use'u test eder.
- Üç zorluk seviyesi; Seviye 3 modaliteler arası uzun tool zincirleri gerektirir.

GAIA "generalist yetenek"i ölçmek için çalıştırdığın şey. Koda-özgü benchmark'larla karıştırma.

### AgentBench (Liu et al., ICLR 2024)

- 8 ortam: kod (Bash, DB, KG), oyunlar (Alfworld, LTP), web (WebShop, Mind2Web) ve açık-uçlu generation.
- Multi-turn, split başına ~4k-13k tur.
- Birincil bulgu: uzun vadeli akıl yürütme, karar verme ve talimat takibi OSS LLM'lerin ticariye yetişmesindeki engeller.

### Bunların ölçmediği şeyler

- Gerçek-dünya operasyonel maliyet (token, wall-clock).
- Adversarial koşullarda safety davranışı.
- Senin domain'inde performans (kendi eval'lerini kullan, Ders 30).
- Tail başarısızlıkları (benchmark'lar ortalama; üretim operatörleri en kötü %1'i önemser).

### Benchmark'lama nerede ters gider

- **Tek-sayı saplantısı.** SWE-bench %50 sana P50/P75/P95 maliyet + adım dağılımından daha azını söyler.
- **Kontamine iddialar.** Verified ya da SWE-bench+'tan bahsetmeden SWE-bench raporlamak yanıltıcı.
- **Geliştirme-hedefi-olarak-benchmark.** Benchmark için optimize etmek üretim faydasından ayrılır.

## İnşa Et

`code/main.py` oyuncak bir SWE-bench-benzeri harness uyguluyor:

- Sentetik bug-fix task'ları (3 task).
- Patch öneren scripted bir "agent."
- FAIL_TO_PASS (bug şimdi fix'lendi) ve PASS_TO_PASS (hiçbir şey kırılmadı) kontrol eden bir test runner.
- Soru dekompozisyon derinliğine dayalı GAIA-tarzı zorluk sınıflandırıcısı.

Çalıştır:

```
python3 code/main.py
```

Çıktı task başına + zorluk başına çözüm oranı gösterir ve evaluator kurallarını somutlaştırır.

## Kullan

- **SWE-bench Verified** kod agent'ları için. Her zaman Verified skorlarını raporla.
- **GAIA** generalist agent'lar için. Özel leaderboard split'i kullan.
- **AgentBench** multi-environment karşılaştırma için.
- **Custom eval'ler** (Ders 30) ürününün gerçek şekli için.

## Yayınla

`outputs/skill-benchmark-harness.md` herhangi bir codebase-task çifti için FAIL_TO_PASS / PASS_TO_PASS kapısıyla SWE-bench-tarzı bir harness kurar.

## Alıştırmalar

1. Oyuncak harness'ı gerçek bir repo (seninkilerden birini seç) üzerinde çalıştırmak için port et. Bilinen bug'lar için 3 FAIL_TO_PASS testi yaz.
2. Bir step-count metriği ekle. 3 task'ında, çözüm başına kaç agent adımı?
3. SWE-bench+ makalesini oku. Bir solution-leakage check uygula (issue text'ini diff'e karşı pattern-match).
4. Public split'ten bir GAIA sorusu indir. GPT-4-sınıfı bir agent'ın ne yapacağını trace et. Hangi tool'lara ihtiyacı var?
5. AgentBench'in ortam-başına dağılımını oku. Hangi ortam ürün yüzeyini yansıtıyor? Orada "SOTA" neye benziyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| SWE-bench | "Kod agent benchmark'ı" | 2,294 GitHub issue; patch FAIL_TO_PASS testleri çevirmeli |
| SWE-bench Verified | "Temiz SWE-bench" | 500 insan-küratörlü task, OpenAI |
| FAIL_TO_PASS | "Fix kapısı" | Patch'ten sonra geçmesi gereken önceden başarısız testler |
| PASS_TO_PASS | "No-regression kapısı" | Geçen ve hâlâ geçmesi gereken testler |
| GAIA | "Generalist benchmark" | 466 insan-kolay / AI-zor multi-tool soru |
| AgentBench | "Multi-env benchmark" | 8 ortam; uzun-ufuk multi-turn |
| Kontaminasyon | "Training-set sızıntısı" | Model eğitiminde mevcut benchmark task'ları |
| SWE-bench+ | "Kontaminasyon audit'i" | Başarılı SWE-bench patch'lerinde bulunan %32.67 çözüm sızıntısı |

## İleri Okuma

- [Jimenez et al., SWE-bench (arXiv:2310.06770)](https://arxiv.org/abs/2310.06770) — orijinal benchmark
- [OpenAI, SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) — küratörlü alt küme
- [Mialon et al., GAIA (arXiv:2311.12983)](https://arxiv.org/abs/2311.12983) — generalist benchmark
- [Liu et al., AgentBench (arXiv:2308.03688)](https://arxiv.org/abs/2308.03688) — multi-environment suite
