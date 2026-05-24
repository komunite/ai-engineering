---
name: skill-latency-profiler
description: Warmup, senkronizasyon, percentile'lar ve bellek izleme ile tam bir latency-benchmark scripti yaz
version: 1.0.0
phase: 4
lesson: 15
tags: [edge, deployment, profiling, benchmarking]
---

# Latency Profiler

Herhangi bir PyTorch modeli için disiplinli bir latency benchmark üret. Aşağı akıştaki herkesin gerçekten güvenebileceği raporlar.

## Ne zaman kullan

- Deploy etmek için seçmeden önce birden çok aday backbone'u karşılaştırırken.
- Quantisation ya da pruning öncesi ve sonrası.
- Bir runtime değişiminden sonra (eager vs ONNX vs TensorRT).
- Bir deployment-readiness raporu üretirken.

## Girdiler

- `model`: PyTorch `nn.Module`.
- `input_shape`: `(1, 3, 224, 224)` gibi tuple.
- `device`: `cpu` | `cuda` | `mps`.
- `warmup`: varsayılan 10.
- `iters`: varsayılan 100.

## Kontroller

### 1. Warmup
Modeli zamanlamadan `warmup` kere çalıştır. İlk forward JIT derlemesini ve cold cache etkilerini yakalar.

### 2. Senkronizasyon
`cuda` için, her zamanlanmış forward pass öncesi ve sonrası `torch.cuda.synchronize()` çağır.
`mps` için, `torch.mps.synchronize()` çağır.

### 3. Timer
Wall-clock ölçümü için `time.perf_counter()` kullan. Milisaniyeye çevir.

### 4. Percentile'lar
Tam zamanlama listesini sırala. `p50, p90, p95, p99, mean, std` raporla.

### 5. Bellek
`cuda` için, çalışmadan sonra `torch.cuda.max_memory_allocated()` çağır ve baseline'ı çıkar.
`cpu` için, öncesi ve sonrası `tracemalloc` ya da `psutil.Process().memory_info().rss` kullan.

### 6. Batch size sweep
Throughput vs latency tradeoff'larını ortaya çıkarmak için opsiyonel olarak `batch_size in [1, 4, 16, 32]` için benchmark'ı tekrarla.

## Çıktı şablonu

```python
import time
import torch
import psutil, os

def profile(model, input_shape, device="cpu", warmup=10, iters=100):
    proc = psutil.Process(os.getpid())
    baseline_rss = proc.memory_info().rss / 1e6

    model = model.to(device).eval()
    x = torch.randn(input_shape, device=device)

    def sync():
        if device == "cuda":
            torch.cuda.synchronize()
        elif device == "mps":
            torch.mps.synchronize()

    with torch.no_grad():
        for _ in range(warmup):
            model(x)
        sync()
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()

        times = []
        for _ in range(iters):
            sync()
            t0 = time.perf_counter()
            model(x)
            sync()
            times.append((time.perf_counter() - t0) * 1000)

    times.sort()
    mean = sum(times) / len(times)
    std  = (sum((t - mean) ** 2 for t in times) / len(times)) ** 0.5

    def pct(p):
        idx = max(0, min(len(times) - 1, int(len(times) * p) - 1))
        return times[idx]

    report = {
        "p50_ms":  pct(0.50),
        "p90_ms":  pct(0.90),
        "p95_ms":  pct(0.95),
        "p99_ms":  pct(0.99),
        "mean_ms": mean,
        "std_ms":  std,
        "rss_mb":  proc.memory_info().rss / 1e6 - baseline_rss,
    }
    if device == "cuda":
        report["peak_cuda_mb"] = torch.cuda.max_memory_allocated() / 1e6

    return report
```

## Kurallar

- Her zaman warmup çalıştır; ilk forward zamanlamasına asla güvenme.
- Ortalama değil, percentile'lar — tek bir outlier ortalamayı iki katına çıkarır ama p50'yi neredeyse hiç oynatmaz.
- Production ile aynı input_shape'i kullan; 224x224'teki latency 384x384 latency'si değil.
- CUDA için, `torch.cuda.synchronize()` asla atlama; bu olmadan sayılar anlamsız.
- torch versiyonu, CUDA versiyonu ve cihaz adını sayıların yanında logla — aksi halde karşılaştırılabilir olmayı bırakırlar.
