# STaR, V-STaR, Quiet-STaR — Self-Taught Reasoning

> Mümkün olan en küçük self-improvement döngüsü rationale'ın içinde oturur. Bir model bir chain of thought üretir, doğru cevaplara ulaşanları tutar ve onlar üzerinde fine-tune yapar. Bu STaR'dır. V-STaR bir verifier ekler, böylece çıkarım zamanı seçimi daha iyi olur. Quiet-STaR rationale'ı her token'a iter. Üçü de işe yarar. Hiçbiri sihir değil — döngü, doğru cevaba ulaşmayı denk getiren herhangi bir kestirmeyi korur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, bootstrap döngüsü simülatörü)
**Ön koşullar:** Faz 13 · 01-03 (Reasoning ve CoT), Faz 15 · 01 (uzun-horizon çerçeve)
**Süre:** ~60 dakika

## Sorun

Bir modele akıl yürütmeyi öğretmenin doğrudan yolu insan yazımı reasoning trace'leri toplamaktır. Bu pahalı, yavaş ve insanların yazmaya razı olduğu yüksek-kaliteli chain-of-thought miktarıyla sınırlıdır.

STaR (Self-Taught Reasoner, Zelikman vd., 2022) şunu sorar: ya model kendi rationale'larını yazıp bilinen cevaplara karşı not verirse? Döngü:

1. Bir reasoning trace artı cevap örnekle.
2. Final cevap doğruysa trace'i tut.
3. Tutulan trace'ler üzerinde fine-tune yap.
4. Tekrarla.

İşe yarıyor. GSM8K ve CommonsenseQA, yeni insan anotasyonu olmadan iyileşti. Ama döngünün yerleşik bir önyargısı var: doğru cevabı üreten herhangi bir rationale, akıl yürütmenin kendisi sağlam olup olmadığına bakılmaksızın korunur. V-STaR (Hosseini vd., 2024) bunu öğrenilmiş bir verifier ile yamalar; Quiet-STaR (Zelikman vd., 2024) fikri token başına dahili rationale'lara genelleştirir.

## Kavram

### STaR: işe yarayan üzerine bootstrap

Bir miktar zayıf akıl yürütme yeteneği olan bir base modelden başla. Her eğitim probleminde bir rationale artı cevap örnekle. Cevap label ile eşleşiyorsa (problem, rationale, cevap) üçlüsünü tut. Tutulan küme üzerinde modeli fine-tune et. Tekrarla.

Bir twist önemli. Model bir problemi asla doğru yapamıyorsa, döngü onun üzerinde öğrenemez. STaR **rationalization** ekler: modelin başarısız olduğu problemler için doğru cevabı bir ipucu olarak enjekte et ve modelin oraya götüren bir rationale üretmesi için yeniden prompt'la. Rationalize edilmiş rationale'lar eğitim kümesine eklenir.

Orijinal makaledeki sonuç (Zelikman vd., 2022): bir GPT-J base model, rationalization ile tekrarlı STaR turları boyunca GSM8K'de %5.8'den %10.7'ye iyileşti — yaklaşık 5 yüzde puanı mutlak. CommonsenseQA'da, STaR ile eğitilmiş GPT-J 6B %72.5'e ulaştı; el-anote edilmiş rationale'lar üzerinde fine-tune edilmiş GPT-3 175B (~%73) ile karşılaştırılabilir — yaklaşık 30 kat daha büyük bir model.

### V-STaR: DPO ile bir verifier eğit

STaR yanlış rationale'ları çöpe atar. Hosseini vd. (2024) bunların da veri olduğunu gözlemledi: her (rationale, "bu doğru mu") çifti bir verifier eğitebilir. Bir ranker inşa etmek için hem doğru hem de yanlış çözümler üzerinde Direct Preference Optimization kullanırlar. Çıkarım zamanında N rationale örnekle ve verifier'ın ilk seçimini al.

