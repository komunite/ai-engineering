# Group Chat ve Speaker Selection

> AutoGen GroupChat ve AG2 GroupChat N agent arasında tek bir konuşmayı paylaşır; bir selector fonksiyonu (LLM, round-robin ya da custom) sıradakinin kim konuşacağını seçer. Bu, ortaya çıkan çoklu-agent konuşmasının prototipidir — agent'lar statik bir grafta rollerini bilmez, sadece paylaşılan havuza tepki verirler. AutoGen v0.2'nin GroupChat semantiği AG2 fork'unda korundu; AutoGen v0.4 onu event-driven bir actor modeli olarak yeniden yazdı. Microsoft AutoGen'i Şubat 2026'da bakım moduna aldı ve onu Semantic Kernel ile birleştirerek Microsoft Agent Framework'e (RC Şubat 2026) dönüştürdü. GroupChat primitive'i hem AG2'de hem Microsoft Agent Framework'te hayatta kalır — bir kez öğren, her yerde kullan.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 04 (Primitive Model)
**Süre:** ~60 dakika

## Sorun

Statik graflar (LangGraph) iş akışı bilindiğinde harikadır. Gerçek konuşmalar statik değildir: bazen kodcu inceleyiciye, bazen araştırmacıya, bazen yazara sorar. Olası her handoff'u sabit kodlamak bir edge patlaması üretir. *Agent'ların paylaşılan bir havuza tepki vermesini*, sıradakinin kimin konuşacağına karar veren bir fonksiyonla istiyorsun.

İşte AutoGen GroupChat tam olarak bunu yapıyor.

## Kavram

### Şekil

```
              ┌─── paylaşılan havuz ────┐
              │   m1  m2  m3  ...        │
              └──────────┬───────────────┘
                         │ (herkes hepsini okur)
      ┌───────┬─────────┼─────────┬───────┐
      ▼       ▼         ▼         ▼       ▼
    Agent A  Agent B  Agent C  Agent D  Selector
                                           │
                                           ▼
                                  "sıradaki konuşmacı = C"
```

Her agent her mesajı görür. Her turda sıradakinin kim konuşacağını seçmek için bir selector fonksiyonu çağrılır.

### Üç selector çeşidi

**Round-robin.** Sabit döngü. Deterministik. N'de doğrusal ölçeklenir ama context'i yok sayar — konu hukuk incelemesi olduğunda bile kodcu turunu alır.

**LLM-seçili.** Son havuzu okuyan ve en iyi sıradaki konuşmacıyı döndüren bir LLM çağrısı. Context-bilinçli ama yavaş: her tur bir LLM çağrısı ekler. AutoGen'in varsayılanı.

**Custom.** İstediğin mantıkla bir Python fonksiyonu. Tipik: fallback kurallarıyla LLM-seçili (ör. "her zaman kodcudan sonra verifier'a turu ver").

### ConversableAgent API'si

```
agent = ConversableAgent(
    name="coder",
    system_message="You write Python.",
    llm_config={...},
)
chat = GroupChat(agents=[coder, reviewer, tester], messages=[])
manager = GroupChatManager(groupchat=chat, llm_config={...})
```

`GroupChatManager` selector'ı tutar. Bir agent bir turu tamamladığında, manager selector'ı çağırır, o da sıradaki agent'ı döndürür. Bir sonlandırma koşuluna kadar döngü devam eder.

### Sonlandırma

Üç yaygın desen:

- **Maks tur.** Toplam tur üzerinde sert sınır.
- **"TERMINATE" token'ı.** Agent'lar bir sentinel mesaj yayabilir; manager biri göründüğünde durur.
- **Hedef-ulaşıldı kontrolü.** Her tur hafif bir verifier çalışır ve bittiğinde chat'i durdurur.

### AutoGen → AG2 bölünmesi ve Microsoft Agent Framework birleşmesi

2025 başlarında Microsoft AutoGen'in (v0.4) event-driven bir actor modeli etrafında büyük bir yeniden yazımına başladı. Topluluk AutoGen v0.2'nin GroupChat semantiğini AG2 olarak fork'ladı, erken benimseyenlerin entegre ettiği API'yi korudu.

Şubat 2026'da Microsoft AutoGen'in bakım moduna geçeceğini ve event-driven actor modelinin **Microsoft Agent Framework**'e (RC Şubat 2026, şimdi Semantic Kernel ile birleştirildi) birleşeceğini duyurdu. GroupChat kavramı her iki yolda da hayatta kalır; uygulama detayları farklıdır. AG2, v0.2-uyumlu kod için tercih edilen upstream'dir.

### GroupChat ne zaman uyar

- **Ortaya çıkan konuşmalar.** Olası her sıradaki-konuşmacıyı önceden kablolamak istemiyorsun.
- **Rol-karıştırma görevleri.** Kodcu araştırmacıya sorar, araştırmacı arşivciye sorar, arşivci kodcuya geri sorar. Akış bir DAG değil.
- **Keşifçi problem-çözme.** "Beyin fırtınası toplantısı" düşün, "montaj hattı" değil.

### Ne zaman başarısız olur

