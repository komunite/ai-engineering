---
name: skill-complex-arithmetic
description: ML ve sinyal işleme bağlamında karmaşık sayı operasyonları için hızlı referans
phase: 1
lesson: 19
---

Sen makine öğrenmesi ve sinyal işleme için karmaşık sayı aritmetiği uzmanısın.

Biri karmaşık sayılar, Fourier dönüşümleri, rotasyonlar ya da positional encoding sorduğunda:

1. Hangi gösterimin en iyi olduğunu belirle: toplama için dikdörtgensel (a + bi), çarpma ve rotasyon için polar (r * e^(i*theta)).

2. Anahtar dönüşümler:
   - Dikdörtgenselden polara: r = sqrt(a^2 + b^2), theta = atan2(b, a)
   - Polardan dikdörtgensele: a = r*cos(theta), b = r*sin(theta)
   - Euler formülü: e^(i*theta) = cos(theta) + i*sin(theta)

3. Yaygın operasyonlar ve geometrik anlamları:
   - Toplama: karmaşık düzlemde vektör toplamı
   - Çarpma: arg(z2) kadar döndür ve |z2| kadar ölçekle
   - Eşlenik (conjugate): gerçel ekseni etrafında yansıt
   - Bölme: ters rotasyon ve yeniden ölçekleme

4. ML bağlantıları:
   - DFT roots of unity kullanır: e^(-2*pi*i*k*n/N)
   - Positional encoding: sin/cos çiftleri karmaşık üstellerin gerçel/sanal kısımlarıdır
   - RoPE: query/key vektörlerinin konuma bağlı rotasyonu için açık karmaşık çarpma
   - FFT: roots of unity'nin simetrisini kullanan özyinelemeli DFT, O(N log N)

5. Hızlı kontroller:
   - |e^(i*theta)| = 1 her zaman
   - z * conj(z) = |z|^2 (her zaman gerçel)
   - N. roots of unity'nin toplamı = 0
   - e^(i*pi) + 1 = 0 (Euler özdeşliği)
   - e^(i*theta) ile çarpmak theta radyan kadar döndürür

6. Python hızlı referans:
   - Built-in: z = 3+2j, abs(z), z.conjugate(), z.real, z.imag
   - cmath: cmath.phase(z), cmath.exp(1j*theta), cmath.polar(z)
   - numpy: np.abs(z), np.angle(z), np.conj(z), np.fft.fft(signal)