Raporlanan delta: GSM8K ve MATH üzerinde önceki self-improvement baseline'larına göre +4 ile +17 yüzde puanı, kazancın çoğu ek üretici fine-tune'undan değil çıkarım-zamanı seçim için verifier kullanmaktan geldi.

### Quiet-STaR: token başına dahili rationale'lar

Zelikman vd. (2024) şunu sordu: ya model her token konumunda, sadece problem ve cevap arasında değil, kısa bir dahili rationale üretmeyi öğrenirse? Quiet-STaR bir modeli her tahmin edilen token'dan önce gizli bir "düşünce" yayması için eğitir, sonra düşünce-farkındalıklı tahmini baseline tahminle öğrenilmiş bir ağırlık üzerinden harmanlar.

Sonuç: Mistral 7B, task-specific fine-tune olmadan GSM8K'de %5.9'dan %10.9'a ve CommonsenseQA'da %36.3'ten %47.2'ye mutlak zero-shot iyileşme kazandı. Model "ne zaman düşüneceğini" öğrendi — zor token'lar daha uzun dahili rationale alır; kolay olanlar neredeyse hiç almaz.

### Üçünün de neden ortak bir safety endişesi var

Üç yöntem de gradient sinyali olarak final cevabı kullanır. Hatalı akıl yürütme yoluyla doğru cevaba ulaşan bir rationale — bir kestirme istismar etme, tahmin etme veya genelleşmeyen bir desen kullanma — pozitif pekiştirilir. Dağılım içi problemlerde kestirme işe yarar. Dağılım dışı problemlerde sessizce kırılır.

V-STaR'ın verifier'ı rationale'ları sıralamayı öğrenerek hafifletir, ama verifier aynı label seti üzerinde eğitilir. İyi formatlı yanlış akıl yürütmeyi dürüst belirsizliğe tercih etmeyi öğrenebilir. Daha safe tasarım STaR tarzı veriyi (a) process-supervised reward model'larla (sadece cevapları değil ara adımları ödüllendirir) ve (b) basit kestirmeleri kıran tutulmuş OOD değerlendirmesiyle birleştirmektir.

### Karşılaştırma

| Yöntem | Eğitim sinyali | Çıkarım maliyeti | Veri israfı | Bilinen failure mode |
|---|---|---|---|---|
| STaR | doğruysa (rationale, cevap) tut | 1x | tüm yanlış rationale'ları atar | kestirme rationale'lar |
| STaR + rationalization | yukarısı + doğru-cevap ipuçlu retry'ler | 1x | daha az | rationalize edilmiş rationale'lar inanılmaz olabilir |
| V-STaR | STaR + her iki sınıftan DPO verifier | Nx (best-of-N) | minimal | verifier kendinden emin yanlışlığı pekiştirebilir |
| Quiet-STaR | token başına rationale + harmanlama ağırlığı | 1.5-3x | minimal | hâlâ cevap-koşullu gradient |

### Bunun 2026 yığınındaki yeri

STaR eski. Ama desen 2025-2026'da her yerde yeniden ortaya çıkıyor. Doğrulanabilir matematik problemleri üzerinde RL (DeepSeek-R1, Kimi-k1.5, o1) STaR'ın cevap-koşullu gradient sinyalidir, ölçeklendirilmiş. Process reward model'lar (Lightman vd., 2023; OpenAI'ın "Let's verify step by step") process-supervised alternatiftir. AlphaEvolve (Ders 3) kod için STaR'dır, label yerine bir program evaluator ile. Darwin Godel Machine (Ders 4) agent iskelesinin kendisi için STaR'dır.

STaR'ı anlamak tüm bunları yerine oturtuyor. Minimum-uygulanabilir self-improvement döngüsüdür.

## Kullan

`code/main.py` oyuncak bir aritmetik görevde simüle edilmiş bir STaR döngüsü çalıştırır. Şunları izleyebilirsin:

- Bootstrap turları boyunca doğruluğun nasıl tırmandığını.
- Kestirmelerin nasıl sızdığını: simülatör doğru cevabı zamanın %40'ında alan ama kötü genelleyen bir "tembel" rationale sınıfı içerir. STaR'ın onları tutup tutmadığını izle.
- Bir verifier'ın (V-STaR tarzı) çıkarımda yardımcı olduğunu ama eğitim sırasında tanıtılan kestirmeleri tamamen budayamayacağını.

## Yayınla

`outputs/skill-star-loop-reviewer.md`, üzerinde eğitim yapmadan önce önerilen bir self-taught-reasoning pipeline'ını denetlemene yardım eder.

## Alıştırmalar

1. Simülatörü çalıştır. Kestirme sıklığını sıfıra, sonra 0.4'e ayarla. Her ikisi de eğitim dağılımında >%90'a ulaşmasına rağmen iki koşu arasında final doğruluk ne kadar ayrışıyor?

2. Simülatöre tutulmuş bir OOD testi ekle. Farklı bir dağılımdan problemler çek ve bootstrap edilmiş modeli hem dağılım içi hem de OOD setlerde değerlendir. Farkı niceliksel olarak ifade et.

3. Quiet-STaR makalesini (arXiv:2403.09629) Bölüm 3'ü oku. "end-of-thought" token'ını ve harmanlama-ağırlığı başlığını üçer cümleyle açıkla.

4. STaR'ın doğruysa-tut filtresini, her rationale adımını bağımsız ödüllendiren process-supervised bir alternatifle karşılaştır. Etiketleme maliyeti farkını ve makul kalite farkını belirle.

5. Deployment edilmiş bir modelde kestirme rationale'ları yakalayacak bir değerlendirme tasarla. Mükemmel olması gerekmez — bir STaR döngüsünün pekiştireceği en basit kestirmeleri kırması gerekir.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| STaR | "Self-Taught Reasoner" | Doğru cevaplara ulaşan model-üretimli rationale'lar üzerinde fine-tune; tekrarla |
| Rationalization | "İpuçlu retry" | Base modelin başarısız olduğu problemlerde doğru cevabı enjekte et ve rationale için yeniden prompt'la |
| V-STaR | "Verifier STaR" | Hem doğru hem yanlış rationale'lar üzerinde DPO ile bir verifier eğit, çıkarım-zamanı seçim için kullan |
| Quiet-STaR | "Token başına rationale'lar" | Her token konumunda gizli düşünceler üret; baseline tahminle harmanla |
| Cevap-koşullu gradient | "Sonuç-tabanlı sinyal" | Eğitim döngüsü akıl yürütme adımlarını değil, final cevapları ödüllendirir |
| Process reward model | "Adım-seviyesi verifier" | Sonuç değil, adım başına doğruluk üzerinde eğitilmiş ödül modeli — STaR ile zıttır |
| Kestirme rationale | "Doğru cevap, yanlış akıl yürütme" | Label'a genelleşmeyen bir desen üzerinden ulaşan rationale; STaR bunları tutar |

## İleri Okuma

- [Zelikman et al. (2022). STaR: Bootstrapping Reasoning With Reasoning](https://arxiv.org/abs/2203.14465) — orijinal makale.
- [Hosseini et al. (2024). V-STaR: Training Verifiers for Self-Taught Reasoners](https://arxiv.org/abs/2402.06457) — çıkarım-zamanı seçim için bir DPO verifier ekler.
- [Zelikman et al. (2024). Quiet-STaR: Language Models Can Teach Themselves to Think Before Speaking](https://arxiv.org/abs/2403.09629) — token başına dahili rationale'lar.
- [Lightman et al. (2023). Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) — process reward model'lar, alternatif gradient sinyali.
- [DeepSeek-R1 paper (arXiv:2501.12948)](https://arxiv.org/abs/2501.12948) — doğrulanabilir görevler üzerinde RL, frontier eğitimine ölçeklenmiş STaR.
