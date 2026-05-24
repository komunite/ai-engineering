# AI Scientist v2 — Workshop-Seviyesi Otonom Araştırma

> Sakana'nın AI Scientist v2'si (Yamada vd., arXiv:2504.08066) tam araştırma döngüsünü çalıştırır: hipotez, kod, deneyler, şekiller, yazım, gönderim. Bir ICLR 2025 workshop'unda üretilmiş bir makalesi peer review'dan geçen ilk sistemdir. Bağımsız değerlendirme (Beel vd.) deneylerin %42'sinin coding hatalarından başarısız olduğunu ve literatür incelemesinin yerleşik kavramları sıkça novel olarak yanlış etiketlediğini buldu. Sakana'nın kendi dokümanları codebase'in LLM yazımı kod çalıştırdığını ve Docker izolasyonu önerdiğini uyarıyor. Bu resmin her iki yarısı da konunun ta kendisidir.

**Tür:** Öğrenim
**Diller:** Python (stdlib, araştırma döngüsü state machine oyuncağı)
**Ön koşullar:** Faz 15 · 03 (AlphaEvolve), Faz 15 · 04 (DGM)
**Süre:** ~60 dakika

## Sorun

Araştırma açık-uçlu bir görevdir. AlphaEvolve'un algoritmik araması veya DGM'nin benchmark-sınırlı self-modification'ından farklı olarak, bir araştırma sonucunun makine-doğrulanabilir bir doğruluk kriteri yoktur. Bir makale unit test'ler değil hakemler tarafından yargılanır. Bu döngüyü kapatmayı daha zor — ve kapatılırsa daha değerli — kılar, çünkü araştırma bileşik ilerlemenin yaşadığı yerdir.

AI Scientist v1 (Sakana, 2024) insan-yazımı template'lerden başlayarak döngüyü kapattı. LLM, sabit bir iskele içinde deneyleri doldurdu. AI Scientist v2 (Yamada vd., 2025) bir vision-language model kritik döngüsüyle agentic tree search kullanarak template gereksinimini kaldırır. Sistem fikirler üretir, deneyler uygular, şekiller üretir, bir makale yazar ve hakem geri bildirimine göre iterasyon yapar.

Peer review verdict'i: bir v2-üretimi makale bir ICLR 2025 workshop'unda kabul edildi (açıklamayla). Bağımsız değerlendirme verdict'i: sistem güvenilir olmaktan uzaktır. Her ikisi de doğru.

## Kavram

### Mimari

1. **Fikir üretimi.** LLM, bir konu ve önceki literatüre koşullu olarak araştırma fikirleri önerir. v1 template kullandı; v2, hipotezler uzayında agentic arama kullanır.
2. **Yenilik kontrolü.** Bir literatür retrieval adımı fikrin yayımlanıp yayımlanmadığını kontrol eder. Bu, Beel vd.'nin değerlendirmesinin yanlış etiketleme bulduğu adımdır — yerleşik yöntemler sıkça novel olarak sınıflandırıldı.
3. **Deney planı.** Agent bir deneysel protokol taslağı çıkarır ve kod yazar.
4. **Yürütme.** Kod bir sandbox'ta çalışır. Failure'lar bir retry döngüsüne geri beslenir. Beel vd.'nin ölçümlerinde deneylerin %42'si bu aşamada coding hatalarından başarısız oldu.
5. **Şekil üretimi.** Bir vision-language model üretilen şekilleri okur ve onları netlik için yeniden yazar. Bu v2'nin anahtar teknik eklemesiydi.
6. **Yazım.** LLM bir makale taslağı çıkarır, bir dahili hakemle iterasyon yapar.
7. **Opsiyonel: gönderim.** Makale bir mekana gönderilir.

### Workshop-kabul sonucunun ne anlama geldiği

