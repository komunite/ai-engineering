# Theory of Mind ve Ortaya Çıkan Koordinasyon

> Li ve diğ. (arXiv:2310.10701) iş birlikçi bir metin oyunundaki LLM agent'larının **ortaya çıkan yüksek-mertebe Theory of Mind** (ToM) sergilediğini gösterdi — bir agent'ın üçüncü bir agent'ın inançları hakkında ne inandığı üzerine akıl yürütme — ama context yönetimi ve halüsinasyon nedeniyle uzun-vadeli planlamada başarısız oldu. Riedl (arXiv:2510.05174) bir popülasyonda yüksek-mertebe sinerjiyi ölçtü ve **yalnızca** ToM-prompt koşulunun kimlik-bağlı farklılaşma ve hedef-yönelimli tamamlayıcılık ürettiğini buldu; daha düşük-kapasiteli LLM'ler yalnızca sahte ortaya çıkışı gösteriyor. Yani, koordinasyon ortaya çıkışı prompt-koşullu ve model-bağımlıdır, bedava değil. Bu ders minimal bir ToM-aware agent uygular, ToM prompt'lu ve prompt'suz iş birlikçi bir görev çalıştırır ve Riedl 2025 protokolüne karşı koordinasyon delta'sını ölçer.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 07 (Society of Mind ve Debate), Faz 16 · 17 (Generative Agent'lar)
**Süre:** ~75 dakika

## Sorun

Çoklu-agent koordinasyonu sıklıkla büyülü görünür: agent'lar iş bölümü yapar, birbirini öngörür, gereksizliği önler. Genellikle bu "ortaya çıkış" prompt mühendisliğinin bir artefaktıdır — biri agent'lara "koordine et" dedi. Prompt'u kaldır, koordinasyonu kaldır.

Riedl'in 2025 bulgusu daha katı: kontrollü koşullar altında, koordinasyon yalnızca agent'lar **diğer agent'ların zihinleri** (ToM) hakkında akıl yürütmeye prompt'landığında ortaya çıkar. ToM prompt'u olmadan, güçlü modeller bile istatistiksel kontrolleri atlatmayan koordinasyon desenleri gösterir. Bu üretim için önemli: takımlar prompt-bağımlı ve kırılgan "çoklu-agent koordinasyonu" özellikleri gönderir.

Bu ders ToM'u belirli bir yetenek olarak ele alır (inançlar hakkında inançlar üzerine akıl yürütme), minimal bir ToM-aware agent inşa eder ve gerçek koordinasyonun nasıl göründüğünü vs prompt süslemesinin nasıl göründüğünü ölçer.

## Kavram

### ToM ne demek

Gelişim psikolojisi: 3 yaşındaki herkesin iç dünyasının kendininkiyle eşleştiğini düşünür. 5 yaşındaki başkalarının farklı inançlara sahip olduğunu anlar. 7 yaşındaki inançlar hakkında inançlar üzerine akıl yürütür ("o, topun bardağın altında olduğunu düşündüğümü düşünüyor"). Bunlar sıfırıncı, birinci ve ikinci-mertebe ToM'dur.

LLM agent'lar için ToM mertebeleri şunlara eşlenir:

- **Sıfırıncı-mertebe:** başkalarının modeli yok. Agent yalnızca kendi gözlemleri üzerinde hareket eder.
- **Birinci-mertebe:** agent her diğer agent'ın inançlarının modeline sahiptir. "Alice X'e inanıyor."
- **İkinci-mertebe:** agent rekürsif inançları modeller. "Alice, Bob'un X'e inandığına inanıyor."

Li ve diğ. 2023 iş birlikçi oyunlarda LLM agent'larında birinci- ve ikinci-mertebe ToM'un ortaya çıktığını ama uzun ufuk ve güvenilmez iletişimle bozulduğunu buldu.

### Sally-Anne testi, kısaca

1985 sahte-inanç testi: Sally bir misketi sepet A'ya koyar, ayrılır. Anne onu sepet B'ye taşır. Sally döndüğünde nereye bakacak? Birinci-mertebe ToM'a sahip bir çocuk sepet A der (Sally'nin inancı gerçeklikten farklı). Olmayan bir çocuk sepet B der.

GPT-4 dönemi LLM'leri açıkça konulduğunda Sally-Anne-stili testleri geçer. Anlatı uzun, sahne birkaç kez değiştiğinde ya da soru dolaylı ifade edildiğinde başarısız olurlar. Üretim LLM'lerinde ToM'un pratik 2026 durumu budur.

### Riedl'in koordinasyon ölçümü

Riedl (arXiv:2510.05174) popülasyon-ölçekli bir test inşa etti: N agent, iş birlikçi bir hedef, değişken prompt koşulları. Ölçüm:

