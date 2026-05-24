# Çoklu-Agent Debate ve İşbirliği

> Du et al. (ICML 2024, "Society of Minds") yanıtları bağımsız öneren N model instance'ı çalıştırır, sonra R tur boyunca iteratif olarak birbirini eleştirip yakınsar. Factuality, kural takibi, akıl yürütme'yi iyileştirir. Sparse topoloji token maliyetinde full mesh'i yener.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 12 (Workflow Desenleri), Faz 14 · 05 (Self-Refine ve CRITIC)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Debate protokolünü açıkla: N öneren, R tur, paylaşılan bir yanıtta yakınsa.
- Debate'in neden factuality, kural takibi ve akıl yürütmeyi iyileştirdiğini açıkla.
- Sparse topolojiyi açıkla: her debater'ın diğer her birini görmesi gerekmez.
- Stdlib'de scripted bir LLM üzerinde full-mesh ve sparse varyantları ile debate uygula; token maliyetini doğruluğa karşı ölç.

## Sorun

Self-Refine (Ders 05) kendini eleştiren tek bir model — groupthink risk'i. CRITIC (Ders 05) eleştiriyi dış tool'larda topraklar — her zaman mevcut değil. Debate üçüncü bir mod tanıtıyor: birden fazla instance, cross-critique, anlaşmazlık ile yakınsama.

## Kavram

### Society of Minds (Du et al., ICML 2024)

- N model instance bağımsız olarak aynı soruya yanıt önerir.
- R tur boyunca her model diğerlerinin önerilerini okur ve onları eleştirir.
- Modeller eleştirilere göre yanıtlarını günceller.
- R tur sonrası, yakınsayan yanıtı döndür.

Orijinal deneyler maliyet nedeniyle N=3, R=2 kullandı. Doğruluk zor problemlerde (MMLU, GSM8K, Chess Move Validity, biyografi üretimi) daha fazla agent ve daha fazla tur ile gelişir.

Cross-model kombinasyonlar single-model debate'leri yener: ChatGPT + Bard birlikte > her biri tek başına.

### Sparse topoloji

"Improving Multi-Agent Debate with Sparse Communication Topology" (arXiv:2406.11776, 2024-2025) full-mesh debate'in her zaman optimal olmadığını gösterdi. Sparse topolojiler (star, ring, hub-and-spoke) daha düşük token maliyetinde doğruluğu yakalayabilir. Her debater yalnızca bir peer alt kümesini görür.

Sonuçlar:

- Full mesh N=5, R=3 = 5 × 3 = 15 öneri, her biri 4 peer okuyor = 60 critique op.
- Star N=5, R=3 (bir hub + 4 spoke) = 15 öneri, spoke'lar yalnızca hub'ı okuyor = 12 critique op.

### Debate ne zaman yardım eder

- **Factuality.** N bağımsız öneri, cross-check halüsinasyonu azaltır.
- **Kural takibi.** Chess move validity — bir model kuralı kaçırır, diğerleri yakalar.
- **Açık-uçlu akıl yürütme.** Birden çok çerçeveleme doğru yanıta daraltır.

### Debate ne zaman zarar verir

- **Latency-hassas UX.** N × R seri tur sahip olmayabileceğin latency.
- **Maliyet-hassas ölçek.** Soru başına N × R token.
- **Basit factual lookup'lar.** Bir lookup beş debate'ten ucuz.

### 2026 pratik gerçekleştirmeler

- **Anthropic orchestrator-workers** (Ders 12) — synthesis adımlı bir debate varyantı.
- **LangGraph supervisor** (Ders 13) — merkezi router + uzman agent'lar debate'i bir node olarak uygulayabilir.
- **OpenAI Agents SDK** (Ders 16) — agent'lar iteratif eleştiri için ileri geri handoff.
- **Multi-agent eval'ler** — eval sinyali için debate + evaluator-optimizer eşleştir.

### Bu desen nerede ters gider

- **Yakınsama çöküşü.** Tüm agent'lar ilk yanlış yanıta yakınsa. Zorunlu anlaşmazlık turlarıyla hafiflet.
- **Hub başarısızlığı.** Bir star topolojide kötü bir hub herkesi bozar. Rotate et ya da birden çok hub kullan.
- **Prompt homojenleşmesi.** Tüm agent'lar aynı prompt'u kullanır; aynı yanıtları üretir. Çeşitli prompt'lar ve/veya modeller kullan.

## İnşa Et

`code/main.py` stdlib debate uyguluyor:

- `Debater` class (per-debater opinion drift'li scripted LLM).
- `FullMeshDebate` ve `SparseDebate` runner'ları.
- Üç soru: biri factual, biri rule-tabanlı, biri reasoning.
- Metrikler: yakınsayan yanıt, yakınsamaya tur sayısı, toplam critique op'ları.

Çalıştır:

```
python3 code/main.py
```

Çıktı: protokol başına doğruluk ve maliyet; sparse 2/3 soruda full mesh'i daha düşük maliyette yakalıyor.

## Kullan

- **Anthropic orchestrator-workers** basit 2-3 worker debate'leri için.
- **LangGraph** checkpointing'li durumlu çok-turlu debate için.
- **Custom** araştırma ya da uzmanlaşmış doğruluk garantileri için.

## Yayınla

`outputs/skill-debate.md` yapılandırılabilir topoloji, N, R ve yakınsama kuralı ile bir çoklu-agent debate iskeler.

## Alıştırmalar

1. Bir "zorla anlaşmazlık" kuralı uygula: 1. turda her debater farklı bir öneri üretmeli. Yakınsama hızı üzerine etkiyi ölç.
2. Confidence-weighted toplama ekle: debater'lar (answer, confidence) döndürür; toplayıcı confidence'a göre ağırlıklar. Yardım eder mi?
3. Bir "agent"ı farklı görüşlere sahip farklı bir scripted LLM ile değiştir. Heterojenlik doğruluğu iyileştirir mi?
4. 3 sorunda full mesh vs sparse için token maliyetini ölç. Maliyeti doğruluğa karşı çiz.
5. Society of Minds makalesini oku. Oyuncağını N=5, R=3'e port et. Ne bozulur? Ne daha iyi olur?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Debate | "Çoklu-agent eleştirisi" | N öneren, R tur cross-critique, yakınsama |
| Full mesh | "Herkes herkesi okur" | Her tur her debater her peer'i okur |
| Sparse topoloji | "Sınırlı peer görünümü" | Debater'lar yalnızca bir peer alt kümesini okur |
| Hub-and-spoke | "Star topoloji" | Bir merkezi debater, N-1 spoke yalnızca hub'ı okur |
| Yakınsama | "Anlaşma" | Debater'lar paylaşılan bir yanıtta yakınsar |
| Society of Minds | "Du et al. debate makalesi" | ICML 2024 çoklu-agent debate yöntemi |

## İleri Okuma

- [Du et al., Society of Minds (arXiv:2305.14325)](https://arxiv.org/abs/2305.14325) — kanonik çoklu-agent debate
- [Sparse Communication Topology (arXiv:2406.11776)](https://arxiv.org/abs/2406.11776) — sparse topoloji sonuçları
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — debate varyantı olarak orchestrator-workers
- [Madaan et al., Self-Refine (arXiv:2303.17651)](https://arxiv.org/abs/2303.17651) — tek-model self-critique karşılığı
