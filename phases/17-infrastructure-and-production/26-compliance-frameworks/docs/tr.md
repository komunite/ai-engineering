# Compliance — SOC 2, HIPAA, GDPR, PCI-DSS, EU AI Act, ISO 42001

> Multi-framework kapsama 2026 enterprise anlaşmaları için masada en az gereken. **EU AI Act**: 1 Ağustos 2024'ten beri yürürlükte. Çoğu yüksek-risk gerekliliği 2 Ağustos 2026'da uygulanır. Yüksek-risk sistem yükümlülükleri için €15M ya da küresel yıllık cironun %3'üne kadar ceza (Md. 99(4)); yasaklanmış AI uygulamaları için €35M ya da %7'ye kadar (Md. 99(3)). AB kullanıcılarına hizmet veriyorsa küresel olarak uygulanır. **Colorado AI Act**: 30 Haziran 2026'da etkili (SB25B-004 tarafından Şubat 2026'dan ertelendi) — yüksek-risk sistemler için impact assessment'lar, AI kararlarına itiraz hakkı. Kredi/istihdam/konut/eğitim için Virginia benzeri. **SOC 2 Type II**: B2B AI'da fiili gereklilik (fintech için Type I değil, Type II). **GDPR**: belgelenmiş en büyük AI-spesifik ceza Clearview AI'ya karşı €30.5M (Hollanda DPA, Eyl 2024); İtalya'nın Garante'si Aralık 2024'te OpenAI'a karşı €15M verdi (Mart 2026'da itirazda iptal edildi). Çıkarımda gerçek zamanlı PII redaction savunulabilir standart; post-processing temizleme yeterli değil. **HIPAA**: sağlık bağlı — BAA olmadan PHI'yi dış AI servislerine gönderemezsin. **PCI-DSS**: AI-etkileşim-katmanı kapsaması config + sözleşmesel anlaşmalar gerektirir, otomatik değil. **ISO 42001**: ortaya çıkan AI yönetişim standardı, ISO 27001 yanında büyüyen procurement gerekliliği. Referans profil: OpenAI SOC 2 Type 2, ISO/IEC 27001:2022, ISO/IEC 27701:2019, GDPR/CCPA/HIPAA (BAA)/FERPA, ChatGPT ödeme bileşenleri için PCI-DSS tutar. Cross-framework eşleme audit yorgunluğunu azaltır: erişim kontrolleri ISO 27001 A.5.15-5.18, GDPR Md. 32, HIPAA §164.312(a) genelinde eşlenir.

**Tür:** Öğrenim
**Diller:** (Python opsiyonel — compliance kod değil, politika + süreç)
**Ön koşullar:** Faz 17 · 25 (Güvenlik), Faz 17 · 13 (Observability)
**Süre:** ~60 dakika

## Öğrenme Hedefleri

