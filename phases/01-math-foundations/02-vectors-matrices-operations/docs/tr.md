# Vektörler, Matrisler ve İşlemler

> Her sinir ağı aslında biraz fazladan adımı olan matris çarpımıdır.

**Tür:** Yapım
**Diller:** Python, Julia
**Ön koşullar:** Faz 1, Ders 01 (Lineer Cebir Sezgisi)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- Eleman bazlı işlemler, matris çarpımı, transpoz, determinant ve inverse içeren bir Matrix sınıfı inşa et
- Eleman bazlı çarpımı matris çarpımından ayırt et ve hangisinin ne zaman uygulandığını açıkla
- Sadece sıfırdan inşa edilen Matrix sınıfını kullanarak tek bir yoğun (dense) sinir ağı katmanı (`relu(W @ x + b)`) implemente et
- Broadcasting kurallarını ve sinir ağı framework'lerinde bias eklemenin nasıl çalıştığını açıkla

## Sorun

Bir sinir ağı inşa etmek istiyorsun. Kodu okuyorsun ve şunu görüyorsun:

```
output = activation(weights @ input + bias)
```

O `@` matris çarpımıdır. `weights` bir matristir. `input` bir vektördür. Bu işlemlerin ne yaptığını bilmiyorsan, bu satır sihirdir. Biliyorsan, bu üç işlemde bir katmanın tüm forward pass'idir.

Modelinin işlediği her görüntü piksel değerlerinden oluşan bir matristir. Her kelime embedding'i bir vektördür. Her sinir ağının her katmanı bir matris dönüşümüdür. Değişkenleri anlamadan kod yazamayacağın gibi, matris işlemlerinde akıcı olmadan da yapay zeka sistemleri inşa edemezsin.

Bu ders bu akıcılığı sıfırdan inşa ediyor.

## Kavram

### Vektörler: sıralı sayı listeleri

Vektör, yönü ve büyüklüğü olan bir sayı listesidir. Yapay zekada vektörler veri noktalarını, feature'ları veya parametreleri temsil eder.

```
v = [3, 4]        -- 2B vektör
w = [1, 0, -2]    -- 3B vektör
```

Bir 2B vektör `[3, 4]`, düzlemdeki (3, 4) koordinatlarına işaret eder. Uzunluğu (büyüklüğü) 5'tir (3-4-5 üçgeni).

### Matrisler: sayılardan oluşan ızgaralar

Matris, 2B bir ızgaradır. Satırlar ve sütunlar. Bir m x n matrisinin m satırı ve n sütunu vardır.

```
A = | 1  2  3 |     -- 2x3 matris (2 satır, 3 sütun)
    | 4  5  6 |
```

Sinir ağlarında, weight matrisleri girdi vektörlerini çıktı vektörlerine dönüştürür. 784 girdili ve 128 çıktılı bir katman, 128x784'lük bir weight matrisi kullanır.

### Şekiller (shape) neden önemli

Matris çarpımının katı bir kuralı vardır: `(m x n) @ (n x p) = (m x p)`. İç boyutlar uyuşmalı.

```
(128 x 784) @ (784 x 1) = (128 x 1)
  weights       input       output

İç boyutlar: 784 = 784  -- geçerli
```

PyTorch'ta shape uyumsuzluğu hatası alıyorsan, sebebi budur.

### İşlemler haritası

| İşlem | Ne yapar | Sinir ağı kullanımı |
|-----------|-------------|-------------------|
| Toplama | Eleman bazlı birleştirme | Çıktıya bias ekleme |
| Skaler çarpım | Her elemanı ölçekle | Learning rate * gradyanlar |
| Matris çarpımı | Vektörleri dönüştür | Katman forward pass |
| Transpoz | Satır ve sütunları çevir | Backpropagation |
| Determinant | Tek sayı özeti | Tersinirlik kontrolü |
| Inverse | Bir dönüşümü geri al | Lineer sistemleri çözmek |
| Identity | Hiçbir şey yapmayan matris | Initialization, residual bağlantılar |

### Eleman bazlı vs matris çarpımı

Bu ayrım yeni başlayanları sürekli ters köşeye yatırır.

Eleman bazlı: eşleşen pozisyonları çarp. Her iki matris de aynı şekilde olmalı.

```
| 1  2 |   | 5  6 |   | 5  12 |
| 3  4 | * | 7  8 | = | 21 32 |
```

Matris çarpımı: satır ve sütunların dot product'ları. İç boyutlar uyuşmalı.

```
| 1  2 |   | 5  6 |   | 1*5+2*7  1*6+2*8 |   | 19  22 |
| 3  4 | @ | 7  8 | = | 3*5+4*7  3*6+4*8 | = | 43  50 |
```

