# Prefix-Ağırlıklı İş Yükleri için SGLang ve RadixAttention

> SGLang KV cache'i radix tree'de saklanan first-class, yeniden kullanılabilir bir kaynak olarak ele alır. vLLM istekleri FCFS (first-come, first-served) ile schedule ederken, SGLang'in cache-aware scheduler'ı daha uzun paylaşılan prefix'lere sahip istekleri önceliklendirir — efektif olarak depth-first bir radix gezintisi, böylece sıcak dallar HBM'de kalır. Llama 3.1 8B'de ShareGPT-benzeri 1K prompt'larda SGLang ~16.200 tok/s'e ulaşırken vLLM ~12.500'de, ~%29 avantaj. Prefix-ağırlıklı RAG iş yüklerinde avantaj 6.4x'e ulaşıyor. Voice-cloning-şekilli iş yüklerinde cache hit oranı %86'yı geçti. 2026'da xAI, LinkedIn, Cursor, Oracle, GCP, Azure, AWS genelinde 400.000+ GPU'ya deploy edildi. Püf nokta: prefix sıralaması tutarsızsa 6.4x sayısı buharlaşır — sıralama mühendisin levyesi.

**Tür:** Öğrenim
**Diller:** Python (stdlib, oyuncak radix-tree cache + cache-aware scheduler)
**Ön koşullar:** Faz 17 · 04 (vLLM Serving İçleri), Faz 14 (Agentic RAG)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- RadixAttention'ı diyagramla: prefix'ler bir radix tree'de nasıl saklanır ve KV block'lar aynı dala kök salan sequence'ler arasında nasıl paylaşılır.
- Cache-aware scheduling'i açıkla ve prefix-ağırlıklı trafik için FCFS'in neden yanlış olduğunu söyle.
- Prefix-cache hit oranı ve prompt uzunluk dağılımı verildiğinde bir iş yükü için beklenen speedup'ı hesapla.
- 6.4x sayısını gerçek yapan ya da kayıp avantaj yapan prompt-sıralama disiplinini adlandır.

## Sorun

Klasik serving her isteğin prompt'unu opak olarak ele alır. 5.000 RAG isteğinin hepsi aynı 2.000-token'lık system prompt artı aynı retrieval preamble ile başlasa bile, vLLM o 2.000-token'lık prefix'i 5.000 kez prefill eder. GPU aynı işi tekrar tekrar yapar.

Gözlem: agentic ve RAG iş yüklerindeki prompt'lar neredeyse her zaman uzun prefix'leri paylaşır. System prompt, tool şemaları, few-shot örnekler, retrieval header'ları, sohbet geçmişi — hepsi istekler arasında tekrarlanır. O prefix için KV cache'i bir kez saklayıp yeniden kullansaydın, onu tekrar prefill etmeyecektin.

RadixAttention tam olarak bunu yapar. Token'lar bir radix tree'de indekslenir; her node kökten kendisine giden yoldaki token sequence için KV block'lara sahiptir. Yeni bir istek ağaçta yürür: token'ı eşleşen herhangi bir node o node'un KV block'larını yeniden kullanır. Prefill maliyeti tam prompt'a değil, "yeni" suffix'e orantılı olur.

Zorluk scheduling. İki istek 2.000-token'lık bir prefix paylaşıyor ve üçüncüsü aynı prefix'in yalnızca 200 token'ını paylaşıyorsa, uzun prefix'in HBM'de kalması için uzun-paylaşılan iki isteği birlikte servis etmek istersin. FCFS tam tersini yapar — ilk gelene servis verir, sonraki uzun-prefix isteği gelmeden önce sıcak dalı potansiyel olarak tahliye eder.

## Kavram

### KV indeksi olarak radix tree

Bir radix tree (kompakt trie) token sequence'lerini saklar. Her node bir token aralığına ve o aralık için hesaplanan KV block'lara sahiptir. Çocuklar sequence'i bir ya da daha fazla token uzatır.

```
root
 |- "You are a helpful assistant..."  (2.000 token, 124 KV block)
      |- "Context: <doc A>..."        (500 token, 31 block)
           |- "Question: Alice..."    (80 token, 5 block)
           |- "Question: Bob..."      (95 token, 6 block)
      |- "Context: <doc B>..."        (520 token, 33 block)
```

