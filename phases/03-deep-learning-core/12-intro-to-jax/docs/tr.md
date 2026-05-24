# JAX'a Giriş

> PyTorch tensor'ları mutate eder. TensorFlow graph'lar kurar. JAX saf fonksiyonları derler. Sonuncusu deep learning hakkında nasıl düşündüğünü değiştirir.

**Tür:** Yapım
**Diller:** Python
**Ön koşullar:** Faz 03 Dersler 01-10, temel NumPy
**Süre:** ~90 dakika

## Öğrenme Hedefleri

- JAX'ın fonksiyonel API'sini (jax.numpy, jax.grad, jax.jit, jax.vmap) kullanarak saf fonksiyon sinir ağı kodu yaz
- PyTorch'un eager mutation'ı ile JAX'ın fonksiyonel derleme modeli arasındaki temel tasarım farkını açıkla
- Naif Python'a kıyasla eğitim döngülerini hızlandırmak için jit derleme ve vmap vektörleştirme uygula
- JAX'ta basit bir ağ eğit ve açık state yönetimini PyTorch'un nesne yönelimli yaklaşımıyla karşılaştır

## Sorun

PyTorch'ta sinir ağları kurmayı biliyorsun. Bir `nn.Module` tanımlarsın, `.backward()` çağırırsın, optimizer'ı adımlarsın. Çalışıyor. Milyonlarca insan kullanıyor.

Ama PyTorch'un DNA'sına işlenmiş bir kısıtlaması var: işlemleri eagerly, teker teker, Python'da izler. Her `tensor + tensor` ayrı bir kernel launch'tır. Her eğitim adımı aynı Python kodunu yeniden yorumlar. Bu, 2,048 TPU'da 540 milyar parametreli bir modeli eğitene kadar gayet iyi çalışır. Sonra ek yük seni öldürür.

Google DeepMind Gemini'yi JAX'ta eğitir. Anthropic Claude'u JAX'ta eğitti. Bunlar küçük operasyonlar değildir — Dünya'daki en büyük sinir ağı eğitim çalışmalarıdır. JAX'ı seçtiler çünkü eğitim döngünü Python çağrıları dizisi olarak değil, derlenebilir bir program olarak ele alıyor.

JAX üç süper güçle NumPy'dir: otomatik türev alma, XLA'ya JIT derleme ve otomatik vektörleştirme. Bir örneği işleyen bir fonksiyon yazıyorsun. JAX sana bir batch'i işleyen, gradyanları hesaplayan, makine koduna derleyen ve birden fazla cihazda çalışan bir fonksiyon veriyor. Hepsi orijinal fonksiyonu değiştirmeden.

## Kavram

### JAX Felsefesi

JAX bir fonksiyonel framework'tür. Sınıf yok, mutable state yok, `.backward()` metodu yok. Bunun yerine:

| PyTorch | JAX |
|---------|-----|
| State'li `nn.Module` sınıfı | Saf fonksiyon: `f(params, x) -> y` |
| `loss.backward()` | `jax.grad(loss_fn)(params, x, y)` |
| Eager execution | XLA üzerinden JIT derleme |
| `for x in batch:` manuel döngü | `jax.vmap(f)` otomatik vektörleştirme |
| `DataParallel` / `FSDP` | `jax.pmap(f)` otomatik paralelizm |
| Mutable `model.parameters()` | Immutable array pytree'si |

Bu bir stil tercihi değil. Bir derleyici kısıtlamasıdır. JIT derleme saf fonksiyonlar gerektirir — aynı girdiler her zaman aynı çıktıları üretir, yan etki yok. Bu kısıtlama 100x hızlanmaları mümkün kılan şeydir.

### jax.numpy: Tanıdık Yüzey

JAX hızlandırıcılarda NumPy API'sini yeniden uygular:

```python
import jax.numpy as jnp

a = jnp.array([1.0, 2.0, 3.0])
b = jnp.array([4.0, 5.0, 6.0])
c = jnp.dot(a, b)
```

Aynı fonksiyon isimleri. Aynı broadcasting kuralları. Aynı dilimleme semantiği. Ama array'ler GPU/TPU'da yaşar ve her işlem derleyici tarafından izlenebilir.

Bir kritik fark: JAX array'leri immutable'dır. `a[0] = 5` yok. Bunun yerine: `a = a.at[0].set(5)`. Bu bir hafta tuhaf hisseder, sonra oturur — immutability `grad`, `jit` ve `vmap` gibi dönüşümleri birleştirilebilir yapan şeydir.

