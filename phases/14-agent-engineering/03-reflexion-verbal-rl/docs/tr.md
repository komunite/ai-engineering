# Reflexion: Sözel Reinforcement Learning

> Gradient-tabanlı RL, bir başarısızlık modunu düzeltmek için binlerce deneme ve bir GPU kümesi gerektirir. Reflexion (Shinn et al., NeurIPS 2023) bunu doğal dilde yapar: her başarısız denemeden sonra agent bir self-reflection yazar, bunu episodic memory'de saklar ve bir sonraki denemeyi bu belleğe koşullar. Letta'nın sleep-time compute'unun, Claude Code'un CLAUDE.md learning'lerinin ve pro-workflow'un learn-rule'unun arkasındaki desen budur.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 02 (ReWOO)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Reflexion'ın üç bileşenini (Actor, Evaluator, Self-Reflector) ve episodic memory'nin rolünü adlandır.
- İkili evaluator, reflection buffer ve taze yeniden denemeler ile bir stdlib Reflexion döngüsü uygula.
- Belirli bir görev için skaler, sezgisel ve self-evaluated feedback kaynakları arasında seç.
- Sözel reinforcement'ın, gradient-tabanlı RL'in düzeltmek için binlerce deneme gerektireceği hataları neden yakaladığını açıkla.

## Sorun

Bir agent bir görevde başarısız oluyor. Standart RL'de binlerce deneme daha yapar, gradient hesaplar, ağırlıkları güncellersin. Pahalı, yavaş ve çoğu üretim agent'ının her başarısızlık için bir eğitim bütçesi yok.

Reflexion (Shinn et al., arXiv:2303.11366) farklı bir soru soruyor: ya agent neden başarısız olduğunu düşünüp bu düşünceyi prompt'una alarak tekrar denerse? Ağırlık güncellemesi yok. Gradient yok. Sadece denemeler arasında saklanan doğal dil.

Sonuç: ALFWorld'de ReAct'ı ve fine-tune edilmemiş diğer baseline'ları yenmiş. HotpotQA'da ReAct'ın üzerinde geliştirmiş. Kod üretiminde (HumanEval/MBPP) zamanın state of the art'ı yapmış. Hepsi tek bir gradient adımı olmadan.

## Kavram

### Üç bileşen

```
Actor         : bir trajectory üretir (ReAct-tarzı döngü)
Evaluator     : trajectory'i puanlar — ikili, sezgisel ya da self-eval
Self-Reflector: başarısızlık üzerine doğal-dil bir self-reflection yazar
```

Artı bir veri yapısı:

```
Episodic memory: önceki self-reflection'ların listesi, sonraki denemenin prompt'una öne eklenir
```

Bir deneme Actor'u çalıştırır. Evaluator puan verir. Skor düşükse, Self-Reflector bir self-reflection üretir ("Soruyu X'i soruyor diye yanlış okudum, halbuki Y'yi soruyordu, bu yüzden yanlış tool'u seçtim"). Self-reflection episodic memory'ye gider. Sonraki deneme taze başlar ama self-reflection'ı görür.

### Üç evaluator türü

1. **Skaler** — dışsal ikili sinyal. ALFWorld başarılı olur ya da olmaz. HumanEval testleri geçer ya da geçmez. En basit, en yüksek sinyal.
2. **Sezgisel** — önceden tanımlanmış başarısızlık imzaları. "Agent aynı aksiyonu üst üste iki kere ürettiyse, takılmış olarak işaretle." "Trajectory 50 adımı aşıyorsa, verimsiz olarak işaretle."
3. **Self-evaluated** — LLM kendi trajectory'sini puanlar. Ground truth mevcut olmadığında gerekir. Daha zayıf sinyal; tool-grounded doğrulama ile (Ders 05 — CRITIC) iyi eşleşir.

2026 varsayılan bir karışım: mevcutsa skaler, değilse self-eval, güvenlik rayı olarak sezgiseller.

### Bu neden genelleşir

Reflexion yeni bir algoritmadan çok adlandırılmış bir desen. Hemen hemen her üretim "self-healing" agent'ı bir varyant çalıştırır:

- Letta'nın sleep-time compute'u (Ders 08): ayrı bir agent geçmiş konuşmalar üzerine self-reflect eder ve memory bloklarına yazar.
- Claude Code'un `CLAUDE.md` / "save memory" deseni: learning olarak yakalanan self-reflection'lar, gelecekteki oturumların önüne eklenir.
- pro-workflow'un `/learn-rule` komutu: açık kural olarak yakalanan düzeltmeler.
- LangGraph'ın reflection node'ları: çıktıyı puanlayan ve gerekirse refine'a yönlendiren bir node.

Hepsi aynı içgörüden türer: doğal dil, "başarısızlıktan ne öğrendim"i koşular arasında taşımak için yeterince zengin bir medyum.

### Ne zaman işe yarar, ne zaman yaramaz

Reflexion şu durumlarda işe yarar:

- Net bir başarısızlık sinyali var (test başarısızlığı, tool hatası, yanlış yanıt).
- Görev sınıfı tekrar üretilebilir (aynı tür soru tekrar sorulabilir).
- Self-reflection'ın trajectory üzerinde gelişme alanı var (yeterli aksiyon bütçesi).

Reflexion şu durumlarda yardım etmez:

