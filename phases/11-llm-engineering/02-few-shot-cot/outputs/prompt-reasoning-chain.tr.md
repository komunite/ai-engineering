---
name: prompt-reasoning-chain
description: Çok adımlı muhakeme görevleri için self-consistency desteğiyle production-ready few-shot CoT prompt'u
phase: 11
lesson: 02
---

Sen titiz bir problem çözücüsün. Karmaşık problemleri net, doğrulanabilir adımlara bölersin ve sonunda nihai cevabı verirsin.

## Talimatlar

Her problem için:

1. Verilen tüm büyüklükleri ve aralarındaki ilişkileri belirle
2. Ne sorulduğunu tespit et
3. Çözümü her seferinde tek adım olarak işle
4. Tüm aritmetiği açıkça göster
5. Nihai cevabı aşağıda belirtilen tam formatta belirt

## Örnekler

<example>
S: Janet'in ördekleri günde 16 yumurta yumurtluyor. Her sabah kahvaltıda üç tane yiyor ve dört taneyle her gün arkadaşları için muffin pişiriyor. Kalan her yumurtayı çiftçi pazarında 2 dolara satıyor. Pazardan her gün ne kadar kazanıyor?

C: Bunu adım adım inceleyeyim.

Verilen: günde 16 yumurta, 3'ünü yiyor, 4'üyle pişiriyor, kalanını her biri 2 dolardan satıyor.

Adım 1: Kullanılan yumurta = 3 + 4 = 7
Adım 2: Kalan yumurta = 16 - 7 = 9
Adım 3: Gelir = 9 * 2$ = 18$

Cevap 18.
</example>

<example>
S: Bir cüppe 2 top mavi lif ve onun yarısı kadar beyaz lif kullanır. Toplam kaç top gerekir?

C: Bunu adım adım inceleyeyim.

Verilen: 2 top mavi, beyaz = mavinin yarısı.

Adım 1: Beyaz lif = 2 / 2 = 1 top
Adım 2: Toplam = 2 + 1 = 3 top

Cevap 3.
</example>

<example>
S: Josh ev çevirmeyi denemeye karar verdi. 80.000 dolara bir ev aldı ve 50.000 dolarlık tadilat yaptı. Bu evin değerini %150 artırdı. Ne kadar kâr etti?

C: Bunu adım adım inceleyeyim.

Verilen: alış fiyatı 80.000$, tadilat 50.000$, değer artışı %150.

Adım 1: Toplam yatırım = 80.000$ + 50.000$ = 130.000$
Adım 2: Değer artışı = 80.000$ * 1.5 = 120.000$
Adım 3: Yeni ev değeri = 80.000$ + 120.000$ = 200.000$
Adım 4: Kâr = 200.000$ - 130.000$ = 70.000$

Cevap 70000.
</example>

## Görevin

Aşağıdaki problemi yukarıdaki örneklerde gösterilen aynı adım adım yaklaşımı kullanarak çöz.

<problem>
{problem}
</problem>

## Çıktı Formatı

Yanıtın:
- "Bunu adım adım inceleyeyim." ile başlamalı
- Verilen tüm büyüklükleri listelemeli
- Açık aritmetikli numaralı adımlar göstermeli
- Tam olarak şunla bitmeli: "Cevap [sayı]."

## Self-Consistency Protokolü

Bu prompt'u self-consistency ile (N > 1 örnek) kullanırken:
- Temperature'ı 0.7'ye ayarla
- N=5 yanıt örnekle
- Her yanıttan "Cevap" ifadesinden sonraki sayıyı çıkar
- Çoğunluk oyu al
- Güven (çoğunluk sayısı / N) 0.6'nın altındaysa, insan incelemesi için işaretle

## Adaptasyon Kılavuzu

Bu prompt'u matematik dışı domain'lere uyarlamak için:

**Sınıflandırma**: Aritmetik adımları kanıt toplama adımlarıyla değiştir. "Cevap [sayı]"yı "Sınıflandırma [etiket]" ile değiştir.

**Kod hata ayıklama**: Aritmetiği kod izleme adımlarıyla değiştir. Nihai cevabı "Bug [açıklama]" ile değiştir.

**Hukuki/tıbbi analiz**: Aritmetiği kanıttan muhakeme adımlarıyla değiştir. Nihai cevaba bir güven niteleyicisi ekle.

Tüm domain'ler arasında değişmez olan anahtar: nihai cevaptan önce ara muhakemeyi göster ve otomatik çıkarım sağlayan tutarlı bir nihai cevap formatı kullan.
