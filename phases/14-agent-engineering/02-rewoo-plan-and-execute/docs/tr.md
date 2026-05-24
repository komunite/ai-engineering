# ReWOO ve Plan-and-Execute: Ayrıştırılmış Planlama

> ReAct, düşünce ve aksiyonu tek bir akışta iç içe geçirir. ReWOO bunları ayırır: önden büyük bir plan, sonra yürüt. 5x daha az token, HotpotQA'da +%4 doğruluk ve planner'ı 7B bir modele damıtabilirsin. Plan-and-Execute bunu genelleştirdi; Plan-and-Act ise web navigasyonuna ölçekledi.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- ReWOO'nun Planner / Worker / Solver ayrımının ReAct'ın iç içe döngüsüne karşı neden token kazandırdığını ve sağlamlık iyileştirdiğini açıkla.
- Bir plan DAG'ı, bağımlılık-sıralı bir executor ve worker çıktılarını birleştiren bir solver uygula — hepsi stdlib.
- 2026 "beş workflow pattern" çerçevesini (Anthropic) kullanarak bir görevin plan-sonra-yürüt mü yoksa iç içe ReAct mı olarak çalışması gerektiğine karar ver.
- Uzun-ufuk web ya da mobil görevleri için Plan-and-Act'in sentetik plan verisinin ne zaman gerektiğini tanı.

## Sorun

ReAct'ın iç içe düşünce-aksiyon-gözlem döngüsü basit ve esnektir, ama her tool çağrısı tam önceki bağlamı taşımak zorunda — her önceki düşünce dahil. Token kullanımı derinlikle karesel büyür. Daha kötüsü: bir tool döngü ortasında başarısız olduğunda, model tüm planı hata gözleminden yeniden türetmek zorunda.

ReWOO (Xu et al., arXiv:2305.18323, Mayıs 2023) bunu fark etti ve bir bahis koydu: her şeyi önden planla, kanıtı paralel olarak çek, sonunda yanıtı birleştir. Plan için bir LLM çağrısı, kanıt için N tool çağrısı (paralel olabilir), çözüm için bir LLM çağrısı. Takas, daha az esneklik (plan statik) karşılığında çok daha iyi token verimliliği ve daha net başarısızlık modları.

## Kavram

### Üç rol

```
Planner:  user_question -> [plan_dag]
Workers:  [plan_dag]     -> [evidence]        (tool çağrıları, muhtemelen paralel)
Solver:   user_question, plan_dag, evidence -> final_answer
```

Planner bir DAG üretir. Her node bir tool'u, argümanlarını ve hangi daha önceki node'lara bağımlı olduğunu (referanslar gibi `#E1`, `#E2`) adlandırır. Worker'lar node'ları topolojik sırada yürütür. Solver her şeyi birleştirir.

### Neden 5x daha az token

ReAct, prompt uzunluğunu adım sayısıyla doğrusal büyütür. Adım 10'da prompt; düşünce 1 artı aksiyon 1 artı gözlem 1 artı düşünce 2 artı aksiyon 2 artı gözlem 2 vb. içerir. Her ara adım orijinal prompt'u da gereksiz içerir.

ReWOO bir planner prompt'u (büyük), N küçük worker prompt'u (her biri sadece tool çağrısı, zincir yok) ve bir solver prompt'u öder. HotpotQA'da makale, +4 mutlak doğruluk skoru ile ~5x daha az token ölçüyor.

### Neden daha sağlam

Worker 3 ReAct'ta başarısız olursa, döngü hatadan akış ortasında akıl yürütmek zorunda. ReWOO'da worker 3 bir hata string'i döndürür; solver bunu orijinal planla birlikte bağlamda görür ve zarif şekilde degrade edebilir. Başarısızlık lokalizasyonu adım başına değil, node başına.

### Planner damıtma

Makalenin ikinci sonucu: planner gözlemleri görmediği için, 175B öğretmenden alınan planner çıktılarında 7B bir modeli fine-tune edebilirsin. Küçük model planlamayı halleder; büyük model çıkarımda gerekmez. Bu artık standart — çoğu 2026 üretim agent'ı küçük bir planner ve büyük bir executor kullanır ya da tam tersi.

### Plan-and-Execute (LangChain, 2023)

LangChain ekibinin Ağustos 2023 yazısı ReWOO'yu bir pattern adına genelleştirdi: Plan-and-Execute. Önden planner bir adım listesi yayar, executor her adımı çalıştırır, opsiyonel bir replanner sonuçları gözlemledikten sonra revize edebilir. Bu, ReWOO'dan ReAct'a daha yakın (replanner gözlemleri planlamaya geri getirir) ama token tasarrufunu korur.

### Plan-and-Act (Erdogan et al., arXiv:2503.09572, ICML 2025)

Plan-and-Act bu deseni uzun-ufuk web ve mobil agent'lara ölçekler. Ana katkı sentetik plan verisi: planın açık olduğu eğitim verisi üreten etiketli bir trajectory üreteci. WebArena-benzeri görevlerde 30–50 adımın ötesinde çalışmaya devam eden planner modellerini fine-tune etmek için kullanılır — tek bir ReAct trajectory'sinin tutarlılığını kaybettiği yerlerde.

### Hangisini ne zaman seçmeli