Farklı işlemler, farklı sonuçlar, farklı kurallar.

### Broadcasting

Çıktılardan oluşan bir matrise bias vektörü eklediğinde, şekiller uyuşmaz. Broadcasting daha küçük diziyi uyacak şekilde genişletir.

```
| 1  2  3 |   +   [10, 20, 30]
| 4  5  6 |

Broadcasting vektörü satırlar boyunca genişletir:

| 1  2  3 |   | 10  20  30 |   | 11  22  33 |
| 4  5  6 | + | 10  20  30 | = | 14  25  36 |
```

Her modern framework bunu otomatik yapar. Bunu anlamak, şekiller yanlış görünmesine rağmen kod çalıştığında kafa karışıklığını önler.

## İnşa Et

### Adım 1: Vector sınıfı

```python
class Vector:
    def __init__(self, data):
        self.data = list(data)
        self.size = len(self.data)

    def __repr__(self):
        return f"Vector({self.data})"

    def __add__(self, other):
        return Vector([a + b for a, b in zip(self.data, other.data)])

    def __sub__(self, other):
        return Vector([a - b for a, b in zip(self.data, other.data)])

    def __mul__(self, scalar):
        return Vector([x * scalar for x in self.data])

    def dot(self, other):
        return sum(a * b for a, b in zip(self.data, other.data))

    def magnitude(self):
        return sum(x ** 2 for x in self.data) ** 0.5
```

### Adım 2: Temel işlemlerle Matrix sınıfı

```python
class Matrix:
    def __init__(self, data):
        self.data = [list(row) for row in data]
        self.rows = len(self.data)
        self.cols = len(self.data[0])
        self.shape = (self.rows, self.cols)

    def __repr__(self):
        rows_str = "\n  ".join(str(row) for row in self.data)
        return f"Matrix({self.shape}):\n  {rows_str}"

    def __add__(self, other):
        return Matrix([
            [self.data[i][j] + other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def __sub__(self, other):
        return Matrix([
            [self.data[i][j] - other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def scalar_multiply(self, scalar):
        return Matrix([
            [self.data[i][j] * scalar for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def element_wise_multiply(self, other):
        return Matrix([
            [self.data[i][j] * other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ])

    def matmul(self, other):
        return Matrix([
            [
                sum(self.data[i][k] * other.data[k][j] for k in range(self.cols))
                for j in range(other.cols)
            ]
            for i in range(self.rows)
        ])

    def transpose(self):
        return Matrix([
            [self.data[j][i] for j in range(self.rows)]
            for i in range(self.cols)
        ])

    def determinant(self):
        if self.shape == (1, 1):
            return self.data[0][0]
        if self.shape == (2, 2):
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]
        det = 0
        for j in range(self.cols):
            minor = Matrix([
                [self.data[i][k] for k in range(self.cols) if k != j]
                for i in range(1, self.rows)
            ])
            det += ((-1) ** j) * self.data[0][j] * minor.determinant()
        return det

    def inverse_2x2(self):
        det = self.determinant()
        if det == 0:
            raise ValueError("Matrix is singular, no inverse exists")
        return Matrix([
            [self.data[1][1] / det, -self.data[0][1] / det],
            [-self.data[1][0] / det, self.data[0][0] / det]
        ])

    @staticmethod
    def identity(n):
        return Matrix([
            [1 if i == j else 0 for j in range(n)]
            for i in range(n)
        ])
```

### Adım 3: Çalıştığını gör

```python
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])

print("A + B =", (A + B).data)
print("A @ B =", A.matmul(B).data)
print("A^T =", A.transpose().data)
print("det(A) =", A.determinant())
print("A^-1 =", A.inverse_2x2().data)

I = Matrix.identity(2)
print("A @ A^-1 =", A.matmul(A.inverse_2x2()).data)
```

### Adım 4: Sinir ağlarına bağla

```python
import random

inputs = Matrix([[0.5], [0.8], [0.2]])
weights = Matrix([
    [random.uniform(-1, 1) for _ in range(3)]
    for _ in range(2)
])
bias = Matrix([[0.1], [0.1]])

def relu_matrix(m):
    return Matrix([[max(0, val) for val in row] for row in m.data])

pre_activation = weights.matmul(inputs) + bias
output = relu_matrix(pre_activation)

print(f"Girdi shape: {inputs.shape}")
print(f"Weight shape: {weights.shape}")
print(f"Çıktı shape: {output.shape}")
print(f"Çıktı: {output.data}")
```

Bu tek bir yoğun katman: `output = relu(W @ x + b)`. Her sinir ağındaki her yoğun katman tam olarak bunu yapar.

## Kullan