Bir v2-üretimi makale bir ICLR 2025 workshop'unda peer review'dan geçti. Yazarlar makalenin kaynağını program komitesine açıkladı. Kabul bir veri noktasıdır; sistemin "araştırma yaptığını" iddia etmek için bir lisans değildir.

Önemli bağlam: workshop makaleleri ana-konferans makalelerinden daha düşük bir çıtadır. Peer review gürültülüdür; herhangi bir günde küçük bir gönderim oranı kabul edilir. Bir başarı bir kavram kanıtıdır, bir güvenilirlik iddiası değil. Nature 2026 makalesi uçtan uca döngüyü belgeler ve insan araştırmacılar tarafından ortak yazılmıştır; "sistem bir Nature makalesi yazdı" değildir.

### Bağımsız değerlendirmenin bulduğu

Beel vd. (arXiv:2502.14297) harici bir değerlendirme yürüttü. Manşet bulgular:

- **Deney başarısızlıkları.** Deneylerin %42'si coding hatalarından başarısız oldu (kötü import'lar, shape uyumsuzlukları, tanımsız değişkenler). Retry döngüsü bazılarını yakaladı, hepsini değil.
- **Yenilik yanlış etiketleme.** Literatür-retrieval adımı sıkça yerleşik kavramları novel olarak işaretledi. Bu hallucination'ın araştırma karşılığıdır.
- **Sunum-kalitesi farkı.** Vision-language şekil kritiği yayımlanma-kalitesinde görseller üretti, altta yatan deneysel zayıflıkları maskeledi.

Son bulgu bu faz için önemli olan. İnandırıcı çıktılar üreten ama inandırıcı araştırma yapmayan bir sistem, açıkça başarısız olandan daha güvenli değil daha tehlikelidir. Değerlendirme şekilde durmamalı, altta yatan iddialara ulaşmalıdır.

### Sandbox-escape endişesi

Sakana'nın kendi repository README'si uyarıyor:

> Bu yazılımın doğası gereği LLM-üretimi kod çalıştırdığı için safety garanti edemiyoruz. Tehlikeli paketlerin, kontrolsüz web erişiminin ve istenmeyen process spawn'larının riskleri vardır. Kendi sorumluluğunuzda kullanın ve Docker izolasyonunu düşünün.

Bu, doğrulanmamış bir domain'de otonominin operasyonel şeklidir. LLM kod yazar; kod çalışır; kod process'in yapmasına izin verilen her şeyi yapabilir. Filesystem, network ve process aksiyonlarını sert sınırlayan bir sandbox olmadan, herhangi bir kendine-yönelik araştırma agent'ı veri exfiltrate edebilir, compute yakabilir veya kendini yeniden yazabilir.

AlphaEvolve'un sandbox hikayesi evaluator'ı sıkı olduğu için daha kolaydır. AI Scientist v2'nin döngüsü açık-uçlu hedeflerle açık-uçlu kod çalıştırır. Bu yüzden daha güçlü izolasyona (minimum Docker; seccomp / gVisor tercih edilir) ve sistemden çıkmadan önce her gönderimin manuel incelemesine ihtiyacı vardır.

### v2'nin frontier yığınındaki yeri

| Sistem | Hedef | Çıktı türü | Evaluator | Bilinen failure |
|---|---|---|---|---|
| AlphaEvolve | algoritmalar | kod | unit + benchmark | evaluator titizliğiyle sınırlı |
| DGM | agent iskelesi | kod | SWE-bench | reward hacking |
| AI Scientist v2 | araştırma makaleleri | metin + kod + şekiller | peer review (zayıf) | deney başarısızlıkları, yanlış etiketleme, cila zayıflığı maskeler |

v2 üçü arasında en zayıf otomatik evaluator'a, en geniş çıktı yüzeyine ve halka açık artifact'lara en kısa yola sahip. Operasyonel kontroller (sandbox, inceleme, açıklama) safety işinin çoğunu yapıyor.

## Kullan

