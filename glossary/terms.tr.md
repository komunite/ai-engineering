# Yapay Zeka Mühendisliği Sözlüğü

## A

### Agent
- **What people say:** "Kendi başına düşünen ve hareket eden otonom bir yapay zeka"
- **What it actually means:** Bir LLM'in sırasıyla hangi tool'u çağıracağına karar verdiği, çağırdığı, sonucu gördüğü ve tekrarladığı bir while döngüsü
- **Why it's called that:** Felsefeden ödünç alınmış — "agent" dünyada eyleyebilen herhangi bir şeydir. Yapay zekada karşılığı sadece "LLM + tool'lar + döngü"

### Attention
- **What people say:** "Yapay zekanın önemli kısımlara odaklanma şekli"
- **What it actually means:** Her token'ın, diğer tüm token'ların değerlerinin ağırlıklı toplamını hesapladığı bir mekanizma; ağırlıklar query ve key vektörlerinin nokta çarpımıyla belirlenir
- **Why it's called that:** 2017'deki "Attention Is All You Need" makalesi, insandaki seçici dikkate benzettiği için bu adı koymuş

### Alignment
- **What people say:** "Yapay zekayı güvenli yapmak"
- **What it actually means:** Bir yapay zeka sisteminin davranışını insan niyetlerine, değerlerine ve tercihlerine — tasarımcının öngöremediği uç durumlar dahil — uydurma teknik problemi

### Autoregressive
- **What people say:** "Yapay zeka her seferinde bir kelime üretir"
- **What it actually means:** Bir sonraki token'ı, kendinden önceki tüm token'lara bakarak tahmin eden ve bu tahmini bir sonraki adımın girdisi olarak geri besleyen model. GPT, LLaMA ve Claude'un hepsi autoregressive'dir.

### Activation Function
- **What people say:** "Katmanların arasındaki doğrusal olmayan şey"
- **What it actually means:** Her doğrusal katmandan sonra uygulanan ve doğrusal olmayanlık ekleyen fonksiyon. Bu olmadan, kaç doğrusal katmanı üst üste koyarsanız koyun, tek bir doğrusal dönüşüme indirgenir. ReLU, GELU ve SiLU en yaygınları. Seçim, eğitim sırasında gradyanların akıp akmamasını doğrudan etkiler.

### Adam (Optimizer)
- **What people say:** "Varsayılan optimizer"
- **What it actually means:** Adaptive Moment Estimation. Momentum'u (birinci moment) parametre başına uyarlanır öğrenme oranlarıyla (ikinci moment) birleştirir. İlk adımlar için bias düzeltmesi içerir. Çoğu görevde fazla ayarlama gerektirmeden iyi çalışır.

### AdamW
- **What people say:** "Adam, ama daha iyisi"
- **What it actually means:** Ayrıştırılmış weight decay'li Adam. Standart Adam'da L2 regularization, parametre başına uyarlanır öğrenme oranıyla çarpılır — ki bu istenen şey değildir. AdamW weight decay'i doğrudan ağırlıklara, gradyan istatistiklerinden bağımsız olarak uygular. Transformer eğitiminin varsayılan optimizer'ı.

### Autograd
- **What people say:** "Otomatik gradyan"
- **What it actually means:** Tensor üzerindeki işlemleri kaydeden ve ters modlu türev alarak gradyanları otomatik hesaplayan sistem. PyTorch'un autograd'ı hesaplama grafiğini anlık (dinamik) kurar; JAX ise fonksiyon dönüşümleri (grad) kullanır. Backpropagation'ı pratik yapan şey budur — siz ileri geçişi yazarsınız, framework tüm türevleri kendisi hesaplar.

## B

### Batch Size
- **What people say:** "Aynı anda kaç örnek"
- **What it actually means:** Ağırlıklar güncellenmeden önce bir ileri/geri geçişte işlenen eğitim örneği sayısı. Daha büyük batch'ler daha kararlı gradyan tahmini verir ama daha çok bellek kullanır. Tipik değerler: eğitim için 32-512, çıkarım için daha büyük. Batch size öğrenme oranıyla etkileşir — batch'i ikiye katlarsanız LR'yi de ikiye katlayın (doğrusal ölçekleme kuralı).

