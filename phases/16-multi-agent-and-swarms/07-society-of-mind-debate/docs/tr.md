# Society of Mind ve Çoklu-Agent Debate

> Minsky'nin 1986 öncülü — zeka uzmanlardan oluşan bir toplumdur — her on yılda yeniden keşfedilir. 2023'te Du ve diğ. bunu somut bir algoritmaya dönüştürdü: birden çok LLM örneği cevaplar önerir, birbirinin cevaplarını okur, eleştirir ve günceller. N tur boyunca, altı akıl yürütme ve gerçeklik görevinde zero-shot CoT ve reflection'ı yenen bir konsensüse yakınsarlar. İki bulgu önemli: hem **çoklu agent** hem **çoklu tur** bağımsız olarak katkıda bulunur. Toplum tek-agent monoloğunu yener; çoklu-tur alışverişi tek-atış oylamayı yener.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 04 (Primitive Model)
**Süre:** ~60 dakika

## Sorun

Self-consistency — bir modeli birçok kez örnekle ve çoğunluk cevabını al — üzerine ekleyebileceğin en ucuz akıl yürütme iyileştirmesidir. Çalışır, ama hızlı doyar. Örneklerini ikiye katlarsın ve başka anlamlı bir sıçrama görmezsin.

Debate doyumu kırar. Bir modelden N bağımsız örnek yerine, N agent birbirinin akıl yürütmesini okur ve revize eder. Örnekler arasındaki korelasyon düşer (artık i.i.d. değiller) ve yakınsama noktası genellikle i.i.d. oylamanın güvenle yanlış olduğu yerde doğrudur.

## Kavram

### Du ve diğ. 2023 algoritması

arXiv:2305.14325'ten (ICML 2024):

1. N agent'ın her biri soruya bir başlangıç cevabı üretir.
2. Tur r = 2..R için: her agent'a diğer agent'ların tur r-1 cevapları gösterilir ve "bunları göz önünde bulundurarak güncellenmiş cevabını ver" denir.
3. R tur sonra final cevapları çoğunluk-oyla.

Makale MMLU, GSM8K, biyografiler, MATH ve faktüel benchmark'larda test eder. Debate sürekli olarak CoT ve Self-Reflection'ı yener.

### İki bağımsız düğme

Aynı makaleden ablation'lar:

- **Yalnızca agent sayısı** (1 tur, N'in çoğunluk oyu) çoğu görevde tek-agent'ı yener, ama plato çizer.
- **Yalnızca tur sayısı** (kendi önceki akıl yürütmesini gören 1 agent) zar zor yardım eder — reflection'ın bilinen zayıflığı.
- **İkisi birlikte** büyük sıçramaları üretir. Birden çok agent arasındaki çoklu-tur alışverişi kazanımı sağlar.

### Neden çalışır

İki mekanizma:

1. **Anlaşmazlığa maruz kalma.** Bir agent başka bir agent'ın farklı bir sonuca sahip akıl yürütme zincirini gördüğünde, ya gerekçelendirmeli ya da güncellemelidir. Her iki şekilde de tur r+1 için context tur r'den daha zengindir.
2. **Korelasyonlu hata azaltma.** Self-consistency'de tüm örnekler aynı modelden gelir, yani hatalar korelasyonludur — güvenle yanlış bir cevapta ortalama alırsın. Farklı modeller ya da farklı seed'ler dekoreleştirir. Farklı *tartışılan görüşler* daha da dekoreleştirir.

### Heterojen debate

A-HMAD ve ilgili takipler farklı agent'lar için *farklı baz modeller* kullanır. Llama + Claude + GPT tartışması monokültür çöküşünü (Ders 26) azaltır çünkü bir model ailesinin korelasyonlu hataları diğerleri tarafından paylaşılmaz.

Dezavantaj: bir debate'e katılan zayıf bir model konsensüsü kendi yanlış cevabına çekebilir (bkz. "Should we be going MAD?", arXiv:2311.17371).

### NLSOM — 129-agent uzantısı

Zhuge ve diğ. ("Mindstorms in Natural Language-Based Societies of Mind," arXiv:2305.17066) bu fikri 129-üye topluluklara ölçekledi. Sonuç: uzmanlaşma ve kendi-kendini-organize etme ölçekle ortaya çıkar ve sistem visual question answering gibi görevlerde tek-agent'tan daha iyi performans gösterir.

### Başarısızlık modları

- **Yalakalık kaskadı.** Tüm agent'lar en kendine güvenen agent'a saygı gösterir. Tartışma en yüksek sese çöker. Karşıt rolleri prompt etmek ("bir agent karşı-pozisyonu savunmalı") yardımcı olur.
- **Konu kayması.** Çok turlu tartışmalar orijinal sorudan kayar. Hafifletme: her tur soruyu yeniden enjekte et.
- **Compute patlaması.** N agent × R tur = N·R LLM çağrısı, her biri büyüyen context ile. 5-agent, 5-tur debate büyüyen context'le 25 çağrıdır. Soru başına maliyet tek bir CoT çağrısının 10×'unu aşabilir.

## İnşa Et

`code/main.py` her agent'ın farklı (muhtemelen yanlış) bir cevapla başladığı bir matematik sorusu üzerinde 3-agent × 3-tur debate çalıştırır. Agent'lar senaryoludur — her biri komşuların cevaplarını senaryolu bir güvenle ağırlıklandırarak ortalayarak "güncellenir". Yakınsama tur-tur log'unda görünür.

Demo iki temel etkiyi gösterir:

- Tek bir alışveriş turu agent'ları doğru cevaba yaklaştırır.
- Tur 2'den sonraki ek turlar azalan getiri gösterir (Du ve diğ.'in platosuyla eşleşir).

