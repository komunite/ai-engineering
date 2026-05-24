# Handoff'lar ve Routine'lar — Stateless Orkestrasyon

> OpenAI Swarm (Ekim 2024) çoklu-agent orkestrasyonunu iki primitive'e indirgedi: **routine'lar** (sistem prompt'u olarak instructions + tool'lar) ve **handoff'lar** (başka bir Agent döndüren tool). State machine yok, branching DSL yok — LLM doğru handoff tool'unu çağırarak yönlendirir. OpenAI Agents SDK (Mart 2025) üretim haleftir. Swarm'ın kendisi en temiz kavramsal referans olarak kalır — tüm kaynağı birkaç yüz satıra sığar. Desen viraldir çünkü API yüzeyi kabaca "agent = prompt + tool'lar; handoff = agent döndüren fonksiyon"dur. Sınırlama: stateless, dolayısıyla bellek arayanın sorunudur.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 04 (Primitive Model)
**Süre:** ~60 dakika

## Sorun

Her çoklu-agent framework'ü sana DSL'ini öğretmek ister: LangGraph node ve edge'ler, CrewAI crew ve task'lar, AutoGen GroupChat ve manager'lar. DSL'ler gerçek soyutlamalardır ama olması gerekenden ağır hissettirirler.

Swarm tam tersi yöne iter: modelin zaten sahip olduğu tool-calling yeteneğini kullan. Handoff'lar tool çağrılarına dönüşür. Orchestrator şu anda konuşmayı tutan hangi agent ise odur. State machine agent'ların sistem prompt'larında örtüktür.

## Kavram

### İki primitive

**Routine.** Bir agent'ın rolünü ve mevcut tool'larını tanımlayan sistem prompt'u. Kapsamlı bir talimat seti gibi düşün: "sen bir triage agent'sın; kullanıcı refund hakkında sorarsa, refund agent'ına handoff yap."

**Handoff.** Agent'ın çağırabileceği ve yeni bir Agent nesnesi döndüren bir tool. Swarm runtime'ı Agent return değerini tespit eder ve aktif agent'ı bir sonraki tur için değiştirir.

Tüm soyutlama bu.

```
def transfer_to_refunds():
    return refund_agent  # Swarm Agent return görür → aktif agent değiştir

triage_agent = Agent(
    name="triage",
    instructions="Route the user to the right specialist.",
    functions=[transfer_to_refunds, transfer_to_sales, transfer_to_support],
)
```

Triage agent'ın sistem prompt'u kullanıcı mesajına göre doğru handoff'u seçmesini sağlar. LLM'in tool-calling'i yönlendirmeyi yapar.

### Neden viral

- **Küçük API.** Öğrenilecek iki kavram.
- **Modelin zaten yaptığını kullanır.** Tool calling sağlayıcılar arasında zaten üretim seviyesindedir.
- **State-machine yükü yok.** Grafı tanımlamazsın; agent'ların prompt'ları kime handoff yaptıklarını tanımlar.

### Stateless takası

Swarm çalıştırmalar arasında açıkça stateless'tir. Framework bir çalıştırma sırasında mesaj geçmişini tutar ama hiçbir şeyi kalıcılaştırmaz. Bellek, süreklilik, uzun süreli görevler — hepsi arayanın sorunu.

Üretimde (OpenAI Agents SDK, Mart 2025) değişen ana şeylerden biri buydu: SDK, handoff primitive'ini korurken yerleşik session yönetimi, guardrail'ler ve tracing ekler.

### Swarm/handoff'lar ne zaman uyar

- **Triage desenleri.** Ön cephe agent kullanıcıyı uzmana yönlendirir.
- **Skill-tabanlı handoff'lar.** "Görev kod gerektiriyorsa, kodcuyu çağır; araştırma gerektiriyorsa, araştırmacıyı çağır."
- **Kısa, sınırlı konuşmalar.** Müşteri desteği, FAQ-to-ticket, basit iş akışları.

### Swarm ne zaman zorlanır

- **Paylaşılan bellekle uzun oturumlar.** Handoff'lar konuşma state'ini yeni agent'ın prompt'u artı geçmişe sıfırlar. Arayan-yönetilen bellek olmadan agent'lar arası kalıcı state yok.
- **Paralel yürütme.** Handoff tek seferde birdir — aktif agent değişir. Paralelizm arayanın birden çok Swarm çalıştırmasını orkestre etmesini gerektirir.
- **Audit ve replay.** Stateless çalıştırmalar tam olarak replay'i zordur; LLM'in handoff seçimi deterministik değildir.

### OpenAI Agents SDK (Mart 2025)

Üretim haleftin eklediği:

- **Session state.** Çalıştırmalar arası kalıcı thread.
- **Guardrail'ler.** Input/output doğrulama hook'ları.
- **Tracing.** Her tool çağrısı ve handoff log'lanır.
- **Handoff filtreleri.** Handoff'ta hangi context'in transfer olacağını kontrol et.

Handoff primitive'i hayatta kalır; üretim ergonomisi etrafına eklenir.

