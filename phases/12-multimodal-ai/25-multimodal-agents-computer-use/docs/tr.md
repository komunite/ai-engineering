# Multimodal Agent'lar ve Computer-Use (Bitirme)

> 2026 frontier ürünü, ekran görüntülerini okuyan, düğmeleri tıklayan, web UI'lerinde gezinen, formları dolduran ve iş akışlarını uçtan uca tamamlayan bir multimodal agent. SeeClick ve CogAgent (2024) GUI-grounding primitive'ini kanıtladı. Ferret-UI mobile ekledi. ChartAgent chart'lar için visual tool-use tanıttı. VisualWebArena ve AgentVista (2026) frontier'ın kovaladığı benchmark'lar — ve hatta Gemini 3 Pro ile Claude Opus 4.7 AgentVista'nın zor görevlerinde ~%30 puanlıyor. Bu bitirme Faz 12'nin her ipliğini birleştiriyor: algı (yüksek-res VLM), akıl yürütme (tool use'lu LLM), grounding (koordinat çıkış), uzun-ufuk bellek ve değerlendirme.

**Tür:** Bitirme
**Diller:** Python (stdlib, action şema + agent döngüsü iskeleti)
**Ön koşullar:** Faz 12 · 05 (LLaVA), Faz 12 · 09 (Qwen-VL JSON), Faz 14 (Agent Mühendisliği)
**Süre:** ~240 dakika

## Öğrenme Hedefleri

- Bir multimodal agent döngüsü tasarla: algıla → akıl yürüt → eyle → gözle → tekrarla.
- VLM'in JSON olarak yayabileceği bir GUI grounding çıkış şeması (click koordinatları, metin yaz, scroll, sürükle) inşa et.
- Yalnızca-ekran-görüntüsü agent'larını accessibility-tree agent'ları ve hibrit agent'larla karşılaştır.
- Küçük bir VisualWebArena diliminde multimodal agent benchmark değerlendirmesi kur.

## Sorun

Rezervasyon-sitesi iş akışı: "15 Nisan için Tokyo'ya, 800$ altı koridor koltuğu uçuş bul, rezervasyon yap."

Bir multimodal agent şunları yapmalı:

1. Tarayıcının ekran görüntüsünü al.
2. Ekran görüntüsü + URL + hedefi bir plana ayrıştır.
3. Yapılandırılmış bir eylem yay: tıkla (x,y'de), "Tokyo" yaz (E elementinde), aşağı scroll et, seç (radio button).
4. Eylemi tarayıcıya uygula.
5. Yeni durumu gözle (sonraki ekran görüntüsü).
6. Görev bitene kadar tekrarla.

Her adım bir multimodal VLM çağrısı. VLM çıktısı ayrıştırılabilir JSON olmalı. Hatalar adımlar arasında birikiyor, bu yüzden recovery önemli.

## Kavram

### GUI grounding — primitive

GUI grounding şudur: bir ekran görüntüsü ve doğal dil instruction'ı verildiğinde, tıklanacak (ya da diğer eylem) (x, y) koordinatını çıkar.

SeeClick (arXiv:2401.10935) ölçekte ilk açık sonuçtu: sentetik + gerçek GUI verisinde bir VLM'i fine-tune et, koordinatları düz metin token'ları olarak çıkar. Çalışıyor.

CogAgent (arXiv:2312.08914) yoğun UI'ler için 1120x1120 yüksek-çözünürlüklü kodlama ekledi. Skor: web navigation'da ~%84.

Ferret-UI (arXiv:2404.05719) mobil UI'lere odaklanır, iOS accessibility verisi ile entegre olur.

Çıkış formatı genellikle JSON:

```json
{"action": "click", "x": 384, "y": 220, "element_desc": "Search button"}
```

`element_desc` recovery'ye yardım eder: koordinatlar ekran görüntüleri arasında kayıyorsa, semantik ipucu sistemin yeniden ground etmesine izin verir.

### Action şemaları

Tipik action şema 6-10 eylem türüne sahiptir:

- `click`: (x, y)
- `type`: (text, x?, y?)
- `scroll`: (direction, amount)
- `drag`: (x0, y0, x1, y1)
- `select`: (option_index)
- `hover`: (x, y)
- `navigate`: (url)
- `wait`: (ms)
- `done`: (success, explanation)

Agent adım başına bir eylem yayar. Tarayıcı wrapper'ı yürütür ve yeni durumu döndürür.

### Yalnızca-ekran-görüntüsü vs accessibility-tree

İki input modu:

- Yalnızca-ekran-görüntüsü: tam görsel, yapısal bilgi yok. En genel; herhangi uygulamada çalışır.
- Accessibility tree: yapılandırılmış DOM / iOS accessibility bilgisi. Grounding için çok daha güvenilir; tree mevcut olduğunda çalışır.
- Hibrit: ikisi, atomik eylemler için güvenilir grounder olarak tree ve semantik context için ekran görüntüsü.

Üretim agent'ları mümkün olduğunda hibrit kullanır. Tarayıcı otomasyonu (Selenium + accessibility) her zaman tree'ye sahip; desktop uygulamalar bazen.

### Uzun-ufuk bellek

20 adımlık iş akışı 20 ekran görüntüsü üretir. VLM'in context'i hızlı dolar. Üç sıkıştırma stratejisi:

- Summary-chain: her 5 adımdan sonra, ne olduğunu özetle, eski ekran görüntülerini düşür.
- Skip-frame: ilkini, sonuncuyu ve her 3.'sünü tut.
- Tool-recorded log: eylemleri yürüt, ne yapıldığının metin log'unu tut; eski ekran görüntülerine yeniden bakma.

Claude'un computer-use API'si log kalıbı kullanır. Daha basit, daha güvenilir.

### Visual tool use

ChartAgent (arXiv:2510.04514) chart anlama için visual tool use tanıtıyor: crop, zoom, OCR, harici detection'ı çağır. Agent "(100, 200, 300, 400) bölgesine crop et sonra OCR çağır"ı tool call olarak çıkarabilir. Tool metin döndürür; VLM akıl yürütmeye devam eder.

Bu kalıp genelleşiyor: set-of-mark prompting, region annotation ve harici detection tool'larının hepsi aynı "bir tool call çıkar, yapılandırılmış yanıt al" şemasına uyar.

### 2026 benchmark'ları

- ScreenSpot-Pro. ~1k web ekran görüntüsünde GUI grounding. Açık SOTA Qwen2.5-VL-72B ~%85. Frontier ~%90.
- VisualWebArena. Uçtan uca web görevleri (alışveriş, forum, ilan). Açık SOTA ~%20. Gemini 3 Pro ~%27.
- AgentVista (arXiv:2602.23166). En zor 2026 benchmark'ı. 12 domain boyunca gerçekçi iş akışları. Frontier modeller %27-40 puanlıyor; açık modeller %10-20.
- WebArena / WebShop. Daha eski benchmark'lar; frontier tarafından doyuruldu.

### Neden hâlâ zor

Agent performans bottleneck'leri:

1. İnce ölçekte görsel grounding. Mobil çözünürlükte "küçük X'i tıkla" sıklıkla başarısız.
2. Uzun-ufuk planlama. 10 eylem sonra agent hedeften kayıyor.
3. Hata recovery. Bir tıklama başarısız olduğunda (yanlış düğme), tespit + recovery nadiren eğitilen veridir.
4. Cross-sayfa context. Tab'lar arasında atlamak ya da uzun formlar durumu kaybeder.

Araştırma yönleri: bellek mimarileri, açık replanning, multimodal doğrulama (eylem başarısı için ekran görüntüsü eşleştirme).

### Bitirme inşa-et

Bitirme görevi: şunu yapan bir computer-use agent inşa et:

1. Bir rezervasyon-sitesi mock sayfasının HTML + ekran görüntüsünü okur.
2. Çok adımlı bir dizi planlar: ara → seç → form doldur → gönder.
3. Action şemasına uyan JSON eylemleri yayar.
4. Sabit 10-görev diliminde değerlendirir.

Ders kolayca gerçek tarayıcıya genişletilebilen scaffold kod sağlar.

## Kullan

`code/main.py` bitirme scaffold'u:

- Action şema JSON tanımı (10 eylem).
- Dict olarak mock tarayıcı durumu.
- Agent döngüsü iskeleti: durum al, eylem yay, uygula, döngü.
- Uçtan uca başarı oranını ölçmek için 10-görevlik mini-benchmark (sentetik sayfalar).
- Bir eylem başarısız olduğunda hata-recovery hook'u.

## Yayınla

Bu ders `outputs/skill-multimodal-agent-designer.md` üretir. Bir computer-use ürünü (domain, action seti, değerlendirme hedefi) verildiğinde, tam agent döngüsünü, bellek stratejisini, grounding modunu ve beklenen benchmark skorunu tasarlar.

## Alıştırmalar

1. Action şemasını bir `screenshot_region` tool'u (crop + zoom) ile genişlet. Hangi görevler fayda görür?

2. AgentVista'yı (arXiv:2602.23166) oku. En zor görev kategorisini betimle ve frontier modellerin neden hâlâ başarısız olduğunu.

3. Uzun-ufuk bellek sıkıştırması: canlı tutulan ≤4 ekran görüntüsü, herhangi sayıda loglanmış bir summary-chain tasarla.

4. Bir hata-recovery hook'u inşa et: eylem başarısızlığında (düğme bulunamadı), agent sonra ne yapar?

5. 10 web görevinde yalnızca-ekran-görüntüsü Claude 4.7'yi hibrit ekran-görüntüsü + accessibility-tree Qwen2.5-VL ile karşılaştır. Hangisi hangi görevde kazanır?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| GUI grounding | "Tıklama koordinatları" | Model bir instruction'ın ekran görüntüsündeki hedefi için (x,y) çıkarır |
| Action schema | "Tool tanımları" | Geçerli eylemlerin JSON betimlemesi (click, type, scroll, drag) |
| Accessibility tree | "Yapılandırılmış DOM" | Tarayıcı/iOS API'lerinden makine-okunabilir UI hiyerarşisi |
| Hibrit agent | "Ekran görüntüsü + tree" | Hem görsel hem yapılandırılmış bilgi kullanır; ikisinden tek başına daha güvenilir |
| Visual tool use | "Zoom/crop/detect" | Agent plan ortasında harici görü tool'ları (OCR, detection) çağırır |
| Summary-chain | "Bellek sıkıştırma" | Periyodik metin özetler uzun ekran görüntüsü geçmişini değiştirir |
| VisualWebArena | "E2E web bench" | Uçtan uca web görevleri için 2024 benchmark'ı |
| AgentVista | "2026 zor bench" | 12-domain gerçekçi iş akışları; Gemini 3 Pro bile ~%30 puanlıyor |

## İleri Okuma

- [Cheng et al. — SeeClick (arXiv:2401.10935)](https://arxiv.org/abs/2401.10935)
- [Hong et al. — CogAgent (arXiv:2312.08914)](https://arxiv.org/abs/2312.08914)
- [You et al. — Ferret-UI (arXiv:2404.05719)](https://arxiv.org/abs/2404.05719)
- [ChartAgent (arXiv:2510.04514)](https://arxiv.org/abs/2510.04514)
- [Koh et al. — VisualWebArena (arXiv:2401.13649)](https://arxiv.org/abs/2401.13649)
- [AgentVista (arXiv:2602.23166)](https://arxiv.org/abs/2602.23166)
