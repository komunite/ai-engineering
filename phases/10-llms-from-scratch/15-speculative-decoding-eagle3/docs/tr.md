# Speculative Decoding ve EAGLE-3

> Faz 7 · Ders 16 matematiği kanıtladı: Leviathan rejection kuralı verifier'ın dağılımını tam olarak korur. Bu ders 2026 production speculative decoding'in training-stack görünümüdür. EAGLE-3, draft model'i ucuz bir yaklaşımdan verifier'ın kendi hidden state'leri üzerinde eğitilen amaç-üretimi minik bir ağa dönüştürdü ve sonra train ile inference dağılımlarını hizalayan bir training-time test loop ekledi. Sonuç: 3× ila 6.5× uçtan uca hızlanma, chat'te 0.9 üzerinde kabul edilen-per-token oranları, hiçbir dağılımsal tradeoff yok. 2026'daki her production inference stack varsayılan olarak yayınlar.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 7 · 16 (speculative decoding matematiği), Faz 10 · 12 (inference optimization)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Leviathan teoremini bir cümlede ifade et ve speculative döngünün verifier ile özdeş şekilde dağıtılmış sample'lar ürettiğini kanıtla.
- Vanilla spec-decoding'ten (Leviathan 2023) EAGLE, EAGLE-2 ve EAGLE-3'e iki yıllık ilerlemeyi yürü ve her adımın kaldırdığı tam sınırlamayı adlandır.
- Acceptance rate `α` ve draft-to-verifier maliyet oranı `c` üzerinden beklenen hızlanmayı hesapla ve her rejim için optimal draft uzunluğu `N`'i seç.
- Tam speculative döngüsünü sıfırdan implement et: draft, verify, residual'den reject-sample, reject'te KV cache'i geri al, tam kabulde bonus token yay.

## Sorun

70B model üzerinde autoregressive decoding H100'de saniyede belki 35 token çalışır. GPU doyma yakınında değil. Memory bandwidth tavan: her token HBM'den 70B ağırlık yükler, bir adım aritmetik yapar ve bir float üretir. Compute birimleri çoğunlukla boş oturur.

Speculative decoding bunu aslında çözebileceğin bir throughput problemine çevirir. Ucuz bir draft `N` token'ı `N` küçük forward pass'ta önerir. Verifier prefix artı tüm `N` draft üzerinde bir kez çalışır. Verifier'ın pozisyon `i`'deki dağılımı draft ile (kesin yapacağımız istatistiksel bir anlamda) anlaşırsa, kabul ederiz; değilse, reject eder ve residual dağılımdan bir düzeltme sample eder. Tek bir büyük-model forward bir yerine `N+1`'e kadar kabul edilen token üretir.

Önemli teorem Leviathan, Kalman, Matias (ICML 2023): output dağılımı doğrudan verifier'dan sample etmenin üreteceği ile özdeştir. Yaklaşık değil. Özdeş. Speculative decoding'in production'da kabul edilebilir olmasının tüm nedeni budur — kalite tradeoff'u olmayan saf bir latency optimizasyonudur.

Faz 7 · Ders 16 sana matematiği verdi. Bu ders sana training stack'ini veriyor. İyi bir draft ucuz bir draft'tan 2× daha fazla hızlanma değerinde. EAGLE, EAGLE-2 ve EAGLE-3 (Li et al., 2024-2025) "draft = aynı modelin daha küçük versiyonu"nu kesin bir mühendislik disiplinine çevirdi. 2026 production inference server'ları varsayılan olarak EAGLE-3.

## Kavram

### Değişmez: Leviathan rejection sampling

`p(t)` draft'ın bir prefix verildiğinde sonraki token için dağılımı olsun, `q(t)` verifier'ınki olsun. Bir draft token `d ~ p` sample et. `min(1, q(d) / p(d))` olasılıkla kabul et. Reject'te, residual dağılımdan sample et `(q - p)_+ / ||(q - p)_+||_1`. Elde edilen sample'lar `q`'ya göre dağıtılır. Bu `p` ne kadar kötü olursa olsun doğrudur — daha kötü, daha sık reject edersin, ama output tam kalır.

`prefix + d_1 + ... + d_N` üzerinde tek bir verifier forward pass kullanarak bu çağrılardan `N` tanesini arka arkaya yığ. Verifier `q_1, q_2, ..., q_{N+1}`'i eşzamanlı döner. Soldan sağa yürü. Pozisyon `j`'deki ilk reject'te, `residual(q_j, p_j)`'den sample et ve dur. Tam kabulde, `q_{N+1}`'den bir bonus token sample et.

### Hızlanmayı Ne Belirler