### jax.grad: Fonksiyonel Autodiff

PyTorch gradyanları tensor'lara (`.grad`) bağlar. JAX gradyanları fonksiyonlara bağlar.

```python
import jax

def f(x):
    return x ** 2

df = jax.grad(f)
df(3.0)
```

`jax.grad` bir fonksiyon alır ve gradyanı hesaplayan yeni bir fonksiyon döndürür. `.backward()` çağrısı yok. Tensor'larda saklanan computation graph yok. Gradyan, çağırabileceğin, birleştirebileceğin ya da JIT-derleyebileceğin başka bir fonksiyondur.

Bu keyfi olarak birleşir:

```python
d2f = jax.grad(jax.grad(f))
d2f(3.0)
```

İkinci türevler. Üçüncü türevler. Jacobian'lar. Hessian'lar. Hepsi `grad`'ı birleştirerek. PyTorch bunu da yapabilir (`torch.autograd.functional.hessian`), ama eklenmiştir. JAX'ta temeldir.

Kısıtlama: `grad` yalnızca saf fonksiyonlarda çalışır. İçeride print ifadeleri yok (çalışma yerine izleme sırasında çalışırlar). Dış state'in mutasyonu yok. Açık key yönetimi olmadan rastgele sayı üretimi yok.

### jit: XLA'ya Derle

```python
@jax.jit
def train_step(params, x, y):
    loss = loss_fn(params, x, y)
    return loss

fast_step = jax.jit(train_step)
```

İlk çağrıda JAX fonksiyonu izler — hangi işlemlerin gerçekleştiğini, onları çalıştırmadan kaydeder. Sonra o izlemeyi XLA'ya (Accelerated Linear Algebra), Google'ın TPU'lar ve GPU'lar için derleyicisine teslim eder. XLA işlemleri füzyon yapar, gereksiz bellek kopyalarını ortadan kaldırır ve optimize edilmiş makine kodu üretir.

Sonraki çağrılar Python'u tamamen atlar. Derlenmiş kod hızlandırıcıda C++ hızında çalışır.

JIT ne zaman yardımcı olur:
- Eğitim adımları (binlerce kez tekrar edilen aynı hesaplama)
- Çıkarım (aynı model, farklı girdiler)
- Benzer şekilli girdilerle birden fazla kez çağrılan herhangi bir fonksiyon

JIT ne zaman zarar verir:
- Değerlere bağlı Python kontrol akışı olan fonksiyonlar (x izlenen bir array iken `if x > 0`)
- Tek seferlik hesaplamalar (derleme yükü çalışma süresini aşar)
- Hata ayıklama (izleme gerçek çalıştırmayı gizler)

Kontrol akışı kısıtlaması gerçektir. `jax.lax.cond` `if/else`'in yerini alır. `jax.lax.scan` `for` döngülerinin yerini alır. Bunlar isteğe bağlı değildir — derlemenin bedelidir.

### vmap: Otomatik Vektörleştirme

Bir örneği işleyen bir fonksiyon yazıyorsun:

```python
def predict(params, x):
    return jnp.dot(params['w'], x) + params['b']
```

`vmap` bir batch işlemek için onu yükseltir:

```python
batch_predict = jax.vmap(predict, in_axes=(None, 0))
```

`in_axes=(None, 0)` demek ki: `params` üzerinde batch'leme yok (paylaşılır), `x`'in 0. eksenine batch'le. Manuel `for` döngüsü yok. Yeniden şekillendirme yok. Batch boyutu iplikleme yok. JAX batch boyutunu çözer ve tüm hesaplamayı vektörleştirir.

Bu sözdizimsel şeker değildir. `vmap` Python döngüsünden 10-100x daha hızlı çalışan füzyonlanmış vektörleştirilmiş kod üretir. Ve `jit` ve `grad` ile birleşir:

```python
per_example_grads = jax.vmap(jax.grad(loss_fn), in_axes=(None, 0, 0))
```

Örnek başına gradyanlar. Bir satır. Bu PyTorch'ta hack'ler olmadan neredeyse imkansızdır.

### pmap: Cihazlar Arası Veri Paralelizmi

```python
parallel_step = jax.pmap(train_step, axis_name='devices')
```

`pmap` fonksiyonu mevcut tüm cihazlara (GPU'lar/TPU'lar) çoğaltır ve batch'i böler. Fonksiyon içinde, `jax.lax.pmean` ve `jax.lax.psum` cihazlar arasında gradyanları senkronize eder.