Çalıştır:

```
python3 code/main.py
```

## Kullan

`outputs/skill-debate-configurator.md` yeni bir görev için bir debate yapılandırır: agent sayısı, tur sayısı, heterojenlik (aynı model vs karışık), rol ataması (simetrik vs bir-karşıt). Ayrıca çalıştırmadan önce token maliyetini tahmin eder.

## Yayınla

Debate gönderirsen:

- **Turları 3'te sınırla.** Du ve diğ. 3 turun kazanımın çoğunu yakaladığını gösterir. Daha fazlası maliyet, kalite değil.
- **Agent'ları 5'te sınırla.** 5'ten sonra context şişmesi ve maliyet baskın olur.
- **Varsayılan olarak heterojen.** Havuzda en az iki farklı baz model.
- **Karşıt slot.** Bir agent ne olursa olsun anlaşmamak için prompt'lanır. Yalakalığı kırar.
- **Her turu log'la.** Ara turları gizleyen debate sistemleri hata ayıklanamaz veya denetlenemez.

## Alıştırmalar

1. `code/main.py`'yi çalıştır, sonra tur sayısını 5 yap ve azalan getirileri izle. Hangi turda ek yakınsama durur?
2. Karşıt rollü dördüncü bir agent ekle: her zaman mevcut çoğunlukla anlaşma. Bu yakınsamayı kırar mı yoksa iyileştirir mi?
3. Tur başına anlaşma skorunu (çoğunluk cevabındaki agent oranı) çiz (yazdır). 1.0'a ne zaman ulaşır ve bu "doğru"ya eşdeğer mi?
4. Du ve diğ. Bölüm 4 ablation'larını oku. Bu kodu kullanarak "yalnızca-agent" vs "yalnızca-tur" vs "ikisi" sonucunu replike et.
5. "Should we be going MAD?" (arXiv:2311.17371) oku ve round-robin'in ötesinde iki debate varyantı listele — ör. judge-led, chain-of-debate, adversarial.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Society of Mind | "Minsky'nin fikri" | Etkileşen uzmanlar olarak zeka; 1986 çerçevesi şimdi LLM debate ile operasyonel hale geldi. |
| Çoklu-agent debate | "Agent'lar tartışır" | N agent önerir, birbirini eleştirir, R tur boyunca revize eder, çoğunluk-oylar. |
| Konsensüs | "Anlaşırlar" | Epistemik gerçek değil — sadece çoğunluk-cevabında-oran. Güvenle yanlış olabilir. |
| Turlar | "Alışveriş adımları" | Bir tur = her agent diğerlerini okur ve bir kez günceller. |
| Heterojen debate | "Model ailelerini karıştır" | Hataları dekoreleştirmek için farklı baz modeller kullanma. |
| Yalakalık kaskadı | "Herkes yüksek olanla anlaşır" | Agent'ların doğruluktan bağımsız olarak en kendine güvenen agent'a saygı gösterdiği debate başarısızlığı. |
| NLSOM | "129-agent toplumu" | Doğal-dil society of mind; Zhuge ve diğ.'in ölçeklenmiş versiyonu. |
| Korelasyonlu hata | "Aynı model, aynı bug" | Self-consistency'nin neden doyduğu; farklı görüşler arasında debate dekoreleştirir. |

## İleri Okuma

- [Du ve diğ. — Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325) — referans makale, ICML 2024
- [Zhuge ve diğ. — Mindstorms in Natural Language-Based Societies of Mind](https://arxiv.org/abs/2305.17066) — 129-agent NLSOM
- [Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs](https://arxiv.org/abs/2311.17371) — debate varyantlarını benchmark'lar
- [Debate project page](https://composable-models.github.io/llm_debate/) — Du ve diğ.'in kodu, demoları ve ablation detayları
