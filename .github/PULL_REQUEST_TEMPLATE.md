<!--
Katkınız için teşekkürler. Uygulanan kısımları doldurun, uymayan bölümleri silin.
İngilizce şablon için: https://github.com/rohitg00/ai-engineering-from-scratch/blob/main/.github/PULL_REQUEST_TEMPLATE.md
-->

## Bu PR ne yapıyor

<!-- Tek cümlelik özet. -->

## Değişiklik türü

- [ ] Yeni ders (yalnızca Türkçe çeviri ya da yeni Türkçe içerik için — İngilizce ders eklemek istiyorsan upstream'e PR aç: `rohitg00/ai-engineering-from-scratch`)
- [ ] Mevcut bir derse düzeltme (Türkçe metin)
- [ ] Yeni çeviri (`docs/tr.md`, `outputs/*.tr.md`, `quiz.tr.json`)
- [ ] Yeni çıktı (prompt, skill, agent, MCP server)
- [ ] Web sitesi / build / araçlar
- [ ] Sözlük / terim çevirisi (`glossary/terms.tr.md`)

## Checklist

- [ ] Kod, listelenen bağımlılıklarla hatasız çalışıyor
- [ ] Kod dosyalarında yorum yok (açıklama doc'ta, kod kendini açıklıyor)
- [ ] Önce sıfırdan inşa, sonra framework (yeni dersler için)
- [ ] Ders klasörü `LESSON_TEMPLATE.tr.md` yapısıyla eşleşiyor
- [ ] ROADMAP satırı markdown link biçiminde (`[Ad](phases/...)`), düz metin değil
- [ ] Ders başına tek commit (atomik per-lesson kuralı)
- [ ] Yerel olarak test edildi / kod çıktısı `docs/tr.md` ya da `docs/en.md`'nin iddia ettiğiyle eşleşiyor
- [ ] Çeviri için: `CLAUDE.md`'deki çeviri konvansiyonları (bölüm başlıkları, çevrilmeyen teknik terimler) takip edildi
- [ ] Quiz çevirisi varsa: `python3 -c "import json; json.load(open('FILE'))"` ile JSON doğrulandı; `stage`, `correct`, `options` sırası korundu

## Faz / ders

<!-- örn. Faz 5 · 03-tokenizers -->

## Reviewer için notlar

<!-- Şaşırtıcı bir şey, şablondan sapmalar, açık sorular. -->
