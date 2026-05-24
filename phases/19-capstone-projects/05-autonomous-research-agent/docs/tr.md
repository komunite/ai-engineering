# Capstone 05 — Otonom Araştırma Agent'ı (AI-Scientist Sınıfı)

> Sakana'nın AI-Scientist-v2'si tam makaleler yayınladı. Agent Laboratory deneyleri çalıştırdı. Allen AI trace'ler paylaştı. 2026 şekli deneyler üzerinde plan-execute-verify ağaç araması, bütçelenmiş maliyet, sandbox'lanmış kod yürütme, vision-feedback bir LaTeX yazıcı ve otomatize NeurIPS-tarzı bir reviewer ensemble. Capstone bir tane inşa etmek, makale başına $30 içinde uçtan uca çalıştırmak ve Sakana'nın belgelediği sandbox-kaçış red team'ini atlatmak.

**Tür:** Bitirme
**Diller:** Python (agent + sandbox), LaTeX (çıktı)
**Ön koşullar:** Faz 2 (ML), Faz 3 (deep learning), Faz 7 (transformer'lar), Faz 10 (LLM'ler sıfırdan), Faz 14 (agent'lar), Faz 15 (otonom), Faz 16 (multi-agent), Faz 18 (safety)
**Egzersize edilen fazlar:** P0 · P2 · P3 · P7 · P10 · P14 · P15 · P16 · P18
**Süre:** 40 saat

## Sorun

Otonom araştırma agent'ları 2026'da bir eşiği geçti. Sakana AI'nin AI-Scientist-v2'si, workshop peer review'unu temizleyen üretilmiş makalelerle Nature'da yayınlandı. ShinkaEvolve (ICLR 2026) çizgiyi evrilen hipotezlere extend etti. AMD'nin Agent Laboratory'si yeniden üretilebilir trace'ler yayınladı. Agent'lar büyü değil — aday deneyler ağacı üzerinde çalışan, cost cap'leri, seed-bound sandbox'ları ve otomatize review'ı olan bir plan-execute-verify loop'u. Zanaat loop'ta, bütçede ve safety hikayesinde.

Loop'u dar bir domain'de bir seed fikre karşı bir tane implement ederek öğreniyorsun (örneğin 100M-parametreli transformer'da attention-sparsity ablation'ları). Değer ilk koşuda yeni bir şey keşfetmekte değil. Değer altyapıda: ağaç araması, deney sandbox'ı, writer-reviewer loop'u, red-team raporu. Sakana ekibi sandbox-kaçış başarısızlıklarını belgeledi; senin agent'ın aynı red team'i geçmeli.

## Kavram

Agent best-first bir ağaç araması. Node'lar deney spesifikasyonları: (hipotez, config, kod, beklenen sonuç). Bir expand adımı küçük edit'lerle çocuklar önerir (optimizer değiştir, batch size kaydır, bir bileşeni ablate et). Her çocuk sert resource cap'li taze bir sandbox'ta çalışır. Sonuçlar, node'ları (yenilik × kalite × kalan bütçe) ile sıralayan bir scoring fonksiyonuna geri besler. Ağaç bütçe tükenene kadar büyür, sonra en iyi branch yazılır.

Yazıcı multimodal. Bir LaTeX taslağı üretir, compile eder, figure'ları render eder ve render edilmiş PDF'i layout, figure okunabilirliği ve iddia-evidence hizalaması için Claude Opus 4.7'nin vision mode'una geri besler. Beş LLM yargıcından oluşan reviewer ensemble NeurIPS-tarzı skorlar emit eder (yenilik, titizlik, netlik, yeniden üretilebilirlik, etki); ortalama eşiğin altına düşerse, makale eleştirisiyle yazıcıya döner.

Safety load-bearing. Her deney network egress'siz, bounded wall-clock'lu ve pinned resource limit'li bir E2B veya Daytona sandbox'ında çalışır. Agent'ın kod üretme adımı sandbox'tan kaçan syscall'ları bloklayan bir policy katmanından geçer. Red-team raporu Sakana-belgelenmiş attack surface'i (fork bomb'lar, filesystem kaçışları, LLM-yazılı network call'ları) yeniden üretir.

## Mimari

```
seed fikir + domain
      |
      v
  literatür arama (Semantic Scholar + OpenAlex + FAISS cache)
      |
      v
  LangGraph plan-execute-verify ağacı
      |
      v
  +--- expand node ----+      node başına sandbox
  |                    |      (E2B / Daytona)
  v                    v      resource cap'leri
  child_1           child_k   network egress yok
  |                    |      deterministik seed'ler
  v                    v
  deney çalıştır       deney çalıştır
  |                    |
  v                    v
  node'ları (yenilik, kalite, bütçe) ile skorla
      |
      v
  en iyi branch -> LaTeX yazıcı
      |
      v
  compile + vision eleştirisi (Opus 4.7 vision)
      |
      v
  reviewer ensemble (5 LLM yargıç, NeurIPS rubrik)
      |
      v
  paper.pdf + review.md + trace.json
```

## Stack

- Orkestrasyon: checkpointing'li ve human-approval gate'li LangGraph
- Ağaç araması: deney node'ları üzerinde custom best-first (Sakana v2'den AB-MCTS-tarzı)
- Sandbox: deney başına E2B, fallback olarak Docker-in-Docker; cgroups üzerinden resource cap'leri
- Literatür: Semantic Scholar Graph API + OpenAlex + abstract'ların lokal FAISS cache'i
- Yazıcı: LaTeX template + figure eleştirisi ve layout için Claude Opus 4.7 (vision mode)
- Reviewer: ağırlıklı aggregation'lı 5 yargıçtan ensemble (Opus 4.7, GPT-5.4, Gemini 3 Pro, DeepSeek R1, Qwen3-Max)
- Deney framework'ü: fiziksel deneyler için PyTorch 2.5, logging için W&B
- Observability: agent trace'leri için Langfuse, makale başına $30 sert bütçe

