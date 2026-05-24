# Milyon-Token Context'te Uzun-Video Anlama

> 24 FPS'te 1 saatlik bir 4K video, patch'lendiğinde ve embed edildiğinde, 60 milyon token mertebesinde üretir. 2 saatlik bir podcast bölümü transcribe edildiğinde 30,000 token. Agresif pooling ile sıkıştırılmış bile tam bir Blu-ray uzun metrajlı film yüzlerce binlerce token. Google'ın Gemini 1.5'i (Mart 2024) bu çağı 10 milyon token context ile açtı, saat uzunluğundaki videolar üzerinde güvenilir needle-in-a-haystack recall yapıyor. LWM (Liu et al., Şubat 2024) ring attention'ın ölçek yolunu gösterdi. LongVILA ve Video-XL ingestion'ı daha da ölçekledi. VideoAgent ham context'i agentic retrieval ile değiştirdi. Her yaklaşım compute, recall ve mühendislik karmaşıklığında farklı bir trade-off. Bu ders onları yan yana okur.

**Tür:** Yapım
**Diller:** Python (stdlib, needle-in-haystack simülatör + agentic-retrieval router)
**Ön koşullar:** Faz 12 · 17 (video temporal token'lar)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Değişken FPS ve pooling'de uzun-form video için toplam görsel-token sayılarını hesapla.
- Üç ölçek yolunu açıkla: brute context (Gemini 1.5), ring attention (LWM), token compression (LongVILA / Video-XL).
- Ham-context video VLM'leri ile agentic-retrieval video VLM'lerini (VideoAgent) doğruluk ve latency'de karşılaştır.
- 30 dakikalık bir video için needle-in-a-haystack testi tasarla ve spesifik bir dakikada recall ölç.

## Sorun

384 native çözünürlükte Qwen2.5-VL boyutunda patch'lerin tek frame'i ~729 token. 3x3 pooling'de bu frame başına 81 token. 1 FPS'te 30 dakikalık klip = 1800 frame = 145,800 token. 2025 açık VLM'leri ile yapılabilir, sıkı. 2 FPS'te 291,600 token — yalnızca en büyük context'ler sığar.

1 FPS'te 2 saatlik film 583k token. Çoğu 2026 açık modelinin ötesinde; Gemini 2.5 Pro ya da daha agresif pooling gerekir.

Üç ölçek yolu çıktı.

## Kavram

### Yol 1: Brute context (Gemini 1.5, Claude Opus)

Soruna donanım at. Context'i milyon token'a ölçekle, her şeyi tek forward pass'te işle.

Gemini 1.5 Pro 1M token ile lansman yaptı; Gemini 1.5 Ultra 10M'ye; Gemini 2.5 Pro 2026'da güvenilir şekilde saatlerce video yapıyor. Makale (arXiv:2403.05530) ~9.5M token'a kadar %99.7 needle-in-a-haystack recall belgeliyor.

Mühendislik: bellek hiyerarşisi (yerel + global + seyrek) artı uzun-context verimliliği için MoE expert routing ile özel attention implementasyonu. Tam detay yayınlanmadı. Açık-kaynak değil.

### Yol 2: Ring attention (LWM, LongVILA)

Ring attention uzun dizileri her cihazın bir parça tuttuğu bir "halkada" cihazlara dağıtır. Tam dizi üzerinde attention her cihazın kendi parçasını halka kalıbında bir sonrakine göndererek, kısmi attention hesaplayarak ve toplayarak gerçekleşir.

LWM (Liu et al., 2024) 1M token context modeli bu şekilde eğitti. Eğitim compute'u context ile lineer ölçekler, kuadratik değil — attention'a kuadratik darbe halkanın cihazları boyunca amortize edilir.

LongVILA (arXiv:2408.10188) kalıbı VLM'lere uyarladı. Frame başına 192 token'da 1400 frame video = 268k context, 8 yollu paralelizm boyunca ring attention ile eğitildi.

### Yol 3: Token compression (Video-XL, LongVA)

Brute context'ten daha ucuz: LLM'in diziyi görmeden önce agresif sıkıştır.

Video-XL (arXiv:2409.14485) bir görsel özet token'ı kullanır: N frame klibinin her biri N üzerinde attend eden tek bir "özet" token üretir. Çıkarımda LLM klip başına bir özet token görür, context'i ciddi şekilde küçültür.

LongVA "long context transfer" tekniği ile LLM context'ini 200k'dan 2M'ye genişletir. Uzun-context metin üzerinde eğit, paylaşılan temsil üzerinden uzun-context videoya transfer et.

Token compression spesifik timestamp'lerde recall'u scalability için takas eder. Model genelde ne olduğunu bilir ama bazen tam frame'leri kaçırır.

### Yol 4: Agentic retrieval (VideoAgent)

Tüm videoyu LLM'e besleme. Bunun yerine, videoyu veritabanı olarak ele al ve sorgulamak için LLM kullan.

VideoAgent (arXiv:2403.10517):

1. LLM soruyu okur.
2. LLM ilgili klipler için bir retrieval tool'una sorar ("bana kedili segmentleri göster").
3. Tool eşleşen klip timestamp'leri döndürür.
4. LLM o klipleri bir VLM üzerinden okur.
5. LLM cevabı oluşturur ya da takip sorgular sorar.

Bu uzun videoya uygulanan LLM-as-agent kalıbı. Daha ucuz çıkarım (yalnızca ilgili klipler kodlanır), daha zor mühendislik (retrieval kalitesi bottleneck olur).

### Needle-in-a-haystack benchmark'ları

Standart uzun-context testi: videoda rastgele bir noktada benzersiz bir görsel ya da metin marker'ı ekle, sonra onu hatırlamayı gerektiren bir sorgu sor.

Metrik: video uzunluğu ve marker pozisyonu boyunca Recall@k.

Gemini 2.5 Pro 90 dakikaya kadar videolarda >%99 recall puanlıyor. Açık 72B modeller (Qwen2.5-VL-72B, InternVL3-78B) 30 dakikada ~%85-90 puanlıyor ve 60'tan sonra bozuluyor.

VideoAgent ham-context modelleri 2+ saatte eşleyebilir ya da yenebilir, çünkü tool iyiyse retrieval needle'a vuruyor.

### Hangi yolu seçmeli

Frontier doğrulukta 15 dakikalık klip için: açık 72B + native context genellikle çalışıyor. Qwen2.5-VL-72B seç.

30 dakikadan 1 saate kadar içerik için: açık için LongVILA ya da Video-XL; kapalı için Gemini 2.5 Pro. Kalite çıtası önemli — frontier kapalıya gidiyor.

2+ saat içerik için: VideoAgent ya da benzer retrieval kalıpları. Alternatif olarak, daha küçük parçalara özetle ve hiyerarşik özetleri besle.

### 2026 üretim kalıbı

Pratikte üretim uzun-video pipeline'ları hibrit:

1. Tüm videoda dynamic-FPS sampling + agresif pooling çalıştır (100k-token global temsil al).
2. Global özet için bir 72B VLM'e geç.
3. User detaylı soru sorarsa, özeti index olarak kullanarak agentic retrieval çalıştır.

Bu global anlama için brute-context'i ve yerel detay için retrieval'ı birleştirir.

## Kullan

`code/main.py`:

- Değişken FPS + pooling'de 1 dakikadan 3 saate videolar için token bütçelerini hesaplar.
- Bir needle-in-a-haystack çalıştırması simüle eder: rastgele bir timestamp'te marker enjekte et, soru sor, recall skorla.
- Aşağı akış VLM'e beslemek için spesifik klipler seçen bir agentic-retrieval router simülatörü içerir.

Bütçe tablosunu çalıştır ve ölçek farkını hisset.

## Yayınla

Bu ders `outputs/skill-long-video-strategy-planner.md` üretir. Bir video süresi ve sorgu karmaşıklığı verildiğinde, brute-context, compression ve agentic retrieval arasından seçer ve latency + kalite beklentilerini hesaplar.

## Alıştırmalar

1. 1 FPS'te 45 dakikalık bir ders, frame başına 81 token. Toplam token? Hangi modellerin context'ine sığar?

2. Bir needle-in-a-haystack testi tasarla: marker'ı hangi dakikada enjekte ediyorsun ve tam sorgu formatı nedir?

3. 1 saatlik videoda brute-context Qwen2.5-VL-72B (80k context) ile VideoAgent (Claude 3.5 + retrieval) karşılaştır. Recall'da hangisi kazanır? Latency'de hangisi kazanır?

4. Ring attention bellek maliyeti dizi uzunluğunda ve cihaz sayısında lineer ölçekler. Nedenini ve ring-rotation fazını düşürürsen neyin başarısız olduğunu açıkla.

5. Gemini 1.5 Bölüm 5'i needle-in-a-haystack üzerine oku. Makale 1M vs 10M token sınırında recall hakkında ne buldu?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Brute context | "Daha çok token" | LLM context'ini milyon token'a ölçekle; her şeyi tek pass'te işle |
| Ring attention | "LWM tarzı paralel" | Her cihazın bir parça tutup döndürdüğü dağıtık attention kalıbı |
| Token compression | "Özet token'lar" | Bir öğrenilmiş kompresör üzerinden LLM'den önce klip başına token'ları azalt |
| Needle-in-haystack | "NIH testi" | Rastgele noktada benzersiz marker ekle, test zamanında modelden onu hatırlamasını iste |
| Agentic retrieval | "Sorgu planlayıcısı olarak LLM" | LLM ilgili klipler için retrieval tool'una sorar, onları VLM üzerinden okur, cevabı oluşturur |
| VideoAgent | "Video için retrieval kalıbı" | Canonical agentic-retrieval tasarımı: soru -> tool -> klip -> cevap |

## İleri Okuma

- [Gemini Team — Gemini 1.5 (arXiv:2403.05530)](https://arxiv.org/abs/2403.05530)
- [Liu et al. — LWM / RingAttention (arXiv:2402.08268)](https://arxiv.org/abs/2402.08268)
- [Xue et al. — LongVILA (arXiv:2408.10188)](https://arxiv.org/abs/2408.10188)
- [Shu et al. — Video-XL (arXiv:2409.14485)](https://arxiv.org/abs/2409.14485)
- [Wang et al. — VideoAgent (arXiv:2403.10517)](https://arxiv.org/abs/2403.10517)