`α` drafted token başına beklenen acceptance rate olsun. `c = cost(draft) / cost(verifier)` maliyet oranı olsun. Verifier forward başına beklenen kabul edilen token sayısı:

```
E[accepted] = (1 - α^(N+1)) / (1 - α)
```

Kabul edilen token başına beklenen toplam wall time `(N * c + 1) / E[accepted]`. Bunu `N`'e göre minimize et ve tatlı noktayı al. `α = 0.8, c = 0.05` için: optimal `N` 5-7 civarında, hızlanma 3.2×. `α = 0.95, c = 0.02` için: optimal `N` 8-10 civarında, hızlanma 5×'i iter.

En büyük tek kaldıraç `α`'dır. Sabit `N = 5`'te `α = 0.6` (vanilla draft)'tan `α = 0.9` (EAGLE-3)'a gitmek seni verifier forward başına 2.2 beklenen kabul edilen token'dan 4.1'e götürür. Aynı verifier'dan neredeyse 2× daha fazla throughput.

### İki Yıllık İlerleme

**Vanilla speculative (Leviathan, 2023).** Draft model aynı aileden bağımsız eğitilmiş daha küçük bir LLM. Wiring up'ı kolay, `α ≈ 0.6`, en iyi ihtimalle 2× hızlanma.

**EAGLE-1 (Li et al., 2024).** Draft minik bir transformer — tipik olarak bir veya iki katman — verifier'ın son-katman hidden state'ini input olarak alır ve sonraki token'ı doğrudan tahmin eder. Draft verifier'ın feature temsilini gördüğü için, dağılımı verifier'ınkine çok daha yakın. `α` 0.7-0.8'e tırmanır.

**EAGLE-2 (Li et al., 2024).** Dinamik bir draft tree ekler: `N` token'lık tek bir sequence önermek yerine, küçük bir aday tree'si öner, her birini bir forward pass'ta verifier ile skorla (tree attention) ve en yüksek-olasılıklı yolu yürü. Draft uzunluğu adım başına adaptif olur. Kabul-edilen-yol token'ı başına `α` 0.85'in üzerine tırmanır.

**EAGLE-3 (Li et al., 2025, NeurIPS).** İki değişiklik daha. Önce, feature-prediction loss'unu tamamen bırak — EAGLE-1/2 draft'ı verifier'ın hidden state'leriyle eşleşmek için eğitiyordu, bu ne kadar veri yardım ettiğini cap'liyor. EAGLE-3 doğrudan token prediction üzerinde eğitir. İkinci olarak, training-time test (TTT): draft eğitimi sırasında, draft'ın kendi önceki tahminlerini birden fazla adım üzerinde input olarak geri besle, inference'ta nasıl çalıştığı şekilde. Bu train ve test dağılımlarını hizalar ve hata birikimini durdurur. Ölçülen hızlanma: chat'te 6.5×'a kadar, H100'de SGLang'da batch 64'te %38 throughput iyileştirmesi.

### KV Cache Rollback

Doğrulama verifier'ın KV cache'ini tek bir pass'ta `N` giriş kadar uzatır. Rejection pozisyon `j`'de olursa, cache içeriği pozisyon `j-1`'den sonrası artık yanlıştır. İki yaygın implementasyon: bir scratch buffer'a yaz ve kabulde commit et (vLLM, TensorRT-LLM) veya fiziksel bir KV cache artı bir mantıksal uzunluk tut ve reject'te truncate et. Her iki şekilde, rollback maliyeti katman başına head başına byte'tır, ki forward-pass maliyetinin yanında ihmal edilebilir.

EAGLE-2 tree search için, verifier tree topolojisine saygılı bir non-causal mask ile attention çalıştırır. Mühendislik karmaşık ama hesaplama özel mask'li standart bir flash-attention çağrısıdır.

### 2026'da Draft Mimarileri

| Strateji | Draft tipi | `α` | Hızlanma | Eğitim maliyeti |
|----------|-----------|-----|---------|---------------|
| Vanilla | Ayrı küçük LLM | 0.55-0.70 | 1.8-2.3× | Yok (mevcut küçük modeli yeniden kullan) |
| Medusa | Verifier üzerinde ekstra LM head'leri | 0.65-0.75 | 2-3× | ~1B SFT token |
| EAGLE-1 | Hidden state'ler üzerinde 1-katmanlı transformer | 0.70-0.80 | 2.5-3× | ~60B token |
| EAGLE-2 | EAGLE-1 + dinamik draft tree | 0.80-0.88 | 3-4× | ~60B token |
| EAGLE-3 | Multi-layer feature fusion + TTT | 0.88-0.92 | 3.5-6.5× | ~60-200B token |
| Lookahead | Draft yok (Jacobi iteration) | N/A | 1.3-1.6× | Yok |