### Backpropagation
- **What people say:** "Sinir ağlarının öğrenme şekli"
- **What it actually means:** Her bir ağırlığın hataya ne kadar katkıda bulunduğunu, zincir kuralını ağ boyunca geriye doğru uygulayarak hesaplayan ve ağırlıkları buna orantılı ayarlayan algoritma
- **Why it's called that:** Hatalar çıkıştan girişe, katman katman geriye yayılır

## C

### Context Window
- **What people say:** "Yapay zekanın hatırlayabildiği miktar"
- **What it actually means:** Tek bir API çağrısına sığan maksimum token sayısı (girdi + çıktı). Bellek değil — her çağrıda sıfırlanan, sabit boyutlu bir tampon

### Chain of Thought (CoT)
- **What people say:** "Yapay zekaya adım adım düşündürmek"
- **What it actually means:** Modelden akıl yürütme adımlarını göstermesini istediğiniz bir prompt tekniği; her adım bir sonraki token üretimini koşullandırdığı için çok adımlı problemlerde doğruluğu artırır

### CNN (Convolutional Neural Network)
- **What people say:** "Görsel yapay zekası"
- **What it actually means:** Yerel örüntüleri tespit etmek için convolution işlemleri (girdinin üzerinde gezinen filtreler) kullanan bir sinir ağı. Convolution'ları üst üste koymak giderek daha karmaşık öznitelikleri yakalar: kenarlar, dokular, nesneler.

### CUDA
- **What people say:** "GPU programlama"
- **What it actually means:** NVIDIA'nın paralel hesaplama platformu. Matris işlemlerini binlerce GPU çekirdeğinde eşzamanlı çalıştırmanıza imkân verir. PyTorch ve TensorFlow kaputun altında CUDA kullanır.

### Chunking
- **What people say:** "Belgeleri parçalara bölmek"
- **What it actually means:** Bir metni, retrieval için embedding'leme öncesinde segmentlere ayırmak. Chunk boyutu arama sonuçlarının granülerliğini belirler. Çok küçük: bağlamı kaybeder. Çok büyük: alaka düzeyini sulandırır. Yaygın stratejiler: örtüşmeli sabit boyut, cümle bazlı veya semantik bölme. Tipik chunk boyutu: %10-20 örtüşmeyle 256-512 token.

### Contrastive Learning
- **What people say:** "Karşılaştırarak öğrenme"
- **What it actually means:** Benzer çiftleri embedding uzayında birbirine yakınlaştırıp, benzemeyen çiftleri uzaklaştırarak eğitmek. CLIP bunu kullanır: eşleşen görsel-metin çiftleri ile eşleşmeyenler.

### Cosine Similarity
- **What people say:** "İki vektörün ne kadar benzediği"
- **What it actually means:** İki vektör arasındaki açının kosinüsü: dot(a, b) / (||a|| * ||b||). -1 (zıt) ile 1 (aynı yön) arası değer alır. Büyüklüğü göz ardı eder; sadece yöne bakar. Embedding'ler ve semantik arama için standart benzerlik metriği.

### Cross-Entropy
- **What people say:** "Sınıflandırma kaybı"
- **What it actually means:** İki olasılık dağılımı arasındaki farkı ölçer. Sınıflandırma için: -sum(y_true * log(y_pred)). Dil modelleri için: doğru bir sonraki token'ın negatif log olasılığı. Düşük olması iyidir. Perplexity, basitçe exp(cross-entropy)'dir.

## D

### Data Augmentation
- **What people say:** "Daha fazla eğitim verisi üretmek"
- **What it actually means:** Mevcut verinin değiştirilmiş kopyalarını oluşturmak (görselleri döndürmek, gürültü eklemek, metni başka kelimelerle anlatmak) — yeni veri toplamadan eğitim seti çeşitliliğini artırır. Overfitting'i azaltır.

### Decoder
- **What people say:** "Çıkış kısmı"
- **What it actually means:** Transformer'larda decoder, nedensel (maskeli) self-attention kullanır; her pozisyon yalnızca önceki pozisyonlara bakabilir. GPT yalnızca decoder, BERT yalnızca encoder, T5 ise encoder-decoder mimarisidir.

