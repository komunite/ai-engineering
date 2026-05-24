---
name: fairness-criterion
description: Bir iddianın hangi fairness kriterini çağırdığını tespit et ve ilgili varsayımları denetle.
version: 1.0.0
phase: 18
lesson: 21
tags: [fairness, demographic-parity, equalized-odds, counterfactual-fairness, impossibility]
---

Bir fairness iddiası veya politikası verildiğinde, hangi kriterin çağrıldığını, iddianın hangi varsayımlara dayandığını ve impossibility teoremlerinin kalan kriterler için ne ima ettiğini tespit et.

Üret:

1. Kriter tanımlaması. İddiayı şunlardan birini hedefleyen olarak etiketle: demographic parity, equalized odds, conditional use accuracy equality, individual fairness, counterfactual fairness. Belirsiz iddialar devam edilmeden önce çözülmelidir.
2. Base-rate denetimi. Deployment'taki grup-başına base rate'ler nedir? Eşit olmayan base rate'ler altında, Chouldechova / KMR 2017 impossibility uygulanır: hiçbir model üç grup kriterini de tatmin etmez.
3. Causal-DAG bağımlılığı. İddia counterfactual fairness ise, causal DAG nedir? Counterfactual fairness yalnızca DAG kadar gerekçelidir. DAG eksikliği iddiayı geçersiz kılar.
4. Benzerlik metriği. İddia individual fairness ise, benzerlik metriği d nedir? Seçim göreve-spesifiktir ve istatistiksel değil bir politika kararıdır.
5. Müdahale yasallığı. İddia counterfactual akıl yürütme kullanıyorsa, korunan attribute'lar üzerinde müdahaleler söz konusu mu? Evet ise, hukuki sorunları atlatmak için backtracking counterfactuals'ı (arXiv:2401.13935) düşün.

Sert reddetmeler:
- Kriter tanımlaması olmadan herhangi bir "fair" iddiası.
- Chouldechova / KMR 2017'yi kabul etmeden eşit olmayan base rate'ler altında "tüm fairness kriterleri tatmin edildi" iddiası.
- Yayımlanmış bir causal DAG olmadan herhangi bir counterfactual-fairness iddiası.

Reddetme kuralları:
- Kullanıcı hangi fairness kriterinin "doğru olanı" olduğunu sorarsa, sıralamayı reddet ve bunun bir politika seçimi olduğunu açıkla.
- Kullanıcı bir modelin "fair" olup olmadığını sorarsa, ikili iddiayı reddet; fairness kriter-göreceli bir şeydir.

Çıktı: yukarıdaki beş bölümü dolduran, uygunsa impossibility'yi işaretleyen ve iddianın içerdiği politika seçimini adlandıran tek sayfalık bir denetim. Dwork et al. 2012, Kusner et al. 2017, Chouldechova 2017'yi uygun olduğunda birer kez alıntıla.
