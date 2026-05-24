# Kill Switch'ler, Circuit Breaker'lar ve Canary Token'lar

> Bir kill switch agent'ın edit yüzeyinin dışında tutulan bir boolean'dır — bir Redis key, bir feature flag, imzalı bir config — agent'ı tamamen devre dışı bırakır. Bir circuit breaker daha ince taneli: belirli bir desende (üst üste beş aynı tool çağrısı) trip eder, ihlal eden yolu duraklatır ve bir insana yükseltir. Bir canary token klasik aldatmadan miras alır: agent'ın dokunmak için meşru bir nedeni olmayan sahte bir credential veya honeypot kayıt, erişimi bir uyarı tetikler. eBPF-tabanlı datapath'ler (örn. Cilium) kernel katmanında karantinaya alınmış bir pod'un egress'ini forensic bir honeypot'a yeniden yazabilir; yayımlanmış Cilium benchmark'ları yük altında milisaniye-altı P99 datapath gecikmesi rapor eder (yayılım bütçen datapath'in kendisine değil, bir politika güncellemesinin node'a nasıl ulaştığına bağlıdır). Hareketli bir baseline'a adapte olan istatistiksel detektörler (EWMA, CUSUM) drift'i sessizce kabul edecektir — onları bükülmeyen sert anayasal limitlerle katmanla.

**Tür:** Öğrenim
**Diller:** Python (stdlib, üç-detektörlü simülatör: kill switch, circuit breaker, canary)
**Ön koşullar:** Faz 15 · 13 (Cost governor'lar), Faz 15 · 10 (Permission mode'ları)
**Süre:** ~60 dakika

## Sorun

Cost governor'lar (Ders 13) agent'ın neyi harcayabileceğini sınırlar. Agent'ın bütçenin içinde ne yapabileceğini sınırlamazlar. 50 $'lık velocity limit'li bir agent hâlâ bir secret'ı exfiltrate edebilir, yanlış postu yayımlayabilir veya bir kaynağı silebilir — pahalı aksiyon sıkça token'larda ucuz olandır.

Bu ders cost katmanının yanında oturan üç detektörü kapsar:

1. **Kill switch**: agent'ın erişiminin dışında tutulan boolean off-button.
2. **Circuit breaker**: belirli bir yolu duraklatan aksiyon-deseni detektörü.
3. **Canary token**: meşru dokunma nedeni olmayan agent'ın dokunarak kendini açığa çıkaracağı yem.

Üçü de pre-LLM mühendisliktir. Klasik aldatma, rate-limit breaker'lar ve feature-flag kill'leri otonom agent'lardan önce gelir. Yeni olan saldırı yüzeyidir: agent'lar untrusted content okur (Ders 11), kendi memory'lerini edit ederler ve birçok safe-görünen aksiyonu unsafe bir aksiyona besteleyebilirler. Burada adlandırılan detektörler işe yarar çünkü agent'ın kendi raporuna güvenmezler.

## Kavram

### Kill switch'ler

Bir kill switch agent'ın okuduğu ama yazamadığı bir boolean'dır. Uygulama seçenekleri:

- **Yönetilen bir servisteki feature flag.** LaunchDarkly, Statsig, Unleash. Güncellemeler saniyeler içinde yayılır.
- **Agent'ın poll ettiği Redis key.** Basit; agent process'inin her turda kontrol etmesini gerektirir.
- **Object storage'da imzalı config.** Agent boot'ta bir imzayı doğrular; imzasız state'leri reddeder.
- **OS-seviyesi sinyal veya container-lifecycle kill.** Docker `kill`, Kubernetes `kubectl delete pod`, systemd stop.

Doğru bir kill switch'in sahip olduğu özellikler:

- Agent bunu `off`a ayarlayamaz. (Agent'ın credential'larının yazmadığı bir sistemde yaşar.)
- Yalnızca başlangıçta değil, her sonuçlu aksiyonda kontrol edilir.
- Off olduğunda, agent agent'ın ulaşabildiği sistemlere loglama dahil dışarıdan gözlemlenebilir hiçbir şey yapmaz.
- Yeniden etkinleştirmek otomatik bir timeout değil, açık bir insan aksiyonudur.