- LLM ürünlerine ilişkili yedi 2026 framework'ünü say ve her birini bir müşteri segmentine eşle.
- EU AI Act uygulama zaman çizelgesini (Ağustos 2024'te yürürlükte; Ağustos 2026'da yüksek-risk uygulaması) ve iki-katmanlı ceza tavanını (yüksek-risk yükümlülükleri için €15M / %3, yasaklanmış uygulamalar için €35M / %7) alıntıla.
- Post-processing PII temizlemenin GDPR için neden yeterli olmadığını açıkla ve gerçek zamanlı çıkarım-katmanı redaction'ını savunulabilir standart olarak adlandır.
- Cross-framework kontrol eşlemeyi tarif et (örn. erişim kontrolü ISO 27001 A.5.15-5.18 + GDPR Md. 32 + HIPAA §164.312(a)'ya eşlenir).

## Sorun

Bir enterprise müşterinin procurement'ı SOC 2 Type II, GDPR, HIPAA BAA, ISO 27001 ve "EU AI Act compliance ifadesi" istiyor. Takımın SOC 2 Type I'da. Type II'den altı ay uzaktasın ve GDPR Article 30 kayıtlarına başlamadın.

Multi-framework kapsama bir LLM sorunu değil — LLM-spesifik üst katmanlarıyla bir enterprise-SaaS sorunu. 2026'da procurement takımları PDF değil, framework başına satır ve kontrol başına sütunlu bir matris istiyor.

## Kavram

### Yedi framework

| Framework | Kapsam | LLM-spesifik gereklilik |
|-----------|-------|--------------------------|
| SOC 2 Type II | B2B SaaS baseline'ı | Süreç kontrolleri 6-12 ay üzerinde audit edildi |
| HIPAA | ABD sağlık | BAA gerekli; imzalı anlaşma olmadan PHI altyapıdan ayrılamaz |
| GDPR | AB kullanıcıları | Gerçek zamanlı PII redaction; data subject hakları; Md. 30 kayıtları |
| PCI-DSS | Ödeme verisi | Ödemeye dokunan AI için config + sözleşmeler |
| EU AI Act | AB kullanıcılarına hizmet | Risk tier sınıflandırma; yüksek-risk sistemler: conformity assessment, dokümantasyon, logging |
| Colorado AI Act | CO sakinlerine hizmet | Impact assessment'lar; itiraz hakkı |
| ISO 42001 | AI yönetişim | Ortaya çıkan; ISO 27001 ile eşleşir |

### EU AI Act zaman çizelgesi

- 1 Ağustos 2024: yürürlükte.
- 2 Şubat 2025: yasaklanmış-AI uygulamaları uygulandı.
- 2 Ağustos 2026: yüksek-risk sistemler uygulandı (conformity assessment, dokümantasyon, logging).
- Ağustos 2027: uyumlaştırılmış yasama altındaki ürünlerde yüksek-risk sistemler.

Risk tier'ları: Kabul edilemez (yasak), Yüksek-risk (conformity + logging), Sınırlı-risk (şeffaflık), Minimum-risk (kısıt yok). Çoğu B2B LLM SaaS sınırlı-risk; istihdam, kredi, eğitim, hukuk uygulama, göç, temel servisler için yüksek-risk devreye girer.

Cezalar (Madde 99): yüksek-risk-sistem yükümlülüklerinin ihlali için €15M ya da küresel yıllık cironun %3'üne kadar (Md. 99(4)); yasaklanmış AI uygulamaları için €35M ya da %7'ye kadar (Md. 99(3)); hangisi daha yüksekse uygulanır.

### GDPR — gerçek zamanlı redaction standart

Post-processing temizleme (LLM gördükten sonra PII redaction) savunulabilir duruş değil — model veriyi zaten gördü. Gerçek zamanlı çıkarım-katmanı redaction 2026 standardı:

- LLM çağrısından önce entity recognition.
- Tutarlı tokenization (Mesh yaklaşımı) semantiği korur.
- Yalnız redacted prompt'ları + onaylı opt-in ham'ı sakla.

Yakın yaptırım: Clearview AI'ya karşı €30.5M (Hollanda DPA, Eyl 2024) bugüne kadar belgelenmiş en büyük AI-spesifik GDPR cezası; OpenAI'a karşı €15M (İtalya'nın Garante'si, Ara 2024) en büyük LLM-spesifik ceza, ama Mart 2026'da itirazda iptal edildi ve karar hâlâ daha fazla inceleme altında. Post-processing iddiaları audit'te başarısız oldu.

### HIPAA — BAA opsiyonel değil

İmzalı bir Business Associate Agreement olmadan PHI'yi dış AI servislerine gönderemezsin. Üç hyperscaler LLM platformu (Bedrock, Azure OpenAI, Vertex) BAA sunar. OpenAI direkt API BAA sunar. Anthropic direkt API BAA sunar. PHI göndermeden önce doğrula.

### SOC 2 Type II

Type I: tasarlanmış ve belgelenmiş kontroller.
Type II: kontroller 6-12 ay boyunca etkili olarak çalışır.

2026'da B2B procurement varsayılan olarak Type II. Type I başlangıç; Type II gate.

Yaygın audit sürücüleri: erişim log'ları (kim neyi gördü), değişim yönetimi (nasıl deploy edildi), risk değerlendirmeleri (üç aylık), olay yanıtı (test edildi mi?). Faz 17 · 25'teki audit log doğrudan yeniden kullanılabilir.

### Cross-framework eşleme

Tek bir erişim kontrol politikası birden fazla framework kontrolünü karşılar:

| Kontrol | Framework'ler |
|---------|-----------|
| Erişim logging | ISO 27001 A.5.15-5.18, GDPR Md. 32, HIPAA §164.312(a) |
| Değişim yönetimi | ISO 27001 A.8.32, PCI DSS Req. 6, HIPAA breach-notification scope |
| Transit'te encryption | ISO 27001 A.8.24, GDPR Md. 32, HIPAA §164.312(e) |
| Secret yönetimi | ISO 27001 A.8.19, PCI DSS Req. 8, SOC 2 CC6.1 |

Compliance araçları (Drata, Vanta, Secureframe) bu eşlemeyi otomatize eder. Ölçekte maliyete değer.

### ISO 42001 — ortaya çıkan

2023 sonunda yayınlandı. ISO 27001 yanında büyüyen procurement gerekliliği. Risk yönetimi, veri kalitesi, şeffaflık, insan denetimi dahil AI yönetişim için framework.

### OpenAI'ın referans profili

OpenAI SOC 2 Type 2, ISO/IEC 27001:2022, ISO/IEC 27701:2019, GDPR/CCPA/HIPAA (BAA)/FERPA, ChatGPT ödeme bileşenleri için PCI-DSS tutar. Bu 2026'da kabaca enterprise masa kazığı.

### Hatırlaman gereken sayılar

- EU AI Act cezaları: €15M / %3'e kadar (yüksek-risk yükümlülükleri, Md. 99(4)); €35M / %7'ye kadar (yasaklanmış uygulamalar, Md. 99(3)).
- EU AI Act yüksek-risk uygulaması: 2 Ağustos 2026.
- En büyük belgelenmiş AI-spesifik GDPR cezası: €30.5M, Clearview AI (Hollanda DPA, Eyl 2024).
- En büyük LLM-spesifik GDPR cezası: €15M, OpenAI (İtalya'nın Garante'si, Ara 2024; Mart 2026 itirazda iptal edildi).
- SOC 2 Type II penceresi: 6-12 ay işletilen kontroller.
- Colorado AI Act yürürlük tarihi: 30 Haziran 2026 (SB25B-004 tarafından Şubat 2026'dan ertelendi).

## Kullan

`code/main.py` Python'da bir compliance-eşleme spreadsheet'i — bir kontrol verildiğinde, karşıladığı framework'leri listeler.

## Yayınla

Bu ders `outputs/skill-compliance-matrix.md` üretir. Müşteri segmenti ve coğrafya verildiğinde, gereken framework'leri ve kontrolleri belirtir.

## Alıştırmalar

1. İlk enterprise müşterin SOC 2 Type II, HIPAA BAA, EU AI Act ifadesi gerektiriyor. Anlaşmayı kazanmak için minimum yaşayabilir compliance duruşu ne?
2. Üç hipotetik LLM ürününü EU AI Act risk tier'larına sınıflandır. Yüksek-riskte ne değişir?
3. Yanlışlıkla BAA olmadan bir sağlayıcıya PHI gönderdin. Olay yanıtını adım adım yaz.
4. Orta-pazar bir AI vendor için ISO 42001'in "2026'da gerekli" olup olmadığını savun.
5. LLM audit log alanlarını (Faz 17 · 25) en az üç framework kontrolüne eşle.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| SOC 2 Type II | "audit edilmiş kontroller" | Bağımsız attestasyonla 6-12 ay boyunca işletilen kontroller |
| HIPAA BAA | "sağlık sözleşmesi" | Business Associate Agreement; PHI için gerekli |
| GDPR | "AB gizliliği" | Gerçek zamanlı PII redaction savunulabilir 2026 standardı |
| EU AI Act | "AB AI kuralları" | Yüksek-risk uygulaması Ağustos 2026; €15M / %3 (yüksek-risk yükümlülükleri) — €35M / %7 (yasaklanmış uygulamalar) |
| Colorado AI Act | "ABD AI eyalet yasası" | 30 Haziran 2026 yürürlük (SB25B-004 tarafından ertelendi); impact assessment'lar |
| ISO 42001 | "AI yönetişim" | AI riski + şeffaflık için ortaya çıkan framework |
| ISO 27001 | "güvenlik ISMS'i" | Information Security Management System baseline'ı |
| Conformity assessment | "AB AI doc paketi" | Yüksek-risk gerekliliği: doc'lar, testing, logging |
| Cross-framework eşleme | "bir kontrol, çok framework" | Tek bir politika birden fazla framework kontrolünü karşılar |

## İleri Okuma

- [OpenAI Security and Privacy](https://openai.com/security-and-privacy/) — referans compliance profili.
- [GuardionAI — LLM Compliance 2026: ISO 42001, EU AI Act, SOC 2, GDPR](https://guardion.ai/blog/llm-compliance-guide-iso-42001-eu-ai-act-soc2-gdpr-2026)
- [Dsalta — SOC 2 Type 2 Audit Guide 2026: 10 AI Controls](https://www.dsalta.com/resources/ai-compliance/soc-2-type-2-audit-guide-2026-10-ai-powered-controls-every-saas-team-needs)
- [EU AI Act official text](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) — birincil kaynak.
- [Colorado AI Act](https://leg.colorado.gov/bills/sb24-205) — birincil kaynak.
- [ISO/IEC 42001:2023](https://www.iso.org/standard/81230.html) — AI yönetim sistemi standardı.