2026 production'da: vLLM ve SGLang EAGLE-3 mevcut olduğunda varsayılan, aksi takdirde EAGLE-2. TensorRT-LLM Meta ve NVIDIA public modelleri için en hızlı Medusa yoluna sahip. llama.cpp CPU deployment'ları için vanilla draft yayınlar.

## İnşa Et

`code/main.py`'a bak. Bu tüm parçalarıyla tam Leviathan speculative döngüsü: draft-of-N, verifier paralel pass, pozisyon başına rejection, residual sampling, bonus token, KV rollback ve output dağılımının `q`'dan doğrudan sample ile eşleştiğinin empirik doğrulaması.

### Adım 1: Rejection Kuralı

```python
def accept(q_prob, p_prob, u):
    if p_prob <= 0:
        return True
    return u < min(1.0, q_prob / p_prob)
```

### Adım 2: Residual Dağılım

```python
def residual(q, p):
    raw = [max(0.0, qi - pi) for qi, pi in zip(q, p)]
    s = sum(raw)
    if s == 0:
        return list(q)
    return [r / s for r in raw]
```

### Adım 3: Tam Bir Speculative Adımı

`spec_step` fonksiyonu `p`'den `N` token draft eder, sonra hepsini bir paralel `q` değerlendirmesinde doğrular. Her drafted token için rejection kuralını uygular ve ilk rejection'da residual'den düzeltmeyi sample eder. Her şey kabul edilirse, `q_{N+1}`'den bir bonus token yayınlar.

### Adım 4: KV Rollback Defter Tutması

Simülatör worker başına mantıksal bir `kv_length` izler. `k` draft kabulünde, `kv_length += k`. Pozisyon `j`'de bir rejection'da, cache zaten `j`'den sonra yazılmıştır, ama mantıksal uzunluk `prefix_length + j + 1`'e ayarlanır — düzeltme token'ından bir sonraya. Sonraki okumalar mantıksal uzunluğa truncate eder.

### Adım 5: Leviathan Kontrolü

50.000 speculative adımı çalıştır. Kabul edilen token'ların empirik dağılımını say. `q`'dan 50.000 doğrudan sample ile karşılaştır. Chi-square istatistik kritik değerin çok altında olmalı. Teorem pratikte geçer.

### Adım 6: Hızlanma vs α

`p`'i farklı genliklerde `q`'dan uzağa perturb ederek draft kalitesini sweep et. `α`'yı ölç, sonra `α` ve `N`'in bir fonksiyonu olarak verifier çağrısı başına beklenen token'ları çiz. Kod EAGLE-3-sınıfı draft kalitesinin (`α ≈ 0.9`) verifier çağrısı başına 4-5 token'ı açtığını gösteren bir tablo yazdırır.

## Kullan

EAGLE-3 ile production-seviyesi `vllm serve`:

```bash
vllm serve meta-llama/Llama-3.3-70B-Instruct \
  --speculative-config '{
    "model": "yuhuili/EAGLE3-LLaMA3.3-Instruct-70B",
    "num_speculative_tokens": 5,
    "method": "eagle3"
  }'
```

H100'de batch 64'te EAGLE-3 ile SGLang: EAGLE-3 makalesine göre batch-64 vanilla decoding'den kabaca 1.38× daha fazla throughput.

Speculative decoding için ne zaman uzanmalı:

- Tepe throughput'tan çok p50 latency'nin önemli olduğu herhangi bir etkileşimli chat workload'u.
- Kod üretimi ve structured output (JSON, SQL). Hedef dağılım son derece tahmin edilebilir olduğu için `α` 0.9'un üzerindedir.
- Uzun-form generation (binlerce token). Amortize edilmiş hızlanma ödemeye devam eder.

Ne zaman değil:

- Çok küçük modeller (< 3B). Draft verifier'dan o kadar ucuz değil.
- Minik batch-1 CPU deployment'ları. Draft model'in memory overhead'i değerli olmayabilir.
- `α`'nın çöktüğü çok-yüksek-temperature yaratıcı sampling.

## Yayınla

Bu ders `outputs/skill-eagle3-tuner.md` üretir. Bir inference workload'u (model, batch size, hedef latency, görev profili) verildiğinde, bir speculative-decoding stratejisi ve ayar parametreleri (draft ailesi, `N`, tree derinliği, temperature-aware switching) önerir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. Leviathan dağılım kontrolündeki chi-square istatistiğinin 50.000 sample'da %95 kritik değerin altında kaldığını doğrula.

