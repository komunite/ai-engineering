---
name: ai-scientist
description: Experiment tree search çalıştıran, vision critique ile LaTeX makale yazan ve sandbox-escape red team'ini geçen autonomous bir araştırma agent'ı kur.
version: 1.0.0
phase: 19
lesson: 05
tags: [capstone, autonomous-agent, ai-scientist, sakana, langgraph, sandbox, research]
---

Bir seed fikir, dar bir domain ve 30 dolarlık compute bütçesi verildiğinde, experiment tree search çalıştıran, gözden geçirilebilir bir LaTeX makale yazan ve bir reproducibility bundle yayan bir agent kur.

Build planı:

1. Literatür taraması: Semantic Scholar Graph API + OpenAlex; abstract'ları FAISS'te cache'le; 1 sayfalık domain digest üret.
2. Tree search: experiment node'ları üzerinde `expand(node) -> children` (her child için bir config edit) ve `score(node) = novelty*0.4 + quality*0.5 + budget*0.1` ile best-first expansion uygula.
3. Node başına sandbox: her deney `docker run --network=none --memory=8g --cpus=2 --pids-limit=256 --read-only` veya E2B eşdeğeri çalıştırır; deterministic seed'ler; kaynak cap zorlanır.
4. Plan-execute-verify: verify adımı loss'un yakınsadığını, baseline'ların çalıştırıldığını ve ablation'ların iddiayı izole ettiğini kontrol eder.
5. Writer: LaTeX üret, PDF'ye derle, PDF'yi layout ve iddia-kanıt hizalaması üzerine critique için Claude Opus 4.7 vision mode'a besle, 3 kereye kadar yineleme yap.
6. Reviewer ensemble: beş hakem (Opus 4.7, GPT-5.4, Gemini 3 Pro, DeepSeek R1, Qwen3-Max) NeurIPS rubric'ine göre skorlar (novelty, rigor, clarity, reproducibility, impact); ortalama < 4.0 writer'a geri döner.
7. Red team: adversarial görevleri entegre et (fork bomb, filesystem escape, LLM tarafından yazılmış network call). Hepsinin engellendiğini doğrula. `red_team.md` yay.
8. Reproducibility bundle: paper.pdf + review.md + tree-search trace JSON + seed'ler + W&B run link'leri + sandbox config + tek satırlık rerun komutu.

Değerlendirme rubric'i:

| Weight | Criterion | Measurement |
|:-:|---|---|
| 25 | Makale kalitesi | Aynı seed konuda yayımlanmış workshop makalelerine karşı blind rubric değerlendirmesi |
| 20 | Deneysel rigor | Baseline'lar, seed'ler, ablation'lar; her iddia results tablosundaki bir hücre tarafından desteklenir |
| 20 | Maliyet ve compute disiplini | Makale başına 30 dolar tavanı zorlanır, Langfuse-trace'lenir |
| 20 | Safety | Sandbox red team geçer; network politikası ve kill-switch loglu girişimlerle doğrulanır |
| 15 | Reproducibility | Tek komutla rerun, makaleyi aynı seed'lerle yeniden üretir |

Sert ret durumları:

- Sandbox dışında çalışan deneyler. Capstone'un tüm tezi yürütmenin kontrol altında olmasıdır.
- Derlenen PDF'i yeniden okumayan writer adımları (vision critique yük taşır).
- Baseline'ı, seed'i veya ablation bölümü olmayan makaleler.
- Yalnızca post-hoc uyarı olarak zorlanan, sert tavan olmayan maliyet bütçeleri.

Reddetme kuralları:

- Açık bir insan override'ı olmadan reviewer ortalaması 4.0/5 altında olan makaleyi yayınlamayı reddet.
- Sandbox içinden network erişimi gerektiren bir seed fikir üzerinde çalışmayı reddet. Bunun yerine ayrı read-only dataset volume ekle.
- Red-team'i çalıştırılıp loglanmamış bir makaleyi yeniden çalıştırmayı reddet.

Çıktı: tree-search engine'i, sandbox politikasını, writer/reviewer döngüsünü, reproducibility bundle'larıyla üç örnek çalıştırmayı, red-team raporunu, maliyet-ledger csv'sini ve Sakana v2 failure mode'larından hangilerini yeniden ürettiğini ve mitigation'ın nasıl çalıştığını adlandıran bir yazımı içeren bir repo.
