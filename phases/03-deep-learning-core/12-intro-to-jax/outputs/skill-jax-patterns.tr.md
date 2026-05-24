---
name: skill-jax-patterns
description: JAX'te fonksiyonel programlama pattern'leri — grad, jit, vmap ve pmap'i ne zaman ve nasıl kullanmalı
version: 1.0.0
phase: 3
lesson: 12
tags: [jax, functional-programming, autodiff, compilation, vectorization]
---

# JAX Fonksiyonel Pattern'leri

JAX saf (pure) fonksiyonları dönüştürür. Aşağıdaki her pattern tek bir kurala uyar: yan etkisi olmadan girdileri alıp çıktıları döndüren bir fonksiyon yaz. Sonra dönüştür.

## Dört Dönüşüm

### grad — Bir fonksiyonun türevini al

```python
grads = jax.grad(loss_fn)(params, x, y)
loss, grads = jax.value_and_grad(loss_fn)(params, x, y)
```

Şunda kullan: optimizasyon için gradient'lere ihtiyacın olduğunda.
Kısıt: fonksiyon bir skaler döndürmeli. Skaler olmayan çıktılar için `jax.jacobian` kullan.

### jit — Bir fonksiyonu derle

```python
fast_fn = jax.jit(f)
```

Şunda kullan: fonksiyon aynı shape'li girdilerle birden fazla kez çağrılacaksa.
Kısıt: traced değerlere bağımlı Python kontrol akışı yok. Koşullar için `jax.lax.cond`, döngüler için `jax.lax.scan` kullan.

### vmap — Bir fonksiyonu vektörize et

```python
batch_fn = jax.vmap(f, in_axes=(None, 0))
```

Şunda kullan: tek örnek için fonksiyon yazdın ve batch'lerde çalışması gerek.
`in_axes` hangi argüman ekseninde batch'lenileceğini belirtir. `None` batch'leme (broadcast) demek değildir.

### pmap — Cihazlar arası paralelize et

```python
parallel_fn = jax.pmap(f, axis_name='devices')
```

Şunda kullan: birden fazla GPU/TPU'n var ve data parallelism istiyorsun.
Fonksiyon içinde `jax.lax.pmean(x, 'devices')` cihazlar arası ortalar.

## Composition Kuralları

Dönüşümler composable. Sıra önemli:

```python
per_example_grads = jax.jit(jax.vmap(jax.grad(loss_fn), in_axes=(None, 0, 0)))
```

Sağdan sola okuyarak: loss_fn'in gradient'ini al, örnekler üzerinde vektörize et, sonucu derle.

Geçerli composition'lar:
- `jit(grad(f))` — derlenmiş gradient hesabı
- `jit(vmap(f))` — derlenmiş batched hesap
- `vmap(grad(f))` — örnek başına gradient
- `pmap(jit(f))` — paralel derlenmiş hesap
- `grad(jit(f))` — derlenmiş fonksiyonun gradient'i (jit(grad(f)) ile aynı)

## Parametre Yönetim Pattern'i

JAX parametreleri pytree'lerdir (iç içe array dict'leri):

```python
params = {
    'layer1': {'w': jnp.zeros((784, 256)), 'b': jnp.zeros(256)},
    'layer2': {'w': jnp.zeros((256, 10)),  'b': jnp.zeros(10)},
}
```

Tüm parametreleri tek seferde güncelle:
```python
params = jax.tree.map(lambda p, g: p - lr * g, params, grads)
```

Parametreleri say:
```python
n_params = sum(p.size for p in jax.tree.leaves(params))
```

## PRNG Key Yönetimi

JAX açık random key gerektirir:

```python
key = jax.random.PRNGKey(0)
key, subkey = jax.random.split(key)
noise = jax.random.normal(subkey, shape)
```

Birden çok random operasyon için bir kez böl:
```python
keys = jax.random.split(key, n)
```

Asla bir key'i yeniden kullanma. Her zaman kullanmadan önce böl.

## Sık Yapılan Hatalar

1. **jit içinde array mutasyonu**: JAX array'leri değişmezdir. `x[i] = v` yerine `x.at[i].set(v)` kullan.

2. **jit içinde Python print kullanmak**: `print` execution sırasında değil tracing sırasında çalışır. `jax.debug.print("{}", x)` kullan.

3. **jit içinde traced değerler üzerinde Python if/for**: `jax.lax.cond`, `jax.lax.switch`, `jax.lax.scan`, `jax.lax.fori_loop` kullan.

4. **`.block_until_ready()`'i unutmak**: JAX async dispatch kullanır. Benchmarking için gerçek tamamlanmayı beklemek için `.block_until_ready()` çağır.

5. **PRNG key'leri yeniden kullanmak**: Aynı key'le iki operasyon aynı "random" değerleri üretir. Her zaman böl.

6. **jit'li fonksiyonlarda global state**: Global değişkenler trace anında yakalanır. Trace sonrası değişiklikler görünmez. Her şeyi argüman olarak geç.

## Karar Checklist'i

1. Fonksiyon birden çok kez çağrılıyor mu? `@jax.jit` ekle.
2. Gradient gerekiyor mu? `jax.grad` ya da `jax.value_and_grad` ile sar.
3. Tek örnek işliyor ama batch'in var mı? `jax.vmap` ile sar.
4. Birden çok cihazın var mı? `jax.pmap` ile sar.
5. Randomness kullanıyor mu? PRNG key'lerini açıkça geçir.
6. Array değerlerinde Python kontrol akışı var mı? `jax.lax` primitive'leriyle değiştir.

## JAX'i Ne Zaman Kullan

JAX'i şunlarda kullan:
- Örnek başına gradient gerektiğinde (differential privacy, Fisher information)
- TPU'da eğitim yapıyorsan (JAX native framework)
- Daha yüksek dereceden türevler gerekirse (Hessian, Jacobian)
- Tüm eğitim adımını tek bir kernel'a derlemek istiyorsan
- Ekibin Google DeepMind ya da Anthropic'teyse

PyTorch'u şunlarda kullan:
- En büyük ekosistemi istiyorsan (HuggingFace, torchvision, Lightning)
- Hata ayıklama kolaylığını ham hızdan önemli görüyorsan
- TorchServe/Triton ile NVIDIA GPU'lara deploy ediyorsan
- İşe alım yapıyorsan (daha fazla PyTorch geliştirici var)
- Yeni mimarilerde hızlı iterasyon istiyorsan