### Diffusion Model
- **What people say:** "Gürültüden görsel üreten yapay zeka"
- **What it actually means:** Aşamalı bir gürültüleme sürecini tersine çevirmek için eğitilmiş model — gürültüyü tahmin edip çıkarmayı öğrenir; üretim aşamasında saf gürültüden başlar ve tekrarlayarak gürültüyü temizler

### DPO (Direct Preference Optimization)
- **What people say:** "Daha basit bir RLHF"
- **What it actually means:** Ödül modelini tamamen atlayan bir eğitim yöntemi — insan tercih çiftlerinde daha iyi yanıtı tercih edecek şekilde dil modelini doğrudan optimize eder

### Dropout
- **What people say:** "Rastgele nöron kapatmak"
- **What it actually means:** Eğitim sırasında, aktivasyonların bir kısmını rastgele sıfırlamak. Ağı tek bir nörona güvenmemeye zorlar. Çıkarım sırasında kapatılır. Basit ama etkili bir regularization.

## E

### Eigenvalue
- **What people say:** "PCA için bir matematik şeyi"
- **What it actually means:** Bir A matrisi için, eigenvalue lambda, Av = lambda*v eşitliğini bir v vektörü için sağlar. Matrisin o yönde vektörleri ne kadar ölçeklediğini söyler. Büyük eigenvalue'lar = verinizdeki yüksek varyans yönleri.

### Embedding
- **What people say:** "Kelimeleri sayılara çeviren bir yapay zeka sihiri"
- **What it actually means:** Ayrık öğelerden (kelime, görsel, kullanıcı) sürekli uzaydaki yoğun vektörlere öğrenilmiş bir eşleme; benzer öğeler birbirine yakın düşer
- **Why it's called that:** Öğeler, mesafenin anlam taşıdığı geometrik bir uzaya "gömülür" (embed edilir)

### Encoder
- **What people say:** "Giriş kısmı"
- **What it actually means:** Transformer'larda encoder iki yönlü self-attention kullanır; her pozisyon tüm pozisyonlara bakabilir. BERT yalnızca encoder'dır. Anlama görevleri (sınıflandırma, NER) için iyi; üretim için değil.

### Epoch
- **What people say:** "Veri üzerinden bir geçiş"
- **What it actually means:** Aynen öyle. Eğitim setindeki her örneğin üzerinden tam bir geçiş. Birden çok epoch = veriyi birden çok kez görmek. Daha çok epoch öğrenmeyi iyileştirebilir ama overfitting riskini artırır.

## F

### Feature
- **What people say:** "Verinizdeki bir sütun"
- **What it actually means:** Verinin tek bir ölçülebilir özelliği. Klasik ML'de feature'ları elle mühendislik edersiniz. Derin öğrenmede ağ, ham veriden feature'ları otomatik öğrenir.

### Few-Shot
- **What people say:** "Yapay zekaya önce birkaç örnek verin"
- **What it actually means:** Görev istemeden önce prompt'a az sayıda girdi-çıktı örneği eklemek. Genelde 3-5 örnek. Model bu örnekler üzerinde örüntü yakalayarak istenen format ve davranışı kavrar. Zero-shot (örneksiz) ve fine-tuning (binlerce örneğin ağırlıklara işlendiği) ile karşılaştırın.

### Fine-tuning
- **What people say:** "Yapay zekayı kendi verinle eğitmek"
- **What it actually means:** Önceden eğitilmiş bir modelin ağırlıklarından başlayıp daha küçük, göreve özgü bir veri kümesinde eğitime devam etmek. Yalnızca mevcut ağırlıkları günceller; sıfırdan yeni bilgi eklemez

### Function Calling
- **What people say:** "Tool kullanabilen yapay zeka"
- **What it actually means:** LLM'lerin dış fonksiyonların çalıştırılmasını talep etmesi için yapılandırılmış bir yol. Tool'ları JSON Schema açıklamalarıyla tanımlarsınız, model hangi fonksiyonu hangi argümanlarla çağırmak istediğini belirten yapılandırılmış bir JSON çıktısı verir, kodunuz onu çalıştırır ve sonuç modele geri döner. Agent'larla aynı şey değildir — function calling mekanizmadır, agent'lar döngüdür.

## G

