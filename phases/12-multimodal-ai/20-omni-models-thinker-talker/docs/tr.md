# Omni Modeller: Qwen2.5-Omni ve Thinker-Talker Bölünmesi

> GPT-4o'nun Mayıs 2024 ürün demosu yıkıcıydı, altta yatan model yüzünden değil ürün biçimi yüzünden — konuştuğun, modelin kameranın gördüğünü gördüğü ve 250ms altında geri konuştuğu bir ses arayüzü. Açık ekosistem 2024'ün ve 2025'in geri kalanını o ürün yüzeyine ulaşmak için yarışarak geçirdi. Qwen2.5-Omni (Mart 2025) referans açık tasarım: bir Thinker (büyük metin üreten transformer) artı bir Talker (paralel konuşma üreten transformer), streaming konuşma token'ları ile bağlı. Mini-Omni basitleştirdi, Moshi latency'sini eşledi, GLM-4-Voice Çince'ye genişletti. Bu ders Thinker-Talker mimarisini ve streaming gerçek zamanlı diyaloğun çalışmasını sağlayan latency bütçesini okur.

**Tür:** Yapım
**Diller:** Python (stdlib, streaming pipeline latency simülatörü + VAD döngüsü)
**Ön koşullar:** Faz 12 · 19 (audio-LLM'ler), Faz 12 · 16 (any-to-any)
**Süre:** ~180 dakika

## Öğrenme Hedefleri

- Çıkarım pipeline'ını Thinker (metin akıl yürütmesi) ve Talker (konuşma sentezi) olarak böl ve paralel streaming'in neden çalıştığını açıkla.
- Bir conversational etkileşim için bileşen-bileşen time-to-first-audio-byte (TTFAB) bütçesini hesapla.
- TMRoPE'nin Thinker içinde vision, audio ve metin boyunca zaman-hizalı pozisyon kodlamasını betimle.
- Üç gerçek zamanlı conversational kalıbı söyle: half-duplex, turn-taking, full-duplex.

## Sorun

Gerçek zamanlı bir ses asistanının çok şey yapması, hızlı, gerekir:

1. Kullanıcıyı duy. Gerçek zamanlı konuşma tokenization, konuşmanın bittiğini bilmek için voice activity detection (VAD).
2. Opsiyonel olarak gör. 2-4 FPS'te kamera input'u, ses yanında Thinker'a stream edilir.
3. Düşün. Konuşma geçmişine koşullu bir yanıt oluştur.
4. Konuş. Ses token'larını sentezle, waveform'a decode et, user'ın hoparlörlerine stream et.

Her adım latency ekler. Conversational-his toplam round-trip < 500ms gerektiriyor — bunun altında user gecikmeyi fark etmemeye başlıyor. GPT-4o ~250ms iddia ediyor. Moshi ~160ms. Qwen2.5-Omni ~350-500ms.

Her bileşenin stream etmesi gerekir. Hiçbir şey "her şeyi batch'le sonra decode et" olamaz.

## Kavram

### Thinker ve Talker

Qwen2.5-Omni'nin ayrıştırması:

- Thinker: 7B-80B metin üreten transformer. Interleaved metin + görsel + ses token'ları tüketir. Ne söyleyeceğini temsil eden metin token'ları çıkarır.
- Talker: daha küçük bir konuşma üreten transformer (200M-1B). Thinker'ın metin çıkış token'ları artı son konuşma-context token'larını tüketir. Ayrık konuşma token'ları (residual-VQ indeksleri) çıkarır.
- Konuşma decoder: konuşma token'larını gerçek zamanda ses örneklerine çeviren bir streaming waveform decoder (SNAC, MoVQGAN ailesi).

Ayrım önemli. Thinker iyi akıl yürütme için büyük olmak zorunda. Talker küçük olabilir çünkü işi yerel — metni konuşma token'larına çevir. Daha büyük Talker daha ifade edici değil; daha yavaş.

İkisini paralel çalıştırma:

1. Thinker metin token'ı t_i yayar.
2. Talker (streaming üzerinden) t_i'yi tüketir ve konuşma token'ları s_i, s_{i+1}, ..., s_{i+k} yayar.
3. Konuşma decoder geldikçe konuşma token'larını tüketir ve ses örnekleri yayar.
4. Thinker metin token'ı t_{i+3}'te olduğunda, Talker zaten t_0..t_{i+2} için ses stream etmiş olur.

### TMRoPE — zaman-hizalı multimodal pozisyonlar

Thinker görsel frame'leri (mesela 4 FPS'te gelen), ses frame'leri (50 frame/saniye'de gelen) ve konuşma geçmişinden metni entegre etmesi gerekiyor. Naif bir dizi sırası (tüm görseller, sonra tüm ses, sonra metin) temporal hizalamayı kaybeder.

TMRoPE her token'a mutlak timestamp atar. t=2.3s'de vision token. t=2.32s'de ses token. user'dan "dur" t=2.35s'de metin token. RoPE attention'ı timestamp'e göre döndürür; model onları temporally eş zamanlı görür.

Bu "merhaba derken el salladı"nın çalışması için altyapı — model video frame'i ve sesi aynı kavramsal anda görür.

### Streaming konuşma sentezi

Konuşma token'ları stream etmeli. Mini-Omni (Xie & Wu, 2024) "dil modelleri streaming'de düşünürken duyabilir, konuşabilir"i tanıttı: Thinker çıkış token'ları ve Talker çıkış token'ları aynı dizide interleave eder. Talker Thinker bir sonraki metin token'ını commit eder etmez ateşler. Batch sınırı yok.

