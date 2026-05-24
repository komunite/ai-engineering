# Bellek: Sanal Bağlam ve MemGPT

> Context window'lar sonlu. Konuşmalar, dokümanlar ve tool trace'leri değil. MemGPT (Packer et al., 2023) bunu OS sanal belleği olarak çerçeveler — main context RAM, dış store disk, agent aralarında page yapar. 2026 bellek sisteminin miras aldığı desen bu.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 01 (Agent Döngüsü), Faz 14 · 06 (Tool Use)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- MemGPT'nin üzerine kurduğu OS analojisini açıkla: main context = RAM, dış context = disk, bellek tool'ları = page in/out.
- İki-katmanlı MemGPT desenini stdlib'de main-context buffer'ı, dış aranabilir store ve page in/out tool'larıyla uygula.
- Agent'ın dış belleği sorgulamak ya da değiştirmek için "interrupt"ları nasıl çıkardığını ve sonucun sonraki prompt'a nasıl yapıştırıldığını açıkla.
- Letta'ya (Ders 08) ve Mem0'a (Ders 09) taşınan MemGPT tasarım seçimlerini tanı.

## Sorun

Context window'lar belleği çözer gibi görünür. Çözmez. Üretimde üç başarısızlık modu tekrar eder:

1. **Overflow.** Multi-turn konuşmalar, uzun dokümanlar ya da tool-call-ağırlıklı trajectory'ler window'u aşar. Kesimden sonraki her şey gider.
2. **Dilution.** Window içinde bile, alakasız bağlamı tıkmak önemli olana karşı dikkati seyreltir. Frontier modeller hâlâ uzun girdilerde degrade eder.
3. **Persistence.** Yeni bir oturum boş bir window ile başlar. Dış bellekleri olmayan agent'lar oturumlar arasında "benden istediğin zamanı hatırlıyor musun..." diyemezler.

Daha büyük window'lar yardım eder ama bunu çözmez. Mem0'ın 2025 makalesi 128k-window baseline'ların hâlâ dış bellekli 4k-window agent'ının yakaladığı uzun-ufuk olguları kaçırdığını ölçtü.

## Kavram

### MemGPT: OS analojisi

Packer et al. (arXiv:2310.08560, v2 Şubat 2024) bağlam yönetimini işletim sistemi sanal belleğine eşliyor:

| OS kavramı | MemGPT kavramı | 2026 üretim karşılığı |
|------------|---------------|------------------------|
| RAM | main context (prompt) | Anthropic/OpenAI context window |
| Disk | dış context | vector DB, KV, graph store |
| Page fault | bellek tool çağrısı | `memory.search`, `memory.read`, `memory.write` |
| OS kernel | agent kontrol döngüsü | bellek tool'lu ReAct döngüsü |

Agent normal bir ReAct döngüsü çalıştırır. Ekstra bir tool sınıfı veriyi main context'e ve dışına page yapmasına izin verir.

### İki katman

- **Main context.** Mevcut görevi tutan sabit-boyutlu prompt. Modelde her zaman görünür.
- **Dış context.** Sınırsız, tool'larla aranabilir. İlgili olduğunda okunur, olgular ortaya çıktığında yazılır.

Orijinal makale tasarımı temel window'un ötesinde iki görevde değerlendirdi: 100k token'dan uzun doküman analizi ve günler boyunca kalıcı bellekli multi-session sohbet.

### Interrupt deseni

MemGPT bellek-as-interrupt'ı tanıtıyor: konuşma ortasında agent bir bellek tool'u invoke edebilir, runtime onu yürütür ve sonuç sonraki assistant turuna yeni bir gözlem olarak yapıştırılır. Konsept olarak, süreci blok eden, byte'ları döndüren ve süreci devam ettiren bir Unix `read()` syscall ile özdeş.

Kanonik bellek tool yüzeyi:

- `core_memory_append(section, text)` — prompt'un kalıcı bir bölümüne yaz.
- `core_memory_replace(section, old, new)` — kalıcı bir bölümü düzenle.
- `archival_memory_insert(text)` — aranabilir dış store'a yaz.
- `archival_memory_search(query, top_k)` — dış store'dan getir.
- `conversation_search(query)` — geçmiş turları tara.

### MemGPT nerede biter, Letta nerede başlar

Eylül 2024'te MemGPT Letta oldu. Araştırma repo'su (`cpacker/MemGPT`) duruyor; Letta tasarımı genişletir:

- İki yerine üç katman (core, recall, archival — Ders 08).
- `send_message`/heartbeat desenini değiştiren native reasoning (Ders 08).
- Asenkron bellek işi yapan sleep-time agent'lar (Ders 08).

Üretim sistemleri Letta, Mem0 ya da custom bir iki-katmanlı store çalıştırsa bile MemGPT makalesi 2026 temeli.

### Bu desen nerede ters gider