1. **Kimlik-bağlı farklılaşma.** Agent'lar zaman içinde stabil rol ayrımları geliştiriyor mu?
2. **Hedef-yönelimli tamamlayıcılık.** Agent'ların eylemleri tekrarlamak yerine birbirini (farklı alt görevler) tamamlıyor mu?
3. **Yüksek-mertebe sinerji.** Grubun hiçbir alt kümenin yapamayacağını başarıp başarmadığının istatistiksel ölçümü.

Sonuç: yalnızca ToM prompt koşulu altında üç metrik de baseline üzerinde sinyal üretir. ToM prompt'u olmadan, orta-kapasiteli modeller için metrikler şansa yakın gezinir. Büyük modeller açık ToM prompt'u olmadan biraz koordinasyon gösterir ama etki açık prompt'lamaya göre daha küçüktür.

### Koordinasyon yanılsaması

İstatistiksel kontroller olmadan, demolardaki "ortaya çıkan koordinasyon" sıklıkla şunları yansıtır:

- Koordinasyonu pişiren prompt mühendisliği ("birlikte çalış" diyen sistem prompt'ları).
- Gözlemci yanlılığı (beklediğimiz desenleri görürüz).
- Başarılı çalıştırmaların post-hoc seçimi.

Ölçülebilir sinyal olmadan "ortaya çıkan koordinasyon" pazarlayan üretim sistemleri pazarlama olarak ele alınmalı. İddia etmeden önce ölç.

### Minimal ToM-aware bir agent

Yapı:

```
agent state:
  own_beliefs:    {agent'ın inandığı gerçekler}
  other_models:   {other_agent_id -> {agent'ın onlara atfettiği inançlar}}
  actions_last_N: [başkalarının eylem geçmişi]

gözlem güncelleme:
  - doğrudan gözlemden own_beliefs'i güncelle
  - eylemleri + önceki inançlardan other_models[agent_id]'i güncelle

eylem seçimi:
  - aday eylemleri sırala
  - her biri için, modellenmiş inançları verildiğinde diğer her agent'ın sıradakini ne yapacağını öngör
  - bu öngörüler altında ortak sonucu maksimize eden eylemi seç
```

`other_models` özniteliği ToM state'idir. Birinci-mertebe ToM yalnızca bir seviye tutar. İkinci-mertebe `other_models[i][other_models_of_j]`'yi ekler — i agent'ın j agent'ın inandığını düşündüğüm.

### Uzun-ufuk neden zarar verir

Li ve diğ. belgeliyor: context sınırları agent'ların hangi inancın kime ait olduğunu unutmasına neden olur. Halüsinasyon diğer-agent modellerine yanlış inançlar ekler. İkisi de zaman içinde bileşen yapan "onun X düşündüğünü düşündüm" hatalarını üretir.

Makalede ve 2024-2026 takiplerinde belgelenen hafifletmeler:

- **Prompt'ta açık ToM state'i.** Yapılandırılmış format: `{agent_id: belief_list}`. Getirmeyi kimlik-inanç bağlamayı korumaya zorlar.
- **Daha kısa akıl yürütme zincirleri.** Tur başına daha az ToM güncellemesi bileşik halüsinasyonu azaltır.
- **Dışsal ToM store.** Modeli LLM context'i dışında tut; tur başına yalnızca ilgili kısımları enjekte et.

### ToM üretimde nerede başarısız olur

- **Adversarial ayarlar.** İyi ToM'lu agent'ları manipüle etmek daha kolay (seni ne modellediklerini modelleyebilirsin, sonra sömürebilirsin).
- **Heterojen takımlar.** Modeller farklı olduğunda, bir rakip için çalışan ToM modeli genelleştirmez.
- **Ground-truth-bağımlı görevler.** ToM inançlar hakkındadır; doğruluk gerçeklere bağlıysa ToM dikkat dağıtıcı olabilir.

### Gerçekten ölçebileceğin koordinasyon

Bir takımın koordinasyonunun prompt-süslü değil, gerçek olduğunun üç pratik sinyali:

1. **Zaman içinde tamamlayıcılık.** Çoklu-tur bir görevde agent'ların eylemleri ayrık alt-görevleri kapsıyor mu?
2. **Öngörü.** Agent A'nın T+1 turundaki eylemi B'nin T+2'deki eylemi hakkında doğru çıkan bir öngörüye mi bağlı?
3. **Düzeltme.** A, T turunda B'nin inancını yanlış okuduğunda, A T+2 turunda düzeltir mi?

Bunlar log'lanmış bir çoklu-agent sisteminde ölçülebilir. "Koordinasyon" anlatısının özsel versiyonudur.

## İnşa Et

`code/main.py` şunları uygular:

- `ToMAgent` — kendi inançlarını ve diğer-agent başına inanç modellerini izler.
- İş birlikçi görev: üç agent üç kutudan üç token toplamalı; her kutu bir token tutabilir. Agent'lar iletişim kuramaz; niyeti birbirinin eylemlerinden çıkarır.
- İki konfigürasyon: `zeroth_order` (ToM yok) ve `first_order` (tek-seviye inanç modeliyle ToM).
- 200 rastgele deneme üzerinde ölçüm: tamamlanma oranı, yineleme oranı (iki agent aynı kutuyu hedefler), tamamlanma için ortalama tur.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı: sıfırıncı-mertebe agent'lar ~%35 oranında çabayı yinelerken 10 turda denemelerin ~%60'ını tamamlar. Birinci-mertebe ToM agent'ları ~%5 yineler ve ~%95 tamamlar. Delta ölçülebilir koordinasyon etkisidir.

## Kullan

`outputs/skill-tom-auditor.md` bir çoklu-agent sisteminin "ortaya çıkan koordinasyon" iddiasını denetleyen bir skill'dir. Prompt süslemesi, bir kontrole karşı istatistiksel anlamlılık ve ölçülen tamamlayıcılığı kontrol eder.

## Yayınla

Koordinasyon iddiaları kontrol listesi:

- **Kontrol koşulu.** Koordinasyon prompt'u olmayan bir sistem versiyonu. İkisini de ölç.
- **İstatistiksel test.** Sistem ve kontrol arasındaki fark metriğinde `p < 0.05` anlamlı mı?
- **Tamamlayıcılık ölçümü.** Yalnızca son başarı değil, zaman içinde eylem-ayrıklığı.
- **Başarısızlık-vaka log'u.** Agent'lar yanlış koordine olduğunda, ToM state'i nasıl görünüyor?
- **Model-kapasite açıklaması.** Etki daha küçük modellerde kayboluyorsa, söyle.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Birinci-mertebe ToM'un yineleme oranını ~7× azalttığını doğrula. 5 agent ve 5 kutuya ölçeklediğinde boşluk devam ediyor mu?
2. İkinci-mertebe ToM uygula (agent A, B'nin C hakkında ne düşündüğünü modeller). Birinci-mertebe üzerinde iyileştiriyor mu? Hangi görevlerde?
3. ToM state'ine bir **halüsinasyon** enjekte et: tur başına rastgele bir inancı çevir. Bu birinci-mertebe performansı ne kadar bozar?
4. Li ve diğ.'i (arXiv:2310.10701) oku. "Uzun-ufuk bozulma" bulgusunu yeniden üret: turlar 10'dan 30'a büyüdüğünde, birinci-mertebe ToM performansın nasıl değişir?
5. Riedl 2025'i (arXiv:2510.05174) oku. Simülasyon log'larında yüksek-mertebe sinerji istatistiğini uygula. Etki ToM prompt koşulu olmadan mevcut mu?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Theory of Mind | "Başkalarının zihinlerini anlama" | Başka bir agent'ın inançlarını modelleme kapasitesi. Mertebeye göre derecelendirilir (0, 1, 2+). |
| Sally-Anne testi | "Sahte-inanç testi" | 1985 gelişim psikolojisi; LLM'ler düz versiyonları geçer, karmaşık olanlarda başarısız olur. |
| Birinci-mertebe ToM | "A X'e inanıyor" | Bir başkasının gerçekler hakkındaki inançlarını modelleme. |
| İkinci-mertebe ToM | "A, B'nin X'e inandığına inanıyor" | Bir seviye daha derinde rekürsif modelleme. |
| Kimlik-bağlı farklılaşma | "Zaman içinde stabil roller" | Riedl'in metriği: roller kalıcı, rastgele değil. |
| Hedef-yönelimli tamamlayıcılık | "Ayrık eylemler" | Agent'lar aynı değil, farklı alt-görevleri hedefler. |
| Yüksek-mertebe sinerji | "Grup herhangi bir alt kümeyi aşar" | Riedl'in gerçek koordinasyon için istatistiksel ölçümü. |
| Koordinasyon yanılsaması | "Koordineli görünüyor" | Ölçülebilir sinyal olmadan koordinasyonun prompt-süslü görünümü. |

## İleri Okuma

- [Li ve diğ. — Theory of Mind for Multi-Agent Collaboration via Large Language Models](https://arxiv.org/abs/2310.10701) — iş birlikçi oyunlarda ortaya çıkan ToM; uzun-ufuk başarısızlık modları
- [Riedl — Emergent Coordination in Multi-Agent Language Models](https://arxiv.org/abs/2510.05174) — popülasyon-ölçekli ölçüm; ToM prompt'lama yük taşıyıcı koşuldur
- [Premack & Woodruff — Does the chimpanzee have a theory of mind?](https://www.cambridge.org/core/journals/behavioral-and-brain-sciences/article/does-the-chimpanzee-have-a-theory-of-mind/1E96B02CD9850E69AF20F81FA7EB3595) — ToM kavramının 1978 kaynağı
- [Baron-Cohen, Leslie, Frith — Does the autistic child have a theory of mind?](https://www.cambridge.org/core/journals/behavioral-and-brain-sciences/article/does-the-autistic-child-have-a-theory-of-mind/) — Sally-Anne makalesi (1985)