Yeni bir istek system prompt + "Context: <doc A>" + "Question: Carol" ile gelir. Scheduler yürür: system prefix eşleşir (124 block yeniden kullanılır), doc-A dalı eşleşir (31 block yeniden kullanılır), sonra yalnızca "Question: Carol" için taze block'lar tahsis edilir (4 block). Prefill maliyeti: 4 block yeni token. Ağaç olmadan: 160 block. Prefill'de ~40x tasarruf.

### Cache-aware scheduling

Cache kömürleşirse radix-tree-destekli yeniden kullanım anlamsızdır. İki anahtar politika:

1. **Depth-first dispatch**. Queue'dan bir sonraki isteği seçerken, çalışan kümeyle aynı dalda kök salan istekleri tercih et. Bu sıcak dalı sabit tutar.
2. **Block seviyesinde değil, dal seviyesinde LRU**. Bireysel block'lardan ziyade bütün dalları (en kısa-kullanılan yapraklardan başlayarak) tahliye et, böylece cache şekli radix şekliyle eşleşir.

FCFS ikisini de ihlal eder. 2.000 token paylaşan bir istek 50 paylaşanın arkasında oturur, sonra 2.000-token'lık dal 50-token'lığı kabul etmek için tahliye edilir.

### Ezberlemen gereken benchmark sayıları

- Llama 3.1 8B, H100, ShareGPT 1K prompt'lar: SGLang ~16.200 tok/s vs vLLM ~12.500 (~%29 avantaj).
- Prefix-ağırlıklı RAG (aynı system + aynı doc, değişen soru): SGLang'de 6.4x'e kadar.
- Voice cloning iş yükleri: %86.4 prefix-cache hit oranı.
- SGLang müşterilerinde üretim hit oranları: prompt disiplinine bağlı olarak %50-99.
- 2026'da 400.000+ GPU'ya deploy edildi.

### Sıralama sürprizi

6.4x sayısı tutarlı prompt-template sıralamasına dayanır. Client'ın prompt'ları bazı isteklerde `[system, tools, context, history, question]` ve diğerlerinde `[system, context, tools, history, question]` olarak inşa ediyorsa, ağaç paylaşılan prefix'i bulamaz. Bir insana paylaşılan prefix gibi görünen şey radix ağacına iki farklı sequence'tir.

Mühendisin levyesi: prompt template'in bir cache anahtarı. Sırayı sabitle. Değişmez olan her şeyi (system, tool'lar, şemalar) önce koy. Retrieval context'i sonra koy. Kullanıcı sorusunu en sona koy. Cache'lenebilir prefix'e dinamik içerik araya katma.

Araştırmadan gerçek bir vaka: dinamik içeriği cache'lenebilir prefix'ten çıkarmak bir deployment'ı tek bir değişiklikle %7'den %74 cache hit oranına çıkardı.

### RadixAttention nerede kazanır ve kaybeder

Kazanır:
- RAG (aynı retrieval preamble, değişen soru).
- Agent'lar (aynı tool şemaları, değişen sorgu).
- Uzun system prompt'lu sohbet.
- Tekrarlanan preamble'lı voice / vision iş yükleri.

Kaybeder (vLLM-seviye throughput'a döner):
- Benzersiz prompt'larla tek-atış üretim (kod tamamlama, system prompt olmadan açık-uçlu sohbet).
- Her isteğin benzersiz içeriği prefix'e araya kattığı dinamik prompt'lar.

### Bu neden yalnızca bir kernel sorunu değil, bir scheduler sorunu

KV yeniden kullanımı bir kernel hilesi olarak uygulayabilirsin. SGLang'in iç görüsü, yeniden kullanım yalnızca scheduler sıcak dalı resident tutarsa öder. Naif bir "mümkünse yeniden kullan" politikası karma yük altında cache'i kömürleştirir. Kernel hilesini %29 üretim avantajına çeviren şey radix-tree-indeksli scheduler.

### vLLM ile etkileşim

İki sistem katı rakipler değil. 2026'da vLLM prefix caching (`--enable-prefix-caching`) ve cache-aware bir router (Rust'ta vLLM Router) ekledi. Fark kapandı ama tamamen kaybolmadı — SGLang'in tüm stack'i radix-öncelikli; vLLM onu üzerine ekledi. Prefix yeniden kullanımının domine ettiği iş yükleri için SGLang varsayılan olarak kalır. Güçlü prefix desenleri olmayan genel-amaçlı serving için vLLM eşit ya da daha iyi kalır.