NumPy yukarıdaki her şeyi daha az satırda ve katlarca daha hızlı yapar.

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

print("A + B =\n", A + B)
print("A * B (eleman bazlı) =\n", A * B)
print("A @ B (matris çarpımı) =\n", A @ B)
print("A^T =\n", A.T)
print("det(A) =", np.linalg.det(A))
print("A^-1 =\n", np.linalg.inv(A))
print("I =\n", np.eye(2))

inputs = np.random.randn(3, 1)
weights = np.random.randn(2, 3)
bias = np.array([[0.1], [0.1]])
output = np.maximum(0, weights @ inputs + bias)

print(f"\nSinir ağı katmanı: {weights.shape} @ {inputs.shape} = {output.shape}")
print(f"Çıktı:\n{output}")
```

Python'daki `@` operatörü `__matmul__`'u çağırır. NumPy bunu C ve Fortran'da yazılmış optimize edilmiş BLAS rutinleri ile implemente eder. Aynı matematik, 100 kat hızlı.

NumPy'da broadcasting:

```python
matrix = np.array([[1, 2, 3], [4, 5, 6]])
bias = np.array([10, 20, 30])
print(matrix + bias)
```

NumPy 1B bias'ı her iki satıra otomatik olarak broadcast eder. Her sinir ağı framework'ünde bias eklemesi bu şekilde çalışır.

## Yayınla

Bu ders, matris işlemlerini geometrik sezgi yoluyla öğretmek için bir prompt üretir. `outputs/prompt-matrix-operations.md` dosyasına bakın.

Burada inşa edilen Matrix sınıfı, Faz 3, Ders 10'da inşa edeceğimiz mini sinir ağı framework'ünün temelidir.

## Alıştırmalar

1. **Inverse'ü doğrula.** `A @ A.inverse_2x2()` çarp ve identity matrisi elde ettiğini doğrula. Üç farklı 2x2 matrisle dene. Determinant sıfır olduğunda ne olur?

2. **3x3 inverse'ü implemente et.** Matrix sınıfını adjugate yöntemini kullanarak 3x3 matrislerin inverse'lerini hesaplayacak şekilde genişlet. NumPy'ın `np.linalg.inv`'ine karşı test et.

3. **İki katmanlı bir ağ inşa et.** Sadece Matrix sınıfını kullanarak (NumPy yok), iki katmanlı bir sinir ağı oluştur: girdi (3) -> gizli (4) -> çıktı (2). Rastgele weight'leri başlat, bir forward pass çalıştır ve tüm shape'lerin doğru olduğunu doğrula.

## Anahtar Terimler

| Terim | İnsanlar ne der | Aslında ne demek |
|------|----------------|----------------------|
| Vektör | "Bir ok" | Sıralı bir sayı listesi. Yapay zekada: yüksek boyutlu uzayda bir nokta. |
| Matris | "Sayılardan oluşan bir tablo" | Lineer dönüşüm. Vektörleri bir uzaydan başka bir uzaya eşler. |
| Matris çarpımı | "Sayıları çarp" | İlk matrisin her satırı ile ikinci matrisin her sütununun dot product'ları. Sıra önemli. |
| Transpoz | "Çevir" | Satır ve sütunları takas et. m x n matrisi n x m'ye çevirir. Backpropagation'da kritik. |
| Determinant | "Matristen elde edilen bir sayı" | Matrisin alanı (2B) veya hacmi (3B) ne kadar ölçeklediğini ölçer. Sıfır dönüşümün bir boyutu çökerttiği anlamına gelir. |
| Inverse | "Matrisi geri al" | Dönüşümü tersine çeviren matris. Sadece determinant sıfır olmadığında vardır. |
| Identity matrisi | "Sıkıcı matris" | 1 ile çarpmanın matris karşılığı. Residual bağlantılarda (ResNet'ler) kullanılır. |
| Broadcasting | "Sihirli şekil düzeltme" | Daha küçük bir diziyi, eksik boyutlar boyunca tekrarlayarak daha büyük bir diziye uyacak şekilde genişletme. |
| Eleman bazlı | "Normal çarpma" | Eşleşen pozisyonları çarp. Her iki dizi de aynı şekilde olmalı (veya broadcastable olmalı). |

## İleri Okuma

- [3Blue1Brown: Essence of Linear Algebra](https://www.3blue1brown.com/topics/linear-algebra) - burada işlenen her işlem için görsel sezgi
- [NumPy broadcasting belgeleri](https://numpy.org/doc/stable/user/basics.broadcasting.html) - NumPy'ın izlediği tam kurallar
- [Stanford CS229 Linear Algebra Review](http://cs229.stanford.edu/section/cs229-linalg.pdf) - ML'ye özel lineer cebir için özlü referans
