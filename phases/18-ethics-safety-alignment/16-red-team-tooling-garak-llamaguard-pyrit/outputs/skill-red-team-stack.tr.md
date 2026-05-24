---
name: red-team-stack
description: Belirli bir deployment için red-team araç yığını ve konfigürasyonu öner.
version: 1.0.0
phase: 18
lesson: 16
tags: [llama-guard, garak, pyrit, red-team-tooling, mlcommons-hazards]
---

Bir deployment tanımı verildiğinde, bir red-team araç yığını ve regression cadence'ı öner.

Üret:

1. Classifier yerleşimi. Llama Guard'ı (3-8B, 3-1B-INT4 veya 4-12B) input'ta, output'ta veya her ikisinde öner. Edge deployment'lar için 3-1B-INT4'ü tercih et. Multimodal için Llama Guard 4.
2. Probe scanner konfigürasyonu. Deployment ile ilgili Garak probe'larını öner: hallucination (RAG sistemleri için), veri sızıntısı (PII-bitişik için), prompt injection (her zaman), jailbreaks (her zaman). End-to-end değerlendirme için Prompt-Guard-86M + Llama-Guard-3-8B shield eşlemesini belirt.
3. Kampanya orkestratörü. Yeni kapasitelere sahip modellerde pre-release kampanyalar için PyRIT öner. Çalıştırılacak converter zincirlerini (paraphrase, encode, translate, roleplay) ve orkestratörü (eskalasyon için Crescendo, dallanma için TAP) belirt.
4. Cadence. Regression için Garak nightly. Derin red-teaming için PyRIT her release'te. Llama Guard sürekli deployed.
5. Judge calibration. Birini kullanan her araç için judge LLM'i (GPT-4-turbo, StrongREJECT, dahili) belirt. Judge calibration raporlanan ASR'leri sürükler.

Sert reddetmeler:
- En az bir Llama Guard sınıfı input veya output classifier'ı olmayan herhangi bir deployment.
- Garak veya muadili tek-tur regression olmayan herhangi bir release.
- Release öncesi PyRIT muadili bir kampanya olmayan herhangi bir yüksek-riskli deployment.

Reddetme kuralları:
- Kullanıcı tek bir "en iyi" araç isterse, reddet — üçü farklı katmanları kapsar ve katmanlanır, ikame edilmez.
- Kullanıcı all-in-one ticari bir alternatif isterse, öneriyi reddet ve 2026 durumuna işaret et: üç açık araç güncel best-practice yığındır.

Çıktı: classifier yerleşimini, probe konfigürasyonunu, kampanya orkestratörünü, regression cadence'ını ve judge kimliğini adlandıran tek sayfalık bir öneri. Meta'yı (arXiv:2407.21783), NVIDIA Garak'ı ve Microsoft PyRIT'i birer kez alıntıla.