## İnşa Et

1. **Seed ve domain scoping.** Bir seed fikir al (örn. "sub-1B transformer'larda attention map'lerinde sparsity pattern'larını araştır"). Arama uzayını tanımla: model'ler, dataset'ler, compute bütçesi.

2. **Literatür geçişi.** Semantic Scholar + OpenAlex'i en çok atıf alan 50 ilgili makale için sorgula; abstract'ları lokal cache'le; 1 sayfalık domain digest üret.

3. **Ağaç iskele.** Root'u seed hipotez ile initialize et. Küçük-edit önerileriyle (çocuk başına bir config değişikliği) `expand(node) -> children` implement et. `score(node)`'u ağırlıklı yenilik × kalite × bütçe terimi olarak implement et.

4. **Sandbox wrap'leme.** Her deney `docker run --network=none --memory=8g --cpus=2 --pids-limit=256 --read-only` çalıştırır (veya eşdeğer E2B policy'si). Seed'ler sandbox'a yazılır; çıktılar read-only mount'la geri çıkar.

5. **Plan-execute-verify loop'u.** `plan` çocukları önerir. `execute` sandbox'ı çalıştırır, log'ları ve metrik'leri yakalar. `verify` metrik'lerde unit check'leri çalıştırır (loss düştü mü? ablation etkiyi izole etti mi?). Başarısız node'lar ağaçta bir başarısızlık sebebi alır.

6. **Yazıcı.** Bütçeden sonra en iyi branch'i seç. matplotlib ile figure'ları render et. Branch trace'i context'te tutarak Claude Opus 4.7 üzerinden bir LaTeX taslağı üret. Compile et. Compile edilmiş PDF'i eleştiri için Opus 4.7 vision'a geri besle. Iterate et.

7. **Reviewer ensemble.** Beş yargıç taslağı (yenilik, titizlik, netlik, yeniden üretilebilirlik, etki) üzerinde NeurIPS-tarzı rubrik'lerle skorlar. Ortalama < 4.0/5 ise eleştiri ile yazıcıya dön. 3 rewrite'tan sonra sert dur.

8. **Red team.** Sandbox'ı hedefleyen bir dizi adversarial task inşa et veya entegre et: fork bomb'lar, network exfiltration denemeleri, filesystem kaçışları, LLM-yazılı shell metacharacter'ları. Hepsinin bloklandığını doğrula. Bulguları yaz.

9. **Yeniden üretilebilirlik.** Her makale ağaç-arama trace JSON'u, seed'ler, W&B run link'leri, sandbox config'leri ve uçtan uca yeniden üreten bir README ile gelir.

## Kullan

```
$ ai-scientist run --seed "sub-1B transformer'larda attention sparsity" --budget 30
[lit]    50 makale, digest 12s'de
[tree]   8 node expand edildi, bütçe 12/30
[exec]   node #3 sparsity=top-8, loss=2.83 (şimdiye kadar en iyi)
[exec]   node #6 sparsity=top-4, loss=3.12 (daha kötü)
[exec]   ...
[tree]   node #3'te kök salan branch'i seçti (yenilik 0.62, kalite 0.81)
[write]  LaTeX taslak v1 tamam
[vision] eleştiri: figure 2 legend çok küçük, iddia-evidence ok
[write]  3 edit sonrası taslak v2
[review] ortalama 4.2/5 (yenilik 3.9, titizlik 4.3, netlik 4.1, repro 4.5, etki 4.2)
[done]   paper.pdf + review.md + trace.json     $28.40 harcandı
```

