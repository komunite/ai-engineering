---
name: prompt-reward-model-designer
description: RLHF alignment için reward model eğitim pipeline'ı tasarla
version: 1.0.0
phase: 10
lesson: 7
tags: [rlhf, reward-model, ppo, alignment, human-feedback, preference-learning]
---

# Reward Model Tasarımcısı

Bir dil modelini hedef davranışa (yardımseverlik, kodlama yeteneği, güvenlik, dürüstlük) hizalamak için bir RLHF pipeline'ı kurarken, veri toplama protokolünü tasarlamak, reward model'i eğitmek ve PPO'yu yapılandırmak için bu çerçeveyi kullan.

## Girdi Gereksinimleri

Şunu sağla:
- **Hedef davranış** (örn. "yardımcı ve zararsız asistan", "uzman Python kodlayıcısı", "güvenlikli tıbbi Q&A")
- **Base model** (örn. SFT sonrası Llama 3 8B, Mistral 7B Chat)
- **Reward model boyutu** (tipik olarak policy modeliyle aynı boyut veya daha büyük)
- **Annotation bütçesi** (insan saati veya mevcut karşılaştırma çifti)
- **Compute bütçesi** (reward model eğitimi + PPO için GPU saati)

## Adım 1: Preference Veri Toplama

### Annotation Protokolü

1. **Prompt seçimi**: SFT eğitim dağılımından artı dağılım dışı prompt'lardan (%10-20 yeni) örnekle
2. **Yanıt üretimi**: Farklı sıcaklıklarla (0.3, 0.7, 1.0) SFT modelini kullanarak prompt başına 2-4 yanıt üret
3. **Karşılaştırma formatı**: Annotator'a tam olarak 2 yanıt göster ve "Hangi yanıt daha iyi?" diye sor
4. **Kriter rubric'i**: Kullanım senaryon için "daha iyi"nin ne anlama geldiğini tanımla

### Rubric Template

| Kriter | Ağırlık | Açıklama |
|-----------|--------|-------------|
| Yardımseverlik | %40 | Soruyu tam ve doğru cevaplıyor mu? |
| Zararsızlık | %25 | Zararlı, önyargılı veya yanıltıcı içerikten kaçınıyor mu? |
| Dürüstlük | %20 | Halüsinasyon yerine belirsizliği kabul ediyor mu? |
| Özlülük | %15 | Yanıt soru için uygun uzunlukta mı? |

Kullanım senaryon için ağırlıkları ayarla. Bir kodlama asistanı doğruluğu %60, özlülüğü %20 ağırlıklayabilir.

### Veri Boyutu Yönergeleri

| Ölçek | Karşılaştırma Çifti | Annotator Saati | Beklenen RM Doğruluğu |
|-------|-----------------|-----------------|---------------------|
| Minimum uygulanabilir | 5,000-10,000 | 400-800 | %60-65 |
| Üretim v1 | 20,000-50,000 | 1,600-4,000 | %65-72 |
| Üretim v2 | 100,000-500,000 | 8,000-40,000 | %72-78 |

InstructGPT 40 yüklenicisinden 33000 karşılaştırma kullandı. Anthropic'in ilk makalesi 20 annotator'dan 22000 kullandı. Annotator'lar arası uzlaşı tipik olarak %70-75 -- reward model insan uzlaşı seviyelerini aşamaz.

### Kalite Kontrol

- **Uzlaşı filtreleme**: %70'ten az annotator'ın uzlaştığı çiftleri at
- **Annotator kalibrasyonu**: Gerçek annotation öncesi bilinen-iyi çiftlerle kalibrasyon turları çalıştır
- **Önyargı tespiti**: Annotator'ların tutarlı şekilde daha uzun yanıtları, resmi dili veya spesifik kalıpları tercih edip etmediğini izle
- **Adversarial örnekler**: Dikkatli okumayan annotator'ları yakalamak için tasarlanmış %5-10 örnek dahil et

## Adım 2: Reward Model Mimarisi

### Mimari Kararları

| Karar | Öneri | Gerekçe |
|----------|---------------|-----------|
| Base mimari | Policy ile aynı transformer | SFT checkpoint'ten weight başlatma güçlü başlangıç feature'ları verir |
| Output head | Son hidden state'ten tek linear projeksiyon | En tam pozisyon temsilinden skaler reward |
| Model boyutu | >= policy model boyutu | Küçük RM PPO'yu istikrarsızlaştıran güvenilmez sinyaller üretir |
| İnitializasyon | Yeni output head ile SFT checkpoint | Pretrain edilmiş feature'lar dil kalitesini zaten yakalar |

### Eğitim Konfigürasyonu

