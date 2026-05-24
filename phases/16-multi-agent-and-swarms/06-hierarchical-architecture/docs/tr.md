# Hiyerarşik Mimari ve Başarısızlık Modu

> Hiyerarşik, iç içe supervisor demektir. Manager agent'lar sub-manager'ların, onlar da worker'ların üzerinde. CrewAI `Process.hierarchical` ders kitabı versiyonudur: bir `manager_llm` dinamik olarak görevleri delege eder ve çıktıları doğrular. LangGraph eşdeğeri `create_supervisor(create_supervisor(...))`'dır. Görev gerçek bir organizasyon şeması olduğunda doğal desendir. Aynı zamanda yönetim döngüsüne en çok çökme olasılığı olan desendir — manager agent'lar işi kötü atar, alt-çıktıları yanlış yorumlar veya konsensüse ulaşamaz. Sequential genellikle onu yener.

**Tür:** Öğrenim + Yapım
**Diller:** Python (stdlib)
**Ön koşullar:** Faz 16 · 05 (Supervisor Deseni)
**Süre:** ~60 dakika

## Sorun

Supervisor deseni oturduktan sonra doğal sonraki adım "ya worker'lar kendileri de supervisor olsaydı?" oluyor. Takımların alt-takımları var; şirketlerin departmanların departmanları var. Hiyerarşik mimariler bunu yansıtır.

Sorun: LLM manager'lar insan manager'larla aynı değil. İnsan manager'ın çalışanlarının ne bildiğine dair stabil önyargıları vardır. LLM manager her turda context'inde ne varsa ondan org'u yeniden akıl yürütür. O context'te ufak bir kayma ve tüm ağaç işi yanlış dağıtır.

## Kavram

### Şekil

```
                 Manager
                 ┌─────┐
                 └──┬──┘
           ┌────────┴────────┐
           ▼                 ▼
       Sub-Mgr A         Sub-Mgr B
       ┌─────┐           ┌─────┐
       └──┬──┘           └──┬──┘
         ┌┴──┬──┐          ┌┴──┐
         ▼   ▼  ▼          ▼   ▼
       W1  W2  W3         W4  W5
```

Her iç node planlar, delege eder ve sentezler. Yalnızca yapraklar iş yapar.

### Nerede parlar

- **Net org eşlemesi.** Gerçek görev departmansal ise ("hukuk dokümanı incele, finans dokümanı incele, mühendislik dokümanı incele, sonra üst yönetim için özetle"), hiyerarşi açıktır.
- **Yerel özetleme.** Her sub-manager üst manager görmeden önce takımının çıktısını sentezler. Üst manager on beş worker çıktısını değil, üç sub-manager özetini görür.

### Nerede kırılır

2026 post-mortem'lerinin bulmaya devam ettiği üç başarısızlık modu:

1. **Görev atama hatası.** Manager hedefi okur, bir parçalamayı halüsinasyon yapar ve yanlış sub-manager'a delege eder. Sub-manager itaatkar bir şekilde verilene çalıştığı için, hata yalnızca üst sentezde ortaya çıkar — bir insanın yakalayabileceği yerden bir seviye uzaklıkta.
2. **Çıktı yanlış yorumu.** Sub-manager "X iddiası doğrulanamadı" döndürür. Üst manager "X iddiası onaylanmadı" olarak özetler. Anlam her seviyede kayar.
3. **Konsensüs döngüleri.** İki sub-manager anlaşmaz; üst manager onlardan uzlaşmalarını ister; aşağı yeniden delege ederler; worker'lar yeniden çalışır; sub-manager'lar biraz farklı cevaplar döndürür; döngü. CrewAI'nın `Process.hierarchical`'ı buna karşı step limit ile korur, ama limitin kendisi artık bir hyperparameter'dır.

### Karar verici soru

Sequential (lineer pipeline) vs hiyerarşik: görevin gerçekten bağımsız alt-takımları var mı, yoksa ağaç gibi davranan tek bir lineer akış mı? İkincisi ise, sequential kullan. İlki ise, hiyerarşik kullan ama açık uzlaşma kuralları için bütçe ayır.

### CrewAI'nın implementasyonu

`Process.hierarchical` uzmanlaşmış crew'ların üzerine bir manager LLM bağlar. Manager:

- üst-seviye görevi alır,
- alt görevleri crew'lara atar,
- crew çıktılarını değerlendirir,
- kabul, yeniden-delege etme ya da iterasyon arasında karar verir.

Dokümantasyon: https://docs.crewai.com/en/introduction (Core Concepts altında "Hierarchical Process"a bak).

### LangGraph'in implementasyonu

LangGraph iç içe `create_supervisor` çağrıları kullanır. İç supervisor'ın kendi grafı var; dış supervisor iç grafı opak bir node olarak ele alır. Bu CrewAI'dan hata ayıklama için daha temizdir (her grafta ayrı ayrı adım atabilirsin) ama ağacın dinamik yeniden şekillendirmesini ifade etmek daha zordur.