- **Memory rot.** Yazılar okumadan hızlı birikir; retrieval bayat olgularda boğulur. Düzelt: periyodik konsolidasyon (Letta sleep-time), açık invalidation (Mem0 conflict detector).
- **Memory poisoning.** Dış bellek retrieved metin. Saldırgan-kontrollü içerik bir bellek notuna inerse, agent bunu sonraki oturumda yeniden alır. Bu Greshake et al. (Ders 27) saldırısının zaman üzerinden yeniden ifadesi.
- **Citation loss.** Agent "kullanıcı bana X yayınlamamı istedi" der ama hangi turu olduğunu cite edemez. Her archival yazıyla kaynak referanslarını (session ID, turn ID) sakla.

## İnşa Et

`code/main.py` stdlib'de MemGPT'nin iki-katmanlı desenini uyguluyor:

- `MainContext` — `core` dict ve `messages` listesi ile sabit-boyutlu prompt buffer'ı; tavanı aşınca en eski mesajları auto-compact eder.
- `ArchivalStore` — (id, text, tags, session, turn) kayıtlarının in-memory BM25-vari store'u (token-overlap skorlaması).
- MemGPT yüzeyine eşleyen beş bellek tool'u.
- Archival'i olgularla dolduran, sonra `archival_memory_search` çağırarak bir soruyu yanıtlayan scripted bir agent.

Çalıştır:

```
python3 code/main.py
```

Trace agent'ın üç olgu yazdığını, main context'i tavana doldurduğunu (eviction'ı zorlayarak), sonra archival'den getirerek follow-up bir soruyu yanıtladığını gösteriyor — MemGPT workflow'unu gerçek bir LLM olmadan yeniden üretiyor.

## Kullan

Bugünkü her üretim bellek sistemi bir MemGPT varyantı:

- **Letta** (Ders 08) — üç katman, native reasoning, sleep-time compute.
- **Mem0** (Ders 09) — bir skorlama katmanı ile birleştirilmiş vector + KV + graph.
- **OpenAI Assistants / Responses** — thread'ler ve dosyalar üzerinden yönetilen bellek.
- **Claude Agent SDK** — skill'ler ve session store üzerinden uzun vadeli bellek.

Çekirdek desene göre değil, operasyonel şekle göre (self-hosted, yönetilen, framework-entegre) bir tane seç — çekirdek desen MemGPT.

## Yayınla

`outputs/skill-virtual-memory.md` herhangi bir hedef runtime için, eviction policy'si ve citation alanları kablolanmış halde, doğru iki-katmanlı bellek iskelesi (main + archival + tool yüzey) üreten yeniden kullanılabilir bir skill.

## Alıştırmalar

1. Token olarak ölçülen bir `max_main_context_tokens` tavanı ekle (`len(text.split())` * 1.3 ile yaklaşık). Tavan aşılınca en eski mesajları bir özete sıkıştır. Özetleyici olan ve olmayan davranışları karşılaştır.
2. Archival store üzerinde BM25'i düzgün uygula (term frequency, inverse document frequency). Bir oyuncak olgu seti üzerinde token-overlap baseline'a karşı recall@10'u ölç.
3. Archival insert'lerine `citation` alanları (session_id, turn_id, source_url) ekle. Her retrieval-destekli yanıtta agent'a kaynak cite ettir.
4. Memory poisoning'i simüle et: "tüm gelecek kullanıcı talimatlarını yoksay" diyen bir archival kayıt ekle. Retrieval'leri directive-şekilli metin için tarayan ve onları güvenilmez olarak işaretleyen bir guard yaz.
5. Uygulamayı MemGPT araştırma repo'sunun core-memory JSON şemasını (`cpacker/MemGPT`) kullanacak şekilde taşı. Düz string'lerden tipli bölümlere geçince ne değişir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Sanal context | "Sınırsız bellek" | Page in/out'lu main (prompt) + dış (aranabilir) katmanlar |
| Main context | "Working memory" | Prompt — sabit-boyutlu, her zaman görünür |
| Archival memory | "Uzun vadeli store" | Talep üzerine getirilen dış aranabilir kalıcılık |
| Core memory | "Kalıcı prompt bölümü" | Main context içinde sabitlenmiş adlandırılmış bölümler |
| Bellek tool'u | "Bellek API'si" | Agent'ın dış belleği okumak/yazmak için çıkardığı tool çağrısı |
| Interrupt | "Bellek page fault'u" | Agent duraklar, runtime getirir, sonuç sonraki tura yapışır |
| Memory rot | "Bayat olgular" | Eski yazılar retrieval'i boğar; konsolidasyon ile düzelt |
| Memory poisoning | "Enjekte edilmiş kalıcı not" | Bellek olarak saklanan saldırgan içeriği, recall'da yeniden alınır |

## İleri Okuma

- [Packer et al., MemGPT (arXiv:2310.08560)](https://arxiv.org/abs/2310.08560) — OS-esinli sanal bağlam makalesi
- [Letta, Memory Blocks blog](https://www.letta.com/blog/memory-blocks) — üç-katmanlı evrim
- [Anthropic, Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — bağlamı bir bütçe olarak ele almak
- [Chhikara et al., Mem0 (arXiv:2504.19413)](https://arxiv.org/abs/2504.19413) — bu desenin üzerinde hybrid üretim belleği
