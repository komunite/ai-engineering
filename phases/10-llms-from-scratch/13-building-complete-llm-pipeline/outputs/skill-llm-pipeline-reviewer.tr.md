---
name: llm-pipeline-reviewer
description: Milyon dolarlık bir koşudan önce uçtan uca LLM eğitim pipeline manifest'ini incele.
version: 1.0.0
phase: 10
lesson: 13
tags: [pipeline, training, manifest, eval-gate, cost, rollback]
---

Önerilen bir eğitim pipeline manifest'i (tokenizer, veri, pretraining, SFT, alignment, değerlendirme, quantization ve sunum aşamalarını tanımlayan YAML veya JSON) verildiğinde, şunları kapsayan bir inceleme üret:

1. Aşama grafiği. Her aşamanın typed girdi ve çıktıları olduğunu doğrula. Eksik bağımlılıkları, implicit state'i veya adlandırılmış artifact hash yerine çıplak directory tüketen herhangi bir aşamayı işaretle.
2. Hash zinciri. N aşamasının output_hash'i her downstream aşamanın input_hashes'lerinden birine eşit olduğunu doğrula. Herhangi bir uyumsuzluk manifest'in tutarsız olduğu anlamına gelir ve pipeline başlamamalıdır.
3. Eval geçidi. Geçit listesindeki her metrik sayısal olmalı, bir operatöre, eşiğe ve ölçüm kaynağına sahip olmalı. Sübjektif ("iyi görünüyor"), sınırsız (eşik yok) veya eğitim verisinde ölçülen herhangi bir geçidi reddet.
4. Regresyon koruması. Yeni modelin temel benchmark'larında (MMLU, MATH, HumanEval+, GPQA veya domain'e özgü eşdeğer) baseline numaraları olmalı. Baseline'sız koşu, regresyon tespiti olmayan koşudur.
5. KL bütçesi. Alignment aşamaları (RLHF, DPO, CAI, GRPO) reference'a karşı kümülatif bir KL üst sınırı bildirmeli. Sınırsız KL, sınırsız drift demektir.
6. Contamination kontrolü. Eğitim veri shard'ları ve değerlendirme setlerinin belgelenmiş bir örtüşme kontrolü olmalı (exact match veya 13-gram). Gerekli pass eşiği: <%0.1.
7. Maliyet tahmini. Her aşama için pre-run tahmini artı toplam, bütçe geçidine karşı karşılaştırılır. Tahmin > bütçe ise pipeline başlatmayı reddeder.
8. Rollback planı. Her aşama için, başarısızlıkta adlandırılmış eylemler: yeniden çalıştır, önceki artifact'a geri dön, girdileri revize edip downstream'i yeniden çalıştır. Pahalı aşamaların (pretraining) sıcak checkpoint stratejisi olmalı.
9. Artifact deposu. Checkpoint'ler, veri setleri, tokenizer'lar, değerlendirme raporları content-addressed olmalı (SHA-256). Filename-addressed artifact'lar ("latest.pt") sert red.
10. Gözlemlenebilirlik. Her aşama trace ID, aşama adı, input hash'ler, output hash, duvar saati ve maliyet ile yapılandırılmış log yaymalı. Eksik trace ID'ler koşunun olaydan sonra hata ayıklanamayacağı anlamına gelir.

İncelemeyi durduran kırmızı bayraklar:
- ölçüm kaynağı eksik geçit (hiçbir aşamanın hesaplamadığı bir metrik üzerinde geçit)
- bir downstream aşamayla checkpoint paylaşan bir aşama (sorumluluk ayrımı yok)
- reference modeli olmayan bir alignment aşaması (KL için çapa yok)
- yargıcın policy ile aynı model ailesinden olduğu LLM-as-judge değerlendirme (contamination)
- bütçeyi %20'den fazla aşan maliyet tahmini
- yalnızca "sıfırdan yeniden çalıştır"dan oluşan rollback planı

Çıktı: geçit başına PASS/HOLD, her verdiği üreten tam manifest alanı veya eksik alan ile iki sayfalık inceleme ve bir HOLD'u PASS'e çevirmek için gereken minimum değişiklik.
