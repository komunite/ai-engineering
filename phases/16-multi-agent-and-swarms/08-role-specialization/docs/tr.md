# Rol Uzmanlaşması — Planner, Critic, Executor, Verifier

> 2026'da en yaygın çoklu-agent parçalaması: bir agent planlar, biri yürütür, biri eleştirir ya da doğrular. MetaGPT (arXiv:2308.00352) bunu rol prompt'larına kodlanmış SOP'lar olarak formelleştirir — Product Manager, Architect, Project Manager, Engineer, QA Engineer — `Code = SOP(Team)` formülünü izleyerek. ChatDev (arXiv:2307.07924) designer, programmer, reviewer, tester'ı "communicative dehallucination" ile bir "chat chain" üzerinden zincirler (agent'lar eksik detayları açıkça ister). Verifier yük taşıyıcıdır: Cemri ve diğ. (MAST, arXiv:2503.13657) her çoklu-agent başarısızlığının eksik ya da bozuk doğrulamaya izlenebileceğini gösterir. PwC, CrewAI'daki yapılandırılmış doğrulama döngülerinden 7× doğruluk kazanımı (%10 → %70) rapor etti.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 04 (Primitive Model), Faz 16 · 05 (Supervisor)
**Süre:** ~60 dakika

## Sorun

Jenerik çoklu-agent sistemler jenerik çıktı üretir. Bir grup chat'teki üç kodcu aynı vasat kodun üç çeşidini yazar. Daha fazla agent ekleyebilir, daha fazla tur ekleyebilirsin ve hâlâ kalite eşiğini geçemezsin.

Çözüm daha fazla agent değil — *farklı* agent'lar. Belirgin roller ata. Critic'e planner'ın sahip olmadığı tool'lar ver. Verifier'a objektif bir test suite ver. Şimdi sistemde sadece paralel tahmin değil, temellendirilmiş düzeltmeyle iç anlaşmazlık var.

## Kavram

### Dört kanonik rol

**Planner.** Hedefi okur, bir adım listesi ya da bir spec üretir. Tool'lar: bilgi getirme, dokümanlar. Çıktı: yapılandırılmış plan.

**Executor.** Tek seferde bir plan adımı okur, artefaktı üretir. Tool'lar: gerçek iş tool'ları (kod derleyici, shell, API client). Çıktı: artefakt.

**Critic.** Executor'ın çıktısını planner'ın niyetine karşı okur. Tool'lar: artefakta salt-okunur erişim, statik analiz. Çıktı: nedenlerle kabul/red.

**Verifier.** Artefaktı okur ve deterministik bir kontrol çalıştırır. Tool'lar: test runner, type checker, schema validator. Çıktı: kanıtla pass/fail.

Critic özneldir, fikirlidir, genellikle LLM-tabanlıdır. Verifier objektiftir, deterministiktir, genellikle kod-tabanlıdır. Aynı rol değildirler.

### MetaGPT'in SOP deseni

MetaGPT (arXiv:2308.00352) yazılım mühendisliği SOP'larını rol prompt'ları olarak kodlar:

- **Product Manager** PRD'yi yazar.
- **Architect** sistem tasarımını üretir.
- **Project Manager** görevleri böler.
- **Engineer** uygular.
- **QA Engineer** testleri çalıştırır.

Her rolün katı bir input/output şeması vardır. Rol prompt'u rolün ne *olduğunu* ve ne *üretmesi gerektiğini* söyler. `Code = SOP(Team)` formülü — deterministik SOP'lar bir LLM takımını öngörülebilir bir pipeline'a dönüştürür.

### ChatDev'in communicative dehallucination'ı

ChatDev temel bir hamle ekler: executor planda olmayan belirli bir detaya ihtiyaç duyduğunda, devam etmeden önce designer'a açıkça sorar. Bu, klasik LLM başarısızlığı olan detayı makulane uydurmayı önler.

Uygulama: rol prompt'u "verilmediği belirli bilgiye ihtiyaç duyduğunda, çıktı üretmeden önce ilgili role ismiyle sor"u içerir.

### Verifier neden en önemli

Cemri ve diğ. (MAST) 1642 çoklu-agent yürütme başarısızlığını izledi. %21.3'ü doğrulama boşluklarıydı — sistem kimsenin kontrol etmediği bir cevap gönderdi. Kalan %79 genellikle "sessizce başarısız olan ya da hiç çalıştırılmayan bir kontrol vardı"a dayanır. Doğrulama yük taşıyıcı roldür.

PwC rapor etti (CrewAI dağıtımları, 2025) ki yapılandırılmış bir doğrulama döngüsü eklemek doğruluğu %10'dan %70'e taşıdı. Bir roldan 7× kazanım.

### Critic vs verifier

- Critic bir artefaktı kalite için inceleyen bir LLM'dir. Özneldir. Makul prozayla kandırılabilir.
- Verifier artefakt üzerinde çalışan deterministik bir programdır. Objektiftir. Kanıtla pass/fail verir.

İkisini de kullan. Critic, verifier'ın ifade edemediği zevk sorunlarını yakalar. Verifier, critic'in göremediği bug'ları yakalar çünkü onlar yalnızca runtime'da görünür.

### Anti-desen

Sistemindeki her rol bir LLM ve her rolün çıktısı "bence iyi". Klasik MAST başarısızlık modu. Pass/fail'i LLM tarafından değil kod tarafından kararlaştırılan en az bir verifier ekle.

### Framework eşlemeleri

- **CrewAI** — `Agent(role, goal, backstory)` ders kitabı uzmanlaşma yüzeyidir.
- **LangGraph** — node'ların uzmanlaşmış prompt'ları olabilir; kenarlar pipeline'ı zorunlu kılar.
- **AutoGen** — bir GroupChat'te tek kelimelik isimli role-özgü ConversableAgent'lar.
- **OpenAI Agents SDK** — role-uzmanlaşmış Agent'lar arası handoff tool'ları.

## İnşa Et

`code/main.py` basit bir Python fonksiyonu inşa eden 4-rol pipeline'ı uygular:

- **Planner** bir spec üretir.
- **Executor** bir kod string'i üretir.
- **Critic** (LLM-simüle edilmiş) bariz sorunları işaretler.
- **Verifier** üretilen kodu bir sandbox'ta (`exec`) bir test case'e karşı çalıştırır.

Demo iki kez çalışır: executor'ın doğru kod ürettiği (critic + verifier ikisi de geçer) ve executor'ın spec-dışı kod ürettiği bir kez (critic bug'ı kaçırır çünkü makul görünür, verifier yakalar çünkü test başarısız olur).

Çalıştır:

```
python3 code/main.py
```

## Kullan

`outputs/skill-role-designer.md` bir görev alır ve rol kadrosunu (3-5 rol), rol başına input/output şemasını ve verifier kontrolünü üretir. Agent'ları bir framework'e bağlamadan önce bunu kullan.

## Yayınla

Kontrol listesi:

- **En az bir deterministik verifier.** Asla tüm-LLM değil.
- **Rol başına açık I/O şeması.** Planner proza değil bir spec döndürür; executor o şemayı okur.
- **Communicative dehallucination.** Executor bilgi eksik olduğunda planner'a sormalı; asla uydurmamalı.
- **Critic/verifier sıralaması.** Critic'i önce çalıştır (ucuz, tasarım sorunlarını yakalar), verifier'ı ikinci (yavaş, bug'ları yakalar).
- **Döngü bütçesi.** İnsana eskalasyondan önce maks 2 critic-executor revizyon turu.

## Alıştırmalar

1. `code/main.py`'yi çalıştır ve verifier'ın critic'in kaçırdığı bug'ı nasıl yakaladığını gözlemle. Ek bir verifier olarak statik analiz kontrolü (`return` sayısı) ekle. Runtime test'in kaçırdığı neyi yakalar?
2. 5. bir rol ekle: kullanıcı isteğini planner-hazır spec'e çeviren "requirements analyst". Hangi communicative dehallucination talepleri ona yukarı akmalı?
3. MetaGPT Bölüm 3 ("Agents")'i oku. MetaGPT'nin 5 rolünün her birinin input/output şemasını listele.
4. ChatDev'in chat-chain diyagramını (arXiv:2307.07924 Şekil 3) oku. Communicative dehallucination'ın aksi takdirde sonsuz olacak bir döngüyü nerede kırdığını belirle.
5. PwC'nin 7× doğruluk kazanımı doğrulama döngülerinden geldi. Verifier eklemenin yardım etmeyeceği üç görev hipotezleştir — doğruluğun deterministik kontrolünün imkansız ya da yasaklayıcı şekilde pahalı olduğu yerler.

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Rol uzmanlaşması | "Farklı agent'lar, farklı işler" | Planner/executor/critic/verifier rolleri için ayarlanmış belirgin sistem prompt'ları. |
| SOP deseni | "Kodlanmış standart operasyon prosedürü" | MetaGPT'nin çerçevesi: rol başına katı I/O şemaları bir takımı pipeline'a dönüştürür. |
| Communicative dehallucination | "Uydurmadan önce sor" | ChatDev deseni: executor bir detay eksik olduğunda uydurmak yerine planner'a sorar. |
| Critic | "LLM inceleyici" | Öznel, fikirli inceleyici. Zevk sorunlarını yakalar. Makul prozayla kandırılabilir. |
| Verifier | "Deterministik kontrol" | Kod-tabanlı pass/fail. Test runner, type checker, schema validator. Kandırılamaz. |
| Doğrulama boşluğu | "Kimse kontrol etmedi" | MAST başarısızlıklarının %21.3'ü. Bug'ı yakalayacak bir kontrol olmadan cevap gönderildi. |
| Revizyon döngüsü | "Critic geri gönderir" | Critic reddi geri bildirimle executor'ı yeniden çalıştırır. Bütçeye ihtiyaç duyar. |
| Tüm-LLM anti-desen | "Bence iyi" | Her rol LLM, deterministik kontrol yok. Klasik MAST başarısızlığı. |

## İleri Okuma

- [Hong ve diğ. — MetaGPT: Meta Programming for Multi-Agent Collaboration](https://arxiv.org/abs/2308.00352) — rol-prompt-olarak-SOP referans makalesi
- [Qian ve diğ. — Communicative Agents for Software Development (ChatDev)](https://arxiv.org/abs/2307.07924) — chat chain + communicative dehallucination
- [Cemri ve diğ. — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) — MAST taksonomisi; doğrulama boşlukları başarısızlıkların %21.3'ü
- [CrewAI docs — Agent roles](https://docs.crewai.com/en/introduction) — üretim rol spesifikasyon yüzeyi
