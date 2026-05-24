# Qwen-VL Ailesi ve Dynamic-FPS Video

> Qwen-VL ailesi — Qwen-VL (2023), Qwen2-VL (2024), Qwen2.5-VL (2025), Qwen3-VL (2025) — 2026'da en etkili açık vision-language modeli soyu. Her nesil, geri kalan açık ekosistemin on iki ay içinde kopyaladığı tek bir kesin mimari bahse girdi: M-RoPE üzerinden native dinamik çözünürlük, mutlak zaman hizalaması ile dynamic-FPS sampling, ViT'te window attention ve yapılandırılmış agent çıkış formatları. Qwen3-VL'e gelindiğinde tarif kararlılaştı: native-aspect-ratio input'lu 2D-RoPE-ViT encoder, büyük bir Qwen3 dil tabanına MLP projector ve OCR, grounding ve agent davranışını birinci-sınıf hedefler olarak vurgulayan eğitim aşamaları. Bu ders aileyi kronolojik okur böylece her ayarın neden orada olduğunu anlarsın.

**Tür:** Öğrenim
**Diller:** Python (stdlib, M-RoPE encoder + dynamic-FPS sampler)
**Ön koşullar:** Faz 12 · 06 (patch-n'-pack)
**Süre:** ~120 dakika

## Öğrenme Hedefleri

- M-RoPE'nin üç eksen rotasyonlarını (temporal, height, width) hesapla ve üçünün de neden gerektiğini açıkla.
- Bir video için bir dynamic-FPS sampling stratejisi seç ve saniye başına token vs olay-tespit doğruluğu hakkında akıl yürüt.
- Dört Qwen-VL nesil yükseltmesini sırayla söyle ve her birinin neyi açtığını.
- Qwen2.5-VL tarzı JSON agent çıkış formatını ekle ve bir VLM yanıtından yapılandırılmış tool call'ları ayrıştır.

## Sorun

Qwen-VL Ağustos 2023'te LLaVA-1.5 ve BLIP-2'ye doğrudan cevap olarak gönderildi. Qwen ekibinin hedeflediği fark üç katlıydı: çözünürlük, video ve yapılandırılmış çıktı.

Çözünürlük: LLaVA-1.5 336x336'da koştu. Fotoğraflar için iyi, Çince bir fatura ya da yoğun bir spreadsheet ekran görüntüsü için işe yaramaz. Qwen-VL'in ilk yeniliği 448x448 ve grounded bounding-box çıktısıydı, modele şeyleri işaret etme yeteneği verdi.

Video: Video-LLaMA frame başına encoder'ları yığdı ve onları LLM'e besledi. Kısa klipler için çalıştı, sinyalin temporal eksen olduğu çok dakikalı videolar için değil. Qwen ekibi zamanı anlayan tek encoder istedi.

Yapılandırılmış çıktı: LLaVA serbest-form metin yayar. Bir agent JSON ister. Qwen-VL bounding-box koordinatları metin olarak dahil açık JSON çıkış formatlarında eğitildi.

Her Qwen-VL nesli bu üç eksenden birini genişletir.

## Kavram

### Qwen-VL (Ağustos 2023)

İlk nesil: encoder olarak OpenCLIP ViT-bigG/14 (2.5B param), LLama-uyumlu Q-Former (256 query ile 1 adım), Qwen-7B base. Katkılar:

- 448x448 çözünürlük (o zamanlar açık bir VLM için SOTA).
- Grounding: açık koordinat-token çıktısı ile image-text çiftleri üzerinde eğitildi. "The cat is at <box>(112, 204), (280, 344)</box>".
- Baştan İngilizce + Çince çok dilli eğitim.

O zaman benchmark'ları: İngilizce'de GPT-4V ile rekabetçi, Çince'de baskın. Grounding gözetimi gerçek manşetti.

### Qwen2-VL (Eylül 2024) — M-RoPE ve native çözünürlük

Qwen2-VL sabit-çözünürlük + Q-Former yığınını natively dinamik-çözünürlük bir ViT encoder ile değiştirdi. Anahtar değişiklikler:

- Native dinamik çözünürlük. ViT 28'e bölünebilen herhangi bir HxW kabul eder (2x spatial merge ile patch 14). 1120x672'de bir görsel (40x24 merged patch) 960 görsel token üretir. Resize yok, tiling yok, thumbnail yok.
- M-RoPE (Multimodal RoPE). Her token 1D yerine 3D bir pozisyon (t, h, w) taşır. Görseller için t=0, video için t = frame_index. RoPE query/key vektörlerini eksen başına bir frekansla döndürür. Positional embedding tablosu yok.
- MLP projector. Q-Former'ı düşür; merged patch token'ları üzerinde 2 katmanlı MLP kullan.
- Dinamik FPS ile video. Video varsayılan olarak 1-2 FPS'te örneklenir, ama model keyfi frame sayılarını kabul eder.

Sonuç: Qwen2-VL-7B birçok multimodal benchmark'ta GPT-4o'yu eşledi ve DocVQA'da onu yendi (94.5 vs 88.4). Mimari değişiklik kesin hamleydi.

### Qwen2.5-VL (Şubat 2025) — dinamik FPS + mutlak zaman

Qwen2.5-VL'in büyük kaydırması videodu. Dinamik FPS yalnızca "gerektiğinde daha çok frame örnekle" değil. Makale formalize etti:

- Mutlak zaman token'ları. Pozisyonel indeksler (frame 0, 1, 2...) yerine gerçek timestamp'leri kullan. "0:04'te kedi zıplıyor." Model frame token'ları arasına interleave edilmiş `<time>0.04</time>` token'ları görür.
- Dinamik FPS. Yavaş kayıt için 1 FPS'te, aksiyon için 4+ FPS'te örnekle. User ya da trainer seçer; M-RoPE adapt eder.
- ViT'te window attention. Throughput için spatial attention windowed (block'lar içinde yerel); her birkaç katmanda global attention.
- Açık JSON çıkış formatı. Tool-call verisi üzerinde eğitildi: "{\"tool\": \"click\", \"coords\": [380, 220]}". Kutudan agent-ready.
- MRoPE-v2 scaling. Pozisyonlar max input boyutu ile ölçeklenir, böylece 10 dakikalık video frekans aralığından çıkmaz.

