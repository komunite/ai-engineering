# Scalable Oversight ve Weak-to-Strong Generalization

> Burns vd. (OpenAI Superalignment, "Weak-to-Strong Generalization", 2023) superalignment problemi için bir proxy önerdi: daha zayıf bir model tarafından üretilen etiketler kullanarak güçlü bir modeli fine-tune et. Güçlü model kusurlu zayıf supervision'dan doğru genelleşirse, mevcut insan ölçeğindeki alignment yöntemleri superhuman sistemlere uzayabilir. Scalable oversight ve W2SG tamamlayıcıdır. Scalable oversight (debate, recursive reward modeling, görev ayrıştırma) oversight altındaki modele ayak uydurabilmesi için gözetmenin etkin yeteneğini artırır. W2SG güçlü modelin gözetmenin sağladığı her türlü kusurlu supervision'dan doğru genelleştiğini sağlar. Debate Helps W2SG (arXiv:2501.13124, Ocak 2025) ikisini birleştirir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, W2SG boşluk simülatörü)
**Ön koşullar:** Faz 18 · 01 (instruction-following), Faz 18 · 10 (AI Control), Faz 09 (RL temelleri)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Scalable oversight ve weak-to-strong generalization'ı tanımla ve nasıl tamamlayıcı olduklarını açıkla.
- Burns vd. 2023 deneysel kurulumunu tarif et: GPT-2'den gelen etiketleri kullanarak GPT-4'ü fine-tune et.
- Performance Gap Recovered (PGR) metriğini ve neyi ölçtüğünü açıkla.
- Üç ana scalable-oversight mekanizmasını (debate, recursive reward modeling, görev ayrıştırma) ve her birinin bir güçlü yanını ifade et.

## Sorun

Faz 18'deki şimdiye kadarki her alignment tekniği gözetmenin modelin davranışını değerlendirebileceğini varsayar. Model superhuman olduğunda, gözetmen zayıf halkadır. Superalignment sorusu: daha zayıf bir supervisor güvenilir şekilde daha güçlü, aligned bir model üretebilir mi?

Burns vd. bunu operasyonel hale getirilmiş bir ampirik kurulumla azaltır: zayıfla güçlüyü gözetle, güçlü modelin yeteneğinin ne kadarının zayıf supervision'da hayatta kaldığını ölç. Bu superalignment'a bir çözüm değil — ilerlemeyi ölçmemize izin veren bir proxy.

## Kavram

### W2SG: Burns vd. kurulumu

- Zayıf model: GPT-2 sınıfı.
- Güçlü model: GPT-4 sınıfı.
- Hedef: görevde güçlü GPT-4 tavanı.

Prosedür:
1. Zayıf modelin görevde zero-shot tahminlerini al.
2. Güçlü modeli zayıf-etiketli veride fine-tune et.
3. Güçlü fine-tuned modelin doğruluğunu ölç.

Baseline'lar: zayıf modelin kendi doğruluğu, gold etiketler üzerinde güçlü modelin supervised tavanı.

Boşluk metriği: Performance Gap Recovered (PGR) = (fine-tuned - zayıf) / (tavan - zayıf). 1.0 PGR zayıf supervision'ın boşluğu tamamen kapattığı anlamına gelir; 0 PGR zayıf supervision'ın yardım etmediği anlamına gelir.

### Burns vd. ampirik bulguları

NLP, satranç-bulmaca ve reward-modeling görevleri arasında PGR sürekli pozitifti: güçlü model zayıf supervisor'ın hatalarının ötesine genelleşti. Göreve-özgü PGR ~%20'den ~%80'e değişti. Güçlü model kusurlu etiketlerden amaçlanan görevi "anlar", pre-trained önceleriyle doldurur.

Burns vd.'nin not ettiği limitler:
- Buradaki zayıftan-güçlüye boşluk yetenek, alignment değildir. Zayıf model aligned; gerçekten superhuman bir model bir insan tarafından aligned edilebilir ama çok daha büyük bir yetenek boşluğuyla.
- Güçlü modelin genelleşmesi ground-truth niyeti kurtarmaktan daha çok görev öncelikleriyle ilgili olabilir.
- Güçlü modelin latent bilgisini elicit etmek gerçek problemdir; PGR spesifik bir operasyonelleştirmeyi ölçer.

### Scalable oversight: üç mekanizma

- **Debate (Irving vd. 2018).** U'nun iki instance'ı karşıt tarafları savunur; zayıf yargıç karar verir. Varsayım: ikna edici bir doğru yanıt bulmak ikna edici bir yanlış yanıt bulmaktan daha kolaydır. Yakın 2024-2025 çalışmaları (Khan vd., Michael vd.) debate'in bazen yardım ettiğini ve bazen yardım etmediğini, yardım edip etmediğinin görev yapısına bağlı olduğunu gösteriyor.
- **Recursive Reward Modeling (Leike vd. 2018).** U insanın U+1 için reward model'i eğitmesine yardım eder. Gözetmenin etkin yeteneği modelle birlikte büyür.
- **Görev Ayrıştırma (Christiano, Shlegeris, Amodei 2018).** Zor bir görevi insanın kontrol edebileceği alt görevlere recursive olarak ayrıştır. Ayrıştırılabilirliği varsayar.

Her mekanizma görev yapısı veya ara bileşenlerin alignment'ı hakkında bir şey varsayar.

### Scalable oversight ve W2SG neden tamamlayıcı

