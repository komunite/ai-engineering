# Fork Rehberi

> 🌐 **English original:** [`FORKING.md`](FORKING.md) · **Upstream:** [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch) (MIT)

Bu curriculum MIT lisanslıdır. Fork'layıp kendi ihtiyaçların için uyarlamakta serbestsin. İşte bunu iyi yapmanın yolu.

> Bu repo (`komunite/ai-engineering`) zaten upstream'in bir Türkçe fork'udur. İngilizce orijinali fork'lamak istiyorsan [`rohitg00/ai-engineering-from-scratch`](https://github.com/rohitg00/ai-engineering-from-scratch)'e git. Türkçe versiyonu temel almak istiyorsan bu repoyu fork'lamak doğru başlangıç.

## Takımlar için

İç eğitim olarak kullanmak ister misin? Fork'la ve özelleştir:

1. Repoyu fork'la
2. Takımının ihtiyaç duymadığı fazları çıkar
3. Şirkete özel örnekler ve veri ekle
4. Çıktılara dahili tool entegrasyonları ekle
5. Atfı koru — topluluğun büyümesine yardımcı olur

## Okullar & Üniversiteler için

Ders materyali olarak kullanmak ister misin?

1. Repoyu fork'la
2. Fazları semester programına eşle
3. Alıştırmalara değerlendirme rubric'leri ekle
4. Kendi ödevlerini ve sınavlarını ekle
5. İyileştirmeleri upstream'e geri katkılamayı düşün

## Bootcamp'ler için

Ücretli bir bootcamp mı çalıştırıyorsun? MIT altında sorun değil.

1. Fork'la ve kohort takvimine göre yapılandır
2. Video içeriği, canlı oturumlar, mentorluk ekle
3. Kod ve dokümanlar üzerinde inşa etme hakkı sende
4. Projeyi sponsor olmayı ya da geri katkı vermeyi düşün

## Diğer Diller için

Bu curriculum'u farklı bir programlama dilinde öğretmek ister misin?

1. Repoyu fork'la
2. Kod örneklerini kendi dilinde yeniden uygula
3. Ders yapısını ve dokümantasyonu koru
4. Ana README'den fork'unu linklemek için PR aç

## Diğer Doğal Diller için

Curriculum'u farklı bir doğal dile çevirmek ister misin?

1. **Doğrudan dersleri çeviriyorsan:** [upstream repo](https://github.com/rohitg00/ai-engineering-from-scratch)'da `docs/<locale>.md` sibling'leri olarak PR aç — `LOCALE=<xx>` ile build edildiğinde tüm site lokalize çıkacaktır.
2. **Tam ülke/topluluk uyarlaması istiyorsan:** bu Türkçe fork'a (`komunite/ai-engineering`) referans alabilirsin. Aynı locale-aware build pipeline, terim sözlüğü konvansiyonu ve `.tr.md` sibling stratejisi başka diller için de çalışır.

## Fork'unu Güncel Tutmak

Upstream'den İngilizce değişiklikleri almak için:

```bash
git remote add upstream https://github.com/rohitg00/ai-engineering-from-scratch.git

git fetch upstream
git merge upstream/main
```

Canonical İngilizce dosyalar upstream'den geldiği için root'ta `README.md`, `ROADMAP.md` vb. orijinal halinde durur. Türkçe çeviriler yan yana `<base>.tr.md` suffix'i ile yaşar (`README.tr.md`, `ROADMAP.tr.md`, `phases/.../README.tr.md`, `quiz.tr.json` vb.) — upstream merge'leri sırasında sıfır çakışma çıkarır.

## Atıf

MIT tarafından zorunlu kılınmasa da takdir edilir:

```
"AI Engineering from Scratch" temellidir
https://github.com/rohitg00/ai-engineering-from-scratch
```

Türkçe versiyonu temel alıyorsan:

```
"Sıfırdan Yapay Zeka Mühendisliği" temellidir (Komünite Türkçe uyarlaması)
https://github.com/komunite/ai-engineering
Orijinali: https://github.com/rohitg00/ai-engineering-from-scratch
```