Referans: https://reference.langchain.com/python/langgraph-supervisor.

## İnşa Et

`code/main.py` 3 seviyeli bir hiyerarşi çalıştırır:

- üst manager: bir görevi "engineering" ve "legal" dallarına böler,
- engineering sub-manager: "frontend" ve "backend" worker'larına böler,
- legal sub-manager: bir worker.

Demo, herkesin anlaştığı mutlu yolu, üst manager'ın parçalamasının "legal"i "finance" olarak yanlış etiketlediği bir **bozulmuş yola** karşı kontrast eder ve hatanın nasıl yığınlaştığını izler — sub-manager itaatkar bir şekilde finans işi yapar, üst sentezleyici finans bulgularını rapor eder, orijinal hukuk sorusu yanıtsız kalır.

Çalıştır:

```
python3 code/main.py
```

Çıktı "ne soruldu" vs "ne teslim edildi"nin net bir yan yana gösterimiyle her iki yolu gösterir.

## Kullan

`outputs/skill-hierarchy-fitness.md` belirli bir görevin hiyerarşik, sequential ya da flat supervisor kullanması gerekip gerekmediğini değerlendirir. Girdiler: görev tanımı, org yapısı, uzlaşma bütçesi. Çıktı: korunulması gereken belirli başarısızlık modlarıyla desen önerisi.

## Yayınla

Hiyerarşik gönderirsen:

- **Ağaç derinliğini 2'de sınırla.** Üç seviye zaten çoğu hatayı observability'den gizler.
- **Açık uzlaşma bütçesi.** Üst manager commit etmek zorunda olmadan önce maks tur sayısı belirle. Genellikle 2.
- **Her sentezde provenance.** Her node'un özeti hangi yaprak çıktılarının ürettiğini belirtmeli.
- **Parçalama kaymasında uyarı.** Manager'ın parçalamasını adım başına log'la; kullanıcı sorgusuna karşı diff'le. Parçalama artık sorguyu kapsamıyorsa alarm tetikle.

## Alıştırmalar

1. `code/main.py`'yi çalıştır ve mutlu vs bozulmuşu karşılaştır. Üst çıktının kullanıcının sorusundan tamamen ayrışması için kaç seviye manager handoff gerekiyor?
2. Üçüncü bir seviye ekle (üst → sub → sub-sub → worker). Derinlik büyüdükçe bozulmuş yolun kendini ne sıklıkla düzelttiğini vs tamamen ayrıştığını ölç.
3. Her sub-manager'da her zaman orijinal kullanıcı sorusunu değişiksiz soran bir "canary" worker uygula. Parçalama kaymasını tespit etmek için canary cevabını kullan. Canary sentezlenmiş cevapla anlaşmadığında manager nasıl tepki vermeli?
4. CrewAI'nın `Process.hierarchical` dokümanlarını oku. CrewAI'nın uyguladığı somut bir guardrail belirle (step limit, manager_llm kısıtı) ve hangi başarısızlık modunu hedeflediğini açıkla.
5. İç içe LangGraph supervisor'larını CrewAI hiyerarşik ile karşılaştır. Hangisi uzlaşma döngülerini tespit etmeyi daha ucuz yapar?

## Anahtar Terimler

| Terim | İnsanların söylediği | Aslında ne anlama geliyor |
|------|----------------|------------------------|
| Hiyerarşik | "Org şeması deseni" | Supervisor'ların supervisor'lar üzerinde; yalnızca yapraklar iş yapar. |
| Manager LLM | "Patron" | Bir iç node'da parçalayan, atayan ve doğrulayan LLM. |
| Parçalama kayması | "Patron olayı kaybetti" | Üst manager'ın bölmesi artık orijinal soruyu kapsamıyor. |
| Uzlaşma döngüsü | "Sonsuz toplantılar" | Sub-manager'lar anlaşmaz; üst yeniden delege eder; worker'lar yeniden çalışır; bütçe bitene kadar döngü. |
| Derinlik-2 tavanı | "2 seviyeden derine gitme" | Ampirik guardrail: 3+ seviye observability'yi çökertir. |
| Canary sorusu | "Her seviyede ground truth" | Kaymayı tespit etmek için her zaman orijinal sorguyu değişiksiz alan bir worker. |
| Provenance zinciri | "Kim ne dedi" | Her sentezden onu üreten yaprak çıktılarına geri trace. |

## İleri Okuma

- [CrewAI introduction — Process.hierarchical](https://docs.crewai.com/en/introduction) — manager LLM ile ders kitabı hiyerarşik
- [LangGraph supervisor reference](https://reference.langchain.com/python/langgraph-supervisor) — `create_supervisor` üzerinden iç içe supervisor
- [Anthropic engineering — Research system](https://www.anthropic.com/engineering/multi-agent-research-system) — Anthropic'in hiyerarşik yerine bilinçli olarak flat supervisor'ı neden seçtiği
- [Cemri ve diğ. — Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) — MAST taksonomisi; koordinasyon başarısızlıkları bölümü parçalama kaymasını belgeler