Scalable oversight gözetmenin etkin sinyal kalitesini artırır.
W2SG gözetmenin sağlayabildiği her türlü kusurlu sinyalden boşluğu kapatır.

Lang vd. — Debate Helps Weak-to-Strong Generalization (arXiv:2501.13124) ikisini birleştirir: bir debate protokolü daha iyi zayıf etiketler sağlar ve güçlü model o etiketlerde eğitilir. NLP görevlerinde rapor edilen PGR kazanımları.

### Organizasyonel drama

OpenAI'nin Superalignment ekibi Mayıs 2024'te Jan Leike'nin Anthropic'e ayrılmasından sonra dağıldı. Gündem (scalable oversight, W2SG, automated alignment research) Anthropic'te ve akademik lab'larda devam etti — MATS (Ders 28), Redwood (Ders 10), Apollo (Ders 8), METR (Ders 28). Organizasyonel yapı değişti; araştırma soruları değişmedi.

### Bu Faz 18'de nereye uyuyor

Dersler 6-10 tehdidi ve U'nun güvenilmez olduğu varsayımı altında defansif paradigmayı tarif ediyor. Ders 11 ofansif paradigmadır: gözetmeni U'nun alignment'ını doğrulayacak kadar güçlü yap. Dersler 12-16 sonra adversarial değerlendirmenin pratik araçlarına döner.

## Kullan

`code/main.py` sentetik bir görev üzerinde bir W2SG fine-tune simüle eder. Zayıf labeler yapılandırılmış hatalarla %70 doğruluğa sahiptir; güçlü modelin gold etiketlerde %95 tavanı vardır. Güçlü modeli zayıf etiketlerde fine-tune edersin, PGR'yi ölçersin ve güçlü-on-gold ve zayıf-tek-başına ile karşılaştırırsın.

## Yayınla

Bu ders `outputs/skill-w2sg-pgr.md` üretir. Bir oversight kurulum açıklaması verildiğinde, zayıf supervisor'ı, güçlü modeli, supervision kalitesini tanımlar ve PGR'yi hesaplar (veya talep eder). İddianın "zayıf güçlüyü gözetleyebilir" mi yoksa "zayıf + oversight mekanizması güçlüyü gözetleyebilir" mi olduğunu işaretler.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. weak_accuracy = 0.60, 0.70, 0.80 için PGR raporla. PGR eğrisinin şeklini açıkla.

2. Zayıf labeler'ı yapılandırılmış hata sahip olacak şekilde modifiye et (örn. spesifik bir input sınıfında her zaman yanlış). PGR artar mı, azalır mı, aynı kalır mı? Açıkla.

3. Burns vd. 2023 Bölüm 4.3'ü (NLP görevleri) oku. "Confidence auxiliary loss" sezgisini yeniden üret: güçlü model zayıf etiketlerden daha emin olduğunda kim kazanır?

4. Bir yazılım-mühendisliği görevi için debate ve görev ayrıştırmayı birleştiren bir scalable-oversight protokolü tasarla. Her bileşenin bir failure mode'unu adlandır ve kombinasyonun her birini nasıl ele aldığını veya ele almadığını açıkla.

5. "Weak-to-strong generalization superalignment için uygulanabilir bir yoldur" iddiasını neyin yanlışlayacağını ifade et. Görmen gereken ampirik imza hakkında spesifik ol.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| Scalable oversight | "gözetmeni daha güçlü yapmak" | Bir gözetmenin daha-yetenekli bir modeli değerlendirme yeteneğini artıran mekanizmalar |
| W2SG | "zayıf güçlüyü gözetler" | Güçlü bir modeli zayıf etiketlerde fine-tune etmek ve kurtarılan yeteneği ölçmek |
| PGR | "performance gap recovered" | (fine-tuned - zayıf) / (tavan - zayıf); 1.0 = tamamen kapalı, 0 = yardım yok |
| Debate | "iki U instance'ı tartışır" | Zayıf bir yargıcın iki U savunucusu arasından seçtiği scalable oversight mekanizması |
| RRM | "recursive reward modeling" | U U+1 için reward model'i eğitmeye yardım eder; gözetmen yeteneği U'yu izler |
| Görev ayrıştırma | "insanın kontrol ettiği alt görevler" | Zor bir görevi insanın doğrulayabileceği alt görevlere recursive olarak böl |
| Superalignment | "superhuman AI'yı align etmek" | İnsanın doğrudan değerlendiremediği modelleri align etmekle ilgili araştırma gündemi |

## İleri Okuma

- [Burns et al. — Weak-to-Strong Generalization (OpenAI 2023)](https://openai.com/index/weak-to-strong-generalization/) — W2SG makalesi
- [Irving, Christiano, Amodei — AI safety via debate (arXiv:1805.00899)](https://arxiv.org/abs/1805.00899) — debate mekanizması
- [Leike et al. — Scalable agent alignment via reward modeling (arXiv:1811.07871)](https://arxiv.org/abs/1811.07871) — recursive reward modeling
- [Khan et al. — Debating with More Persuasive LLMs Leads to More Truthful Answers (arXiv:2402.06782)](https://arxiv.org/abs/2402.06782) — daha güçlü tartışmacılarla debate'in 2024 ampirik çalışması
- [Lang et al. — Debate Helps Weak-to-Strong Generalization (arXiv:2501.13124)](https://arxiv.org/abs/2501.13124) — debate + W2SG 2025 kombinasyonu
