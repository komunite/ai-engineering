# Paylaşılan Bellek ve Blackboard Desenleri

> 2026 çoklu-agent sistemlerinde iki yaklaşım bir arada yaşar: **message pool** (herkes herkesin mesajlarını görür, AutoGen GroupChat ya da MetaGPT'deki gibi) ve **abonelikli blackboard** (agent'lar ilgili event'lere abone olur, Context-Aware MCP ya da Matrix framework'ündeki gibi). İkisi de bir çoklu-agent sisteminin tek stateful kısmıdır — bu da ikisinin de ilginç bug'ların yaşadığı yer olduğu anlamına gelir. Referans başarısızlık modu **bellek zehirlenmesi**'dir: bir agent bir "gerçeği" halüsinasyon yapar, diğer agent'lar bunu doğrulanmış olarak ele alır ve doğruluk anında çökmekten çok daha zor hata ayıklanan bir şekilde kademeli olarak bozulur. Bu ders her iki yapıyı da stdlib'den inşa eder, bir zehirleme saldırısı enjekte eder ve üretimde gerçekten işe yarayan üç hafifletmeyi gösterir.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib, `threading`)
**Ön koşullar:** Faz 16 · 04 (Primitive Model), Faz 16 · 09 (Parallel Swarm Networks)
**Süre:** ~75 dakika

## Sorun

Çoklu-agent sistemleri agent'ların gerçekleri paylaşacağı bir yere ihtiyaç duyar. Birebir bir seçenek "her şeyi mesajlarda ilet"tir — ama bu paylaşılan state'i ekstra kopyalamayla yeniden icat eder. Bir diğeri "herkese global bir log ver"dir — ama global log'lar sınırsız büyür ve kolayca zehirlenir. Üçüncüsü "agent başına bir görünüm projeksiyonu yap"tır — ölçeklenebilir ama şema-ağırlıklı.

Agent'lardan biri halüsinasyon yapıp halüsinasyonu paylaşılan state'e yazdığında, o state'i okuyan her downstream agent halüsinasyonu gerçek olarak benimser. İnsan fark ettiğinde, akıl yürütme zinciri beş adım derinliktedir ve kök neden yazılmış üçüncü mesajdır. Çoklu-agent doğruluk bozulmasını hata ayıklamak bir crash'i hata ayıklamaktan zordur.

Bu bellek zehirlenmesi. MAST taksonomisindeki ikinci-en-belgelenen başarısızlık ailesidir (Cemri ve diğ., arXiv:2503.13657) ve yapısaldır: provenance ve yazılamaz bir verifier olmayan herhangi bir paylaşılan-bellek tasarımı eninde sonunda bunu sergiler.

## Kavram

### İki ana topoloji

**Tam message pool.** Her agent her mesajı okur. AutoGen GroupChat ve MetaGPT bunu kullanır. Basit, şeffaf, denetlenebilir ama ~10 agent'ın ötesine ölçeklenmez çünkü her agent'ın context'i diğer agent'ların işiyle dolar.

```
agent-A ──yaz──▶ ┌────────────────┐ ◀──oku── agent-D
                 │ message pool   │
agent-B ──yaz──▶ │                │ ◀──oku── agent-E
                 │ (global log)   │
agent-C ──yaz──▶ └────────────────┘ ◀──oku── agent-F
```

**Abonelikli blackboard.** Agent'lar konulara ilgi bildirir; substrat yalnızca ilgili mesajları yönlendirir. CA-MCP (arXiv:2601.11595) ve Matrix merkeziyetsiz framework (arXiv:2511.21686) bunu kullanır. Daha fazla ölçeklenir ama abonelikleri anlamlı yapmak için önceden şema tasarımı gerektirir.

```
                   ┌─ konu: prices ───┐
agent-A ──pub────▶ │                  │ ──▶ agent-D (abone)
                   ├─ konu: orders ───┤
agent-B ──pub────▶ │                  │ ──▶ agent-E (abone)
                   ├─ konu: alerts ───┤
agent-C ──pub────▶ │                  │ ──▶ agent-F (abone)
                   └──────────────────┘
```

### Her biri ne zaman kazanır

- **Tam pool** agent'lar az (< 10), heterojen ve konuşma kısa-vadeli olduğunda kazanır. Herkes her şeyi gördüğünde kim ne dedi üzerine akıl yürütmek basittir.
- **Blackboard** agent'lar çok, rolde homojen ama örnekte çok sayıda (sürüler) ve konuşma uzun süreli olduğunda kazanır. Yönlendirme token maliyeti ve context kirlenmesini tasarruf eder.

Üretim sistemleri sıklıkla karıştırır: üstte (planlama katmanı) küçük bir tam pool, altında (worker katmanı) blackboard'lar.

### Bellek zehirlenmesi, bir senaryoda

Üç agent bir araştırma görevi üzerinde çalışır. Agent A bir getirme agent'ı. Agent B özetleyici. Agent C analist.

