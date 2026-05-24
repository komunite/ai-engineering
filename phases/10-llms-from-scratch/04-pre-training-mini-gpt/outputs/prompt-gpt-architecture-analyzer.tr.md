---
name: prompt-gpt-architecture-analyzer
description: Herhangi bir GPT tarzı transformer modelindeki mimari seçimleri analiz et
version: 1.0.0
phase: 10
lesson: 4
tags: [gpt, transformer, architecture, attention, kv-cache, scaling, pre-training]
---

# GPT Mimari Analizörü

Bir teknik rapor, model kartı veya eğitim log'undan GPT tarzı bir modeli değerlendirirken, mimariyi parçalamak ve tasarım takaslarını tespit etmek için bu çerçeveyi kullan.

## Analiz Protokolü

### 1. Parametre Dağılımı Dökümü

Her bileşen için tam parametre sayısını hesapla:

- **Token embedding**: vocab_size x embed_dim
- **Position embedding**: max_seq_len x embed_dim
- **Block başına attention**: 4 x embed_dim x embed_dim (Q, K, V, output projeksiyonları)
- **Block başına FFN**: 2 x embed_dim x ff_dim + embed_dim + ff_dim (iki linear katman + bias'lar)
- **Block başına LayerNorm**: 4 x embed_dim (iki norm, her biri scale + bias ile)
- **Son LayerNorm**: 2 x embed_dim
- **Output head**: vocab_size x embed_dim (token embedding ile weight-tied ise 0)

Tek bir bileşen toplam parametrelerin %40'ını aşıyorsa işaretle. Küçük modellerde embedding matrisi baskın olur. Büyük modellerde attention ve FFN baskın olur.

### 2. Attention Tasarım Analizi

Attention konfigürasyonunu değerlendir:

- **Head boyutu**: embed_dim / num_heads. Standart 64 (GPT-2) veya 128 (Llama 3). 32 altı head başına ifade gücünü sınırlar. 128 üstü çok az faydayla compute israfı yapar.
- **Katman başına head**: Daha fazla head = daha çeşitli attention pattern'leri ama KV cache için daha çok bellek.
- **Grouped Query Attention (GQA)**: Model birden fazla Q head arasında K/V head'leri paylaşıyor mu? Llama 3, 32 Q head için 8 KV head ile GQA kullanır. Bu KV cache'i 4x azaltır.
- **Context length**: Max position embedding'ler. RoPE eğitim uzunluğunun ötesinde extrapolation'a izin verir. Mutlak position embedding'ler vermez.

### 3. Bellek Bütçesi

Modelin maksimum context length'inde çıkarım için:

- **Ağırlıklar (FP16)**: total_params x 2 byte
- **KV Cache (FP16)**: 2 x num_layers x num_kv_heads x head_dim x max_seq_len x 2 byte
- **Aktivasyonlar**: batch_size x seq_len x embed_dim x 2 byte x num_layers (yaklaşık)

KV cache ağırlık belleğini aşarsa işaretle. Bu uzun-context modellerde (128K+) olur ve modelin decode sırasında memory-bound olduğunu gösterir.

### 4. Compute Profili

- **Prefill FLOPS per token**: yaklaşık 2 x total_params (parametre başına bir matmul, forward pass)
- **Decode FLOPS per token**: prefill ile aynı ama tek token üzerinde
- **Prefill darboğazı**: compute-bound (GPU TFLOPS)
- **Decode darboğazı**: memory-bound (GPU bellek bant genişliği)
- **Aritmetik yoğunluk**: erişilen bellek byte başına FLOPS. 100 altı = memory-bound.

### 5. Ölçeklendirme Kararları

Bilinen scaling laws karşısında değerlendir:

- **Chinchilla optimal**: Belirli bir compute bütçesi C için, optimum model boyutu N ve token sayısı D, N ~ D'yi tatmin eder (kabaca eşit ölçeklendirme). 7B model ~140B token'a ihtiyaç duyar.
- **Llama 3 overtrained**: Meta, Llama 3 8B'yi 15T token üzerinde eğitti (100x Chinchilla optimal). Küçük modelleri daha fazla veride aşırı eğitmek, token başına daha iyi çıkarım maliyeti üretir.
- **Width vs depth**: Daha derin modeller (daha çok katman), aynı parametre sayısı için daha geniş modellerden (daha büyük embed_dim) genellikle daha sample-verimlidir.

## Kırmızı Bayraklar

- **FFN oranı 4x değil**: Standart ff_dim = 4 x embed_dim. Llama, SwiGLU ile 8/3 x embed_dim kullanır. Sapmalar gerekçelendirilmeli.
- **Weight tying yok**: vocab_size embed_dim'e göre çok büyük olmadıkça, output head token embedding ile weight paylaşmalı.
- **13B üstü GQA yok**: grouped-query attention olmayan 13B üstü modeller aşırı büyük KV cache'lere sahip olur.
- **Uzun context için RoPE yok**: Mutlak position embedding'ler eğitim uzunluğunun ötesine extrapolate olmaz. 32K+ context hedefleyen modeller rotary embedding kullanmalı.
- **Model boyutu için learning rate fazla yüksek**: Büyük modeller daha düşük peak learning rate'e ihtiyaç duyar. GPT-2 Small 6e-4 kullanır. Llama 3 405B 8e-5 kullanır.

## Çıktı Formatı

1. **Parametre Tablosu**: yüzdelerle bileşen bazlı parametre sayıları
2. **Bellek Bütçesi**: max context length'te ağırlıklar, KV cache ve aktivasyon belleği
3. **Compute Profili**: A100/H100 için prefill ve decode throughput tahminleri
4. **Tasarım Değerlendirmesi**: modelin neyi doğru yaptığı ve neyin standart dışı olduğu
5. **Ölçeklendirme Verdiği**: modelin eğitim verisi için uygun ölçekte olup olmadığı