Benchmark'lar: Qwen2.5-VL-72B çoğu video benchmark'ında GPT-4o'yu yener, belgelerde Gemini 2.0'ı eşler ve GUI grounding için açık-model SOTA'sını belirler (ScreenSpot: %84 doğruluk vs GPT-4o için %38).

### Qwen3-VL (Kasım 2025)

Qwen3-VL yeniden icat etmek yerine konsolide eden bir artımlı yükseltme: daha büyük LLM backbone (Qwen3-72B), genişletilmiş eğitim verisi, geliştirilmiş OCR, Qwen3 "thinking mode" üzerinden daha güçlü akıl yürütme. ViT ve M-RoPE kalır. Makale mimari yerine veri ve eğitim iyileştirmelerine odaklanır.

Soy çıkarımı: 2025'e kadar Qwen-VL mimarisi kararlılaştı. Ek nesiller compute ve veri ölçekler, primitive'leri değil.

### M-RoPE matematiksel olarak

Klasik RoPE, `d` boyutundaki bir `q` query'sini eşli koordinatlar kullanarak `m` pozisyonu ile döndürür:

```
q_rot[2i]   = q[2i]   * cos(m * theta_i) - q[2i+1] * sin(m * theta_i)
q_rot[2i+1] = q[2i]   * sin(m * theta_i) + q[2i+1] * cos(m * theta_i)
theta_i     = 10000^(-2i/d)
```

M-RoPE hidden dim'i üç banda böler. `d = 96` diyelim. Temporal'a 32 dim, height'a 32, width'a 32 ata. Her bant kendi eksen pozisyonu ile döner. (t=5, h=10, w=20)'deki bir patch üç bandına `R_t(5)`, `R_h(10)`, `R_w(20)` rotasyonları uygulanmış olur.

Metin token'ları `t = text_index, h = 0, w = 0` (ya da normalize edilmiş seçim) kullanır, uyumluluğu korur. Video frame'leri `t = frame_time, h = row, w = col` kullanır. Tek görseller `t = 0` kullanır.

Fayda: tek pozisyon kodlaması metni, görseli ve videoyu dallanan kod ya da farklı pozisyon tabloları olmadan halleder.

### Dynamic-FPS sampling mantığı

Süresi `T` saniye olan bir video ve hedef-token bütçesi `B` verildiğinde:

1. Karşılayabileceğin maksimum FPS'i hesapla: `fps_max = B / (T * tokens_per_frame)`.
2. `{1, 2, 4, 8}`'den `fps <= fps_max`'i sağlayan bir hedef FPS seç.
3. Hareket yüksekse (optical-flow sezgisi ya da açık user isteği), daha yüksek FPS seç. Hareket düşükse daha düşük seç.
4. Seçilen FPS'te uniform örnekle; frame'ler arasına `<time>t</time>` token'ları ekle.

Qwen2.5-VL bu mantığı implicit eğitiyor; çıkarımda user `fps` parametresi üzerinden kontrol eder. Frame başına 81 token ile 4 FPS'te 60 saniyelik aksiyon dizisi = 19440 token, 32k context'te yönetilebilir.