1. A bir sayfayı çeker ve paylaşılan state'e bir mesaj yazar: "Çalışma %42 doğruluk artışı raporluyor."
2. Çekilen sayfa aslında "%4.2 artış" dedi. A bir ondalık halüsinasyon yaptı.
3. B paylaşılan state'i okuyarak yazar: "Büyük %42 doğruluk kazanımı raporlandı (kaynak: A)."
4. C paylaşılan state'i okuyarak yazar: "Benimsenmesini öner — %42 sıçrama dönüştürücüdür."
5. Final rapor hiç var olmamış %42 rakamını alıntılar.

Hiçbir agent çökmedi. Hiçbir test başarısız olmadı. Sistem "çalıştı". Halüsinasyon bir agent'ın context'inden paylaşılan state üzerinden her downstream agent'ın akıl yürütmesine geçti.

### Bu neden yapısal

Paylaşılan state olmadan A'nın halüsinasyonu A'nın context'inde kalır. Downstream agent'lar yeniden getirir ya da yeniden türetir ve hatayı yakalayabilir. Naif paylaşılan state ile A'nın context'i herkesin context'i olur ve halüsinasyon gerçeğe aklanmış olur.

Sorun paylaşılan state başına değil — sorun **provenance ve bağımsız verifier olmadan paylaşılan state**. Üç hafifletme bunu adresliyor:

1. **Her yazımda provenance ata.** Paylaşılan state'teki her giriş kimin yazdığını, ne zaman, hangi prompt altında ve (varsa) agent'ın hangi kaynağı alıntıladığını kaydeder. Downstream agent'lar provenance'a göre şüpheyle okur.
2. **Yazımları sürümle; append-only olarak ele al.** Düzeltme yerinde güncelleme değil, eskisinin yerini alan yeni bir girdidir. Audit trail korunur.
3. **Paylaşılan state'e yazamayan en az bir agent tut.** Salt-okunur bir verifier agent girdileri örnekler, kaynakları yeniden getirir ve tutarsızlıkları işaretler. Pool'a yazamadığı için pool tarafından zehirlenemez.

### Blackboard öncülü (Hayes-Roth, 1985)

Blackboard deseni LLM agent'larından dört on yıl önce gelir. Hayes-Roth (1985, "A Blackboard Architecture for Control") global bir blackboard'u gözlemleyen, kısmi çözümlere katkıda bulunan ve diğer kaynakları tetikleyen uzmanlaşmış Knowledge Source'ları tanımladı. 2026 blackboard'u (CA-MCP, Matrix) aynı desendir — Knowledge Source olarak LLM agent'ları ve kısmi çözüm olarak JSON blob'ları. Eski literatür modern sistemlerin yeniden keşfettiği yazma çekişmesi, fırsatçı kontrol ve tutarlılık için belgelenmiş çözümlere sahiptir.

### Projeksiyon vs tam görünüm

Saf blackboard her aboneye aynı projeksiyonu verir (topic-kapsamlı). Daha agresif bir tasarım **agent başına projeksiyon**'dur: her agent rolüne özelleştirilmiş bir görünüm alır. LangGraph'in state reducer'ları kanonik 2026 implementasyonudur — reducer fonksiyonu global state'i role-özgü bir dilime katlar.

Agent başına projeksiyon daha fazla ölçeklenir ama bir şemaya ihtiyaç duyar. Şema olmadan her agent'ın prompt'unda ad-hoc projeksiyon yeniden inşa edersin.

### Yazma-çekişme desenleri

Birden çok agent'ın aynı anda yazması bir eş zamanlılık problemidir, sadece LLM problemi değildir. Üç desen çalışır:

- **Sıralı yazıcı (tek üretici).** Tüm yazımlar serileştiren bir koordinatör agent'tan geçer. Basit, ama dar boğaz.
- **Sürümlemeli iyimser eş zamanlılık.** Her girdinin bir sürümü vardır; yazıcılar sürüm uyuşmazlığında başarısız olur ve retry yapar. Klasik veritabanı tekniği.
- **Konu bölümleme.** Farklı agent'lar farklı konulara sahip. Konu-arası çekişme yok. Tasarlanmış bölme sınırları gerektirir.

Çoğu 2026 framework'ü varsayılan olarak sıralı yazıcıya gider çünkü LLM çağrıları çekişme nadir olacak ve dar boğaz canı yakmayacak kadar yavaştır.

### Yazılamaz verifier

En yük taşıyıcı hafifletme salt-okunur verifier'dır. Uygulama kuralları:

- Verifier takımla state'i paylaşır (blackboard ya da pool'u okur).
- Verifier'ın paylaşılan state'e yazma tanıtıcısı yoktur — yalnızca ayrı bir doğrulama kanalına.
- Verifier bağımsız olarak yazımlarda alıntılanan kaynakları getirir. Anlaşmazlığı işaretler.
- Verifier'ın kendi çıktıları bir insana ya da ayrı bir karar agent'ına yönlendirilir, asla pool'a geri beslenmez.

Bu ayrım olmadan verifier'ın çıktıları pool'da yeni girdiler olur, bu da zehirlenmiş bir pool'un verifier'ı zehirlemesi, onun da doğrulamalarını zehirlemesi anlamına gelir.