### Guardrails
- **What people say:** "Yapay zeka için güvenlik filtreleri"
- **What it actually means:** Bir LLM'in çevresinde, zararlı içeriği, prompt injection denemelerini, PII sızıntısını veya konu dışı yanıtları tespit edip engelleyen girdi/çıktı doğrulama katmanları. Tipik olarak bir hat: girdi filtresi -> LLM -> çıktı filtresi. Kural bazlı (regex, anahtar kelime listesi) ya da model bazlı (güvenliği puanlayan bir sınıflandırıcı) olabilir.

### GPT
- **What people say:** "ChatGPT" veya "yapay zeka"
- **What it actually means:** Generative Pre-trained Transformer — büyük metin külliyatlarında eğitilmiş, yalnızca decoder'dan oluşan bir transformer kullanarak bir sonraki token'ı tahmin eden belirli bir mimari
- **Why it's called that:** Generative (metin üretir), Pre-trained (büyük veride bir kere eğitilir, sonra uyarlanır), Transformer (mimari)

### GAN (Generative Adversarial Network)
- **What people say:** "İki yapay zekanın birbiriyle dövüşmesi"
- **What it actually means:** Bir generator ağı gerçekçi veri üretmeye çalışırken bir discriminator ağı gerçek ile sahteyi ayırt etmeye çalışır. Birlikte eğitilirler: generator discriminator'ı kandırmada gelişir, discriminator sahteyi tespit etmede.

### Gradient
- **What people say:** "Eğim"
- **What it actually means:** En dik artışın yönüne işaret eden kısmi türevler vektörü. ML'de kaybı azaltmak için gradyanın tersine doğru gidersiniz (gradient descent).

### Gradient Descent
- **What people say:** "Yapay zekanın iyileşme şekli"
- **What it actually means:** Parametreleri, kayıp fonksiyonunu en dik biçimde azaltacak yönde ayarlayan bir optimizasyon algoritması — yüksek boyutlu bir manzarada yokuş aşağı yürümek gibi

## H

### Hyperparameter
- **What people say:** "Ayarladığınız ayarlar"
- **What it actually means:** Eğitim sürecinin kendisini kontrol eden, eğitim öncesinde belirlenen değerler: learning rate, batch size, katman sayısı, dropout oranı. Model parametrelerinin (ağırlıklar) aksine, bunlar veriden öğrenilmez.

### Hallucination
- **What people say:** "Yapay zeka yalan söylüyor" veya "uyduruyor"
- **What it actually means:** Modelin, eğitim verisinde ya da verilen bağlamda dayanağı olmayan, ama kulağa makul gelen metin üretmesi — örüntü tamamlıyor, gerçek bilgi getirmiyor

## I

### Inference
- **What people say:** "Yapay zekayı çalıştırmak"
- **What it actually means:** Eğitilmiş bir modeli yeni veri üzerinde tahmin yapmak için kullanmak. Ağırlık güncellemesi olmaz. Production'da yaptığınız şey budur: girdiyi gönder, çıktıyı al.

### Inductive Bias
- **What people say:** Hiç duymadım
- **What it actually means:** Bir modelin mimarisine işlenmiş varsayımlar. CNN'ler yerel örüntülerin önemli olduğunu varsayar (convolution). RNN'ler sıranın önemli olduğunu varsayar (sıralı işleme). Transformer'lar her şeyin her şeyle ilişkili olabileceğini varsayar (attention). Doğru bias, modelin daha az veriyle daha hızlı öğrenmesine yardım eder.

### JAX
- **What people say:** "Google'ın ML framework'ü"
- **What it actually means:** NumPy uyumlu bir kütüphane; otomatik türev (grad), JIT derleme (jit), otomatik vektörleştirme (vmap) ve çoklu cihaz paralelliği (pmap) ekler. PyTorch'un nesne yönelimli tarzının aksine JAX tamamen fonksiyoneldir — gizli durum yok, yerinde mutasyon yok. Google DeepMind tarafından AlphaFold, Gemini ve büyük ölçekli araştırmalarda kullanılıyor.

## K

### KV Cache
- **What people say:** "Çıkarımı hızlandırır"
- **What it actually means:** Autoregressive üretim sırasında, önceki token'lardan gelen key ve value matrislerini her adımda yeniden hesaplamamak için cache'lemek. Bellek karşılığında hız satın alır. Hızlı LLM çıkarımı için olmazsa olmaz.

## L

