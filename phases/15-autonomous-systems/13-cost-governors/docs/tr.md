# Aksiyon Bütçeleri, Iterasyon Tavanları ve Cost Governor'lar

> Orta ölçekli bir e-ticaret agent'ının aylık LLM maliyeti, takımı "sipariş izleme" skill'ini etkinleştirdikten sonra 1.200 dolardan 4.800 dolara sıçradı. Bu bir fiyatlandırma bug'ı değil. Bu yeni bir döngü bulan ve içinde harcamaya devam eden bir agent. Microsoft'un Agent Governance Toolkit'i (2 Nisan 2026) bu sınıfa karşı savunmayı kodlar: request başına `max_tokens`, görev başına token ve dolar bütçeleri, gün/ay başına tavanlar, iterasyon tavanları, katmanlı model routing, prompt caching, context windowing, pahalı aksiyonlarda HITL checkpoint'leri, bütçe ihlalinde kill switch'ler. Anthropic'in Claude Code Agent SDK'sı aynı primitif'leri farklı adlarla yayınlar. Finansal velocity limit'leri — örn. 10 dakikada >50 $'da erişimi kes — döngüleri aylık tavanlardan daha hızlı yakalar.

**Tür:** Öğrenim
**Diller:** Python (stdlib, katmanlı cost-governor simülatörü)
**Ön koşullar:** Faz 15 · 10 (Permission mode'ları), Faz 15 · 12 (Durable execution)
**Süre:** ~60 dakika

## Sorun

Otonom agent'lar her turda gerçek para harcar. Bir chatbot'un kötü çıktısı kötü bir cevaptır; bir agent'ın kötü döngüsü bir faturadır. Failure mode için endüstri-belgelenmiş terim "Denial of Wallet"tır — agent akıl yürütmeye devam eder, tool-çağırmaya devam eder, fatura etmeye devam eder ve hiçbir şey onu durdurmaz çünkü hiçbir şey öyle tasarlanmamıştır.

Düzeltme tek bir sayı değil. Farklı zaman ölçeklerinde ve granülariteler de bir limit yığınıdır: request başına, görev başına, saat başına, gün başına, ay başına. İyi tasarlanmış bir yığın bir runaway döngüsünü dakikalar içinde, yavaş bir sızıntıyı saatler içinde ve kötü bir release'i bir gün içinde yakalar. Aynı yığın agent uzun-horizon ve otonom olduğunda bütçeyi tutar.

Bu bir mühendislik dersi: matematik trivial'dir, disiplin takımların başarısız olduğu yerdir. Aşağıdaki limit listesi ya Microsoft Agent Governance Toolkit'inde ya da Anthropic Claude Code Agent SDK dokümanlarında adlandırılmıştır.

## Kavram

### Cost-governor yığını

1. **Request başına `max_tokens`.** Basit. Herhangi bir tek çağrının sınırsız completion yayımlamasını önler.
2. **Görev başına token bütçesi.** Tüm koşu boyunca N token'ı aşma. Tavanda sert durdurma.
3. **Görev başına dolar bütçesi.** Token'larla aynı ama para birimi cinsinden. Claude Code'da `max_budget_usd`.
4. **Tool başına çağrı tavanı.** N'den fazla `WebFetch` çağrısı yok, N `shell_exec` çağrısı, vb.
5. **Iterasyon tavanı (`max_turns`).** Toplam agent döngüsü iterasyonu; sonsuz akıl yürütme döngülerini önler.
6. **Dakika / saat / gün / ay başına tavan.** Rolling window'lar. Farklı zaman ölçeklerinde sızıntıları yakalar.
7. **Finansal velocity limit.** Örn. "harcama 10 dakikada 50 $'ı aşarsa erişimi kes." Aylık tavanlar ateşlemeden önce döngü-tabanlı yanmayı yakalar.
8. **Katmanlı model routing.** Varsayılan olarak daha küçük bir model; yalnızca bir classifier görevin gerektirdiğine karar verdiğinde daha büyük olana yükselt.
9. **Prompt caching.** Sistem prompt'u ve kararlı context sağlayıcı cache'inde depolanır; yeniden gönderme token maliyeti sıfıra yakındır.
10. **Context windowing.** Aktif context'i bir eşiğin altında tutmak için sıkıştırma / özetleme; doğrudan token-maliyeti azaltma.
11. **Pahalı aksiyonlarda HITL checkpoint'leri.** Pahalı olduğu bilinen bir aksiyondan önce (uzun tool çağrısı, büyük indirme, pahalı bir model yükseltmesi) insan tap'i gerektir.
12. **Bütçe ihlalinde kill switch.** Herhangi bir tavan ateşlendiğinde oturum iptal olur. Tavan kaydedilir; ayrı bir yeniden etkinleştirme yolu gerektirir.

### Tek bir tavan değil, yığın neden

Tek bir aylık tavan, runaway bir agent'ı yalnızca cüzdan gittikten sonra yakalar. Tek bir request başına tavan oturum seviyesinde hiçbir şey yakalamaz. Farklı failure mode'lar farklı zaman ölçekleri gerektirir:

- **Runaway döngü** (agent 5 saniyelik retry'da sıkışmış): velocity limit ile yakalanır.
- **Yavaş sızıntı** (agent görev başına ~2x beklenen iş yapıyor): günlük tavan ile yakalanır.
- **Kötü release** (yeni versiyon 5x token kullanır): haftalık / aylık tavan ile yakalanır.
- **Meşru sıçrama** (gerçek talep, bug değil): net log'lu saat / gün tavanı ile yakalanır.

### Claude Code'un bütçe yüzeyi

Claude Code Agent SDK açığa çıkarır (kamuya açık dokümanlar):

- `max_turns` — iterasyon tavanı.
- `max_budget_usd` — dolar tavanı; ihlalde oturum iptal olur.
- `allowed_tools` / `disallowed_tools` — tool allowlist ve denylist.
- Özel cost-accounting için tool kullanımından önce hook noktaları.

Permission-mode merdiveniyle (Ders 10) birleştir. `max_budget_usd`'siz bir `autoMode` oturumu yönetilmemiş otonomidir. Anthropic Auto Mode'u açıkça bütçe kontrolleri gerektirdiği şekilde çerçeveler; classifier maliyetle orthogonal'dır.

### EU AI Act, OWASP Agentic Top 10

Microsoft'un Agent Governance Toolkit'i OWASP Agentic Top 10'u ve EU AI Act Madde 14 (human oversight) gereksinimlerini kapsar. EU'da üretim için, logging ve tavan zorlanması opsiyonel değil.

### Gözlemlenen 1.200 $ → 4.800 $ vakası

Microsoft dokümanlarındaki gerçek vaka: aylık maliyeti yeni bir tool eklendikten sonra üçe katlanan bir e-ticaret agent'ı. Tool agent'a her oturumda sipariş durumunu poll etmesine izin verdi. Döngü tespiti yok. Tool başına tavan yok. Hafta-üzerine-hafta büyümede uyarı yok. Düzeltme tool başına bir tavan artı günlük-büyüme uyarısıydı. Bu bir template'tir: her yeni tool yüzeyi yeni bir potansiyel döngüdür; her yeni tool kendi tavanına ve kendi uyarısına ihtiyaç duyar.

## Kullan

`code/main.py` katmanlı bir cost-governor yığını ile ve olmadan bir agent koşusunu simüle eder. Simüle edilen agent bazı turlardan sonra bir polling döngüsüne drift eder; katmanlı yığın bunu velocity penceresi içinde yakalarken tek bir aylık tavan günler sonra ateşlemez.

## Yayınla

`outputs/skill-agent-budget-audit.md`, önerilen bir agent deployment'ının cost-governor yığınını audit eder ve eksik katmanları işaretler.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Velocity limit'in polling-döngüsü trajectory'sinde iterasyon tavanından önce ateşlendiğini doğrula. Şimdi velocity limit'i devre dışı bırak ve iterasyon tavanı yakalayana kadar agent'ın ne kadar "harcadığını" ölç.

2. Bir browser agent için (Ders 11) tool başına bir tavan seti tasarla. Hangi tool en sıkı tavana ihtiyaç duyar? Hangi tool risk olmadan sınırsız çalışabilir?

3. Microsoft Agent Governance Toolkit dokümanlarını oku. Toolkit'in adlandırdığı her tavan tipini listele. Her birini failure mode'lardan birine (runaway döngü, yavaş sızıntı, kötü release, sıçrama) eşleştir.

4. Gerçekçi bir görev (örn. "bir repo'da 50 issue'yu triage et") için gece bir gözetimsiz koşunun fiyatını belirle. `max_budget_usd`'i nokta tahmininin 2x'inde ayarla. 2x'i gerekçelendir.

5. Claude Code'un `max_budget_usd`'i oturum toplam maliyetinde ateşlenir. Harici olarak zorlayacağın tamamlayıcı bir velocity limit tasarla. Kesme noktasını ne tetikler ve yeniden etkinleştirme nasıl görünür?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|---|---|---|
| Denial of Wallet | "Runaway fatura" | Onu durdurmak için tavansız harcama üreten agent döngüsü |
| max_tokens | "Request başına tavan" | Tek bir completion'ın boyutuna tavan |
| max_turns | "Iterasyon tavanı" | Bir oturumda agent döngüsü iterasyonuna tavan |
| max_budget_usd | "Dolar kill switch" | Oturum maliyet tavanı; ihlalde iptal eder |
| Velocity limit | "Oran tavanı" | Kısa pencere başına harcama limiti (örn. 50 $ / 10 dk) |
| Katmanlı routing | "Önce küçük model" | Ucuz model varsayılan; yalnızca classifier gerektirdiğinde yükselt |
| Prompt caching | "Cache'lenmiş sistem prompt'u" | Sağlayıcı tarafı cache yeniden gönderme token maliyetini sıfıra yakın azaltır |
| HITL checkpoint | "İnsan onay gate'i" | Pahalı aksiyondan önce gerekli insan tap'i |

## İleri Okuma

- [Anthropic Claude Code Agent SDK — agent loop and budgets](https://code.claude.com/docs/en/agent-sdk/agent-loop) — `max_turns`, `max_budget_usd`, tool allowlist'leri.
- [Microsoft Agent Framework — human-in-the-loop and governance](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) — cost-governor checkpoint'leri.
- [Anthropic — Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) — sağlayıcı-tarafı maliyet kontrolleri.
- [Anthropic — Prompt caching (Claude API docs)](https://platform.claude.com/docs/en/prompt-caching) — caching mekanikleri.
- [Anthropic — Measuring agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) — uzun-horizon agent'lar için maliyet profili.
