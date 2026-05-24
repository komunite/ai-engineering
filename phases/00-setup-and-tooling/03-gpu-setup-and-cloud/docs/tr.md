# GPU Kurulumu & Bulut

> CPU'da eğitim öğrenmek için tamam. Gerçek eğitim için GPU lazım.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 0, Ders 01
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- `nvidia-smi` ve PyTorch'un CUDA API'si ile yerel GPU varlığını doğrula
- Ücretsiz bulut deneyleri için Google Colab'i T4 GPU ile yapılandır
- CPU vs GPU'da matris çarpımı için benchmark çalıştır ve hızlanmayı ölç
- fp16 kural-i kaidesini kullanarak VRAM'ine sığacak en büyük modeli tahmin et

## Sorun

Faz 1-3'teki derslerin çoğu CPU'da rahat çalışır. Ama CNN, transformer veya LLM eğitmeye başladığında (Faz 4+) GPU hızlandırması lazım. CPU'da 8 saat süren bir eğitim koşusu GPU'da 10 dakika sürer.

Üç seçeneğin var: yerel GPU, bulut GPU veya Google Colab (ücretsiz).

## Kavram

```
Seçeneklerin:

1. Yerel NVIDIA GPU
   Maliyet: $0 (zaten sende var)
   Kurulum: CUDA + cuDNN kur
   En iyi: Düzenli kullanım, büyük veri setleri

2. Google Colab (ücretsiz tier)
   Maliyet: $0
   Kurulum: Yok
   En iyi: Hızlı deneyler, evde GPU yok

3. Bulut GPU (Lambda, RunPod, Vast.ai)
   Maliyet: $0.20-2.00/saat
   Kurulum: SSH + install
   En iyi: Ciddi eğitim, büyük modeller
```

## İnşa Et

### Seçenek 1: Yerel NVIDIA GPU

Var mı diye kontrol et:

```bash
nvidia-smi
```

PyTorch'u CUDA ile kur:

```python
import torch

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

### Seçenek 2: Google Colab

1. [colab.research.google.com](https://colab.research.google.com) adresine git
2. Runtime > Change runtime type > T4 GPU
3. Doğrulamak için `!nvidia-smi` çalıştır

Bu kursun notebook'larını doğrudan Colab'e yükleyebilirsin.

### Seçenek 3: Bulut GPU

Lambda Labs, RunPod veya Vast.ai için:

```bash
ssh user@your-gpu-instance

pip install torch torchvision torchaudio
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### GPU yok mu? Sorun değil.

Derslerin çoğu CPU'da çalışır. GPU gerektirenler bunu söyler ve Colab linkleri içerir.

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using: {device}")
```

## İnşa Et: GPU vs CPU benchmark

```python
import torch
import time

size = 5000

a_cpu = torch.randn(size, size)
b_cpu = torch.randn(size, size)

start = time.time()
c_cpu = a_cpu @ b_cpu
cpu_time = time.time() - start
print(f"CPU: {cpu_time:.3f}s")

if torch.cuda.is_available():
    a_gpu = a_cpu.to("cuda")
    b_gpu = b_cpu.to("cuda")

    torch.cuda.synchronize()
    start = time.time()
    c_gpu = a_gpu @ b_gpu
    torch.cuda.synchronize()
    gpu_time = time.time() - start
    print(f"GPU: {gpu_time:.3f}s")
    print(f"Speedup: {cpu_time / gpu_time:.0f}x")
```

## Alıştırmalar

1. Yukarıdaki benchmark'ı çalıştır ve CPU vs GPU sürelerini karşılaştır
2. GPU'n yoksa Google Colab'de çalıştır ve karşılaştır
3. Ne kadar GPU belleğin olduğunu kontrol et ve sığabilecek en büyük modeli tahmin et (kural-i kaide: fp16 için parametre başına 2 byte)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| CUDA | "GPU programlama" | NVIDIA'nın paralel hesaplama platformu, kodu GPU'da çalıştırmanı sağlar |
| VRAM | "GPU belleği" | GPU üzerindeki Video RAM, sistem RAM'inden ayrı. Model boyutunu sınırlar. |
| fp16 | "Yarım hassasiyet" | 16-bit kayan nokta, minimum doğruluk kaybıyla fp32'nin yarısı kadar bellek kullanır |
| Tensor Core | "Hızlı matris donanımı" | Matris çarpımı için özelleşmiş GPU çekirdekleri, normal çekirdeklerden 4-8x daha hızlı |