Moshi (Défossez et al., Ekim 2024) en hızlı açık implementasyon. Tek A100'de 160ms TTFAB. Mimari: değişen pozisyonlarda metin ve konuşma token'ları yayan tek 7B transformer, dikkatli eğitimle düşünme akışını konuşma akışından ayıran bir "inner monologue" ile. Bu efektif olarak Thinker + Talker'ı dikkatli eğitimle tek modele birleştirir.

### VAD ve turn-taking

Voice activity detection input tarafında çalışır. İki kalıp:

- Half-duplex: user konuşur, model dinler. Model konuşur, user dinler. VAD sessizlik tespiti ile net handoff (~200ms).
- Full-duplex: ikisi de eş zamanlı konuşabilir. Model backchannel yapabilir ("hı-hı") ya da bölebilir. Çok daha zor. Moshi bunu destekler.

Qwen2.5-Omni varsayılan olarak half-duplex destekler, sessizlik eşiği üzerinden turn-taking ile. Full-duplex uygulama-katmanı ele alma gerektirir.

### Qwen3-Omni (Kasım 2025)

Halefi. Qwen3-80B Thinker, daha büyük Talker, geliştirilmiş TMRoPE-v2. Latency GPT-4o'nun 250ms'sine yakın. Açık ağırlık. OmniBench'te benchmark'lar Gemini 2.0 Live ile rekabetçi.

### Üretim latency bütçesi

Tipik streaming etkileşim için:

- Mikrofon -> ses token: 40-80ms.
- Prefill (prompt + geçmiş): 7B'de 100-200ms, 70B'de çok daha fazla.
- İlk Thinker metin token'ı: 40ms.
- Talker ilk metin token'ını işler: 20ms.
- İlk konuşma token'ları commit eder: 40ms.
- Residual-VQ decode: 30ms.
- Konuşma waveform decode: 50-80ms.

Toplam TTFAB: 7B'de 320-510ms, 70B'de 600-900ms. Frontier kalitesi genellikle 70B+ anlamına geliyor; bu yüzden frontier latency farkı.

### Token oranı matematiği

50 Hz base konuşma token'lı 16kHz konuşmada çıkış saniye başına 50 konuşma token'ına ihtiyacın var. Talker'ın ayak uyduracak şekilde ≥50 tok/s yayması gerekir. H100'de 30-80 tok/s tipik LLM throughput'unda küçük (200-300M) bir Talker yeterince hızlı; 7B Talker geride kalır.

Bu yüzden "sadece ana modeli kullan" yerine küçük adanmış Talker modelleri var.

## Kullan

`code/main.py`:

- Mock token-yayım oranları ile bir Thinker-Talker pipeline'ı simüle eder.
- Konfigüre edilebilir model boyutları ve mikrofon örnekleme oranları için TTFAB hesaplar.
- VAD sessizlik eşiği ile half-duplex turn-taking gösterir.

## Yayınla

Bu ders `outputs/skill-omni-streaming-budget.md` üretir. Gerçek zamanlı ses ürününün hedef TTFAB'ı ve feature seti (vision-in, iki dilli, full-duplex) verildiğinde, Qwen2.5-Omni, Qwen3-Omni, Moshi ya da Mini-Omni seçer ve Thinker/Talker boyutlandırır.

## Alıştırmalar

1. Hedef TTFAB 300ms. 7B Thinker ve 300M Talker'da, her bileşenin latency'sini yaz.

2. Qwen2.5-Omni TMRoPE kullanır. user'ın t=1s'de konuşmaya başladığı ve kameranın t=1.2s'de bir jest yakaladığı bir prompt için modelin ne gördüğünü betimle.

3. Full-duplex desteği modelin dinlerken ses yaymasını gerektirir. Bunu öğreten bir eğitim veri formatı öner.

4. Moshi'nin makalesi Bölüm 4'ü oku. "Inner monologue" ayrımını ve neden Thinker-Talker bölünmesinden kaçındığını betimle.

5. Throughput bütçesi hesapla: 50 base-katman token/s'de 16kHz konuşmaya ayak uyduracak şekilde Talker'ın token yayma hızı ne kadar olmalı?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|------------------------|
| Thinker | "Akıl yürütme beyni" | Ne söyleyeceğini üreten büyük metin üreten transformer |
| Talker | "Konuşma üreten ağız" | Thinker'ın metninden ayrık konuşma token'ları üreten küçük transformer |
| TTFAB | "Latency bütçesi" | Time-to-first-audio-byte: user konuşma sonundan ilk ses örneği çıkışına kadar |
| TMRoPE | "Zaman-hizalı RoPE" | Vision, ses, metin boyunca mutlak timestamp'ler kullanan pozisyon kodlaması |
| Half-duplex | "Turn-taking" | User ve model değişir; VAD sessizlik user-done'u tespit eder |
| Full-duplex | "Eş zamanlı" | Model aynı anda konuşabilir ve dinleyebilir; backchannel yetenekli |
| Inner monologue | "Moshi ayrımı" | Düşünme-akışının ve konuşma-akışının interleave ettiği tek-model tasarımı |

## İleri Okuma

- [Xu et al. — Qwen2.5-Omni (arXiv:2503.20215)](https://arxiv.org/abs/2503.20215)
- [Qwen Team — Qwen3-Omni (arXiv:2509.17765)](https://arxiv.org/html/2509.17765v1)
- [Xie & Wu — Mini-Omni (arXiv:2408.16725)](https://arxiv.org/abs/2408.16725)
- [Défossez et al. — Moshi (arXiv:2410.00037)](https://arxiv.org/abs/2410.00037)
- [Zeng et al. — GLM-4-Voice (arXiv:2412.02612)](https://arxiv.org/abs/2412.02612)