### Latent Space
- **What people say:** "Gizli temsil"
- **What it actually means:** Benzer girdilerin yakın noktalara eşlendiği, sıkıştırılmış, öğrenilmiş bir temsil uzayı. Autoencoder'lar, VAE'ler ve diffusion modeller hep latent space'te çalışır. Girdiden daha düşük boyutludur ama önemli yapıyı yakalar.

### Learning Rate
- **What people say:** "Yapay zekanın ne hızda öğrendiği"
- **What it actually means:** Gradient descent sırasında adım büyüklüğünü kontrol eden bir skaler. Çok yüksek: minimumu aşar ve ıraksar. Çok düşük: çok yavaş yakınsar ya da takılır. Tek başına en önemli hiperparametre.

### LLM (Large Language Model)
- **What people say:** "Yapay zeka" veya "beyin"
- **What it actually means:** Bir dizide bir sonraki token'ı tahmin etmek üzere eğitilmiş, milyarlarca parametreye sahip, internet ölçeğinde metin verisinde eğitilmiş transformer tabanlı bir sinir ağı

### LoRA (Low-Rank Adaptation)
- **What people say:** "Verimli fine-tuning"
- **What it actually means:** Tüm ağırlıkları güncellemek yerine, orijinal ağırlıkların yanına küçük düşük ranklı matrisler eklemek. Sadece bu küçük matrisler eğitilir, bellek 10-100 kat azalır

### Loss Function
- **What people say:** "Yapay zekanın ne kadar yanıldığı"
- **What it actually means:** Tahmin ile gerçek çıktı arasındaki farkı ölçen bir fonksiyon. Eğitim bu fonksiyonu minimize eder. Regresyon için MSE, sınıflandırma için cross-entropy, embedding'ler için contrastive loss. Loss fonksiyonu seçimi, modele göre "iyi"nin ne anlama geldiğini tanımlar.

## M

### Mixed Precision
- **What people say:** "Hız için eğitim numarası"
- **What it actually means:** İleri geçiş ve çoğu işlem için float16 (daha hızlı, daha az bellek), ama gradyan biriktirme ve ağırlık güncellemesi için float32 (daha hassas) kullanmak. İhmal edilebilir doğruluk kaybıyla 2 kat hız sağlar.

### MoE (Mixture of Experts)
- **What people say:** "Modelin yalnızca bir kısmı çalışır"
- **What it actually means:** Çok sayıda "uzman" alt ağı olan, bir yönlendirme mekanizmasının her girdiyi yalnızca birkaç uzmana gönderdiği bir model. Tüm model devasadır ama her ileri geçiş ucuzdur çünkü uzmanların çoğu atlanır. Mixtral ve GPT-4 bunu kullanır.

### MCP (Model Context Protocol)
- **What people say:** "Yapay zekanın tool kullanması için bir yol"
- **What it actually means:** Yapay zeka uygulamalarının dış veri kaynaklarına ve tool'lara nasıl bağlanacağını standartlaştıran açık bir protokol (stdio/HTTP üzerinde JSON-RPC); tool, kaynak ve prompt'lar için tipli şemalar içerir

## N

### NaN (Not a Number)
- **What people say:** "Eğitim çöktü"
- **What it actually means:** Tanımsız sonucu (0/0, inf-inf) gösteren bir kayan nokta değeri. Eğitimde NaN loss genelde şu demek: çok yüksek learning rate, patlayan gradyanlar, sıfırın logaritması veya sıfıra bölme. Eğitim başarısız olduğunda kontrol edeceğiniz ilk şey.

### Normalization
- **What people say:** "Veriyi ölçeklemek"
- **What it actually means:** Değerleri standart bir aralığa çekmek. Batch normalization bir batch boyunca normalleştirir. Layer normalization feature'lar boyunca normalleştirir. İkisi de eğitimi stabilize eder ve daha yüksek learning rate'lere izin verir.

## O

### Overfitting
- **What people say:** "Model veriyi ezberledi"
- **What it actually means:** Modelin eğitim verisinde iyi, görmediği veride kötü performans göstermesi. Sinyali değil gürültüyü öğrenmiştir. Çözüm: daha çok veri, regularization (dropout, weight decay), early stopping, data augmentation, daha basit model.

