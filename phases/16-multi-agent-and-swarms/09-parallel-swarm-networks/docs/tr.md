# Paralel / Sürü / Ağ Mimarileri

> Supervisor ile kontrast: merkezi karar verici yok. Agent'lar paylaşılan bir event bus okur, asenkron iş alır, sonuçları geri yazar. LangGraph merkeziyetsiz, dinamik ortamlar için "Swarm Architecture"ı açıkça destekler. Matrix (arXiv:2511.21686) orchestrator dar boğazını ortadan kaldırmak için hem kontrol hem veri akışını dağıtık kuyruklar üzerinden iletilen serileştirilmiş mesajlar olarak temsil eder. Takas açıktır: ölçeklenebilirlik için determinizm ve takip edilebilirlik. Sürü, birçok bağımsız alt-soruna sahip görevlere uyar; tek bir tutarlı plan gerektiren görevlere uymaz.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib, `threading`, `queue`)
**Ön koşullar:** Faz 16 · 05 (Supervisor Deseni), Faz 16 · 04 (Primitive Model)
**Süre:** ~75 dakika

## Sorun

Supervisor birkaç worker'a ölçeklenir. Yüzlerce ne olacak? Supervisor'ın kendisi dar boğaz olur: kimin ne yapacağı hakkındaki her karar bir agent'tan geçer. Yavaş bir plan adımı tüm sistemi durdurur.

Sürü mimarileri tasarımı tersine çevirir. Merkezi bir planlayıcının iş dağıtması yerine, worker'lar paylaşılan bir kuyruktan iş alır. "Koordinasyon" event bus semantiğine pişirilir. Orchestrator yok; sistem kuyruk ölçeklenene kadar ölçeklenir.

## Kavram

### Şekil

```
                ┌──── paylaşılan kuyruk ────┐
                │                            │
       ┌────────┼────────┐  ◄──────┬────────┘
       ▼        ▼        ▼         │
     Worker  Worker  Worker   Worker
      A       B       C        D
       │        │        │         │
       └────────┴────────┴─────────┘
                 │
                 ▼
            sonuç havuzu
```

Orchestrator yok. Her worker tekrarlar: bir görev al, işle, sonucu yaz (ve isteğe bağlı olarak takipleri kuyruğa al).

### Sürü ne zaman uyar

- **Çok sayıda bağımsız görev.** Scraping, dönüştürme, sınıflandırma. Görevler birbirine bağlı değildir.
- **Değişken-süreli iş.** Bazı görevler 100ms, diğerleri 10s sürüyorsa, sürü yükü otomatik olarak dengeler — hızlı worker'lar bir sonraki işleri alır. Supervisor süreyi tahmin etmek zorundadır.
- **Determinizm yerine throughput.** Katı sıralamayı değil, toplam tamamlanma süresini önemsersin.

### Sürü ne zaman başarısız

- **Sıralı iş akışları.** Adım 3 adım 2'nin çıktısına ihtiyaç duyuyorsa, sürü adım 2 bitmeden adım 3'ün ateşlenmesi riskini taşır.
- **Global plan görevleri.** Karmaşık araştırma soruları bir planlayıcıdan yararlanır. Bir araştırmacı sürüsü tutarlı bir rapor değil, bağımsız gerçekler üretir.
- **Hata ayıklama.** Merkezi log olmadan ve asenkron işle, bir bug'ı yeniden üretmek pahalıdır.

### Matrix (arXiv:2511.21686)

Matrix, sürüyü doğal sonucuna götüren 2025 makalesidir: hem kontrol akışı hem veri akışı dağıtık kuyruklar üzerinde serileştirilmiş mesajlardır. Merkezi koordinatör yok. Hata toleransı mesaj dayanıklılığından gelir. Ölçeklenebilirlik mesaj broker'ın sorunu, sistemin değil.

Katkı: çoklu-agent koordinasyonunun "bu agent hangi mesaj konusuna abone?" olduğu, "supervisor'ın sıradaki agent'ı kim?" olmadığı bir programlama modeli. Bu sistemi pub/sub event mesh'e benzetir.

### LangGraph'in Swarm Architecture'ı

LangGraph 2025 dokümanları "Swarm Architecture"ı çoklu-agent desenlerinden biri olarak açıkça tanımlar: agent'lar node'dur, ama kenarlar döngülerle yönlü bir graf oluşturur ve havuzdan herhangi bir node etkinleştirilebilir. Bir worker, supervisor ataması ile değil, koşulla mevcut işten seçer.

### Başarısızlık modu: starvation ve hot-spotting

Tüm worker'lar en hızlı-mevcut görevi alırsa, uzun süreli görevler kalan tek olana kadar asla alınmaz. Klasik kuyruk açlığı.

Hafifletmeler:
- Açık yaşlandırmalı priority queue'lar (bekleme süresiyle priority artar).
- Worker uzmanlaşması: bazı worker'lar yalnızca "uzun" görevler alır.
- Back-pressure: kuyruğa kaç hızlı görevin gireceğini sınırla.

### İçerik-tabanlı yönlendirme bağlantısı

Sürü doğal olarak içerik-tabanlı yönlendirme (Ders 22) ile eşleşir. Jenerik bir kuyruk yerine, mesaj tipi başına bir kuyruk. Uzman worker'lar yalnızca kendi tiplerine abone olur. Bu, binlerce agent'a ölçeklenen mesaj-bus mimarilerinin temelidir.