| Parametre | Aralık | Notlar |
|-----------|-------|-------|
| Learning rate | 1e-5 - 5e-5 | SFT'den düşük çünkü görev daha basit |
| Epoch | 1-3 | Sınırlı karşılaştırma verisi ile overfitting büyük risk |
| Batch boyutu | 64-256 | Her "örnek" bir çift, yani effective veri 2x |
| Loss fonksiyonu | Bradley-Terry: -log(sigmoid(r_preferred - r_rejected)) | Pairwise karşılaştırmalar için standart |
| Validation split | %10-20 | Tutulan çiftlerde doğruluğu izle |

### Değerlendirme Metrikleri

1. **Pairwise doğruluk**: RM tutulan preference çiftlerinin ne kadarını doğru sıralıyor? Hedef: > %65
2. **Margin dağılımı**: (r_preferred - r_rejected) dağılımını çiz. Negatif çok az, 0 üstünde merkezlenmiş olmalı.
3. **Kalibrasyon**: sigmoid(r_preferred - r_rejected) gerçek insan preference olasılığına yakın mı?
4. **OOD genelleme**: Eğitimden farklı dağılım promptları üzerinde test et. Doğruluk < %10 düşmeli.

## Adım 3: PPO Konfigürasyonu

### Hiperparametreler

| Parametre | Tipik Değer | Çok Yüksek Olma Etkisi | Çok Düşük Olma Etkisi |
|-----------|--------------|-------------------------|------------------------|
| KL katsayısı (beta) | 0.01-0.05 | Model zar zor öğrenir, SFT'ye fazla yakın kalır | Reward hacking, dejenere çıktılar |
| Learning rate | 5e-6 - 3e-5 | Eğitim istikrarsızlığı, divergence | Yavaş yakınsama, compute israfı |
| Clip oranı (epsilon) | 0.1-0.3 | Büyük, potansiyel olarak istikrarsızlaştırıcı güncellemeler | Çok muhafazakâr güncellemeler, yavaş öğrenme |
| Batch başına PPO epoch | 1-4 | Mevcut batch'e overfitting | Her batch'in yetersiz kullanımı |
| Generation batch boyutu | 128-512 | Bellek sorunları | Gürültülü gradient tahminleri |
| Max yanıt uzunluğu | 256-1024 | Yavaş üretim, bellek sorunları | Faydalı yanıtları keser |

### İzleme Paneli

PPO eğitimi sırasında bu metrikleri takip et:

1. **Ortalama reward**: Eğitim boyunca artmalı. Plato sorun değil; düşüş istikrarsızlık anlamına gelir.
2. **KL divergence**: 10-20 nat altında kalmalı. Sıçrama = reward hacking.
3. **Yanıt uzunluğu**: Stabil kalmalı. Monoton artış = verbosity reward hacking.
4. **Entropy**: Token dağılım entropisi yavaş düşmeli. Hızlı düşüş = mode collapse.
5. **Reward model uzlaşısı**: PPO yanıtlarını reward model ile puanla; uzlaşı iyileşmeli.

### PPO Sırasında Kırmızı Bayraklar

| Belirti | Olası Sebep | Düzeltme |
|---------|-------------|-----|
| Reward artıyor ama çıktılar bozuluyor | Reward hacking | KL katsayısını artır, RM'i adversarial örneklerle yeniden eğit |
| KL divergence patlıyor | Learning rate fazla yüksek veya KL katsayısı fazla düşük | lr'yi azalt, beta'yı artır |
| Yanıt uzunluğu monoton büyüyor | RM verbosity'i ödüllendiriyor | Reward'a uzunluk cezası ekle, RM'i length-controlled çiftlerle yeniden eğit |
| Tüm yanıtlar aynı oluyor | Mode collapse | Generation sıcaklığını artır, PPO epoch'unu azalt |
| Reward vahşice salınıyor | PPO istikrarsızlığı | Learning rate'i azalt, clip oranını artır |

## Adım 4: Uçtan Uca Doğrulama

RLHF-eğitilmiş bir modeli deploy etmeden önce:

1. **SFT vs A/B test**: SFT ve RLHF modellerini 200+ test promptu üzerinde çalıştır. 3+ değerlendirici yanıtları karşılaştırsın. RLHF model > %60 kazanmalı.
2. **Güvenlik değerlendirmesi**: Bilinen adversarial promptlarda (jailbreak'ler, zararlı istekler) test et. RLHF model uygun şekilde reddetmeli.
3. **Regresyon kontrolü**: Standart benchmark'ları (MMLU, HumanEval, MT-Bench) çalıştır ve RLHF modelinin temel yetenekleri kaybetmediğini doğrula.
4. **Forgetting kontrolü**: Genel metin corpus'unda perplexity ölç. SFT modeline kıyasla artış < %10 olmalı.
5. **Uzunluk analizi**: SFT ve RLHF modelleri arasında ortalama yanıt uzunluğunu karşılaştır. RLHF > %50 daha uzunsa, reward modelinin muhtemelen verbosity önyargısı var.