Google Gemini'yi binlerce TPU v5e çipi boyunca `pmap` (ve halefi `shard_map`) kullanarak eğitir. Programlama modeli: tek cihaz versiyonunu yaz, `pmap` ile sar, tamam.

### Pytree'ler: Evrensel Veri Yapısı

JAX "pytree'ler" üzerinde çalışır — listelerin, tuple'ların, dict'lerin ve array'lerin iç içe geçmiş kombinasyonları. Modelinin parametreleri bir pytree'dir:

```python
params = {
    'layer1': {'w': jnp.zeros((784, 256)), 'b': jnp.zeros(256)},
    'layer2': {'w': jnp.zeros((256, 128)), 'b': jnp.zeros(128)},
    'layer3': {'w': jnp.zeros((128, 10)),  'b': jnp.zeros(10)},
}
```

Her JAX dönüşümü — `grad`, `jit`, `vmap` — pytree'leri nasıl dolaşacağını bilir. `jax.tree.map(f, tree)` her yaprağa `f`'yi uygular. Optimizer'ların tüm parametreleri aynı anda nasıl güncellediği budur:

```python
params = jax.tree.map(lambda p, g: p - lr * g, params, grads)
```

`.parameters()` metodu yok. Parametre kaydı yok. Tree yapısı modeldir.

### Fonksiyonel vs Nesne Yönelimli

PyTorch state'i nesneler içinde saklar:

```python
class Model(nn.Module):
    def __init__(self):
        self.linear = nn.Linear(784, 10)

    def forward(self, x):
        return self.linear(x)
```

JAX açık state'li saf fonksiyonlar kullanır:

```python
def predict(params, x):
    return jnp.dot(x, params['w']) + params['b']
```

Params dışarıdan geçirilir. Hiçbir şey saklanmaz. Hiçbir şey mutate edilmez. Bu her fonksiyonu test edilebilir, birleştirilebilir ve derlenebilir yapar. Aynı zamanda params'ı sen yönetirsin — ya da Flax ya da Equinox gibi bir kütüphane kullanırsın.

### JAX Ekosistemi

JAX sana primitif'ler verir. Kütüphaneler sana ergonomi verir:

| Kütüphane | Rol | Stil |
|---------|------|-------|
| **Flax** (Google) | Sinir ağı katmanları | Açık state'li `nn.Module` |
| **Equinox** (Patrick Kidger) | Sinir ağı katmanları | Pytree tabanlı, Pythonic |
| **Optax** (DeepMind) | Optimizer'lar + LR schedule'ları | Birleştirilebilir gradyan dönüşümleri |
| **Orbax** (Google) | Checkpointing | Pytree'leri kaydet/geri yükle |
| **CLU** (Google) | Metrikler + loglama | Eğitim döngüsü yardımcıları |

Optax standart optimizer kütüphanesidir. Gradyan dönüşümünü (Adam, SGD, clipping) parametre güncellemesinden ayırır, bu da birleştirmeyi önemsizleştirir:

```python
optimizer = optax.chain(
    optax.clip_by_global_norm(1.0),
    optax.adam(learning_rate=1e-3),
)
```

### Ne Zaman JAX, Ne Zaman PyTorch

| Faktör | JAX | PyTorch |
|--------|-----|---------|
| TPU desteği | Birinci sınıf (Google ikisini de kurdu) | Topluluk yönetiminde (torch_xla) |
| GPU desteği | İyi (XLA üzerinden CUDA) | Sınıfında en iyi (yerel CUDA) |
| Hata ayıklama | Zor (izleme + derleme) | Kolay (eager, satır satır) |
| Ekosistem | Araştırma odaklı (Flax, Equinox) | Büyük (HuggingFace, torchvision, vb.) |
| İşe alım | Niş (Google/DeepMind/Anthropic) | Ana akım (her yerde) |
| Büyük ölçek eğitim | Üstün (XLA, pmap, mesh) | İyi (FSDP, DeepSpeed) |
| Prototipleme hızı | Daha yavaş (fonksiyonel ek yük) | Daha hızlı (mutate et ve git) |
| Üretim çıkarımı | TensorFlow Serving, Vertex AI | TorchServe, Triton, ONNX |
| Kim kullanır | DeepMind (Gemini), Anthropic (Claude) | Meta (Llama), OpenAI (GPT), Stability AI |

Dürüst cevap: JAX kullanmak için belirli bir nedenin olmadıkça PyTorch kullan. Bu nedenler — TPU erişimi, örnek başına gradyan ihtiyacı, büyük ölçekli çok cihazlı eğitim ya da Google/DeepMind/Anthropic'te çalışmak.