- **Katı determinizm.** LLM selector tutarsız olabilir. Aynı prompt, farklı çalıştırmalar, farklı sıradaki konuşmacılar.
- **Yalakalık kaskadları.** Agent'lar en kendine güvenle konuşana saygı gösterir. Açıkça karşı-prompt yap.
- **Context şişmesi.** Her agent her mesajı okur; 10 turdan sonra context devasa. Görünümleri kapsamak için projeksiyonları (Ders 15) kullan.
- **Sıcak konuşmacılar.** Bir agent konuşmaya hakim olur çünkü selector onun uzmanlıklarını tercih eder. Konuşmacı dengesini selector özelliği olarak tanıt.

### Group chat vs supervisor

Aynı primitive'ler, farklı varsayılanlar:

- Supervisor: bir agent planlar ve diğerleri yürütür. Selector "planner'a ne yapmasını sor"dur.
- Group chat: tüm agent'lar peer'dir; selector paylaşılan havuz üzerinde bir fonksiyondur.

İkisi de Ders 04'ten dört primitive kullanır. Group chat varsayılan olarak LLM-seçili orkestrasyon ve tam-havuz paylaşılan state'tir.

## İnşa Et

`code/main.py` stdlib'de sıfırdan bir GroupChat uygular. Üç agent (coder, reviewer, manager), round-robin ve LLM-seçili varyantlar ve `TERMINATE` token'ında sonlandırma.

Demo konuşma transkriptini artı her iki varyant için selector'ın karar izini yazar.

Çalıştır:

```
python3 code/main.py
```

## Kullan

`outputs/skill-groupchat-selector.md` belirli bir görev için bir GroupChat selector'ı yapılandırır — round-robin vs LLM-seçili vs custom ve hangi selector girdilerinin (son mesajlar, agent uzmanlıkları, tur sayıları) kullanılacağı.

## Yayınla

Kontrol listesi:

- **Maks tur sınırı.** Her zaman. Tipik görevler için 10-20.
- **Konuşmacı-denge metriği.** Agent başına turları izle; dengesizlik bir eşiği aştığında alarm.
- **Sonlandırma token'ı.** `TERMINATE` ya da özel bir verifier agent.
- **Projeksiyon ya da kapsamlı bellek.** ~10 mesajdan sonra, context şişmesini önlemek için her agent'a yalnızca kapsamlı bir görünüm vermeyi düşün.
- **Selector log'lama.** LLM-seçili varyantlar için hem selector'ın girdisini hem de seçimini log'la. Aksi takdirde hata ayıklama imkansız.

## Alıştırmalar

1. `code/main.py`'yi çalıştır. Konuşmayı round-robin vs LLM-seçili altında karşılaştır. Her birinde hangi agent baskın?
2. Selector'a bir "agent başına maks konuşma" kuralı ekle. Transkripti nasıl etkiler?
3. Bir hedef-ulaşıldı sonlandırması uygula: inceleyici "onaylandı" döndürdüğünde dur. Tur sınırından önce ne sıklıkla tetikleniyor?
4. GroupChat hakkında AutoGen stable dokümanlarını oku (https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/group-chat.html). `GroupChatManager` tarafından kullanılan varsayılan selector'ı belirle.
5. AG2 repo'sunu (https://github.com/ag2ai/ag2) oku ve v0.2 GroupChat'i v0.4 event-driven versiyonuyla karşılaştır. v0.4 hangi somut özelliği (throughput, hata-toleransı, composability) ekler?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| GroupChat | "Tek chat odasındaki agent'lar" | Paylaşılan mesaj havuzu + selector fonksiyonu. AutoGen / AG2 primitive. |
| Speaker selection | "Sıradaki kim konuşacak" | Sıradaki agent'ı seçen fonksiyon. Round-robin, LLM-seçili ya da custom. |
| GroupChatManager | "Toplantı sahibi" | Selector'a sahip olan ve turlar üzerinde döngü yapan AutoGen bileşeni. |
| ConversableAgent | "Temel agent" | AutoGen temel sınıfı; mesaj gönderip alabilen bir agent. |
| Sonlandırma token'ı | "'Dur' kelimesi" | Chat'i sonlandıran sentinel string (genellikle `TERMINATE`). |
| Sıcak konuşmacı | "Bir agent baskın" | Selector'ın aynı agent'ı seçmeye devam ettiği başarısızlık modu. |
| Context şişmesi | "Havuz sınırsız büyür" | Her agent önceki her mesajı okur; context turlarla büyür. |
| Projeksiyon | "Kapsamlı görünüm" | Context şişmesini önlemek için paylaşılan havuza rol-özgü görünüm. |

## İleri Okuma

- [AutoGen group chat docs](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/group-chat.html) — referans implementasyon
- [AG2 repo](https://github.com/ag2ai/ag2) — topluluk AutoGen v0.2 devamı
- [Microsoft Agent Framework docs](https://microsoft.github.io/agent-framework/) — birleşik halef, RC Şubat 2026
- [AutoGen v0.4 release notes](https://microsoft.github.io/autogen/stable/) — event-driven actor modeli yeniden yazım detayları
