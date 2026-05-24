# Oylama, Self-Consistency ve Debate Topolojisi

> En ucuz toplama: N bağımsız agent örnekle, çoğunluk-oyla. Wang ve diğ. 2022 self-consistency bunu bir modeli N kez örnekleyerek yaptı. Çoklu-agent monokültürden kaçmak için **heterojen** agent'larla genişletir — farklı modeller, farklı prompt'lar, farklı sıcaklıklar, farklı context'ler. Çoğunluk oyunun ötesinde, debate topolojisi önemlidir: MultiAgentBench (arXiv:2503.01935, ACL 2025) star / chain / tree / graph koordinasyonunu değerlendirdi ve **graph araştırma için en iyi** olduğunu buldu, ~4 agent'tan sonra bir "coordination tax" ile. AgentVerse (ICLR 2024) iki ortaya çıkan deseni belgeler — gönüllü davranışlar ve uyum davranışları — ve uyum hem bir özelliktir (konsensüs bulma) hem bir risktir (groupthink, Ders 24). Bu ders topoloji uzayını eşler, her varyantı inşa eder ve coordination tax'ı ölçer.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 07 (Society of Mind ve Debate), Faz 16 · 14 (Konsensüs ve BFT)
**Süre:** ~75 dakika

## Sorun

Debate doğruluğu iyileştirebilir (Du ve diğ., arXiv:2305.14325). Onu bozabilir de. Debate'in yardım edip etmediği dört yapısal seçime bağlıdır:

1. Kimin kiminle konuştuğu (topoloji).
2. Kaç tur (Du 2023: turlar VE agent'lar bağımsız olarak önemlidir).
3. Agent'ların heterojen olup olmadığı (farklı baz modeller monokültürü kırar).
4. Bir karşıt sesin mevcut olup olmadığı (steel-manning vs straw-manning).

Bir göreve "5 agent çalıştır ve oyla" bağlayan takımlar genellikle tek bir agent'a karşı geriler. Başarısızlıklar rastgele değil. Topoloji ve heterojenliği takip ederler. Bu ders topoloji haritasıdır.

## Kavram

### Self-consistency, tek-model baseline'ı

Wang ve diğ. 2022 ("Self-Consistency Improves Chain of Thought Reasoning") aynı modeli sıcaklık > 0'da N kez örnekledi ve akıl yürütme-yol cevapları üzerinde çoğunluk-oyladı. GSM8K'da sonuç: tek greedy decode üzerine N=40 örnekle önemli kazanımlar. Self-consistency çoklu-agent oylamanın tek-agent öncülüdür.

Sınır: self-consistency bir baz model kullanır. Hatalar yapı gereği korelasyonludur. Modelin sistematik bir yanlılığı varsa, tüm N örnek bunu paylaşır.

### Çoklu-agent oy, heterojen uzantı

N örneği N *farklı* agent ile değiştir. Farklı baz modeller (Claude, GPT, Llama), farklı prompt'lar, farklı tool erişimi. Fayda: korelasyonsuz hatalar. Maliyet: farklı agent'lar farklı miktarda mal olur; onları koordine etmek overhead ekler.

Heterojen debate için kanonik 2026 ismi **A-HMAD** — Adversarial Heterogeneous Multi-Agent Debate. Evrensel olarak benimsenmedi, ama makaleler bu terimi "farklı modeller tartışır, bu da monokültür çöküşünden korelasyonlu hataları azaltır" için kullanır.

### Dört topoloji

```
star                chain               tree                graph

    ┌─A─┐           A─B─C─D         ┌──A──┐              A───B
    │   │                           │     │              │ × │
    B   C                           B     C              D───C
    │   │                          / \   / \
    D   E                         D   E F   G           (tam bağlantılı)
```

Star: bir hub, diğerleri yalnızca hub'la konuşur. Geri kanalsız supervisor-worker'a eşdeğer.
Chain: doğrusal, her agent öncekinin çıktısını görür. Pipeline benzeri.
Tree: hiyerarşik, hiyerarşik agent sistemleri tarafından kullanılır (Ders 06).
Graph: any-to-any. Tam bağlantılı clique ve keyfi DAG'lar dahil.

### Coordination tax (MultiAgentBench)

MultiAgentBench (MARBLE, ACL 2025, arXiv:2503.01935) star, chain, tree, graph'ı araştırma, kodlama ve planlama dahil bir görev suite'inde benchmark'ladı. Temel ölçülen sonuçlar:

- **Graph** topoloji araştırma görevlerinde kazanır. Bilgi any-to-any akar; agent'lar birbirini eleştirebilir.
- **Star** hızlı-cevap faktüel görevlerde kazanır. Hub filtreler ve konsolide eder.
- **Chain** adım adım pipeline'larda (aşamalı iyileştirme) kazanır.
- **Coordination tax** graph topolojide ~4 agent'tan sonra görünür. Duvar-saati ve token maliyeti kaliteden daha hızlı büyür.

4-agent tavanı ampiriktir, temel değil. 2026 LLM context kapasitesini yansıtır: her agent'ın context'i peer çıktılarıyla dolar ve N+1 agent'ı eklemenin marjinal değeri herkes herkesi görebildiğinde düşer.

### Multi-Agent Debate Stratejileri ("Should we be going MAD?")

arXiv:2311.17371 MAD stratejilerinin 2023 taramasıdır. Başkaları tarafından replike edilen temel bulgu: self-consistency'ye *yapısal olarak benzer* MAD varyantları (bağımsız örnekleme + toplama) aynı bütçeyi kullandığında self-consistency'den genellikle daha kötü performans gösterir. MAD en çok agent'lar gerçekten heterojen olduğunda ve debate karşıt yapıya sahip olduğunda (bir agent karşı tartışır) yardım eder.

### AgentVerse ortaya çıkan desenleri

AgentVerse (ICLR 2024, https://proceedings.iclr.cc/paper_files/paper/2024/file/578e65cdee35d00c708d4c64bce32971-Paper-Conference.pdf) açık tasarım olmadan bile çoklu-agent debate'ten ortaya çıkan iki davranışı belgeler:

- **Volunteer.** Bir agent ("bir sonraki adımı alabilirim") yardım önerir, sorulmadan. Faydalı: bir alt görev için en yetenekli agent'a iş ayırır.
- **Conformity.** Bir agent eleştirmen yanlış olsa bile duruşunu eleştirmene eşleşecek şekilde ayarlar. Bu debate-eşdeğeri yalakalıktır (Ders 14).

Konformite, anlaşmaya kadar debate'in zorbaları neden ödüllendirdiğidir. Ayrı yargıçlı sınırlı turlar hafifletir.

### Heterojenlik: doğruluğu hareket ettiren gerçek düğme

Pratik literatürde 2024-2026 deseni: N agent'larından birini farklı bir baz modelle değiştirmek, N'i 1 artırmaktan daha büyük bir doğruluk sıçraması verir. Sezgi monokültürdür — her yeni bağımsız-hata kaynağı ek bir korelasyonlu örnekten daha değerlidir.

Sınırda heterojenlik çokluğu yener. Üç farklı model temiz ground truth'a sahip çoğu görevde bir modelin beş kopyasını yener.

### Jüri yöntemleri

Sibyl framework'ü (Minsky-LLM literatüründe atıfta bulunulur) bir "jüri"yi formelleştirir — her aşamada oylayarak cevapları iyileştiren küçük bir uzmanlaşmış agent kümesi. Düz çoğunluk oyu aksine, bir jüri rolleri vardır: bir agent çapraz sorgu yapar, bir context sağlar, bir makullüğü puanlar. Jüri yöntemleri düz oy (ucuz, monokültür eğilimli) ile tam MAD (pahalı, konformite eğilimli) arasında bir orta noktadır.

### Vote-with-debate ne zaman baskındır

- Sorun ground truth'a sahiptir (gerçek, matematik, kod davranışı). Oy yakınsaması anlamlıdır.
- Agent'lar farklı kaynaklara ya da tool'lara erişebilir (heterojenlik mevcuttur).
- Turlar sınırlıdır (tipik 2-3) ve ayrı bir yargıç ya da verifier vardır.
- Bütçe 3-5 agent'a izin verir. Graph topolojide 5-7'nin ötesinde coordination tax baskın olur.

### Vote-with-debate ne zaman zarar verir

- Sorun fikir-şeklindedir. Agent'lar en doğru görünene değil, en kendine güvenle görünene yakınsar.
- Tüm agent'lar bir baz model paylaşır. Monokültür konsensüsü anlamsız kılar.
- Turlar sınırsızdır. Konformite her zaman kazanır.
- Görev basittir. N=5'te self-consistency'li tek bir agent daha ucuz ve aynı doğruluktadır.

## İnşa Et

`code/main.py` şunları uygular:

- `run_star(agents, hub, question)` — hub her worker'ı sorgular, toplar.
- `run_chain(agents, question)` — sıralı iyileştirme.
- `run_tree(root, children, question)` — depth-2 toplamayla hiyerarşik.
- `run_graph(agents, question, rounds)` — all-to-all debate, sınırlı turlar.
- Senaryolu bir heterojenlik düğmesi: her agent'ın sistematik yanlışlığını gösteren bir `error_bias`'ı vardır.
- Her topolojiyi N=3, 5, 7'de çalıştıran ve (accuracy, total_tokens, wallclock_simulated) rapor eden bir ölçüm harness'i.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: topoloji × N → (accuracy, tokens, latency) tablosu. Graph araştırma-stili görevlerde N=3-5'te kazanır; star hızlı-faktüel görevlerde kazanır; N=7'de graph coordination tax'i gösterir (latency accuracy'den daha hızlı şişer).

## Kullan

`outputs/skill-topology-picker.md` bir görev tanımını okuyan ve bir topoloji (star / chain / tree / graph), bir N (agent sayısı), bir heterojenlik profili (kullanılacak baz modeller) ve bir tur sınırı öneren bir skill'dir.

## Yayınla

Herhangi bir ensemble için:

- **N=5'te bir güçlü baz model kullanarak self-consistency** ile başla. Ucuz baseline'dır.
- Doğruluk önemliyse **N=3'te heterojen oylamaya** yükselt. Farkı ölç.
- Yalnızca görev yapıya sahipse (araştırma, çok-adımlı) ve sınırlı turlar uygulanabilirse **debate topolojiye** yükselt.
- Her zaman azınlık kümesini log'la. Bir azınlık ısrarla doğru olduğunda, bir çeşitlilik sinyalin var.
- Doğruluğun yanında duvar-saati ve token'ları benchmark'la. "10× maliyette daha iyi doğruluk" bir iş kararıdır.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Graph topoloji için coordination-tax eğrisini çiz: N'e karşı accuracy, N'e karşı token. Hangi N'de eğri eğilir?
2. A-HMAD uygula: kasıtlı olarak farklı yanlılıklara sahip üç agent. All-same-bias baseline'ı Ders 14'teki monoculture saldırısında A-HMAD ile nasıl karşılaştırılır?
3. Graph topolojisine bir "judge" rolü ekle ki oy vermesin, yalnızca final konsensüsü puanlasın. Bu ortaya çıkan konformite davranışını değiştiriyor mu?
4. AgentVerse makalesini (ICLR 2024) oku. Implementasyonunun en güçlü şekilde sergilediği ortaya çıkan davranışı belirle. Bir prompt değişikliği ile zıt davranışı çağırabilir misin?
5. MultiAgentBench (arXiv:2503.01935) Bölüm 4 (topoloji deneyleri)'ni oku. Harness'ini kullanarak makaledeki bir görevde "graph-wins-research" sonucunu yeniden üret.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Self-consistency | "N kez örnekle, oyla" | Wang 2022. Tek model, N sıcaklık>0 örneği, akıl yürütme yolları üzerinde çoğunluk oy. |
| Heterojenlik | "Farklı modeller" | Farklı baz modeller ya da prompt aileleri ensemble'ı. Monokültürü kırar. |
| MAD | "Multi-agent debate" | Agent'ların turlar üzerinde eleştiriler alışverişi için jenerik terim. Du 2023'e bak. |
| A-HMAD | "Adversarial Heterogeneous MAD" | Farklı modelleri + karşıt yapıyı vurgulayan MAD varyantı. |
| Topoloji | "Kim kiminle konuşur" | Star, chain, tree, graph. Bilgi akışını belirler. |
| Coordination tax | "Azalan getiri" | Graph'ta ~4 agent'ın üstünde maliyet kaliteden daha hızlı büyür. |
| Volunteer davranışı | "Sorulmamış yardım" | AgentVerse ortaya çıkan deseni: bir agent bir adım almayı önerir. |
| Conformity davranışı | "Baskı altında anlaşma" | AgentVerse ortaya çıkan deseni: bir agent bir eleştirmenle hizalanır. |
| Jüri | "Küçük uzmanlaşmış panel" | Rollerle Sibyl-stili ensemble (examiner, context, scorer). |

## İleri Okuma

- [Wang ve diğ. — Self-Consistency Improves Chain of Thought Reasoning](https://arxiv.org/abs/2203.11171) — tek-model baseline
- [Du ve diğ. — Improving Factuality and Reasoning via Multiagent Debate](https://arxiv.org/abs/2305.14325) — agent'lar VE turlar bağımsız olarak önemli
- [MultiAgentBench / MARBLE](https://arxiv.org/abs/2503.01935) — araştırma için en iyi graph, pipeline'lar için chain'i gösteren topoloji benchmark'ı
- [Should we be going MAD?](https://arxiv.org/abs/2311.17371) — MAD-strateji taraması; MAD'in eşit bütçede self-consistency'ye sıklıkla kaybettiğini bulur
- [AgentVerse (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/file/578e65cdee35d00c708d4c64bce32971-Paper-Conference.pdf) — volunteer ve konformite ortaya çıkan desenleri
- [MARBLE repo](https://github.com/ulab-uiuc/MARBLE) — referans benchmark implementasyonu
