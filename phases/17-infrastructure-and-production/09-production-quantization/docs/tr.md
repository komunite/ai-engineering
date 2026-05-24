# Üretim Quantization'ı — AWQ, GPTQ, GGUF K-quant'lar, FP8, MXFP4/NVFP4

> Quantization formatı evrensel bir seçim değil — donanımın, serving motorunun ve iş yükünün fonksiyonu. GGUF Q4_K_M ya da Q5_K_M llama.cpp ve Ollama üzerinden teslim edilerek CPU ve edge'e sahiptir. vLLM içinde aynı base üzerinde multi-LoRA'ya ihtiyacın olduğunda GPTQ kazanır. Marlin-AWQ kernel'leriyle AWQ, 7B sınıfı bir modelde INT4'te en iyi Pass@1 ile ~741 tok/s sunar — 2026 datacenter üretim varsayılanı. FP8 Hopper, Ada ve Blackwell'de orta zemin olarak kalır — neredeyse kayıpsız ve geniş destekli. NVFP4 ve MXFP4 (Blackwell microscaling) agresif ve block başına doğrulama gerektirir. İki tuzak takımları ısırır: kalibrasyon dataset'i deployment alanıyla eşleşmeli ve KV cache ağırlık quantization'ından ayrı — "modelim artık 4 GB" AWQ dersi üretim batch boyutlarında 10-30 GB KV cache'i unutur.

**Tür:** Öğrenim
**Diller:** Python (stdlib, formatlar arasında oyuncak bellek ve throughput karşılaştırması)
**Ön koşullar:** Faz 10 · 13 (Quantization temelleri), Faz 17 · 04 (vLLM Serving İçleri)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Altı üretim quantization formatını ve 2026'daki sweet spot'larını adlandır.
- Donanım (CPU vs GPU, Hopper vs Blackwell), motor (vLLM, TRT-LLM, llama.cpp) ve iş yükü (rutin sohbet, reasoning, multi-LoRA) verildiğinde bir format seç.
- Seçilen bir format için tasarruf edilen ağırlık belleğini ve dokunulmamış kalan KV cache'i hesapla.
- Alan trafiğinde quantized modelleri bozan kalibrasyon-dataset tuzağını adlandır.

## Sorun

Quantization belleği ve HBM bant genişliğini azaltır, ki decode'un tam ihtiyacı bu. FP16 70B model 140 GB ağırlıktır. Ağırlıkları INT4'e (AWQ ya da GPTQ) quantize et ve model 35 GB olur — KV cache için yer ile tek H100'e sığar, ki bu önemli çünkü 2k context'li 128 eşzamanlı sequence'te tek başına KV cache 20-30 GB.

Ama quantization bedava değil. Agresif quantization kaliteyi bozar, özellikle reasoning-ağırlıklı görevlerde. Farklı formatlar farklı motorlarla çalışır. Farklı donanım farklı hassasiyetleri yerel olarak destekler. 2026'nın format hayvanat bahçesi gerçek ve başkasının seçimini kopyalayamazsın — stack'ine göre seçmek zorundasın.

## Kavram

### Altı format

| Format | Bit | Sweet spot | Motorlar |
|--------|------|-----------|---------|
| GGUF Q4_K_M / Q5_K_M | 4-5 | CPU, edge, laptop'lar | llama.cpp, Ollama |
| GPTQ | 4-8 | vLLM'de Multi-LoRA | vLLM, TGI |
| AWQ | 4 | Datacenter GPU üretimi | vLLM (Marlin-AWQ), TGI |
| FP8 | 8 | Hopper/Ada/Blackwell datacenter | vLLM, TRT-LLM, SGLang |
| MXFP4 | 4 | Blackwell multi-user | TRT-LLM |
| NVFP4 | 4 | Blackwell multi-user | TRT-LLM |

### GGUF — CPU/edge varsayılanı

GGUF bir dosya formatı, kendi başına bir quantization şeması değil — K-quant varyantlarını (Q2_K, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K, Q8_0) tek bir container'da paketler. Q4_K_M ve Q5_K_M üretim varsayılanları — 4-5 bit'te BF16'ya yakın kalite. CPU ya da edge serving için en iyi seçim çünkü llama.cpp açık ara en hızlı CPU çıkarım motoru.