### Optimizer
- **What people say:** "Ağırlıkları güncelleyen şey"
- **What it actually means:** Gradyanları kullanarak model parametrelerini güncelleyen bir algoritma. SGD en basiti. Adam en yaygını. Her optimizer'ın farklı özellikleri var: yakınsama hızı, bellek kullanımı, hiperparametre hassasiyeti.

## P

### Parameter
- **What people say:** "Model boyutu"
- **What it actually means:** Modeldeki öğrenilebilir bir değer, tipik olarak bir ağırlık ya da bias. "7B parametre" = 7 milyar öğrenilebilir sayı. Her float32 parametre 4 byte kaplar, yani 7B parametre = sadece ağırlıklar için 28GB bellek.

### Perplexity
- **What people say:** "Modelin ne kadar kafasının karıştığı"
- **What it actually means:** Ortalama cross-entropy loss'un üsteli. Düşük olması iyidir. Perplexity 10, modelin her adımda 10 token arasından üniform seçim yapıyor gibi belirsiz olduğu anlamına gelir.

### Precision & Recall
- **What people say:** "Doğruluk metrikleri"
- **What it actually means:** Precision = işaretlediklerinin kaçı doğruydu. Recall = tüm doğruların kaçını yakaladın. İkisi takas eder: her spam e-postayı yakalamak (yüksek recall) daha çok yanlış alarm demektir (düşük precision). F1 skoru ikisinin harmonik ortalamasıdır. Yanlış pozitiflerin maliyeti yüksekse precision'a, yanlış negatiflerin maliyeti yüksekse recall'e bakın.

### Prompt Engineering
- **What people say:** "Yapay zekayla doğru şekilde konuşmak"
- **What it actually means:** İstenen çıktıları güvenilir biçimde üretmek için girdi metnini tasarlamak — system prompt'lar, few-shot örnekler, format talimatları ve chain-of-thought tetikleyicileri dahil

### Prompt Injection
- **What people say:** "Yapay zekayı kelimelerle hacklemek"
- **What it actually means:** Girdideki zararlı metnin sistem prompt'unu veya talimatları geçersiz kıldığı bir saldırı. Doğrudan injection: kullanıcı "Önceki talimatları yok say" yazar. Dolaylı injection: getirilen bir belgenin içinde gizli talimatlar olur. LLM'in SQL injection karşılığı. Tam bir çözümü yok — savunma; katmanlar halinde girdi doğrulama, çıktı filtreleme ve ayrıcalık ayrımı.

## Q

### QLoRA
- **What people say:** "LoRA, ama daha ucuzu"
- **What it actually means:** Quantized LoRA. Dondurulmuş baz model ağırlıklarını 4-bit hassasiyette (NF4 formatı) tutarken LoRA adapter'larını 16-bit eğitir. Standart LoRA'ya kıyasla belleği 3-4 kat daha azaltır. LoRA ile 14GB gerektiren bir 7B model, QLoRA ile 4-6GB'a sığar. Çoğu benchmark'ta kalite, tam fine-tuning'in %1 yakınında.

## R

### RAG (Retrieval-Augmented Generation)
- **What people say:** "Arama yapabilen yapay zeka"
- **What it actually means:** Bir bilgi tabanından (embedding benzerliği kullanarak) ilgili belgeleri çekip prompt'a sıkıştırdığınız ve LLM'in bu bağlama dayanarak cevap verdiği bir desen
- **Why it's called that:** Retrieval (belgeleri bul) + Augmented (prompt'a ekle) + Generation (LLM cevabı yazar)

### RLHF (Reinforcement Learning from Human Feedback)
- **What people say:** "Yapay zekayı yardımcı yapma yöntemi"
- **What it actually means:** Bir eğitim hattı: (1) model çıktıları üzerinden insan tercihlerini topla, (2) bu tercihler üzerinde bir ödül modeli eğit, (3) LLM'i daha yüksek ödüllü çıktılar üretecek şekilde PPO ile optimize et

### Quantization
- **What people say:** "Modeli küçültmek"
- **What it actually means:** Model ağırlıklarının hassasiyetini float32'den (4 byte) int8 (1 byte) ya da int4'e (0.5 byte) düşürmek. Küçük bir doğruluk kaybı karşılığında 4-8 kat daha az bellek ve daha hızlı çıkarım. GPTQ, AWQ ve GGUF yaygın formatlardır.