### Circuit breaker'lar

Bir circuit breaker tüm agent'ı değil belirli bir deseni duraklatır. Klasik şekil (2007 Nygard kitabından, hâlâ güncel):

- **Closed**: aksiyona izin verilir.
- **Open**: aksiyon bloklanır.
- **Half-open**: bir cool-down'dan sonra 1-3 probe denemesine izin verilir (varsayılan 1); başarı breaker'ı kapatır, kalan herhangi bir failure onu yeniden açar.

Agent ile ilgili tetikleyiciler:

- Üst üste beş aynı tool çağrısı (tekrarlı döngü).
- Farklı input'larla aynı tool'da art arda beş failure (sistemik failure).
- Bir eşiğin üstünde tool çağrı oranı (Ders 13 velocity).
- Güven-dışı bir content read'inden sonra çağrılan belirli tool (örn. `file.delete`) (Ders 11).

### Canary token'lar

Canary token'lar (honeytoken da denir) agent'ın asla dokunmaması gereken input'lardır. Erişim alarmdır.

Agent'lar için örnekler:

- Ortamda gerçek ayrıcalık olmayan sahte bir `AWS_SECRET_ACCESS_KEY`. Exfiltration denemeleri anında atfedilebilir.
- Bilinen bir sentinel değerle işaretlenmiş sahte bir database kaydı. Bu kaydın herhangi bir read veya update'i bir uyarı ateşler.
- Workspace'te sahte bir dosya. Bu dosyanın read'leri veya edit'leri şüphelidir.
- Oturum başlangıcında enjekte edilen sahte bir memory girdisi. Daha sonraki bir çıktıda görünürse, memory exfiltrate edilmiştir.

Canary tasarımı workflow'a özgüdür. Agent'ın dokunmak için meşru bir nedeni olan bir canary gürültüdür.

### İstatistiksel ve sert limitler neden katmanlanır

İstatistiksel detektörler (EWMA, CUSUM, tool-çağrı oranlarında z-skor) hareketli bir baseline'a adapte olur. Bu meşru drift için bir özellik ve adversarial drift için bir bug'dır. Sabırlı bir saldırgan baseline'ı hiçbir alarm ateşlenmeyecek kadar yavaş kaydırabilir.

Sert anayasal limitler (Ders 17) bükülmez. Anayasal bir kural olarak "asla `secrets@`'a email atma" daha basittir, audit edilebilir ve yavaş drift ile game edilemez. Katmanlama deseni: istatistiksel detektörler gürültünün çoğunu yakalar, sert limitler detektörün yanından geçen saldırıyı yakalar.

### eBPF datapath redirect ile karantina

Cilium'un eBPF-tabanlı network policy'si kernel katmanında karantinaya alınmış bir pod'un egress'ini forensic bir honeypot'a yeniden yazabilir. Cilium'un kamuya açık benchmark'ları TCP_RR'da milisaniye-altı P99 datapath gecikmesi raporluyor; cluster'ında karantinayı *tetiklemek* için wall-clock bütçesi, bir politika güncellemesinin control plane'inden node'a nasıl yayıldığı tarafından domine edilir (operatör ön-yüklenmiş Kubernetes'te birkaç yüz milisaniye gerçekçi; tail latency cluster boyutuna ve reconcile cadence'ine bağlıdır). Bu sana iki şey verir: agent gerçek bir şey exfiltrate etmez ve agent'ın honeypot içindeki davranışı tamamen gözlemlenir. Canary token ile aynı desen, farklı katman: agent contained iken yapmaya çalıştığı şeyle niyetini açığa çıkarır.

### Hiçbir detektörün yakalamadığı