2. `α` 0.9'da ve `c` 0.04'te sabit tutulurken `N`'i 1'den 10'a sweep et. Verifier çağrısı başına beklenen token'ları ve token başına gerçek wall time'ı çiz. Wall time'ı minimize eden `N`'i bul. Eğrinin şeklini açıkla.

3. Kodu EAGLE-2 tree search simüle etmek için değiştir: her adımda, draft `[2, 2, 2]` şeklinde bir tree önerir (sekiz aday yol). Verifier bir kez çalışır ve en yüksek-olasılıklı kabul edilen yol kazanır. Yaprak başına `α`'yı ve verifier çağrısı başına toplam token'ları hesapla. Eşdeğer compute'ta linear-chain spec-decoding ile karşılaştır.

4. İki eşzamanlı sequence için batched bir KV rollback simülatörü implement et. Sequence A'nın tüm draft'ları kabul edilir; sequence B pozisyon 2'de reject eder. Doğru `kv_length`'in sequence başına güncellendiğini ve iş israfı olmadığını göster.

5. EAGLE-3 makalesinin Bölüm 4'ünü (Training-Time Test) oku. TTT olmadan naif draft eğitiminin neden exposure bias'tan acı çektiğini ve eğitim sırasında draft'a kendi tahminlerini besletmenin neden düzelttiğini iki cümlede açıkla. Bunu seq2seq'teki scheduled-sampling literatürüne bağla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Leviathan rule | "min(1, q over p)" | `min(1, q(d)/p(d))` olasılıkla Bernoulli accept/reject, rejection'da residual'dan sample ettiğinde verifier dağılımını tam korur |
| Residual distribution | "(q eksi p) artı, normalized" | `(q - p)_+` sıfıra clamp'lenmiş ve renormalized — rejection'da sample edilecek doğru dağılım |
| Acceptance rate α | "draft ne sıklıkla doğru" | Rejection kuralı altında beklenen per-token Bernoulli-başarı olasılığı; tüm hızlanma matematiğini yönetir |
| EAGLE-1 | "hidden-state draft" | Verifier'ın son-katman hidden state'ine koşullu minik transformer draft (Li et al., 2024) |
| EAGLE-2 | "dinamik draft tree" | EAGLE-1 artı tek bir verifier pass'ta tree attention ile skorlanan aday devam tree'si |
| EAGLE-3 | "training-time test" | Feature-prediction loss'unu bırakır, eğitim sırasında draft'a kendi output'larıyla beslenmiş doğrudan token prediction üzerinde eğitir |
| Training-time test (TTT) | "exposure bias düzeltmesi" | Eğitim sırasında draft'ı autoregressive çalıştır böylece train ve test input dağılımları eşleşir — scheduled sampling'in doğrudan analogu |
| KV rollback | "reject edilen draft'ları geri al" | Rejection sonrası verifier'ın KV cache'ini kabul edilen-prefix uzunluğuna sıfırlayan defter tutması |
| Bonus token | "ücretsiz olan" | Tüm `N` draft kabul edildiğinde, ek bir verifier maliyeti olmadan `q_{N+1}`'den bir ekstra sample et |
| Tree attention | "birçok adayı bir kerede doğrula" | Bir draft tree'sinin topolojisine saygılı non-causal mask'li attention; tree'deki her node için `q_i`'yi tek bir forward pass'ta hesaplar |

## İleri Okuma

- [Leviathan, Kalman, Matias -- Fast Inference from Transformers via Speculative Decoding (arXiv:2211.17192, ICML 2023)](https://arxiv.org/abs/2211.17192) -- temel makale ve eşdeğerlik teoremi
- [Chen et al. -- Accelerating Large Language Model Decoding with Speculative Sampling (arXiv:2302.01318)](https://arxiv.org/abs/2302.01318) -- temiz bir kanıtla eşzamanlı bağımsız tanıtım
- [Li et al. -- EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty (arXiv:2401.15077)](https://arxiv.org/abs/2401.15077) -- EAGLE-1, hidden-state-koşullu draft
- [Li et al. -- EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees (arXiv:2406.16858)](https://arxiv.org/abs/2406.16858) -- dinamik tree search
- [Li et al. -- EAGLE-3: Scaling up Inference Acceleration via Training-Time Test (arXiv:2503.01840, NeurIPS 2025)](https://arxiv.org/abs/2503.01840) -- 2026 production varsayılanı
- [Cai et al. -- Medusa: Multiple Decoding Heads (arXiv:2401.10774)](https://arxiv.org/abs/2401.10774) -- alternatif draft-free yaklaşım
- [vLLM Speculative Decoding documentation](https://docs.vllm.ai/en/latest/features/spec_decode.html) -- tüm stratejilerin wire'lı olduğu standart production referansı