`code/main.py`, v2 döngüsünü bir state machine olarak simüle eder: fikir → yenilik kontrolü → deney → şekil → yazım → inceleme → kabul-veya-iterasyon. Her state'in Beel vd. bulgularından çekilmiş yapılandırılabilir bir failure olasılığı vardır. Simülatörü N döngü için çalıştır ve say:

- Kaç fikir gönderime ulaşıyor.
- Kaç gönderim cilalı makalenin gizlediği kritik bir deneysel kusura sahip olurdu.
- Retry bütçelerinin kalite vs verim arasında nasıl trade-off yaptığını.

## Yayınla

`outputs/skill-ai-scientist-sandbox-review.md`, bir araştırma-döngüsü agent'ı tarafından üretilen herhangi bir şey için sandbox'tan çıkmadan önce iki-kapılı bir inceleme checklist'idir.

## Alıştırmalar

1. `code/main.py`'yi varsayılan parametrelerle çalıştır. Döngü koşularının ne kadarı "temiz" bir makale üretiyor? Ne kadarı şekil kritiğinin cilaladığı bir deney-başarısızlığı kusuruna sahip bir makale üretiyor?

2. Varsayılanlar zaten Beel vd.'nin %42 / %25'ini kullanıyor. `--experiment-failure 0.20 --novelty-mislabel 0.10` ile, sonra `--experiment-failure 0.60 --novelty-mislabel 0.40` ile yeniden çalıştır. İki koşu arasında cilalı-ama-kusurlu pay nasıl kayıyor?

3. Sakana'nın AI Scientist v2 repo README'sini sandbox gereksinimleri üzerine oku. Çoklu-gün otonom koşu için uygulayacağın iki ek kısıtlama (Docker'ın ötesinde) söyle.

4. Beel vd. 4. bölümü sunum-kalitesi farkı üzerine oku. Cilalı görünen ama deneysel olarak kusurlu makaleleri yakalayacak bir ek evaluator tasarla.

5. "Bir PhD her makaleyi okur"dan daha iyi ölçeklenen, araştırma-agent'ı çıktıları için bir insan-inceleme protokolü öner. Darboğazı belirle ve etrafında tasarla.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| AI Scientist v1 | "Sakana'nın template'li araştırma agent'ı" | Deneyleri sabit bir iskeleye doldurdu |
| AI Scientist v2 | "Template-siz araştırma agent'ı" | VLM şekil kritiğiyle agentic tree search |
| Agentic tree search | "Dallanan araştırma agent'ı" | Birden fazla deney planını paralel genişletir; dahili kritikçi ile budar |
| Vision-language kritik | "Şekiller üzerinde VLM cilası" | Çoklu-modal model şekilleri okur ve netlik için yeniden yazar |
| Literatür retrieval | "Yenilik kontrolü" | Fikir yeniliğini onaylamak için önceki çalışmayı arar — yanlış etiketleme belgelenmiş |
| Cila maskeleme | "Güzel makale, kırık araştırma" | Sunum kalitesi deneysel kaliteyi aşar; zayıflıkları gizler |
| Sandbox escape | "LLM kodu dışarı kırılır" | Agent-yürütümlü kod döngü tasarımcısının amaçlamadığı şeyleri yapar |

## İleri Okuma

- [Yamada et al. (2025). The AI Scientist-v2](https://arxiv.org/abs/2504.08066) — makale.
- [Sakana blog on the Nature 2026 publication](https://sakana.ai/ai-scientist-nature/) — peer-review bağlamıyla satıcı özeti.
- [Beel et al. (2025). Independent evaluation of The AI Scientist](https://arxiv.org/abs/2502.14297) — harici değerlendirme rakamları.
- [Sakana AI Scientist v1 paper](https://arxiv.org/abs/2408.06292) — template'li öncül.
- [Anthropic — Measuring AI agent autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) — açık-uçlu araştırma agent'larının daha geniş çerçevesi.
