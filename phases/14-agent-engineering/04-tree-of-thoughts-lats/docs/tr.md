# Tree of Thoughts ve LATS: Bilinçli Arama

> Tek bir CoT trajectory'sinin geri dönme alanı yok. ToT (Yao et al., 2023) akıl yürütmeyi her node üzerinde self-evaluation'lı bir ağaca dönüştürür. LATS (Zhou et al., 2024) ToT'yi ReAct ve Reflexion ile Monte Carlo Tree Search altında birleştirir. Game of 24 %4'ten (CoT) %74'e (ToT) çıkar; LATS HumanEval'da %92.7 pass@1'e ulaşır.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 03 (Reflexion)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Akıl yürütmeyi arama olarak çerçevele: node'lar "düşünceler," edge'ler "genişlemeler," value "ne kadar umut verici."
- Self-evaluation puanlamasıyla bir stdlib ToT-tarzı BFS ağaç araması uygula.
- Select / expand / simulate / backpropagate ile oyuncak bir LATS MCTS döngüsüne genişlet.
- Arama'nın token çarpanına ne zaman değdiğine (Game of 24, kod üretimi) ve ne zaman tek bir trajectory'nin yeterli olduğuna (basit Q&A) karar ver.

## Sorun

CoT doğrusal bir yürüyüş. İlk adım yanlışsa, sonraki her adım kötü bir önerme üzerinde çalışır. Game of 24'te (24 yapmak için + − × ÷ ile dört rakam kullan), GPT-4 CoT %4 doğruluk yapar. Model erken yanlış alt-ifadeyi seçer ve kurtulamaz.

Akıl yürütmenin ihtiyaç duyduğu şey, birden çok aday önerip onları değerlendirme, umut vericileri seçme ve çıkmaz sokaklar göründüğünde geri dönme becerisi. Bu arama. Tree of Thoughts ve LATS iki kanonik formülasyon.

## Kavram

### Tree of Thoughts (Yao et al., NeurIPS 2023)

Her node tutarlı bir ara adım ("bir düşünce"). Her node K çocuk düşünceye genişleyebilir. LLM her node'u bir puanlama prompt'uyla self-evaluate eder. Arama ağacı keşfeder — BFS, DFS ya da beam.

```
                     (root: "4 6 4 1'den 24 bul")
                    /               |            \
           ("6 - 4 = 2")    ("4 + 1 = 5")    ("4 * 6 = 24")  <- Skor: YÜKSEK
              /   \              |                  |
          ...    ...          ...                finish
```

Self-evaluation taşıyıcı parça. Makale üç varyant gösteriyor: `sure / likely / impossible` sınıflandırması, `1..10` numerik skor ve adaylar arasında oy. Üçü de Game of 24'te CoT'yi önemli ölçüde yeniyor (GPT-4 ile %4 -> %74).

### LATS (Zhou et al., ICML 2024)

LATS, ToT, ReAct ve Reflexion'ı MCTS altında birleştirir. LLM üç rol oynar:

- **Policy**: aday sonraki aksiyonları önerir (ReAct-tarzı).
- **Value function**: kısmi bir trajectory'i puanlar (ToT-tarzı self-eval).
- **Self-reflector**: başarısızlıkta, doğal-dil bir self-reflection yazar (Reflexion-tarzı) ve gelecekteki rollout'ları yeniden tohumlamak için kullanır.

