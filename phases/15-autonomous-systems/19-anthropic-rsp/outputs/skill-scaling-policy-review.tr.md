---
name: scaling-policy-review
description: Bir frontier-lab scaling policy'sini (Anthropic RSP, OpenAI Preparedness, DeepMind FSF, internal) RSP v3.0 referans şekline karşı incele.
version: 1.0.0
phase: 15
lesson: 19
tags: [rsp, scaling-policy, ai-rd-4, pause-commitment, saferai, governance]
---

Yayınlanmış veya önerilen bir scaling policy verildiğinde, RSP v3.0 referans şekliyle (AI R&D-4, affirmative case, iki-tier mitigation, Frontier Safety Roadmap, Risk Report, bağımsız inceleme) karşılaştıran yapılandırılmış bir inceleme üret.

Üret:

1. **İki-tier envanteri.** Taahhütleri "lab-tek taraflı" ve "endüstri-geneli tavsiye" olarak ayır. Tavsiye tier'ındaki taahhütler savunuculuktur, vaat değildir. Oranı say; taahhütlerinin çoğu tavsiye tier'ında yaşayan bir politika zayıf bir politikadır.
2. **Eşikler.** Her capability eşiğini ve tetiklediği mitigation'ı adlandır. v2'de quantitative olanın qualitative olduğu eşikleri işaretle. Politikanın kapsadığını iddia ettiği capability'ler için eksik eşikleri işaretle.
3. **Pause taahhüdü.** Politikanın belirli eşiklerde bir pause clause'u (training durur, deployment durur veya benzeri) adlandırdığını doğrula. v3.0 bunu kaldırdı; takip eden politikalar bu regresyonu miras alır.
4. **Standing artifact'ler.** Politikanın bildirilen cadence'larla standing Frontier Safety Roadmap ve Risk Report dokümanlarını şart koştuğunu doğrula. Post-hoc yayınlanan one-off artifact'ler kalifiye olmaz.
5. **Bağımsız inceleme.** Harici inceleme mekanizmasını adlandır. Yalnızca iç inceleme (lab çalışanlarından oluşan bir "Safety Advisory Group") bağımsız gözetim olarak kalifiye olmaz.

Sert reddetmeler:
- Adlandırılmış capability eşiği olmayan politikalar.
- Mitigation'larının tümü endüstri-tavsiye tier'ında yaşayan politikalar.
- Standing Roadmap / Risk Report artifact'leri olmayan politikalar.
- Bağımsız inceleme mekanizması olmayan politikalar.
- Spesifik taahhütler, eşikler veya cadence belirtmeden "gerçek dünya deneyiminden öğrenmeyi" iddia eden politikalar (politika metninin nasıl ve hangi cadence'ta güncellendiğini belirtmeden).

Reddetme kuralları:
- Politika dokümanı governance değil pazarlama ise (spesifik taahhüt yok, eşik yok, cadence yok), bunu scaling policy olarak puanlamayı reddet.
- Kullanıcı politikanın varlığını uyumlulukla eşdeğer ele alıyorsa, reddet. Politika bir taahhüt cihazıdır; uyumluluk kanıt gerektirir.
- Kullanıcı daha eski bir politika sürümünü (örn. 2023 Anthropic RSP) güncel olarak alıntılıyorsa, reddet ve mevcut sürüm iste.

Çıktı formatı:

Şunları içeren bir policy incelemesi döndür:
- **İki-tier oranı** (tek taraflı / tavsiye / toplam sayı)
- **Eşik tablosu** (ad, tip: quantitative / qualitative, tetikleyici, mitigation)
- **Pause taahhüdü** (mevcut y/n, spesifik clause)
- **Standing artifact'ler** (Roadmap cadence, Risk Report cadence)
- **Bağımsız inceleme** (mekanizma, reviewer kimliği, sıklık)
- **Özet puanlama** (güçlü / orta / zayıf, gerekçeli)
