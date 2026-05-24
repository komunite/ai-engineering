---
name: workbench-benchmark
description: Aynı görevi bir projenin kendi sample app'i üzerinde prompt-only ve workbench-rehberli pipeline'lardan geçir ve beş sonuçlu bir before/after raporu yay.
version: 1.0.0
phase: 14
lesson: 41
tags: [benchmark, before-after, evaluation, workbench, sample-app]
---

Bir repo, agent ürünü ve küçük bir sample app verildiğinde, prompt-only'i workbench-rehberli pipeline'a karşı karşılaştıran taşınabilir bir değerlendirme harness'ı üret.

Üret:

1. `eval/sample_app/` — projenin alanından alınmış minimum-viable bir sample app.
2. Her biri bir görev tanımı alan ve bir `TaskOutcome` döndüren `eval/run_prompt_only.py` ve `eval/run_workbench.py`.
3. Her iki pipeline'ı çalıştıran ve `before-after-report.md` artı `comparison.json` yazan `eval/report.py`.
4. Sabit bir görev suite'inde workbench sonuçları gerilediğinde başarısız olan CI workflow'u.
5. Beş sonucu ve neyin regresyon sayıldığını açıklayan `docs/benchmark.md`.

Sert ret durumları:

- Yalnızca bir pipeline'lı benchmark. Karşılaştırma tüm meseledir.
- Payda olmadan yüzde olarak ifade edilen sonuçlar. Her zaman `n / m` raporla.
- Agent ürününün üzerinde eğitildiği bir sample app. Alana ayarlanmış bir fixture kullan.
- False negative'leri gizleyen raporlar. Prompt-only'in daha hızlı olduğu görevler sıralanmalı.

Reddetme kuralları:

- Projenin kabul komutu yoksa, benchmark'ı göndermeyi reddet. Ölçülecek hiçbir şey yok.
- Workbench pipeline'ı median görevde prompt-only pipeline'ın 3x'inden fazlasını alıyorsa, bu bulguyu yüzdür; workbench sadeleştirmeye ihtiyaç duyar, model değil.
- Harness offline çalışamıyorsa, CI'ya bağlamayı reddet. Network flakiness karşılaştırmayı bozar.

Çıktı yapısı:

```
<repo>/
├── eval/
│   ├── sample_app/
│   ├── run_prompt_only.py
│   ├── run_workbench.py
│   └── report.py
├── outputs/eval/
│   ├── before-after-report.md
│   └── comparison.json
├── docs/benchmark.md
└── .github/workflows/benchmark.yml
```

"Bundan sonra ne okumalı" notu ile bitir:

- Workbench pipeline tarafından kullanılan her yüzeyi paketleyen capstone pack için Lesson 42.
- Bunu tamamlayan makro benchmark'lar için Lesson 19 (SWE-bench, GAIA, AgentBench).
- Benchmark bağlandıktan sonra devam eden eval döngüleri için Lesson 30 (Eval-Driven Agent Development).