### ReLU
- **What people say:** "Aktivasyon fonksiyonu"
- **What it actually means:** Rectified Linear Unit: f(x) = max(0, x). En basit doğrusal olmayan aktivasyon. Hesaplaması hızlı, pozitif değerlerde doymuyor. Her yerde kullanılır çünkü çalışıyor ve ucuz. Varyantları: LeakyReLU, GELU, SiLU.

### ROUGE
- **What people say:** "Özetleme metriği"
- **What it actually means:** Recall-Oriented Understudy for Gisting Evaluation. Üretilen metin ile referans metin arasındaki örtüşmeyi ölçer. ROUGE-1 unigram eşleşmelerini, ROUGE-2 bigram eşleşmelerini, ROUGE-L en uzun ortak alt diziyi sayar. Hesaplaması ucuz, ama yalnızca yüzeysel benzerliği ölçer — aynı anlama gelen iki cümle farklı kelimelerle yazılmışsa düşük puan alır.

## S

### Semantic Search
- **What people say:** "Anlamı anlayan akıllı arama"
- **What it actually means:** Belgeleri anahtar kelime eşleştirmesi yerine anlama göre bulmak. Sorguyu ve tüm belgeleri aynı vektör uzayına gömün, ardından embedding'leri sorgu embedding'ine en yakın olan belgeleri döndürün. "ödeme başarısız", "işlem reddedildi"yi tek bir ortak kelime olmamasına rağmen bulur. Embedding modelleri + vektör veritabanlarıyla çalışır.

### Streaming
- **What people say:** "Yanıtın kelime kelime belirmesi"
- **What it actually means:** LLM'in token'ları üretildikçe, tüm yanıtı beklemeden göndermesi. Server-Sent Events (SSE) ya da WebSocket protokollerini kullanır. İlk token'a kadar algılanan gecikmeyi saniyelerden milisaniyelere indirir. Production sohbet arayüzleri için zorunlu. Her parça bir delta içerir (kısmi token ya da kelime).

### Self-Attention
- **What people say:** "Modelin neye odaklanacağına karar verme şekli"
- **What it actually means:** Her token kendi query, key ve value vektörlerini hesaplar. İki token arasındaki attention ağırlığı = query ve key'lerinin nokta çarpımının ölçeklenip softmax'tan geçirilmesi. Çıktı = value vektörlerinin ağırlıklı toplamı. Her token'ın diğer her token'ı görmesine olanak verir.

### SFT (Supervised Fine-Tuning)
- **What people say:** "Modele talimat takip etmeyi öğretmek"
- **What it actually means:** Önceden eğitilmiş bir modeli (talimat, yanıt) çiftleriyle fine-tune etmek. Model, talimat verildiğinde yanıtı üretmeyi öğrenir. Bir baz modeli sohbet modeline çeviren şey budur.

### Softmax
- **What people say:** "Sayıları olasılığa çevirir"
- **What it actually means:** softmax(x_i) = exp(x_i) / sum(exp(x_j)). Rasgele gerçek sayılardan oluşan bir vektörü olasılık dağılımına dönüştürür (hepsi pozitif, toplam 1). Sınıflandırma başlıklarında, attention ağırlıklarında ve olasılık gerektiğinde her yerde kullanılır.

### Swarm
- **What people say:** "Arılar gibi birlikte çalışan bir grup yapay zeka agent'ı"
- **What it actually means:** Durumu paylaşan ve mesaj geçişi yoluyla koordine olan birden çok agent; merkezi kontrol yerine basit bireysel kurallardan kendiliğinden davranış doğar

## T

### System Prompt
- **What people say:** "Yapay zekanın talimatları"
- **What it actually means:** Bir konuşmanın başında modelin davranışını, kişiliğini ve kısıtlarını ayarlayan özel bir mesaj. Kullanıcı mesajlarından önce işlenir. Çoğu UI'da kullanıcıya görünmez. Modelin ne yapması ve yapmaması gerektiğini, tonunu, format tercihlerini ve alan odağını tanımlar. Kullanıcı prompt'larından farklıdır — system prompt'lar geliştirici tarafından ayarlanır.