### JAX'ta Rastgele Sayılar

JAX'ın global bir rastgele state'i yoktur. Her rastgele işlem açık bir PRNG key gerektirir:

```python
key = jax.random.PRNGKey(42)
key1, key2 = jax.random.split(key)
w = jax.random.normal(key1, shape=(784, 256))
```

Bu önceleri can sıkıcıdır. Ama cihazlar ve derlemeler arasında tekrarlanabilirliği garanti eder — PyTorch'un `torch.manual_seed`'inin çok GPU ayarlarında garanti edemediği bir özellik.

## İnşa Et

### Adım 1: Kurulum ve Veri

JAX ve Optax kullanarak MNIST üzerinde 3 katmanlı bir MLP eğiteceğiz. 784 giriş, 256 ve 128 nöronlu iki gizli katman, 10 çıktı sınıfı.

```python
import jax
import jax.numpy as jnp
from jax import random
import optax

def get_mnist_data():
    from sklearn.datasets import fetch_openml
    mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
    X = mnist.data.astype('float32') / 255.0
    y = mnist.target.astype('int')
    X_train, X_test = X[:60000], X[60000:]
    y_train, y_test = y[:60000], y[60000:]
    return X_train, y_train, X_test, y_test
```

### Adım 2: Parametreleri Başlat

Sınıf yok. Sadece bir pytree döndüren bir fonksiyon:

```python
def init_params(key):
    k1, k2, k3 = random.split(key, 3)
    scale1 = jnp.sqrt(2.0 / 784)
    scale2 = jnp.sqrt(2.0 / 256)
    scale3 = jnp.sqrt(2.0 / 128)
    params = {
        'layer1': {
            'w': scale1 * random.normal(k1, (784, 256)),
            'b': jnp.zeros(256),
        },
        'layer2': {
            'w': scale2 * random.normal(k2, (256, 128)),
            'b': jnp.zeros(128),
        },
        'layer3': {
            'w': scale3 * random.normal(k3, (128, 10)),
            'b': jnp.zeros(10),
        },
    }
    return params
```

He-initialization, manuel olarak yapıldı. Bir tohumdan üç PRNG key'i bölünmüş. Her ağırlık iç içe bir dict'te immutable bir array.

### Adım 3: Forward Pass

```python
def forward(params, x):
    x = jnp.dot(x, params['layer1']['w']) + params['layer1']['b']
    x = jax.nn.relu(x)
    x = jnp.dot(x, params['layer2']['w']) + params['layer2']['b']
    x = jax.nn.relu(x)
    x = jnp.dot(x, params['layer3']['w']) + params['layer3']['b']
    return x

def loss_fn(params, x, y):
    logits = forward(params, x)
    one_hot = jax.nn.one_hot(y, 10)
    return -jnp.mean(jnp.sum(jax.nn.log_softmax(logits) * one_hot, axis=-1))
```

Saf fonksiyonlar. Params girer, tahmin çıkar. `self` yok, saklanan state yok. `loss_fn` cross-entropy'yi sıfırdan hesaplar — softmax, log, negatif ortalama.

### Adım 4: JIT-Derlenmiş Eğitim Adımı

```python
@jax.jit
def train_step(params, opt_state, x, y):
    loss, grads = jax.value_and_grad(loss_fn)(params, x, y)
    updates, opt_state = optimizer.update(grads, opt_state, params)
    params = optax.apply_updates(params, updates)
    return params, opt_state, loss

@jax.jit
def accuracy(params, x, y):
    logits = forward(params, x)
    preds = jnp.argmax(logits, axis=-1)
    return jnp.mean(preds == y)
```

`jax.value_and_grad` tek bir pass'te hem loss değerini hem de gradyanları döndürür. `@jax.jit` dekoratörü her iki fonksiyonu da XLA'ya derler. İlk çağrıdan sonra her eğitim adımı Python'a dokunmadan çalışır.

### Adım 5: Eğitim Döngüsü