| Pattern | Ne zaman |
|---------|------|
| ReAct | Kısa görevler, bilinmeyen ortam, reaktif istisna ele alma ihtiyacı |
| ReWOO | Bilinen tool'lu yapılandırılmış görevler, token-hassas, paralelleştirilebilir kanıt |
| Plan-and-Execute | ReWOO gibi ama kısmi yürütme sonrası replanning ile |
| Plan-and-Act | Uzun-ufuk (>30 adım), web/mobil/computer-use |
| Tree of Thoughts | Arama yapmaya değer (Ders 04) |

Anthropic'in Aralık 2024 rehberi: en basitiyle başla. Görev bir tool çağrısı artı bir özetse, ReWOO kurma. Görev 40 adımlık bir araştırma ödeviyse, yalnızca ReAct yapma.

## İnşa Et

`code/main.py` bir oyuncak ReWOO uygular:

- `Planner` — bir prompt'tan plan DAG'ı yayan scripted policy.
- `Worker` — her node'un tool çağrısını registry üzerinden dispatch eder.
- `Solver` — kanıtı okuyan ve nihai yanıt üreten scripted komposizyon.
- Bağımlılık çözümlemesi — `#E1` gibi referanslar önceki worker çıktılarıyla değiştirilir.

Demo, "Fransa'nın başkentinin nüfusu milyon olarak yuvarlanmış kaç?" sorusunu iki adımlı planla yanıtlıyor: (1) başkenti ara, (2) nüfusu ara, sonra çöz.

Çalıştır:

```
python3 code/main.py
```

Trace önce tüm planı, sonra worker sonuçlarını, sonra solver komposizyonunu gösterir. Token sayısını (kaba bir karakter sayısı yazdırıyoruz) ReAct-tarzı iç içe bir koşuyla karşılaştır — ReWOO bu tür yapılandırılmış görevlerde kazanır.

## Kullan

LangGraph, Plan-and-Execute'i bir tarif olarak yayıyor (ReAct için `create_react_agent`, plan-execute için custom graph'lar). CrewAI'nin Flow'ları deseni doğrudan kodluyor: görevleri önden tanımlarsın ve Flow DAG'ı bunları yürütür. Plan-and-Act'in sentetik veri yaklaşımı hâlâ çoğunlukla araştırma; runtime deseni (açık plan DAG) LangGraph ve CrewAI Flow'lar üzerinden üretimde yayınlanıyor.

## Yayınla

`outputs/skill-rewoo-planner.md` bir kullanıcı isteğinden, bir tool kataloğu verildiğinde, bir ReWOO plan DAG'ı üretir. Bir executor'a devretmeden önce planı doğrular (asiklik, her referans çözümlenmiş, her tool var).

## Alıştırmalar

1. Bağımsız plan node'ları için worker yürütmesini paralelleştir. 2 paralel grup içeren 6-node bir DAG'da sana ne kazandırır?
2. Herhangi bir worker hata döndürürse tetiklenen bir replanner node'u ekle. ReWOO'yu Plan-and-Execute yapan en küçük değişiklik nedir?
3. `Planner`'ı küçük bir modelle (7B sınıfı) değiştir ve `Solver`'ı bir frontier modelde tut. Uçtan-uca kaliteyi karşılaştır — ayrım nerede başarısız oluyor?
4. ReWOO makalesinin planner damıtması üzerine 4. bölümünü oku. 175B -> 7B sonucunu kavramsal olarak yeniden üret: hangi eğitim verisine ihtiyacın var ve plan kalitesini nasıl puanlarsın?
5. Oyuncağı Plan-and-Act'in trajectory şekline taşı: plan bir DAG değil, bir dizi. Hangi tradeoff'lar değişir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| ReWOO | "Gözlemler olmadan akıl yürütme" | Planla, sonra paralel kanıt çek, sonra çöz — planlama prompt'unda gözlem yok |
| Plan-and-Execute | "LangChain'in plan-execute pattern'i" | Yürütmeden sonra opsiyonel replanner node'lu ReWOO |
| Plan-and-Act | "Ölçeklenmiş plan-execute" | Uzun-ufuk görevler için sentetik plan eğitim verili açık planner/executor ayrımı |
| Evidence reference | "#E1, #E2, ..." | Dispatch sırasında önceki worker çıktısıyla değiştirilen plan-node placeholder'ı |
| Planner damıtma | "Küçük planner, büyük executor" | Büyük öğretmenden alınan planner trace'lerinde küçük bir modeli fine-tune et |
| Token verimliliği | "Daha az round trip" | Makalede HotpotQA'da ReAct'a karşı 5x daha az token |
| DAG executor | "Topolojik dispatcher" | Plan node'larını bağımlılık sırasında çalıştırır; her seviyede paralel |

## İleri Okuma

- [Xu et al., ReWOO: Decoupling Reasoning from Observations (arXiv:2305.18323)](https://arxiv.org/abs/2305.18323) — kanonik makale
- [Erdogan et al., Plan-and-Act (arXiv:2503.09572)](https://arxiv.org/abs/2503.09572) — sentetik planlı ölçeklenmiş planner-executor
- [LangGraph Plan-and-Execute tutorial](https://docs.langchain.com/oss/python/langgraph/overview) — framework tarifi
- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — işe yarayan en basit pattern'i seç
