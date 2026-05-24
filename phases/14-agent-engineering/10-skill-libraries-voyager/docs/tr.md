# Skill Library'leri ve Yaşam Boyu Öğrenme (Voyager)

> Voyager (Wang et al., TMLR 2024) yürütülebilir kodu bir skill olarak ele alır. Skill'ler adlandırılmış, getirilebilir, kompoze edilebilir ve ortam feedback'i ile rafine edilir. Claude Agent SDK skill'leri, skillkit ve 2026 skill-library deseni için referans mimari bu.

**Tür:** Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 14 · 07 (MemGPT), Faz 14 · 08 (Letta Block'lar)
**Süre:** ~75 dakika

## Öğrenme Hedefleri

- Voyager'ın üç bileşenini — automatic curriculum, skill library, iterative prompting — ve her birinin rolünü adlandır.
- Voyager'ın aksiyon uzayını neden primitive komutlar değil, kod yaptığını açıkla.
- Registration, retrieval, composition ve failure-driven refinement ile bir stdlib skill library uygula.
- Voyager'ın desenini 2026 Claude Agent SDK skill'lerine ve skillkit ekosistemine eşle.

## Sorun

Her oturumda her yeteneği sıfırdan yeniden kuran agent'lar üç şey yanlış yapar:

1. **Token israfı.** Her görev aynı akıl yürütmeyi yeniden çıkarır.
2. **İlerleme kaybı.** Oturum A'da öğrenilen bir düzeltme oturum B'ye transfer olmaz.
3. **Uzun-ufuk kompozisyonunda başarısızlık.** Karmaşık görevlerin yetenek hiyerarşilerine ihtiyacı var; one-shot prompt'lar bunları ifade edemez.

Voyager'ın yanıtı: her yeniden kullanılabilir yeteneği bir library'de saklanan, benzerlikle getirilebilir, diğer skill'lerle kompoze edilebilir ve yürütme feedback'i ile rafine edilen adlandırılmış bir kod parçası olarak ele al.

## Kavram

### Üç bileşen

Voyager (arXiv:2305.16291) bir agent'ı şunların etrafında yapılandırır:

1. **Automatic curriculum.** Curiosity-driven bir öneren, agent'ın mevcut skill set'i ve ortam state'ine göre bir sonraki görevi seçer. Keşif bottom-up.
2. **Skill library.** Her skill yürütülebilir kod. Bir görev başarılı olduğunda yeni skill'ler eklenir. Skill'ler query-to-description benzerliği ile getirilir.
3. **Iterative prompting mechanism.** Başarısızlıkta agent yürütme hataları, ortam feedback'i ve self-verification çıktısı alır, sonra skill'i rafine eder.

Minecraft değerlendirmesi (Wang et al., 2024): baseline'lara karşı 3.3x daha fazla unique öğe, 8.5x daha hızlı stone tool'lar, 6.4x daha hızlı iron tool'lar, 2.3x daha uzun harita dolaşımı. Sayılar Minecraft'a özgü ama desen transfer eder.

### Aksiyon uzayı = kod

Çoğu agent primitive komutlar yayar. Voyager JavaScript fonksiyonları yayar. Bir skill:

```
async function craftIronPickaxe(bot) {
  await mineIron(bot, 3);
  await mineStick(bot, 2);
  await placeCraftingTable(bot);
  await craft(bot, 'iron_pickaxe');
}
```

Alt-skill'lerden kompoze edilmiş. Description ve embedding ile anahtarlanmış saklanır. Prompt olarak değil program olarak getirilir.

Bu 2026 Claude Agent SDK skill'i: agent'ın talep üzerine yüklediği adlandırılmış, getirilebilir bir kod parçası artı talimatlar.

### Skill retrieval

Yeni görev "diamond pickaxe yap." Agent:

1. Görev açıklamasını embed eder.
2. Skill library'i top-k benzer skill'ler için sorgular.
3. `craftIronPickaxe`, `mineDiamond`, `placeCraftingTable` vb. getirir.
4. Yeni skill'i getirilen primitive'lerden + yeni mantıktan kompoze eder.

MCP resources (Faz 13) ve Agent SDK skill'lerinin uyguladığı desen bu: mevcut göreve scope'lanmış bir bilgi/kod yüzeyi üzerinde retrieval.

### İteratif refinement

Voyager'ın feedback döngüsü:

1. Agent bir skill yazar.
2. Skill ortama karşı çalışır.
3. Üç sinyalden biri döner: `success`, `error` (stack trace ile), `self-verification failure`.
4. Agent skill'i sinyali context olarak kullanarak yeniden yazar.
5. Başarı ya da maks tur'a kadar döngü.

Bu, ortam-topraklanmış doğrulama ile kod üretimine uygulanmış Self-Refine (Ders 05). CRITIC (Ders 05) dış tool'ları doğrulayıcı olarak alan aynı desen.

### Curriculum ve keşif

Voyager'ın curriculum modülü "göl yakınında bir barınak inşa et" gibi görevleri agent'ın neye sahip olduğu ve henüz neyi yapmadığına göre önerir. Öneren, ortam state'i + skill envanterini kullanarak mevcut yeteneğin hemen üstünde bir görev seçer — keşfin sweet spot'u.

Üretim agent'ları için bu bir "neyin eksik" operatörüne tercüme olur: mevcut skill library ve bir domain verildiğinde, hangi skill'leri henüz kapsamıyoruz? Ekipler tipik olarak bunu manuel olarak curriculum review olarak uygular.

### Bu desen nerede ters gider

- **Skill library rot.** Aynı skill biraz farklı açıklamalarla 10 kez eklenmiş. Yazıda deduplication ekle; retrieval yalnızca bir tane döndürür.
- **Komoze-skill drift'i.** Parent skill rafine edilmiş bir child'a bağımlı. Skill'leri versiyonla; v1'e sabitlenmiş bir parent sihirli şekilde v3'ü almaz.
- **Retrieval kalitesi.** Skill açıklamaları üzerinde vector retrieval, library birkaç yüzü geçince degrade eder. Tag filter'ları ve sert kısıtlamalarla destekle ("yalnızca `category=tooling` olan skill'ler").

## İnşa Et

`code/main.py` bir stdlib skill library uyguluyor:

- `Skill` — name, description, code (string olarak), version, tag'ler, bağımlılıklar.
- `SkillLibrary` — register, search (token overlap), compose (bağımlılıkların topolojik sıralaması) ve refine (güncellemede version bump).
- Üç primitive skill kaydeden, bir dördüncüyü kompoze eden, bir başarısızlığa çarpan ve rafine eden scripted bir agent.

Çalıştır:

```
python3 code/main.py
```

Trace library yazılarını, retrieval'i, kompozisyonu, başarısız bir yürütmeyi ve bir v2 refinement'ı gösteriyor — Voyager'ın döngüsü uçtan uca.

## Kullan

- **Claude Agent SDK skill'leri** (Anthropic) — 2026 referansı: her skill'in bir açıklaması, kodu ve talimatları var; bir agent oturumu sırasında talep üzerine yüklenir.
- **skillkit** (npm: skillkit) — 32+ AI kodlama agent'ı için cross-agent skill yönetimi.
- **Custom skill library'leri** — domain'e özgü (data agent'ları için SQL skill'leri, infra agent'ları için Terraform skill'leri). Voyager deseni aşağı ölçeklenir.
- **OpenAI Agents SDK `tools`** — alt uçta; her tool hafif bir skill.

## Yayınla

`outputs/skill-skill-library.md` herhangi bir hedef runtime için registration, retrieval, versiyonlama ve refinement kablolanmış Voyager-şekilli bir skill library üretir.

## Alıştırmalar

1. `compose()`'a bir dependency-cycle detector ekle. Skill A B'ye, B A'ya bağımlıysa ne olur? Hata mı uyarı mı?
2. Skill başına version pinning uygula. Bir parent skill child `crafting@1`'i kompoze ettiğinde, `crafting@2`'ye bir refinement parent'ı sessizce yükseltmemeli.
3. Token-overlap retrieval'i sentence-transformers embedding'leri (ya da stdlib BM25 impl) ile değiştir. 50-skill'lik bir oyuncak library'de retrieval@5'i ölç.
4. Bir "curriculum" agent'ı ekle: mevcut library ve bir domain açıklaması verildiğinde, 5 eksik skill öner. Haftalık çağır.
5. Anthropic'in Claude Agent SDK skill dokümanlarını oku. Oyuncak library'i SDK'nın skill şemasına taşı. Keşfedilebilirlik hakkında ne değişir?

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| Skill | "Yeniden kullanılabilir yetenek" | Benzerlikle getirilebilir adlandırılmış kod parçası + açıklama |
| Skill library | "Agent'ın how-to belleği" | Aranabilir ve kompoze edilebilir kalıcı skill store'u |
| Curriculum | "Görev öneren" | Mevcut yetenek boşluğu tarafından yönlendirilen bottom-up hedef üretici |
| Composition | "Skill DAG'ı" | Skill'ler skill'leri invoke eder; yürütmede topolojik sıralı |
| Iterative refinement | "Self-correcting loop" | Env feedback + hatalar + self-verification sonraki versiyona geri katlanır |
| Action-space-as-code | "Programatik aksiyonlar" | Zamansal olarak uzatılmış davranış için primitive komut değil, fonksiyon yay |
| Yazıda dedup | "Skill collapse" | Yakın-duplikat açıklamalar tek kanonik skill'e çöker |

## İleri Okuma

- [Wang et al., Voyager (arXiv:2305.16291)](https://arxiv.org/abs/2305.16291) — orijinal skill-library makalesi
- [Claude Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — skill'ler 2026 ürünleştirmesi olarak
- [Anthropic, Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) — pratikte skill'ler ve alt-agent'lar
- [Madaan et al., Self-Refine (arXiv:2303.17651)](https://arxiv.org/abs/2303.17651) — Voyager'ın altındaki refinement döngüsü