## İnşa Et

`code/main.py` stdlib Python'da her iki topolojiyi artı bir oyuncak zehirleme saldırısı ve üç hafifletmeyi uygular.

- `MessagePool` — tam okumayla thread-safe append-only log.
- `Blackboard` — agent başına aboneliklerle topic-keyed pub/sub.
- `ProvenanceEntry` — her yazım (writer, timestamp, prompt_hash, source_uri) kaydeder.
- `PoisoningScenario` — agent A'nın bir ondalık halüsinasyon yaptığı bir üç-agent araştırma görevini çalıştırır. Final rapor yazar.
- `Verifier` — kaynakları yeniden getiren ve tutarsızlıkları işaretleyen salt-okunur agent. Aynı senaryoyu verifier mevcut iken çalıştırır.

Çalıştır:

```
python3 code/main.py
```

Beklenen çıktı:
- Çalıştırma 1 (verifier yok): halüsinasyon yapılmış %42 final rapora yayılır.
- Çalıştırma 2 (verifier var): verifier tutarsızlığı işaretler, pool "flagged" olarak etiketlenir, final rapor bir geri çekme içerir.

## Kullan

`outputs/skill-memory-auditor.md` herhangi bir çoklu-agent sisteminin paylaşılan-bellek tasarımını provenance, sürümleme ve verifier ayrımı için denetleyen bir skill'dir. Üretimden önce yeni çoklu-agent mimarileri üzerinde çalıştır.

## Yayınla

Herhangi bir paylaşılan-bellek tasarımı için:

- Her yazımda provenance kaydet: `(writer, timestamp, prompt_hash, tool_calls_cited, source_uri)`.
- Log'u append-only yap. Düzeltmeler yerini aldıkları girdiye referans veren yeni girdilerdir.
- Bağımsız kaynak erişimine sahip en az bir salt-okunur verifier agent dağıt.
- Verifier çıktısını paylaşılan pool'a geri değil, ayrı bir kanala yönlendir.
- Üst alma olan yazım oranını log'la — yükselen bir oran halüsinasyon desenlerinin erken kanıtıdır.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Çalıştırma 1'in halüsinasyonu yaydığını ve çalıştırma 2'nin yakaladığını doğrula.
2. İkinci bir halüsinasyon ekle: agent B bir veri seti boyutu uydurur. Verifier ikisi için de elle ayarlanmadan ikisini de yakalamalı.
3. Tam pool'u konu bölmeli (`prices`, `summaries`, `analyses`) bir blackboard'a değiştir. Konu bölümleme hangi zehirleme senaryolarını çekmeyi zorlaştırır ve hangisinde yardım etmez?
4. Hayes-Roth (1985, "A Blackboard Architecture for Control")'u oku. Bu derste tartışılmayan ama 2026 sistemlerinin yararlanacağı iki kontrol desenini belirle.
5. CA-MCP (arXiv:2601.11595)'i oku. Shared Context Store'unu `code/main.py`'deki MessagePool ya da Blackboard sınıfından birine eşle. CA-MCP üzerine hangi primitive'leri ekler?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Message pool | "Paylaşılan sohbet geçmişi" | Her agent'ın okuduğu append-only log. Tam şeffaflık, zayıf ölçekleme. |
| Blackboard | "Paylaşılan çalışma alanı" | Topic-keyed pub/sub. Agent'lar ilgili konulara abone olur. Daha fazla ölçeklenir. |
| Provenance | "Kim ne yazdı" | Her yazımda metadata: writer, timestamp, prompt, kaynaklar. |
| Bellek zehirlenmesi | "Yayılan halüsinasyonlar" | Bir agent'ın hatası paylaşılan state'e girer, downstream agent'lar onu gerçek olarak benimser. |
| Append-only | "Yerinde güncelleme yok" | Düzeltmeler yer alan yeni girdilerdir. Audit trail'i korur. |
| Yazılamaz verifier | "Bağımsız denetçi" | Kaynakları yeniden getiren ve tutarsızlıkları işaretleyen salt-okunur agent. |
| Projeksiyon | "Kapsamlı görünüm" | Global state'ten hesaplanan agent başına görünüm. LangGraph reducer'ları kanonik durumdur. |
| Knowledge Source | "Uzman agent" | Hayes-Roth'un 1985 terimi; blackboard katılımcısı. |

## İleri Okuma

- [Cemri ve diğ. — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) — MAST taksonomisi; bellek zehirlenmesi koordinasyon-başarısızlık alt-ailesi
- [CA-MCP — Context-Aware Multi-Server MCP](https://arxiv.org/abs/2601.11595) — koordineli MCP sunucuları için Shared Context Store
- [Matrix — merkeziyetsiz çoklu-agent framework](https://arxiv.org/abs/2511.21686) — merkezi orchestrator olmadan mesaj-kuyruk tabanlı blackboard
- [LangGraph state and reducers](https://docs.langchain.com/oss/python/langgraph/workflows-agents) — üretimde agent başına projeksiyon deseni
- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — üretim dağıtımından provenance ve doğrulama notları