```python
optimizer = optax.adam(learning_rate=1e-3)

X_train, y_train, X_test, y_test = get_mnist_data()
X_train, X_test = jnp.array(X_train), jnp.array(X_test)
y_train, y_test = jnp.array(y_train), jnp.array(y_test)

key = random.PRNGKey(0)
params = init_params(key)
opt_state = optimizer.init(params)

batch_size = 128
n_epochs = 10

for epoch in range(n_epochs):
    key, subkey = random.split(key)
    perm = random.permutation(subkey, len(X_train))
    X_shuffled = X_train[perm]
    y_shuffled = y_train[perm]

    epoch_loss = 0.0
    n_batches = len(X_train) // batch_size
    for i in range(n_batches):
        start = i * batch_size
        xb = X_shuffled[start:start + batch_size]
        yb = y_shuffled[start:start + batch_size]
        params, opt_state, loss = train_step(params, opt_state, xb, yb)
        epoch_loss += loss

    train_acc = accuracy(params, X_train[:5000], y_train[:5000])
    test_acc = accuracy(params, X_test, y_test)
    print(f"Epoch {epoch + 1:2d} | Loss: {epoch_loss / n_batches:.4f} | "
          f"Eğitim Doğr: {train_acc:.4f} | Test Doğr: {test_acc:.4f}")
```

10 epoch. ~%97 test doğruluğu. İlk epoch yavaştır (JIT derlemesi). Epoch 2-10 hızlıdır.

Eksik olanlara dikkat: `.zero_grad()` yok, `.backward()` yok, `.step()` yok. Tüm güncelleme tek bir birleştirilmiş fonksiyon çağrısıdır. Gradyanlar hesaplanır, Adam tarafından dönüştürülür ve parametrelere uygulanır — hepsi `train_step` içinde.

## Kullan

### Flax: Google Standardı

Flax en yaygın JAX sinir ağı kütüphanesidir. `nn.Module`'ı geri ekler ama açık state yönetimiyle:

```python
import flax.linen as nn

class MLP(nn.Module):
    @nn.compact
    def __call__(self, x):
        x = nn.Dense(256)(x)
        x = nn.relu(x)
        x = nn.Dense(128)(x)
        x = nn.relu(x)
        x = nn.Dense(10)(x)
        return x

model = MLP()
params = model.init(jax.random.PRNGKey(0), jnp.ones((1, 784)))
logits = model.apply(params, x_batch)
```

PyTorch ile aynı yapı ama `params` modelden ayrıdır. `model.init()` params'ı yaratır. `model.apply(params, x)` forward pass'i çalıştırır. Model nesnesinin state'i yoktur.

### Equinox: Pythonic Alternatif

Equinox (Patrick Kidger tarafından) modelleri pytree olarak temsil eder:

```python
import equinox as eqx

model = eqx.nn.MLP(
    in_size=784, out_size=10, width_size=256, depth=2,
    activation=jax.nn.relu, key=jax.random.PRNGKey(0)
)
logits = model(x)
```

Modelin kendisi bir pytree'dir. `.apply()` gerekmez. Parametreler sadece modelin yapraklarıdır. Bu JAX'ın nasıl düşündüğüne daha yakındır.

### Optax: Birleştirilebilir Optimizer'lar

Optax gradyan dönüşümünü güncellemeden ayırır:

```python
schedule = optax.warmup_cosine_decay_schedule(
    init_value=0.0, peak_value=1e-3,
    warmup_steps=1000, decay_steps=50000
)

optimizer = optax.chain(
    optax.clip_by_global_norm(1.0),
    optax.adamw(learning_rate=schedule, weight_decay=0.01),
)
```

Gradient clipping, learning rate warmup, weight decay — hepsi bir dönüşüm zinciri olarak birleştirildi. Her dönüşüm gradyanları görür, onları değiştirir ve sonrakine geçirir. Monolitik bir optimizer sınıfı yok.

## Yayınla

**Kurulum:**

```bash
pip install jax jaxlib optax flax
```

GPU desteği için:

```bash
pip install jax[cuda12]
```

TPU (Google Cloud) için:

```bash
pip install jax[tpu] -f https://storage.googleapis.com/jax-releases/libtpu_releases.html
```

**Performans tuzakları:**

- İlk JIT çağrısı yavaştır (derleme). Benchmark'tan önce ısın.
- JIT içinde JAX array'leri üzerinde Python döngülerinden kaçın. `jax.lax.scan` ya da `jax.lax.fori_loop` kullan.
- `jax.debug.print()` JIT içinde çalışır. Normal `print()` çalışmaz.
- `jax.profiler` ya da TensorBoard ile profile et. XLA derlemesi darboğazları gizleyebilir.
- JAX varsayılan olarak GPU belleğinin %75'ini önceden ayırır. Devre dışı bırakmak için `XLA_PYTHON_CLIENT_PREALLOCATE=false` ayarla.

**Checkpointing:**