## Yayınla

Teslimat `outputs/skill-ai-scientist.md`. Bir seed fikir + bir domain + bir $30 bütçesi verildiğinde, full pipeline'ı çalıştırır ve incelenebilir bir makale artı bir yeniden üretilebilirlik paketi emit eder.

| Ağırlık | Kriter | Nasıl ölçülür |
|:-:|---|---|
| 25 | Makale kalitesi | Yayınlanmış workshop makalelerine karşı kör rubrik incelemesi |
| 20 | Deneysel titizlik | Baseline'lar, seed'ler, ablation'lar; her iddia sonuç tablosundaki bir hücreyle desteklenir |
| 20 | Maliyet ve compute disiplini | $30/makale tavanı uygulanır, Langfuse-trace'lenir |
| 20 | Safety | Sandbox red team'i geçer; network policy ve kill-switch doğrulanır |
| 15 | Yeniden üretilebilirlik | Identik seed'lerle tek komutluk yeniden çalıştırma makaleyi üretir |
| **100** | | |

## Alıştırmalar

1. Pipeline'ı aynı domain'de üç farklı seed fikre karşı çalıştır. Ağaç-aramasının hangi kısımlarının örtüştüğünü karşılaştır. Duplike edilmiş boşa giden compute'u belirle.

2. $5 üzerinde tahmin edilen node'lar için deney yürütmeden önce bir human-in-the-loop gate ekle. Toplam maliyetin ne kadar düştüğünü ölç.

3. Reviewer ensemble'ı tek bir yargıçla değiştir. Bilinen-kötü makalelerin holdout set'inde false-accept oranını ölç.

4. Bir network-exfiltration red team testi tanıt: agent harici bir adrese `curl` yapan kod yazar. `--network=none` policy'sinin onu blokladığını doğrula. Denemeyi logla.

5. Ağaç-aramanı flat random baseline ile karşılaştır (aynı bütçe, expansion stratejisi yok). Yenilik × kalite kazancını raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Ağaç araması | "AB-MCTS-tarzı expansion" | Yenilik×kalite×bütçe skoruyla deney node'ları üzerinde best-first keşif |
| Sandbox | "Deney izolasyonu" | Network yok, bounded CPU/memory'li, pinned seed'li, read-only input'lu container |
| Vision eleştirisi | "Render-then-read" | Makaleyi PDF'e compile et, PDF'i layout ve iddia-evidence eleştirisi için VLM'e geri besle |
| Reviewer ensemble | "Otomatize peer review" | NeurIPS rubriği ile makaleyi skorlayan birden çok LLM yargıç; ağırlıklı aggregate pipeline'ı kapılar |
| Yenilik skoru | "Bu yeni mi?" | 50-makale literatür cache'ine yakınlığı cezalandıran heuristic |
| Cost ceiling | "$ bütçesi" | Makale başına toplam harcamanın sert cap'i; Langfuse counter'ları + pre-run tahminleri |
| Red team | "Sandbox-kaçış denetimi" | Policy yanlışsa sandbox'tan kaçacak adversarial task'lar |

## İleri Okuma

- [Sakana AI-Scientist-v2 repository'si](https://github.com/SakanaAI/AI-Scientist-v2) — referans üretim araştırma agent'ı
- [Sakana AI-Scientist-v1 makalesi (arXiv:2408.06292)](https://arxiv.org/abs/2408.06292) — orijinal methodology
- [ShinkaEvolve (Sakana ICLR 2026)](https://sakana.ai) — evrimsel extension
- [Agent Laboratory (AMD)](https://github.com/SamuelSchmidgall/AgentLaboratory) — multi-role research-lab framework'ü
- [LangGraph dokümantasyonu](https://langchain-ai.github.io/langgraph/) — referans orkestrasyon katmanı
- [Semantic Scholar Graph API](https://api.semanticscholar.org/) — literatür arama
- [E2B sandbox'ları](https://e2b.dev) — referans deney izolasyonu
- [NeurIPS reviewer guideline'ları](https://neurips.cc/Conferences/2026/Reviewer-Guidelines) — reviewer ensemble'ın encode ettiği rubrik