## İnşa Et

`code/main.py` paylaşılan bir `queue.Queue`'dan çeken 4 worker thread'inden oluşan bir sürü uygular. Görevlerin değişken süreleri vardır (bazıları hızlı, bazıları yavaş). Demo şunları karşılaştırır:

- **Sıralı baseline:** bir worker tüm görevleri seri olarak işler.
- **Sabit atama:** her görev belirli bir worker'a önceden atanır (supervisor-stili).
- **Sürü:** worker'lar paylaşılan bir kuyruktan çeker.

Sürü yükü otomatik olarak dengeler; sabit atama, atanan görev yavaş olduğunda hızlı worker'ları boş bırakır.

Çalıştır:

```
python3 code/main.py
```

Çıktı worker başına görev sayılarını (sürü eşit olmayan ama optimal şekilde dağıtır) ve duvar-saati sürelerini gösterir.

## Kullan

`outputs/skill-swarm-fit.md` bir görevin sürü vs supervisor kullanması gerekip gerekmediğini değerlendirir. Girdiler: görev bağımsızlığı, süre varyansı, sıralama gereksinimleri, hata ayıklanabilirlik ihtiyaçları.

## Yayınla

Kontrol listesi:

- **Yaşlandırmalı priority queue.** Uzun görev açlığını önle.
- **Worker idempotency.** Worker bir çalıştırma ortasında çökerse bir görev birden fazla kez alınabilir. Worker'lar idempotent olmalı.
- **Dayanıklı kuyruk.** Üretim için Kafka, Redis Streams ya da veritabanı destekli kuyruk kullan. `queue.Queue` yalnızca in-memory'dir.
- **Görev başına observability.** Her görevin bir trace ID'si vardır; her worker onunla start/end log'lar.
- **Back-pressure.** Kuyruk worker'ların boşaltabileceğinden hızlı büyüyorsa, üreticiyi yavaşlat.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Sürü, değişken-süreli workload'da sıralıdan ne kadar daha hızlı? Sabit atamadan ne kadar daha hızlı?
2. Bir priority queue varyantı ekle (`queue.PriorityQueue` kullan). Priority'yi görev "importance" alanıyla ata. Sürekli yük altında düşük-priority görevlerin hiç aç kalıp kalmadığını gözlemle.
3. Bir hot-spot dedektörü uygula: herhangi bir worker en yavaş worker'ın 3× fazlasını işlediğinde log'la. Bu görev-süre dağılımı hakkında ne gösterir?
4. Matrix makalesinin (arXiv:2511.21686) özetini ve Bölüm 3'ünü oku. Matrix'in kabul ettiği belirli bir takas (ölçeklenebilirlik kazanımı) ve vazgeçtiği birini (takip edilebilirlik, determinizm) belirle.
5. Sürü demosunu (task_type, payload) tuple'larından oluşan bir `queue.Queue` kullanacak şekilde dönüştür, worker'lar yalnızca belirli tiplere abone olur. Görevler heterojen olduğunda hangi yönlendirme kuralları mantıklı?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Sürü mimarisi (swarm) | "Merkeziyetsiz agent'lar" | Worker'lar paylaşılan kuyruktan çeker; merkezi orchestrator yok. |
| Event bus | "Agent'lar konulara abone olur" | Görevleri tipe ya da içeriğe göre worker'lara yönlendiren mesaj broker. |
| Starvation | "Görev hiç çalışmaz" | Daha yüksek-priority iş sürekli geldiği için düşük-priority görev hiç alınmaz. |
| Hot-spotting | "Bir worker boğulur" | Bir worker'ın çoğu görevi aldığı yük dengesizliği. |
| Back-pressure | "Üreticiyi yavaşlat" | Kuyruk dolduğunda upstream'e üretmeyi durdurmasını sinyaller mekanizma. |
| Idempotent worker | "Yeniden çalıştırması güvenli" | İki kez işlenen bir görev aynı sonucu üretir. Worker'lar çalışma ortasında çökebileceğinden gereklidir. |
| Dayanıklı kuyruk | "Çökmelerde hayatta kalır" | Disk ya da replike depolama destekli kuyruk; worker çöktüğünde görevler kaybolmaz. |
| Matrix framework | "Tam mesaj-iletimi sürüsü" | Hem veri hem kontrol akışı dağıtık kuyruklarda serileştirilmiş mesajlardır. |

## İleri Okuma

- [LangGraph workflows and agents — Swarm Architecture](https://docs.langchain.com/oss/python/langgraph/workflows-agents) — açık sürü desteği
- [Matrix — A Decentralized Framework for Multi-Agent Systems](https://arxiv.org/abs/2511.21686) — tam mesaj-iletimi sürüsü
- [Anthropic engineering — Research'te neden sürü değil supervisor](https://www.anthropic.com/engineering/multi-agent-research-system) — belirli bir üretim sisteminin sürü yerine supervisor'ı neden açıkça seçtiği
- [AutoGen v0.4 actor-model docs](https://microsoft.github.io/autogen/stable/) — event-driven actor yeniden yazımı, v0.2'nin GroupChat'inden sürüye daha yakın