Ortam feedback'i (gözlemler) value function'a karışır, böylece arama yalnızca model görüşleriyle değil gerçek tool sonuçlarıyla bilgilendirilmiş olur. Makale zamanındaki sonuçlar: GPT-4 ile HumanEval pass@1 %92.7 (SOTA), GPT-3.5 ile WebShop ortalama 75.9 (gradient-tabanlı fine-tuning'e yaklaşıyor).

### MCTS, en az haliyle

İterasyon başına dört faz:

1. **Select** — UCT (upper confidence bound for trees) kullanarak root'tan bir leaf'e yürü.
2. **Expand** — policy üzerinden K çocuk üret.
3. **Simulate** — bir çocuktan policy kullanarak rollout, value function ile (ya da ortam ödülü ile) leaf'i puanla.
4. **Backpropagate** — ziyaret sayılarını ve value tahminlerini yol boyunca güncelle.

UCT formülü: `Q(s, a) + c * sqrt(ln N(s) / N(s, a))`. İlk terim exploitation; ikincisi exploration. `c`'yi göreve göre ayarla.

### Maliyet gerçeği

Arama token'ları patlatır. Game of 24'te ToT, CoT'nin 100–1000x'i kadar token kullanır. LATS benzer. Bu bedava değil; aramayı şu durumlar için sakla:

- Tek bir trajectory'nin kanıtlanabilir şekilde yetersiz olduğu görevler (Game of 24, karmaşık kod).
- Wall-clock'un doğruluktan daha az önemli olduğu görevler.
- Ucuz, güvenilir bir value function'ı olan görevler (kod için unit testler, matematik için açık hedef).

Görevin tek bir doğru yanıtı ve gürültülü bir evaluator'ı varsa, arama genellikle işleri kötüleştirir — "iyi-skorlu" bir yanlış yanıt bulur.

### 2026 konumlanması

Çoğu üretim agent'ı LATS çalıştırmaz. Tool-grounded doğrulamalı ReAct çalıştırırlar (CRITIC, Ders 05). Arama özelleşmiş nişlerde görünür:

- Testleri value function olarak çalıştıran kodlama agent'ları (HumanEval-tarzı).
- Birden çok sorgu yolu keşfeden deep-research agent'ları.
- LangGraph alt-graph'ları içindeki planlama-ağırlıklı workflow'lar.

AlphaEvolve (Ders 11) 2025'in uç noktası: kod üzerinde evrimsel arama, makine-doğrulanabilir fitness, frontier kazançlar (56 yılda ilk 4x4 matmul iyileştirmesi).

## İnşa Et

`code/main.py` şunları uygular:

- Stilize "aritmetik op seç" görevinde minik bir ToT BFS.
- Aynı görevde UCT seçimi ile oyuncak bir LATS MCTS döngüsü (Select / Expand / Simulate / Backpropagate).
- Sembolik skor artı self-eval skor besteleyen bir value function.

Çalıştır:

```
python3 code/main.py
```

Trace, BFS ile node başına üç aday genişleten ToT'yi, MCTS üzerinden en iyi rollout'a yakınsayan LATS ile karşılaştırarak gösterir. Her ikisi için de token sayıları yazdırılır.

## Kullan

LangGraph ToT-tarzı keşfi alt-graph desenleri olarak yayar; LangChain ekibinin LATS üzerine blogu (Mayıs 2024) referans tutorial. LlamaIndex bir `TreeOfThoughts` agent yayar. Çoğu 2026 üretim agent'ı için bu desen `if task_complexity > threshold: use_search()` kapısının arkasında yaşar — Ders 05'teki evaluator-optimizer desenine bak.

## Yayınla

`outputs/skill-search-policy.md` görev şekli, bütçe ve evaluator sadakati verildiğinde doğrusal ReAct, ToT, LATS ve evrimsel arama arasında seçim yapar.

## Alıştırmalar

1. Oyuncak LATS'i UCT c=0.1 vs c=2.0 ile çalıştır. Trace'te ne değişir?
2. Value function'ı daha gürültülü bir skorlayıcı ile değiştir (rastgele jitter ekle). MCTS hâlâ en iyi leaf'i bulur mu? Tolere ettiği minimum signal-to-noise nedir?
3. Beam-search ToT (her seviyede top-k tut) uygula ve BFS ile karşılaştır. Sıkı token bütçesinde hangisi daha iyi?
4. LATS Bölüm 5.1'i oku. HumanEval trajectory sayısını yeniden üret: raporlanan pass@1'e ulaşmak kaç rollout alıyor?
5. LATS makalesinin "LATS'ın daha az yardım ettiği zamanlar" tartışmasını oku. Görev şeklini arama stratejisine eşleyen bir paragraflık karar kuralı yaz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Tree of Thoughts | "Dallı CoT" | Yao et al. — self-evaluation'lı düşünce node ağacı |
| LATS | "LLM'ler için MCTS" | Zhou et al. — ToT + ReAct + Reflexion'ı MCTS altında birleştirir |
| UCT | "Upper confidence bound" | Exploitation (Q) ve exploration (ln N / n)'yi dengeleyen seçim formülü |
| Value function | "Bu state ne kadar iyi" | Prompt'lanmış LLM skoru ya da ortam ödülü; backprop'u besler |
| Policy | "Aksiyon önerici" | ReAct-tarzı üretici; aday sonraki düşünceler/aksiyonlar yayar |
| Rollout | "Simüle edilmiş trajectory" | Bir node'dan policy kullanarak leaf'e yürü, value ile puanla |
| Backpropagate | "Ataları güncelle" | Leaf'in ödülünü yol boyunca yukarı it, ziyaret sayılarını ve Q'yu güncelle |
| Arama maliyeti | "Token patlaması" | Game of 24'te CoT'nin 100-1000x'i; benimsemeden önce bütçele |

## İleri Okuma

- [Yao et al., Tree of Thoughts (arXiv:2305.10601)](https://arxiv.org/abs/2305.10601) — kanonik makale
- [Zhou et al., LATS (arXiv:2310.04406)](https://arxiv.org/abs/2310.04406) — Reflexion feedback'li MCTS
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — arama için alt-graph desenleri
- [AlphaEvolve (arXiv:2506.13131)](https://arxiv.org/abs/2506.13131) — programatik evaluator'lı evrimsel arama
