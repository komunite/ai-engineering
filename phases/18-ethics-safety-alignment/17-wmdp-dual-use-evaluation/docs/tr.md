# WMDP ve Dual-Use Capability Değerlendirmesi

> Li vd., "The WMDP Benchmark: Measuring and Reducing Malicious Use With Unlearning" (ICML 2024, arXiv:2403.03218). Biosecurity (1.520), cybersecurity (2.225) ve kimya (412) arasında 4.157 çoktan seçmeli soru. Sorular "sarı bölge"de çalışır — multi-expert review ve ITAR/EAR yasal uyumla filtrelenmiş yakın enabling bilgisi. Çift amaç: dual-use capability'nin proxy değerlendirmesi ve unlearning benchmark'ı (companion RMU yöntemi genel capability'yi korurken WMDP performansını azaltır). 2024-2025 alan anlatısı: erken OpenAI/Anthropic 2024 değerlendirmeleri internet aramasına göre "hafif uplift" raporladı; Nisan 2025'te OpenAI'nin Preparedness Framework v2'si modellerin "yeni başlayanların bilinen biyolojik tehditleri anlamlı şekilde yaratmalarına yardım etmenin eşiğinde" olduğunu söyledi. Anthropic'in bioweapon-acquisition denemesi 2.53x uplift gösterdi, ASL-3'ü dışlamak için yetersiz.

**Tür:** Öğrenim
**Diller:** Python (stdlib, WMDP-şekilli uplift değerlendirme harness'ı)
**Ön koşullar:** Faz 18 · 16 (red-team araçları), Faz 14 (agent mühendisliği)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- WMDP'nin üç alanını, soru sayılarını ve "sarı bölge" filtre kriterini tarif et.
- RMU'yu ve WMDP'nin neden hem bir değerlendirme hem de bir unlearning benchmark'ı olduğunu açıkla.
- 2024-2025 uplift anlatısını tarif et: "hafif uplift" -> "eşikte" -> "ASL-3'ü dışlamak için yetersiz."
- Yeni başlayan-göreceli uplift'i uzman-mutlak capability'den ayır.

## Sorun

Dual-use capability her lab'ın frontier safety framework'ü altındaki ölçüm problemidir (Ders 18). Soru: X modeli yeni başlayan birinin bio, chem veya cyber'de toplu zarara neden olma yeteneğini maddi olarak ilerletir mi? Doğrudan ölçüm (modelden gerçekten zarar üretmesini iste) yasadışı ve etik dışıdır. Proxy ölçümü modelin reddedemeyeceği (dürüst capability sayıları üretmek için) ama soruları kendileri zararlı yayınlar olmayan bir benchmark gerektirir.

## Kavram

### "Sarı bölge"

Zararlı bir sürecin doğrudan bir sentez tarifi olmadan yakın, enabling bilgisini gerektiren sorular. "[Bilinen patwayin] 4. adımını hangi reagent katalize eder?" "[Tehlikeli bileşik] nasıl yapılır?" değil. Her soru birden çok alan uzmanı tarafından incelenir; ITAR/EAR export-control uyumu için filtrelenir.

Toplam 4.157 soru:
- Biosecurity: 1.520
- Cybersecurity: 2.225
- Kimya: 412

Çoktan seçmeli format. Modeller herhangi bir şeyle yardım etmeleri istenmeden yanıt verir; capability zararlı davranışı elicit etmeden ölçülebilir.

### RMU — Representation Misdirection for Unlearning

Companion unlearning yöntemi. LLaMa-2-7B'ye uygulandı, MMLU ve diğer genel-capability benchmark'larını birkaç yüzde puanı içinde korurken WMDP skorlarını neredeyse rastgele seviyeye düşürdü. Yayınlanan yöntem sonraki her bio-chem-cyber unlearning makalesi için unlearning baseline'ıdır.

### 2024-2025 uplift anlatısı

Üç faz:

1. **2024 "hafif uplift."** Erken OpenAI ve Anthropic Preparedness/RSP değerlendirmeleri bio-bitişik görevleri deneyen yeni başlayanlar için internet aramasına göre küçük avantajlar raporladı. Kamu çerçevelemesi: frontier modeller yardım eder, ama Google'dan önemli ölçüde fazla değil.

2. **Nisan 2025 "eşikte."** OpenAI'nin Preparedness Framework v2'si modellerin "yeni başlayanların bilinen biyolojik tehditleri anlamlı şekilde yaratmalarına yardım etmenin eşiğinde" olduğunu raporladı. Bir capability iddiası değil — eşiğin yakın olduğu bir uyarı.

3. **Anthropic'in 2025 bioweapon-acquisition denemesi.** Yeni başlayan katılımcılarla kontrollü çalışma, acquisition-fazı görevlerinde göreceli başarıyı ölçtü. Raporlanan 2.53x uplift. ASL-3'ü (Ders 18) dışlamak için yetersiz — Anthropic'in Responsible Scaling Policy katman 3 eşiği karşılandı veya yaklaşıldı.

### Yeni başlayan-göreceli vs uzman-mutlak

Kritik bir ayrım:

- **Yeni başlayan-göreceli uplift.** Model bir uzman olmayanına ne kadar yardım eder? Çarpımsal. Göreceli avantaj yüksek çünkü yeni başlayanlar az şey bilir; küçük bilgi bile yardım eder.
- **Uzman-mutlak capability.** Model maksimum çabada ne kadar bilgi üretir? Bir uzman yeni başlayandan daha fazla çıkarabilir. Mutlak tavan yüksek.

Safety case'leri (Ders 18) ikisini de hedef alır: "model bir yeni başlayana yürütmek için yeterli uplift veremez" artı "bir uzman modelden zaten yayınlanmamış bilgi çıkaramaz".

### Ölçüm tuzağı

WMDP bir capability proxy'sidir, deployment ölçümü değil. WMDP'de yüksek puan alan bir model pratikte bir yeni başlayan tarafından sömürülebilir olabilir veya olmayabilir, şunlara bağlı:
- Elicitation direnci (capability'yi safety filtrelerini tetiklemeden çıkarmak ne kadar zor)
- Tacit bilgi (bilgi değil, wet-lab beceri gerektiren capability)
- Yürütme engelleri (procurement, ekipman)

Anthropic'in 2025 bioweapon-acquisition denemesi WMDP-tarzı capability'nin üzerine yeni başlayan-elicit katmanını ekler: gerçek görev başarısını ölçer, çoktan seçmeli capability değil.

### Bu Faz 18'de nereye uyuyor

Dersler 12-16 model çıktılarında saldırı ve savunma araçlarıdır. Ders 17 dual-use capability katmanıdır — frontier safety framework'lerinin (Ders 18) değerlendirdiği ölçüm. Ders 30 mevcut 2026 cyber/bio/chem/nuclear uplift kanıtıyla yayı kapatır.

## Kullan

`code/main.py` bir oyuncak WMDP-şekilli değerlendirme harness'ı inşa eder. Bir mock model kategori-bin'li sorularda test edilir; alan başına skorlar raporlanır. Basit bir unlearning müdahalesi (alana özgü temsili sıfırla) skorları azaltır; trade-off'u genel capability'ye karşı ölçebilirsin.

## Yayınla

Bu ders `outputs/skill-wmdp-eval.md` üretir. Bir dual-use capability iddiası verildiğinde ("modelimiz bioweapon'larla anlamlı şekilde yardım etmez"), audit eder: hangi benchmark'lar çalıştırıldı, değerlendirme için hangi reddetme yolu kullanıldı (ham tamamlama vs policy-gated) ve yeni başlayan-elicit çalışmalarının çoktan seçmeli sonucu tamamlayıp tamamlamadığını.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Oyuncak unlearning adımından önce ve sonra alan başına doğruluğu raporla. Genel-capability trade-off'unu açıkla.

2. Oyuncak WMDP'yi dördüncü bir alanla (örn. radiological) genişlet. Sarı bölgede iki örnek soru türü belirt. Bu tür soruları hazırlamanın MMLU-şekilli sorular eklemekten neden daha zor olduğunu açıkla.

3. WMDP 2024 Bölüm 5'i (RMU metodolojisi) oku. Daha basit bir unlearning yaklaşımı çiz (örn. alan içeriği için top-k nöronları bastır) ve beklenen genel-capability maliyetini tarif et.

4. Anthropic 2025'in bioweapon-acquisition denemesi 2.53x uplift raporluyor. Bu sayının yukarı yönlü (yeni başlayan örneklem boyutu, görev fidelity) ve aşağı yönlü (elicitation tavanı, model safety gating) yanlanmış olabileceği iki yolu tarif et.

5. ASL-3 için bir safety case'in WMDP unlearning'i geçmek dışında ne gerektirdiğini ifade et. En az iki tamamlayıcı elicitation çalışması adlandır.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|-----------------|------------------------|
| WMDP | "dual-use benchmark'ı" | Sarı bölgede bio/cyber/chem arasında 4.157 MCQ sorusu |
| Sarı bölge | "enabling ama sentez değil" | Sentez tarifi olmadan zararlı capability'ye bitişik yakın bilgi |
| RMU | "unlearning baseline'ı" | Representation Misdirection for Unlearning; WMDP skorlarını azaltır, genel capability'yi korur |
| Yeni başlayan-göreceli uplift | "uzman olmayanlara ne kadar yardım eder" | Bir yeni başlayan için status-quo internet aramasına göre çarpımsal avantaj |
| Uzman-mutlak capability | "uzmanlar için tavan" | Motive bir uzman tarafından modelden çıkarılabilen maksimum bilgi |
| Acquisition-fazı görevi | "sentezden önceki adımlar" | Procurement, ekipman, izinler — zarar pathway'inin en erken kısımları |
| ITAR/EAR | "export-control uyumu" | Belirli enabling bilgisini yayınlamayı kısıtlayan yasal çerçeveler |

## İleri Okuma

- [Li et al. — The WMDP Benchmark (arXiv:2403.03218, ICML 2024)](https://arxiv.org/abs/2403.03218) — benchmark ve RMU makalesi
- [OpenAI — Preparedness Framework v2 (15 Nisan 2025)](https://openai.com/index/updating-our-preparedness-framework/) — "eşikte" dili
- [Anthropic — Responsible Scaling Policy v3.0 (Şubat 2026)](https://www.anthropic.com/responsible-scaling-policy) — ASL-3 bio eşiği ve acquisition deneme sonuçları
- [DeepMind — Frontier Safety Framework v3.0 (Eylül 2025)](https://deepmind.google/blog/strengthening-our-frontier-safety-framework/) — bio-uplift CCL
