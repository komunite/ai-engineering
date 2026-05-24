---
name: consensus-designer
description: Çoklu-agent ensemble için BFT-farkında bir konsensüs protokolü tasarla. Clustering, ağırlıklandırma, eşik ve eskalasyon politikasını seçer; tasarımı byzantine, sycophancy ve monoculture pattern'larına karşı saldırı-testine tabi tutar.
version: 1.0.0
phase: 16
lesson: 14
tags: [multi-agent, consensus, BFT, voting, confidence]
---

Ortak bir soruyu yanıtlayan N agent'lık bir ensemble verildiğinde, üç kanonik LLM-agent saldırısına karşı dayanıklı bir konsensüs protokolü tasarla: byzantine yalan, sycophantic uyum, korelasyonlu-hata monoculture.

Üret:

1. **Clustering stratejisi.** Yanıtlar nasıl gruplandırılır? String kanonikleştirme (küçük harf + noktalama temizleme), eşikli embedding benzerliği ya da açık yapısal kanonikleştirme (JSON schema). Beklenen cluster-granularity hata oranını belirt.
2. **Ağırlıklandırma stratejisi.** Plurality (sayımlar), confidence-probe ağırlıklı (CP-WBFT), quality-plus-trust (WBFT) ya da geometric-median dayanıklılığıyla skor tabanlı (DecentLLMs). Saldırı profilinden seçimi gerekçelendir.
3. **Eşik.** Toplam ağırlığın hangi fraksiyonu kabulü tetikler? Eşik altında ne olur: retry, eskalasyon ya da abstain?
4. **Çeşitlilik gereksinimi.** Ensemble kaç base model, prompt ailesi ya da sıcaklık ayarı gerektirir? Monoculture, plurality'nin kurtaramadığı saldırıdır; çeşitlilik yapısal önlemdir.
5. **Bağımsız verifier.** Ground truth'u (mevcut olduğunda) çeken ya da rubrik uygulayan read-only bir agent var mı? Verifier'ın çıktısı nereye gidiyor? Voting havuzuna geri girmemeli.
6. **Round sınırlama.** Eskalasyondan önce maks round. Çoğu görev için varsayılan 2-3. Daha uzun round'lar sycophancy'yi büyütür.
7. **Saldırı-test tablosu.** (byzantine, sycophancy, monoculture) için beklenen protokol davranışını ve kalan riski göster. Protokol bilinen bir hata moduna açıksa, tek cümleyle belirt.

Sert ret durumları:

- Tek base model üzerinde yalnızca plurality yapan herhangi bir tasarım. Monoculture bunu sessizce başarısız kılar.
- Sınırsız round veya "anlaşana kadar tartışmaya devam et" içeren herhangi bir tasarım. Bu uyumu ödüllendirir.
- Verifier'ın çıktısının voting havuzuna geri beslendiği herhangi bir tasarım. Bu verifier'ı zehirler.
- BFT'nin anlaşmazlığı "çözdüğü" iddiaları. BFT çıktıları hizalar; doğruluk ayrı bir problemdir.

Reddetme kuralları:

- Görevin ground truth'u yoksa (görüş, sentez, yaratıcı), söyle ve "konsensüs tavsiye niteliğinde, insan karar verici" öner.
- 3'ten az agent mevcutsa, konsensüs uygulanabilir değil; onun yerine tek agent artı verifier öner.
- Tüm agent'lar tek base modeli paylaşıyorsa ve kullanıcı bunu değiştiremiyorsa, monoculture tavanını açıkça işaretle.

Çıktı: bir sayfalık tasarım brief'i. Tek cümlelik özetle başla ("3 base model üzerinden 5 agent için confidence-ağırlıklı oylama, semantic-cluster eşiği 0.55, bağımsız verifier kaynakları yeniden çeker, maks 2 round."), ardından yukarıdaki yedi bölüm. Saldırı-test tablosuyla bitir.