```python
import orbax.checkpoint as ocp
checkpointer = ocp.PyTreeCheckpointer()
checkpointer.save('/tmp/model', params)
restored = checkpointer.restore('/tmp/model')
```

**Bu ders şunları üretir:**
- `outputs/prompt-jax-optimizer.md` — doğru JAX optimizer konfigürasyonunu seçmek için bir prompt
- `outputs/skill-jax-patterns.md` — JAX'taki fonksiyonel desenleri kapsayan bir skill

## Alıştırmalar

1. MLP'ye dropout ekle. JAX'ta dropout bir PRNG key gerektirir — forward pass boyunca bir key thread et ve her dropout katmanı için onu böl. Olan ve olmayan test doğruluğunu karşılaştır.

2. 32 MNIST görüntüsü batch'i için örnek başına gradyanları hesaplamak için `jax.vmap` kullan. Her örnek için gradyan normunu hesapla. En büyük gradyanlara hangi örnekler sahip ve neden?

3. Manuel forward fonksiyonunu herhangi bir katman sayısı için çalışan genel bir `mlp_forward(params, x)` ile değiştir. Derinliği otomatik olarak belirlemek için `jax.tree.leaves` kullan.

4. `@jax.jit` olan ve olmayan eğitim adımını benchmark et. Her birinin 100 adımını zamanla. Donanımında hızlanma ne kadar büyük? İlk çağrıdaki derleme yükü nedir?

5. `optax.chain(optax.clip_by_global_norm(1.0), optax.adam(1e-3))` birleştirerek gradyan kırpmasını uygula. Kırpma olan ve olmayan eğit. Etkiyi görmek için eğitim boyunca gradyan normunu çiz.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|----------------------|
| XLA | "JAX'ı hızlı yapan şey" | Accelerated Linear Algebra — bir computation graph'tan işlemleri füzyon yapan ve optimize edilmiş GPU/TPU kernel'leri üreten bir derleyici |
| JIT | "Just-in-time derleme" | JAX fonksiyonu ilk çağrıda izler, XLA'ya derler, sonra sonraki çağrılarda derlenmiş versiyonu çalıştırır |
| Saf fonksiyon | "Yan etki yok" | Çıktının yalnızca girdilere bağlı olduğu bir fonksiyon — global state yok, mutasyon yok, açık key'ler olmadan rastgelelik yok |
| vmap | "Otomatik batch'leme" | Bir örneği işleyen bir fonksiyonu, yeniden yazmadan bir batch'i işleyene dönüştürür |
| pmap | "Otomatik paralelizm" | Bir fonksiyonu birden fazla cihaza çoğaltır ve giriş batch'ini böler |
| Pytree | "İç içe array dict'i" | JAX'ın dolaşıp dönüştürebileceği listelerin, tuple'ların, dict'lerin ve array'lerin herhangi bir iç içe yapısı |
| İzleme | "Hesaplamayı kaydetme" | JAX fonksiyonu, gerçek sonuçları hesaplamadan, computation graph kurmak için soyut değerlerle çalıştırır |
| Fonksiyonel autodiff | "Bir fonksiyonun grad'ı" | Tensor'lara gradyan depolaması eklemekle değil, fonksiyonları dönüştürerek türevleri hesaplama |
| Optax | "JAX'ın optimizer kütüphanesi" | Adam, SGD, kırpma, scheduling — birbirine zincirleyen gradyan dönüşümlerinden oluşan birleştirilebilir bir kütüphane |
| Flax | "JAX'ın nn.Module'ı" | Google'ın JAX için sinir ağı kütüphanesi; state'i açık tutarken katman soyutlamaları ekler |

## İleri Okuma

- JAX dokümantasyonu: https://jax.readthedocs.io/ — grad, jit ve vmap üzerine mükemmel öğreticilerle resmi dokümanlar
- "JAX: composable transformations of Python+NumPy programs" (Bradbury et al., 2018) — tasarım felsefesini açıklayan orijinal makale
- Flax dokümantasyonu: https://flax.readthedocs.io/ — Google'ın JAX için sinir ağı kütüphanesi
- Patrick Kidger, "Equinox: neural networks in JAX via callable PyTrees and filtered transformations" (2021) — Flax'a Pythonic alternatif
- DeepMind, "Optax: composable gradient transformation and optimisation" — standart optimizer kütüphanesi
- "You Don't Know JAX" (Colin Raffel, 2020) — T5 yazarlarından biri tarafından JAX tuzakları ve desenlerine pratik bir kılavuz