vLLM'de throughput cezası: 7B'de ~93 tok/s — format GPU kernel'leri için optimize değil. Deployment hedefi CPU/edge olduğunda GGUF kullan. Aksi takdirde değil.

### GPTQ — vLLM'de multi-LoRA

GPTQ kalibrasyon pass'li bir post-training quantization algoritması. Marlin kernel'leri onu GPU'da hızlı yapar (Marlin-olmayan GPTQ'ya karşı 2.6x speedup). 7B'de ~712 tok/s.

Benzersiz kazanç: GPTQ-Int4 vLLM'de LoRA adapter'larını destekler. Bir base modeli artı 10-50 fine-tuned varyant (her biri LoRA olarak) servis ediyorsan, GPTQ yolun. 2026 başı itibarıyla NVFP4 henüz LoRA desteklemiyor.

### AWQ — datacenter GPU varsayılanı

Activation-aware Weight Quantization. Quantization sırasında ~%1 en-öne-çıkan ağırlığı korur. Marlin-AWQ kernel'leri: naif'e karşı 10.9x speedup. 7B'de ~741 tok/s, INT4 formatları arasında en iyi Pass@1.

Multi-LoRA'ya ihtiyacın yoksa (GPTQ) ya da agresif Blackwell FP4'e (NVFP4) yoksa yeni GPU serving için AWQ seç.

### FP8 — güvenilir orta

8-bit floating point. Neredeyse kayıpsız. Geniş destekli. Hopper Tensor Core'ları FP8'i yerel olarak hızlandırır. Blackwell devralır. FP8 kalitenin pazarlık dışı olduğu (reasoning, tıbbi, kod-üretim) durumlarda 2026 güvenli varsayılanı. Bellek tasarrufları INT4'ün yarısı ama kalite riski çok daha düşük.

### MXFP4 / NVFP4 — Blackwell agresif

Microscaling FP4. Her ağırlık block'unun kendi scale faktörü var. Agresif ama Blackwell Tensor Core'larda donanım-hızlandırılmış. FP8'e karşı token başına byte'ı yarıya indir — Faz 17 · 07'deki ekonomik kazanç.

Uyarılar:
- Henüz LoRA desteği yok (2026 başı).
- Reasoning-ağırlıklı iş yüklerinde görünür kalite düşüşü.
- Model başına eval set'inde doğrula.

### Kalibrasyon tuzağı

AWQ ve GPTQ bir kalibrasyon dataset'i gerektirir — tipik olarak C4 ya da WikiText. Alan modelleri (kod, tıbbi, hukuk) için, genel web metninde kalibre etmek algoritmanın hangi ağırlıkları koruyacağı konusunda yanlış kararlar almasına izin verir. HumanEval'da Pass@1 birkaç puan düşebilir.

Çözüm: alan-içi veride kalibre et. Genelde yüzlerce alan örneği yeterli. Yayınlamadan önce eval set'inde test et.

### KV cache tuzağı

AWQ ağırlıkları 4 bit'e küçültür. KV cache ayrıdır ve FP16/FP8'de kalır. AWQ'lu 70B model için:

- Ağırlıklar: ~35 GB (140 GB'dan INT4).
- 128 eşzamanlı × 2k context'te KV cache: ~20 GB.
- Aktivasyonlar: ~5 GB.
- Toplam: ~60 GB — H100 80GB'a sığar.

Naif "modelimi 4 GB'a quantize ettim" diğer 30-50 GB'ı unutur. HBM'i bütünsel olarak bütçele.

Ayrı olarak, KV cache quantization'ı (FP8 KV ya da INT8 KV) kendi tradeoff'larıyla farklı bir seçim — attention doğruluğunu doğrudan etkiler ve bedava bir kazanç değil.

### AWQ INT4 reasoning için tehlikeli

Chain-of-thought, matematik, uzun context'li kod-üretimi — bunlar agresif quantization'dan görünür şekilde acı çeker. AWQ INT4 MATH'ta ~3-5 puan kaybeder. Reasoning-ağırlıklı iş yükleri için, FP8 ya da BF16 yayınla; bellek maliyetini kabul et.

### 2026 seçim rehberi

- CPU/edge serve: GGUF Q4_K_M. Bitti.
- GPU serve, rutin sohbet, LoRA yok: AWQ.
- GPU serve, multi-LoRA: Marlin'li GPTQ.
- Reasoning iş yükü: FP8.
- Blackwell datacenter, doğrulanmış kalite: NVFP4 + FP8 KV.
- Belirsiz: her aday formatta 1.000 örneklik eval çalıştır.

## Kullan

`code/main.py` bir aralık model boyutu için altı format genelinde bellek ayak izini (ağırlıklar + KV + aktivasyonlar) ve göreli throughput'u hesaplar. KV cache'in nerede domine ettiğini, ağırlık sıkıştırmanın nerede ödediğini ve FP8'in nerede güvenli seçim olduğunu gösterir.

## Yayınla

Bu ders `outputs/skill-quantization-picker.md` üretir. Donanım, model boyutu, iş yükü tipi ve kalite toleransı verildiğinde bir format seçer ve bir kalibrasyon/doğrulama planı üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. 2k context'te 128 eşzamanlı 70B model için, her format için toplam HBM'i hesapla. Hangi format tek H100 80GB'a sığmana izin verir?
2. 7B'lik bir kod modelin var. Bir format seç ve gerekçelendir. Kalite toleransı konusunda yanılıyor olsaydın, kurtarma yolu ne?
3. Bir tıbbi alan modeli için AWQ'yu kalibre etmek için gereken kalibrasyon-dataset boyutunu hesapla. Daha fazla veri neden her zaman daha iyi değil?
4. Marlin-AWQ kernel makalesini ya da release notes'ları oku. AWQ'nun 7B'de 741 tok/s'e ulaşırken ham GPTQ'nun ~712'ye ulaşmasının nedenini üç cümlede açıkla.
5. AWQ ağırlıkları FP8 KV cache ile birleştirmenin KV'yi BF16'da tutmaya karşı ne zaman anlamlı olduğunu açıkla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| GGUF | "llama.cpp formatı" | K-quant varyantlarını paketleyen dosya formatı; CPU/edge varsayılanı |
| Q4_K_M | "Q4 K M" | 4-bit K-quant medium; üretim GGUF varsayılanı |
| GPTQ | "gee pee tee q" | Kalibrasyonlu post-train INT4; vLLM'de LoRA destekler |
| AWQ | "a w q" | Activation-aware INT4; Marlin kernel'leri; INT4'te en iyi Pass@1 |
| Marlin kernel'leri | "hızlı INT4 kernel'leri" | Hopper'da INT4 için custom CUDA kernel'ler; 10x speedup |
| FP8 | "sekiz-bit float" | Hopper/Ada/Blackwell'de güvenli hassasiyet varsayılanı |
| MXFP4 / NVFP4 | "microscaling dört" | Block başına scale faktörlü Blackwell 4-bit FP |
| Kalibrasyon dataset'i | "cal verisi" | Quantization parametrelerini seçmek için kullanılan input metni; alana uymalı |
| KV cache quantization | "KV INT8" | Ağırlıklardan ayrı seçim; attention doğruluğunu etkiler |

## İleri Okuma

- [VRLA Tech — LLM Quantization 2026](https://vrlatech.com/llm-quantization-explained-int4-int8-fp8-awq-and-gptq-in-2026/) — karşılaştırmalı benchmark'lar.
- [Jarvis Labs — vLLM Quantization Complete Guide](https://jarvislabs.ai/blog/vllm-quantization-complete-guide-benchmarks) — format bazında throughput sayıları.
- [PremAI — GGUF vs AWQ vs GPTQ vs bitsandbytes 2026](https://blog.premai.io/llm-quantization-guide-gguf-vs-awq-vs-gptq-vs-bitsandbytes-compared-2026/) — format-bazında seçim.
- [vLLM docs — Quantization](https://docs.vllm.ai/en/latest/features/quantization/index.html) — desteklenen formatlar ve flag'ler.
- [AWQ paper (arXiv:2306.00978)](https://arxiv.org/abs/2306.00978) — orijinal AWQ formülasyonu.
- [GPTQ paper (arXiv:2210.17323)](https://arxiv.org/abs/2210.17323) — orijinal GPTQ formülasyonu.