### Swarm vs GroupChat

İkisi de LLM-driven yönlendirme kullanır ama **sıradakini kimin seçtiğinde** farklılaşırlar:

- GroupChat: bir selector (fonksiyon ya da LLM) dışarıdan sıradaki konuşmacıyı seçer.
- Swarm: mevcut agent bir handoff tool'unu çağırarak haleflerini seçer.

Swarm "agent sıradakini seçer"dir; GroupChat "manager sıradakini seçer"dir. Swarm'ın kararı aktif agent'ın tool çağrısında yaşar; GroupChat'in kararı `GroupChatManager`'da yaşar.

## İnşa Et

`code/main.py` Swarm'ı sıfırdan uygular: bir Agent dataclass, bir handoff mekanizması (tool Agent döndürür) ve agent değişimlerini tespit eden bir run loop.

Demo: bir triage agent refund, sales ya da support uzmanlarına yönlendirir. Her uzmanın kendi tool'ları vardır. Run loop her handoff'u yazar.

Çalıştır:

```
python3 code/main.py
```

## Kullan

`outputs/skill-handoff-designer.md` belirli bir görev için bir handoff topolojisi tasarlar: hangi agent'ların var olduğu, hangi handoff'ları çağırabilecekleri, hangi context'in transfer olduğu.

## Yayınla

Kontrol listesi:

- **Handoff log'lama.** Her handoff from-agent, to-agent, context anlık görüntüsüyle bir trace event yazar.
- **Context transfer kuralları.** Handoff'ta neyin hareket ettiğine karar ver: tam geçmiş (pahalı), son N mesaj ya da özet.
- **Handoff'ta guardrail.** Farklı tool izinlerine sahip bir uzmana handoff doğrulanmalı — aksi takdirde prompt injection istenmeyen handoff'ları zorlayabilir.
- **Döngü tespiti.** İki agent'ın birbirine geri handoff yapması yaygın bir başarısızlıktır; basit bir last-K ring kontrolüyle tespit et.
- **Fallback agent.** Bir handoff hedefi yoksa, güvenli bir varsayılana geri dön.

## Alıştırmalar

1. `code/main.py`'yi çalıştır, refund agent'a triage. İkinci turun aktif agent'ının refund olduğunu doğrula.
2. Bir döngü-tespit kuralı ekle: aynı iki agent art arda 3 kez handoff yaptıysa, bir çıkış zorla. Fallback'i tasarla.
3. Handoff filtreleri hakkında OpenAI Agents SDK dokümanlarını oku. Bir "summarize-on-handoff" versiyonu uygula: gelen agent devraldıkça giden agent context'i bir madde özetine sıkıştırır.
4. Swarm handoff'unu bir GroupChatManager selector'ına karşılaştır. Hangi desen prompt injection'ı daha kötü yapar ve neden?
5. Swarm cookbook'unu (https://developers.openai.com/cookbook/examples/orchestrating_agents) oku. Swarm'ın OpenAI Agents SDK'nın değiştirdiği ya da koruduğu açık bir tasarım kararını belirle.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Routine | "Agent prompt'u" | Sistem prompt'u + tool listesi. Rolü ve mevcut handoff'ları tanımlar. |
| Handoff | "Başka bir agent'a transfer" | Aktif agent'ın çağırabileceği ve yeni bir Agent döndüren bir tool. Runtime aktif agent'ı değiştirir. |
| Stateless | "Çalıştırmalar arasında bellek yok" | Swarm hiçbir şeyi kalıcılaştırmaz; bellek arayanın sorumluluğu. |
| Aktif agent | "Şimdi kim konuşuyor" | Şu anda konuşmayı tutan agent. Handoff bunu değiştirir. |
| Context transfer | "Handoff'ta ne hareket eder" | Gelen agent'ın gördüğü geçmiş için politika: tam, son N ya da özetlenmiş. |
| Handoff döngüsü | "Agent'lar ping-pong oynar" | İki agent'ın birbirine geri handoff yapmaya devam ettiği başarısızlık modu. |
| OpenAI Agents SDK | "Üretim Swarm'ı" | Mart 2025 haleft; handoff primitive'inin üzerine session'lar, guardrail'ler, tracing ekler. |
| Handoff filtresi | "Transferde geçit" | Handoff sınırında context'i denetlemek ve değiştirmek için SDK özelliği. |

## İleri Okuma

- [OpenAI cookbook — Orchestrating Agents: Routines and Handoffs](https://developers.openai.com/cookbook/examples/orchestrating_agents) — referans ifade
- [OpenAI Swarm repo](https://github.com/openai/swarm) — orijinal implementasyon, kavramsal referans olarak korunuyor
- [OpenAI Agents SDK docs](https://openai.github.io/openai-agents-python/) — session'lar ve tracing ile üretim haleft
- [Anthropic handoff-in-Claude notes](https://docs.anthropic.com/en/docs/claude-code) — Claude Code subagent'larının `Task` üzerinden handoff-benzeri bir deseni nasıl kullandığı