### Tensor
- **What people say:** "Çok boyutlu dizi"
- **What it actually means:** Derin öğrenme framework'lerinin temel veri yapısı. 0B tensor bir skaler, 1B vektör, 2B matris, 3B+ ise tensor'dur. PyTorch ve JAX'te tensor'lar otomatik türev için hesaplama geçmişlerini takip eder ve CPU ya da GPU'da yaşayabilir. Sinir ağındaki tüm girdiler, çıktılar, ağırlıklar ve gradyanlar birer tensor'dur.

### Token
- **What people say:** "Kelime"
- **What it actually means:** BPE gibi bir tokenleştiricinin ürettiği alt sözcük birimi (İngilizcede tipik olarak 3-4 karakter). "unbelievable" 3 token olabilir: "un" + "believ" + "able". Türkçede kelimeler eklerle uzadığı için tek bir kelime birden çok token'a bölünür.

### Temperature
- **What people say:** "Yaratıcılık ayarı"
- **What it actually means:** Softmax öncesinde logit'leri bölen bir skaler. Temperature=1 varsayılan. Yüksek = daha düz dağılım = daha rasgele çıktılar. Düşük = daha sivri dağılım = daha deterministik. Temperature=0 argmax'tır (her zaman en olası token'ı seç).

### Transfer Learning
- **What people say:** "Önceden eğitilmiş bir modeli kullanmak"
- **What it actually means:** Bir görevde eğitilmiş modeli alıp başka bir göreve uyarlamak. Erken katmanlar genel öznitelikleri (kenarlar, söz dizimi örüntüleri) öğrenir ve bu bilgi taşınabilir. Sadece sonraki katmanlar göreve özgü eğitim gerektirir. Bu nedenle BERT'i herhangi bir NLP görevine fine-tune edebilirsiniz.

### Transformer
- **What people say:** "Modern yapay zekanın altındaki mimari"
- **What it actually means:** Sıraları, recurrence yerine self-attention ile (her pozisyonun diğer her pozisyona bakmasına izin vererek) işleyen ve büyük ölçekli paralelleşmeye olanak veren bir sinir ağı mimarisi
- **Why it's called that:** Girdi temsillerini attention katmanları aracılığıyla çıktı temsillerine "dönüştürür" (transform eder)

## U

### Underfitting
- **What people say:** "Model öğrenmiyor"
- **What it actually means:** Modelin, verideki örüntüleri yakalamak için fazla basit kalması. Eğitim loss'u yüksek kalır. Çözüm: daha çok parametre, daha çok katman, daha uzun eğitim, daha az regularization, daha iyi feature'lar.

## V

### VAE (Variational Autoencoder)
- **What people say:** "Üretken bir model"
- **What it actually means:** Encoder çıktısını Gauss dağılımına uymaya zorlayarak düzgün bir latent space öğrenen autoencoder. Bu dağılımdan örnekleyip decode ederek yeni veri üretebilirsiniz. Reparameterization trick'i, backpropagation üzerinden eğitilebilir kılar.

### Vector Database
- **What people say:** "Yapay zeka için özel bir veritabanı"
- **What it actually means:** Vektörleri (yoğun float dizileri) saklamak ve hızlı yaklaşık en yakın komşu araması yapmak için optimize edilmiş veritabanı. Benzerlik araması, RAG ve öneri sistemlerinin çekirdek işlemi.

## W

### Weight
- **What people say:** "Modelin öğrendiği şey"
- **What it actually means:** Modelin parametre matrisindeki tek bir sayı. Girdi boyutu 768, çıktı boyutu 3072 olan bir doğrusal katmanda 768*3072 = 2.359.296 ağırlık vardır. Eğitim, her ağırlığı loss fonksiyonunu minimize edecek şekilde ayarlar.

### Weight Decay
- **What people say:** "Regularization"
- **What it actually means:** Loss fonksiyonuna, ağırlıkların büyüklüğüyle orantılı bir ceza eklemek. L2 regularization'a denktir. Ağırlıkların aşırı büyümesini engeller. Tipik değer: 0.01-0.1.

## Z

### Zero-Shot
- **What people say:** "Eğitime gerek yok"
- **What it actually means:** Bir modeli, açıkça eğitilmediği bir görevde, prompt'ta göreve özgü hiçbir örnek olmadan kullanmak. Model, ön eğitimden genelleme yapar. Büyük modeller, yeni görev formatlarını idare edecek kadar çeşitlilik gördüğü için işe yarar.