- **İzin verilen primitif'lerden besteleyen anlamsal saldırılar.** Her bireysel aksiyon her detektörü geçer; kompozisyon problemdir. Bu Ders 10'daki Auto Mode kompozit failure'ıdır.
- **Detektörü payload'ın parçası olarak içeren saldırılar.** Bir agent "eyleme geçmeden önce canary'yi devre dışı bırak" diyen bir sayfa okursa ve agent kapasiteye sahipse, detektör tehlikeye atılmıştır. Canary token'lar agent'ın modifiye edemediği sistemlerde olmalıdır.

## Kullan

`code/main.py` üç detektör boyunca kısa bir agent trajectory'sini simüle eder. Harici bir dict'te tutulan bir kill switch; üst üste beş aynı tool çağrısında trip eden bir circuit breaker; read'i bir uyarı tetikleyen sahte bir canary dosyası. Sentetik bir trajectory besler: meşru aksiyonlar, tekrarlı döngü, canary probe ve agent'ın aksiyonlarının durdurulduğu kill-switch-tetiklenmiş bir senaryo.

## Yayınla

`outputs/skill-tripwire-design.md`, bir agent deployment'ı için önerilen bir detektör yığınını inceler ve boşlukları işaretler (eksik kill switch, eksik canary, çok gevşek circuit breaker eşiği).

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Circuit breaker'ın 5. turda (beşinci aynı çağrı) ve canary'nin 9. turda (sahte-key read'i) ateşlendiğini doğrula.

2. Bir istatistiksel detektör ekle: tool-çağrı oranında EWMA z-skoru. Yavaş drift eden bir trajectory besle ve detektörün asla ateşlenmediğini göster. Şimdi sert bir limit ekle (10 dakikada 50'den fazla tool çağrısı yok) ve sert limitin aynı trajectory'de ateşlendiğini göster.

3. Bir browser agent (Ders 11) için bir canary token seti tasarla. En az üç canary listele ve her birinin neyi tespit edeceğini.

4. Cilium network-policy dokümanlarını oku. Egress-redirect karantina flow'unu somut olarak tarif et: hangi politika seçici, hangi pod, hangi egress yeniden yazımı, hangi uyarı. "Karantinaya karar ver"den "ilk yönlendirilmiş paket"e wall-clock gecikmesini ne yönetir?

5. Kill-switch'lenmiş bir agent için bir yeniden etkinleştirme prosedürü tanımla. Kim yeniden etkinleştirebilir? Ne belgelenmeli? Yeniden etkinleştirme öncesi agent hakkında ne değişmeli?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Kill switch | "Off button" | Agent'ın edit yüzeyinin dışında boolean; her sonuçlu aksiyonda kontrol edilir |
| Circuit breaker | "Desen duraklatma" | Tekrar, failure oranı veya rate-limit'te aksiyon-spesifik trip |
| Canary token | "Honeytoken" | Agent'ın dokunmak için meşru nedeni olmayan yem; erişim uyarı ateşler |
| Honeypot | "Forensic sandbox" | Karantinaya alınmış agent'ın gözlemlendiği yönlendirilmiş trafik / workspace |
| EWMA | "Hareketli ortalama" | Exponentially weighted; drift'e adapte olur (özellik + bug) |
| CUSUM | "Kümülatif toplam" | Baseline'dan sürekli kaymayı tespit eder |
| Sert limit | "Anayasal kural" | Adapte olmaz; geçmiş ne olursa olsun sabit |
| Anayasal limit | "Her zaman-doğru kural" | Ders 17'nin anayasasına bağlı; agent tarafından edit edilemez |

## İleri Okuma

- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — otonom agent'lar için kill-switch ve circuit-breaker çerçevesi.
- [Microsoft Agent Framework — HITL and oversight](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) — üretim governance desenleri.
- [OWASP LLM / Agentic Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — detection-and-response gereksinimleri.
- [Cilium — Network policy and eBPF](https://docs.cilium.io/en/stable/security/network/) — pod-seviyesi egress yönlendirme ve forensic honeypot desenleri.
- [Anthropic — Claude's Constitution (January 2026)](https://www.anthropic.com/news/claudes-constitution) — "anayasal limitler" olarak hardcoded yasaklar.