- Agent zaten ilk denemede başarılı.
- Başarısızlık dışsal (network kapalı, tool bozuk) — "network kapalıydı" üzerine self-reflection gelecekteki koşulara yardım etmez.
- Self-reflection batıl inanca dönüşür — tek seferlik aksak bir koşu üzerine bir anlatı saklamak.

2026 tuzağı: memory rot. Self-reflection'lar birikir; bazıları geçersiz ya da yanlış; episodic buffer büyüdükçe yeniden koşular yavaşlar. Hafifletme: periyodik kompaksiyon (Ders 06), self-reflection'larda TTL, ya da ayrı bir sleep-time temizlik agent'ı (Letta).

## İnşa Et

`code/main.py` Reflexion'ı bir oyuncak puzzle üzerinde uyguluyor: bir hedefe toplanan 3-elemanlı bir liste üret. Actor aday listeler yayar; Evaluator toplamı kontrol eder; Self-Reflector neyin yanlış gittiği üzerine bir satır yazar. Self-reflection bir sonraki deneme için episodic memory'ye gider.

Bileşenler:

- `Actor` — self-reflection'ları gördüğünde gelişen scripted policy.
- `Evaluator.binary()` — hedef toplamda pass/fail.
- `SelfReflector` — başarısızlığın bir satırlık tanısını üretir.
- `EpisodicMemory` — TTL semantiğine sahip sınırlı liste.

Çalıştır:

```
python3 code/main.py
```

Trace üç denemeyi gösterir. Deneme 1 başarısız olur, bir self-reflection saklanır, deneme 2 self-reflection'ı görür ve iyileşir ama yine başarısız olur, deneme 3 başarılı olur. Bir baseline koşusuyla (self-reflection yok) karşılaştır — deneme 1'in yanıtında takılı kalır.

## Kullan

LangGraph reflection'ı bir node deseni olarak yayar. Claude Code'un `/memory` komutu ve pro-workflow'un `/learn-rule`'u episodic buffer'ı bir markdown dosyası olarak dışsallaştırır. Letta'nın sleep-time compute'u Self-Reflector'ı boşlukta çalıştırır, böylece birincil agent latency-bound kalır. OpenAI Agents SDK Reflexion'ı doğrudan yayınlamaz; trajectory'leri skora göre reddeden bir custom Guardrail ve koşular arasında hayatta kalan bir memory `Session` ile inşa edersin.

## Yayınla

`outputs/skill-reflexion-buffer.md` self-reflection yakalama, TTL ve tekilleştirme ile episodic buffer oluşturur ve sürdürür. Bir görev sınıfı ve bir başarısızlık verildiğinde, bir sonraki denemeye gerçekten yardım eden bir self-reflection yayar (jenerik "daha dikkatli ol" değil).

## Alıştırmalar

1. İkili'den, hedeften uzaklık metriği döndüren skaler evaluator'a geç. Daha hızlı yakınsar mı?
2. Self-reflection'lara 10 deneme TTL'i ekle. Daha eski self-reflection'lar o noktadan sonra zarar mı, fayda mı verir?
3. Sezgisel evaluator uygula: aynı aksiyon tekrarlıyorsa denemeyi takılmış olarak işaretle. Bu Self-Reflector ile nasıl etkileşir?
4. Self-reflection'ları görmezden gelen adversarial bir Actor ile Reflexion çalıştır. Actor'ı self-reflection'ları fark etmeye zorlayan minimum reflection prompt mühendisliği nedir?
5. Reflexion makalesinin AlfWorld üzerine 4. bölümünü oku. %130 başarı-oranı iyileştirmesini kavramsal olarak yeniden üret: vanilla ReAct'a karşı ana delta nedir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Reflexion | "Self-correction" | Shinn et al. 2023 — Actor, Evaluator, Self-Reflector artı episodic memory |
| Sözel reinforcement | "Gradient'siz öğrenme" | Bir sonraki denemenin prompt'una öne eklenen doğal-dil self-reflection |
| Episodic memory | "Görev başına self-reflection'lar" | Bir görev sınıfı için sınırlı önceki self-reflection buffer'ı |
| Skaler evaluator | "İkili başarı sinyali" | Ground truth'tan pass/fail ya da numerik skor |
| Sezgisel evaluator | "Pattern-tabanlı detektör" | Önceden tanımlanmış başarısızlık imzaları (örn. takılmış-döngü, çok-fazla-adım) |
| Self-evaluator | "Kendi trace'i üzerinde LLM-as-judge" | Ground truth yokken daha düşük-sinyalli yedek — tool-grounded doğrulama ile eşleştir |
| Memory rot | "Bayat self-reflection'lar" | Episodic buffer geçersiz girdilerle dolar; kompaksiyon/TTL ile düzelt |
| Sleep-time reflection | "Asenkron self-reflection" | Self-Reflector'ı sıcak yoldan ayrı çalıştır, böylece birincil agent hızlı kalır |

## İleri Okuma

- [Shinn et al., Reflexion: Language Agents with Verbal Reinforcement Learning (arXiv:2303.11366)](https://arxiv.org/abs/2303.11366) — kanonik makale
- [Letta, Sleep-time Compute](https://www.letta.com/blog/sleep-time-compute) — üretimde asenkron self-reflection
- [Anthropic, Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — episodic buffer'ı bağlamın parçası olarak yönetmek
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) — reflection node deseni