## Kullan

`code/main.py` bir oyuncak radix-tree KV cache artı iki politikalı bir scheduler uygular: FCFS ve cache-aware. Aynı iş yükünü her ikisinden çalıştırır, prefix-cache hit oranı ve throughput delta'yı raporlar. Sonra 6.4x'in çöküşünü göstermek için bir "scrambled ordering" iş yükü çalıştırır.

## Yayınla

Bu ders `outputs/skill-radix-scheduler-advisor.md` üretir. Bir iş yükü tanımı verildiğinde (prompt-template şekli, retrieval deseni, eşzamanlı tenant sayısı), bir prompt-sıralama reçetesi ve SGLang benimsemesi için go/no-go üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Aynı iş yükünde FCFS ve cache-aware'ı karşılaştır. Delta nereden geliyor — prefill tasarrufu, decode tasarrufu ya da queue gecikmesi?
2. İş yükünü prompt'ları rastgele `[system, tools, context]` olarak permüte edecek şekilde modifiye et. Yeniden çalıştır. Hit oranına ne oluyor? Neden?
3. Llama 3.1 8B'de 2.000-token'lık bir system prompt'u tek bir radix dalı olarak resident tutmanın HBM maliyetini hesapla. Prefix yeniden kullanımı olmadan 16-sequence batch'in maliyetiyle karşılaştır.
4. SGLang RadixAttention makalesini oku. Prefix-ağırlıklı yük altında neden tree-şekilli LRU tahliyesinin block-şekilli LRU'yu yendiğini üç cümleyle açıkla.
5. Bir müşteri yalnızca %8 cache hit oranı bildiriyor. Üç olası sebep adlandır ve her biri için çalıştıracağın teşhisi söyle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| RadixAttention | "SGLang şeyi" | Paylaşılan prefix'lerin block'ları yeniden kullanması için radix tree olarak indekslenmiş KV cache |
| Radix tree | "kompakt trie" | Her node'un bir token aralığına ve KV block'larına sahip olduğu ağaç |
| Cache-aware scheduler | "sıcak-dal-önce" | Resident dalı paylaşan istekleri tercih eden scheduler |
| Prefix-cache hit oranı | "prompt'unun ne kadarı bedavaydı" | Yeniden kullanılan KV block'lardan servis edilen prompt token'larının fraksiyonu |
| FCFS | "first-come first-served" | Prefix yerelliğini bozan varsayılan scheduling |
| Dal-seviyesi LRU | "yaprağı tahliye et" | Radix şekliyle eşleşen tahliye politikası |
| Prompt template sıralaması | "cache anahtarı" | Prompt'un bileşen sırası ağacın neyi paylaşabileceğini belirler |
| System prompt pinning | "resident prefix" | Tahliye thrash'inden kaçınmak için değişmez system bölümünü pin'le |

## İleri Okuma

- [SGLang GitHub](https://github.com/sgl-project/sglang) — kaynak ve dokümanlar.
- [SGLang documentation](https://sgl-project.github.io/) — RadixAttention ve scheduling detayları.
- [SGLang paper — Efficiently Programming Large Language Models (arXiv:2312.07104)](https://arxiv.org/abs/2312.07104) — tasarım referansı.
- [LMSYS blog — SGLang with RadixAttention](https://www.lmsys.org/blog/2024-01-17-sglang/) — benchmark sayıları ve scheduler gerekçesi.
- [vLLM — Prefix Caching](https://docs.vllm.ai/en/latest/features/prefix_caching.html) — karşılaştırma için vLLM'in kendi radix-benzeri uygulaması.