### Yapılandırılmış agent çıktısı

Qwen2.5-VL'in agent eğitimi yapılandırılmış tool call'ları açıkça hedefler:

```
{
  "tool": "mouse_click",
  "coords": [1024, 512],
  "button": "left",
  "modifier": null
}
```

Ayrıştırma deterministik: modelin çıktısı üzerinde JSON.parse. Regex ve belirsizlik halleme gerektiren serbest-form "click at (1024, 512)" ile karşılaştır. Kayma, Qwen2.5-VL'in ScreenSpot skorlarının Qwen2-VL'in %55'inden %84'e atlamasının nedeni.

## Kullan

`code/main.py` şunları uygular:

- Metin, görsel patch'leri ve video frame'lerini karıştıran paketlenmiş bir dizi için M-RoPE pozisyon hesabı.
- Dynamic-FPS sampler: (duration, budget, motion_level) verildiğinde, FPS seç ve frame timestamp'leri yay.
- Koordinat alanlı tool-call yanıtlarını ele alan oyuncak bir Qwen2.5-VL JSON-çıkış parser'ı.

Çalıştır, sonra 5 dakikalık bir videoda sabit-FPS'i dinamik-FPS ile değiştirdiğinde farkı hisset.

## Yayınla

Bu ders `outputs/skill-qwen-vl-pipeline-designer.md` üretir. Bir video görevi (izleme, agent, action recognition, erişilebilirlik) verildiğinde Qwen2.5-VL konfigürasyonunu (frame bütçesi, FPS stratejisi, window-attention flag'i, agent-çıkış modu) ve bir latency tahmini yayar. Bir video ürünü için Qwen-VL-family modelini deploy ettiğinde bunu kullan.

## Alıştırmalar

1. Hidden 48 (bant başına 16, base theta 10000) ile (t=3, h=5, w=7)'deki bir patch için M-RoPE rotasyonlarını hesapla. Her banttaki ilk üç çift için rotasyon açılarını göster.

2. 1 FPS'te 10 dakikalık bir güvenlik kamera kaydı kaç frame üretir? 3x pool ile 384 çözünürlükte toplam kaç token? Qwen2.5-VL'in varsayılan 32k context'i bunu halleder mi?

3. 30 saniyelik tenis maçı vs 30 saniyelik tarif demosu vs 30 saniyelik UI-agent kaydı için FPS seç. Her birini dinamik-FPS mantığı ile haklı çıkar.

4. Qwen2.5-VL Q-Former'ı tamamen düşürdü. Basit bir MLP 2025'te neden çalışıyor ama 2023'te değildi? (İpucu: veri ölçeği ve encoder kalitesi.)

5. Üç Qwen2.5-VL JSON tool-call çıktısını Python dict'lerine ayrıştır. Bozuk JSON için ne başarısız olur ve Qwen cookbook hangi recovery stratejisini öneriyor?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| M-RoPE | "Multimodal RoPE" | Hidden dim'de temporal, height ve width bantları olan 3D rotary position embedding |
| Dinamik FPS | "Akıllı sampling" | Hareket, süre ve token bütçesine dayalı video başına seçilen frame sampling oranı |
| Mutlak zaman token'ı | "Timestamp token" | Modelin frame indeksi yerine gerçek saniyeleri görmesi için dizide interleave edilmiş `<time>t</time>` |
| Window attention | "Yerel attention" | Hız için küçük pencerelere kısıtlı spatial self-attention; periyodik olarak global attention eklendi |
| Yapılandırılmış agent çıktısı | "JSON mode" | VLM'e coord'lar ve tool adlarıyla ayrıştırılabilir JSON yayma öğreten eğitim verisi gözetimi |
| min_pixels / max_pixels | "Çözünürlük sınırları" | Toplam piksel sayısını ve dolayısıyla token sayısını sınırlayan istek başına Qwen2.5-VL kontrolleri |
| Grounding | "Onu işaret et" | Bounding-box koordinatlarını metin token'ları olarak çıkarmak; Qwen-VL v1'den beri kullanılıyor |

## İleri Okuma

- [Bai et al. — Qwen-VL (arXiv:2308.12966)](https://arxiv.org/abs/2308.12966)
- [Wang et al. — Qwen2-VL (arXiv:2409.12191)](https://arxiv.org/abs/2409.12191)
- [Qwen Team — Qwen2.5-VL Technical Report (arXiv:2502.13923)](https://arxiv.org/abs/2502.13923)
- [Qwen Team — Qwen3-VL (arXiv:2511.21631)](https://arxiv.org/abs/2511.21631)
- [Zhu et al. — InternVL3 (arXiv:2504.10479)](https://arxiv.org/abs/2504.10479)
