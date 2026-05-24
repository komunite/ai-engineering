---
name: skill-library
description: Kayıt, benzerliğe göre retrieval, kompozisyonel yürütme ve başarısızlık-güdümlü iyileştirme ile Voyager-şekilli skill kütüphanesi üret.
version: 1.0.0
phase: 14
lesson: 10
tags: [voyager, skills, library, composition, refinement]
---

Bir hedef runtime ve bir alan verildiğinde, Voyager'ın üç bileşenini destekleyen bir skill kütüphanesi üret: curriculum kancası, geri alınabilir skill store, iteratif iyileştirme.

Üret:

1. `name`, `description`, `code`, `version`, `tags`, `depends_on`, `history` içeren `Skill` tipi. Her write önceki kodu kaydeder.
2. `register(skill, dedup=True)` (yeni veya version artırımı), `search(query, top_k, tag_filter)`, `get(name)`, `topo_order(name)` (bağımlılık çözümleme), `execute(name, context)` (topolojik çalıştırma) ile `SkillLibrary`.
3. Retrieval, tam kütüphane üzerinde LLM scoring değil, embedding similarity veya BM25 kullanmalıdır. LLM re-rank top-k shortlist üzerinde izin verilir.
4. Execution skill başına exception'ları yakalamalı VE iyileştirme döngüsünün tüketebileceği feedback olarak trace'e yüzdürmelidir.
5. Bir iyileştirme kancası: başarısız bir `execute`'tan sonra, runtime (task, skill_name, error, env_state) toplar, bunu modele iletir ve yeniden yazılan skill üzerinde `register` çağırır. Version artar; history eski kodu korur.

Sert ret durumları:

- Skill'lerin kod değil, düzyazı string'leri olduğu bir kütüphane. Skill'ler yürütülebilir. Düzyazı `description`'a ait.
- Topolojik sıralama olmadan kompozisyon. Cycle detection olmadan depth-first skill DAG'larında kırılır.
- Sessiz version üzerine yazma. Her iyileştirme `version`'ı artırmalı VE denetim için eski kodu `history`'ye itmelidir.

Reddetme kuralları:

- Hedef runtime'da skill execution için sandbox yoksa, skill'lerin production sistemlerine dokunduğu alanlar için reddet. Sevkıyat öncesi sandbox talep et (Lesson 09 prensipleri).
- Kullanıcı "iyileştirme olmadan her başarısızlıkta otomatik retry" isterse, reddet. İyileştirme olmadan retry'lar bug'ı amplify eder; düzeltmezler.
- Kütüphane düz retrieval ile ~200 skill'i aşıyorsa, onu "production-ready" diye adlandırmayı reddet. Önce tag filtreleri ve hiyerarşik namespace'ler ekle.

Çıktı: `skill.py`, `library.py`, `execute.py`, `refine.py` ve dedup kuralını, retrieval backend'ini, iyileştirme prompt'unu ve version politikasını açıklayan bir `README.md`. "Bundan sonra ne okumalı" notu ile bitir: Claude Agent SDK entegrasyonu için Lesson 17, OpenAI Agents SDK tool çevirisi için Lesson 16 veya skill-library kalitesini değerlendirmek için Lesson 30.
