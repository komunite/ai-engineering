# Chatbot'lar — Kural Tabanlıdan Sinirsele LLM Agent'larına

> ELIZA pattern match'leriyle cevap verdi. DialogFlow niyetleri eşledi. GPT ağırlıklardan cevapladı. Claude araçları çalıştırıp doğrular. Her dönem öncekinin en kötü başarısızlığını çözdü.

**Tür:** Öğrenim
**Diller:** Python
**Ön koşullar:** Faz 5 · 13 (Soru-Cevap), Faz 5 · 14 (Bilgi Erişimi)
**Süre:** ~75 dakika

## Sorun

Bir kullanıcı "I want to change my flight." diyor. Sistemin ne istediğini, hangi bilginin eksik olduğunu, onu nasıl alacağını ve eylemi nasıl tamamlayacağını çözmesi gerekiyor. Sonra kullanıcı "wait, what if I cancel instead?" diyor ve sistemin bağlamı hatırlaması, görev değiştirmesi ve state'i koruması gerekiyor.

Konuşma bir ML sistemi için zordur. Girdi açık uçludur. Çıktının birçok tur boyunca tutarlı olması gerekir. Sistemin dünya üzerinde harekete geçmesi gerekebilir (bir uçuşu değiştir, bir kart çek). Her yanlış adım kullanıcıya görünür.

Chatbot mimarileri dört paradigmadan döndü, her biri öncekinin çok belirgin biçimde başarısız olduğu için tanıtıldı. Bu ders onları sırayla yürür. 2026 üretim manzarası son ikisinin bir hibridiidir.

## Kavram

![Chatbot evrimi: kural tabanlı → retrieval → sinirsel → agent](../assets/chatbot.svg)

**Kural tabanlı (ELIZA, AIML, DialogFlow).** Elle yazılmış pattern'ler kullanıcı girdisini eşler ve yanıtlar üretir. Niyet sınıflandırıcıları önceden tanımlı akışlara yönlendirir. Slot-doldurma state machine'leri gerekli bilgiyi toplar. Tasarlandığı dar kapsamın içinde mükemmel çalışır. Dışında hemen başarısız olur. Halüsinasyonun tolere edilmediği güvenlik-kritik alanlarda (banka kimlik doğrulama, havayolu rezervasyonu) hâlâ gönderiliyor.

**Retrieval tabanlı.** Bir FAQ tarzı sistem. Her (söyleyiş, yanıt) çiftini encode et. Çalışma zamanında, kullanıcının mesajını encode et ve en yakın saklı yanıtı getir. Zendesk'in klasik "benzer makaleler" özelliğini düşün. Paraphrase'leri kurallardan daha iyi ele alır. Üretim yok, dolayısıyla halüsinasyon yok.

**Sinirsel (seq2seq).** Konuşma logları üzerinde eğitilmiş encoder-decoder. Sıfırdan yanıtlar üretir. Akıcı ama generic çıktılara ("I don't know") ve factual drift'e eğilimli. Asla güvenilir biçimde konu üzerinde değil. Google, Facebook ve Microsoft'un 2016-2019'da hayal kırıklığı yaratan chatbot'larının sebebi budur.

**LLM agent'ları.** Plan yapan, araçları çağıran ve sonuçları doğrulayan bir döngüye sarmalanmış bir dil modeli. Uzun bir prompt ile chatbot değil. Bir agent döngüsü: planla → aracı çağır → sonucu gözlemle → sonraki adıma karar ver. Retrieval-first grounding (RAG) onu halüsinasyondan korur. Tool çağrıları gerçekten bir şeyler yapmasına izin verir. 2026 mimarisi budur.

Dört paradigma sıralı yer değiştirmeler değildir. 2026 üretim chatbot'u dördünden geçer: kimlik doğrulama ve destructive eylemler için kural tabanlı, FAQ için retrieval, doğal ifadeleme için sinirsel üretim, belirsiz açık uçlu sorgular için LLM agent.

## İnşa Et

### Adım 1: kural tabanlı pattern eşleme

```python
import re


class RulePattern:
    def __init__(self, pattern, response_template):
        self.regex = re.compile(pattern, re.IGNORECASE)
        self.template = response_template


PATTERNS = [
    RulePattern(r"my name is (\w+)", "Nice to meet you, {0}."),
    RulePattern(r"i (need|want) (.+)", "Why do you {0} {1}?"),
    RulePattern(r"i feel (.+)", "Why do you feel {0}?"),
    RulePattern(r"(.*)", "Tell me more about that."),
]


def rule_based_respond(user_input):
    for pattern in PATTERNS:
        m = pattern.regex.match(user_input.strip())
        if m:
            return pattern.template.format(*m.groups())
    return "I don't understand."
```

20 satırda ELIZA. Reflection numarası ("I feel sad" → "Why do you feel sad") Weizenbaum 1966'dan kanonik psikoterapi demosudur. Hâlâ öğretici.

### Adım 2: retrieval tabanlı (FAQ)

Bu örnekleyici snippet `pip install sentence-transformers` gerektirir (torch'u getirir). Bu dersin çalıştırılabilir `code/main.py`'i yerine stdlib Jaccard similarity kullanır, böylece ders dış bağımlılıklar olmadan çalışır.

```python
from sentence_transformers import SentenceTransformer
import numpy as np


FAQ = [
    ("how do i reset my password", "Go to Settings > Security > Reset Password."),
    ("how do i cancel my order", "Go to Orders, find the order, click Cancel."),
    ("what is your return policy", "30-day returns on unused items, original packaging."),
]


encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
faq_questions = [q for q, _ in FAQ]
faq_embeddings = encoder.encode(faq_questions, normalize_embeddings=True)


def faq_respond(user_input, threshold=0.5):
    q_emb = encoder.encode([user_input], normalize_embeddings=True)[0]
    sims = faq_embeddings @ q_emb
    best = int(np.argmax(sims))
    if sims[best] < threshold:
        return None
    return FAQ[best][1]
```

Eşik tabanlı refusal anahtar tasarım seçimidir. En iyi eşleşme yeterince yakın değilse, `None` döndür ve sistemin escalate etmesine izin ver.

### Adım 3: sinirsel üretim (baseline)

Küçük bir instruction-tuned encoder-decoder (FLAN-T5) ya da fine-tune edilmiş konuşma modeli kullan. 2026'da kendi başına üretimde kullanılamaz (çelişki, konu dışı drift, factual saçmalık), ama doğal ifadeleme için hibrit sistemlerin içinde gönderilir. DialoGPT tarzı decoder-only modeller tutarlı yanıtlar üretmek için açık tur ayırıcılar ve EOS handling gerektirir; bir FLAN-T5 text2text pipeline'ı öğretim örneği için kutudan çıkar çıkmaz çalışır.

```python
from transformers import pipeline

chatbot = pipeline("text2text-generation", model="google/flan-t5-small")

response = chatbot("Respond politely to: Hi there!", max_new_tokens=40)
print(response[0]["generated_text"])
```

### Adım 4: LLM agent döngüsü

2026 üretim şekli:

```python
def agent_loop(user_message, tools, llm, max_steps=5):
    history = [{"role": "user", "content": user_message}]
    for _ in range(max_steps):
        response = llm(history, tools=tools)
        tool_call = response.get("tool_call")
        if tool_call:
            tool_name = tool_call.get("name")
            args = tool_call.get("arguments")
            if not isinstance(tool_name, str) or tool_name not in tools:
                history.append({"role": "assistant", "tool_call": tool_call})
                history.append({"role": "tool", "name": str(tool_name), "content": f"error: unknown tool {tool_name!r}"})
                continue
            if not isinstance(args, dict):
                history.append({"role": "assistant", "tool_call": tool_call})
                history.append({"role": "tool", "name": tool_name, "content": f"error: arguments must be a dict, got {type(args).__name__}"})
                continue
            fn = tools[tool_name]
            result = fn(**args)
            history.append({"role": "assistant", "tool_call": tool_call})
            history.append({"role": "tool", "name": tool_name, "content": result})
        else:
            return response["content"]
    return "I could not complete the task in the step budget."
```

Adı anılacak üç şey. Tools, LLM'in çağırabileceği callable fonksiyonlardır. Döngü, LLM tool çağrısı yerine nihai bir cevap döndürdüğünde sona erer. Step budget belirsiz görevlerde sonsuz döngüleri önler.

Gerçek üretim ekler: retrieval-first grounding (her LLM çağrısından önce ilgili belgeleri enjekte et), guardrail'lar (onay olmadan destructive eylemleri reddet), observability (her adımı logla) ve evaluations (agent davranışının spec'te kaldığı otomatik kontroller).

### Adım 5: hibrit yönlendirme

```python
def hybrid_chat(user_input):
    if is_destructive_action(user_input):
        return structured_flow(user_input)

    faq_answer = faq_respond(user_input, threshold=0.6)
    if faq_answer:
        return faq_answer

    return agent_loop(user_input, tools, llm)


def is_destructive_action(text):
    danger_words = ["delete", "cancel", "charge", "refund", "transfer"]
    return any(w in text.lower() for w in danger_words)
```

Desen: destructive olan her şey için deterministik kurallar, hazır FAQ'lar için retrieval, geri kalan her şey için LLM agent'lar. 2026 müşteri-destek sistemlerinde gönderilen şey budur.

## Kullan

2026 stack'i:

| Kullanım durumu | Mimari |
|---------|---------------|
| Rezervasyon, ödeme, kimlik doğrulama | Kural tabanlı state machine'lar + slot filling |
| Müşteri destek FAQ'ları | Kuratlanmış cevaplar üzerinde retrieval |
| Açık uçlu yardım sohbeti | RAG + tool call'lar ile LLM agent |
| İç araçlar / IDE asistanları | Tool call'lar (search, read, write) ile LLM agent |
| Companion / karakter chatbot'ları | Persona system prompt'lu, bilgi üzerinde retrieval'lı ayarlanmış LLM |

Üretimde her zaman hibrit yönlendirme kullan. Hiçbir tek mimari her isteği iyi ele almaz. Yönlendirme katmanının kendisi tipik olarak küçük bir niyet sınıflandırıcısıdır.

## Hâlâ gönderilen başarısızlık modları

- **Özgüvenli uydurma.** LLM agent, tamamlamadığı bir eylemi tamamladığını iddia eder. Azaltım: sonuçları doğrula, tool call'ları logla, LLM'in başarılı bir tool dönüşü olmadan bir şey yaptığını iddia etmesine asla izin verme.
- **Prompt injection.** Kullanıcı system prompt'unu geçersiz kılan metin ekler. OWASP Top 10 for LLM Applications 2025'te LLM01 olarak sıralanmıştır. İki tat: doğrudan injection (sohbete yapıştırılmış) ve dolaylı injection (agent'ın okuduğu belgelerde, e-postalarda ya da tool çıktılarında saklanmış).

  Saldırı oranları senaryoya göre değişir. Genel tool-use ve coding benchmark'larında ölçülen başarı oranları frontier modeller arasında ~%0.5-8.5 arasında değişir. Belirli yüksek-riskli kurulumlar (AI coding agent'larına karşı adaptif saldırılar, savunmasız orkestrasyon) ~%84'e ulaştı. Üretim CVE'leri arasında EchoLeak (CVE-2025-32711, CVSS 9.3) bulunur — Microsoft 365 Copilot'ta saldırgan kontrollü bir e-posta tarafından tetiklenen sıfır-tıklamalı veri sızdırma açığı.

  Azaltımlar: kullanıcı girdisini döngü boyunca güvenilmez kabul et; tool call'larından önce sanitize et; tool çıktılarını ana prompt'tan izole et; agent'ın önce planladığı, sonra çalıştırmadan önce her eylemi o plana karşı doğruladığı Plan-Verify-Execute (PVE) desenini kullan (bu tool sonuçlarının yeni planlanmamış eylemler enjekte etmesini durdurur); destructive eylemler için kullanıcı onayı gerektir; tool kapsamlarına least-privilege uygula.

  Hiçbir miktarda prompt mühendisliği bu riski tamamen ortadan kaldırmaz. Harici çalışma zamanı savunma katmanları (LLM Guard, allowlist doğrulama, semantik anomali tespiti) gereklidir.
- **Scope creep.** Bir tool çağrısı teğet ilişkili bilgi döndürdüğü için agent görev dışına çıkar. Azaltım: dar tool kontratları; system prompt'unu odaklı tut; off-task oranı için evaluation ekle.
- **Sonsuz döngüler.** Agent aynı tool'u çağırmaya devam eder. Azaltım: step budget, tool-call deduplikasyon, "ilerliyor muyuz" üzerinde LLM judge.
- **Bağlam penceresi tükenmesi.** Uzun konuşmalar en erken turları bağlam dışına iter. Azaltım: eski turları özetle, benzerliğe göre ilgili geçmiş turları getir ya da uzun bağlamlı bir model kullan.

## Yayınla

`outputs/skill-chatbot-architect.md` olarak kaydet:

```markdown
---
name: chatbot-architect
description: Design a chatbot stack for a given use case.
version: 1.0.0
phase: 5
lesson: 17
tags: [nlp, agents, chatbot]
---

Given a product context (user need, compliance constraints, available tools, data volume), output:

1. Architecture. Rule-based, retrieval, neural, LLM agent, or hybrid (specify which paths go where).
2. LLM choice if applicable. Name the model family (Claude, GPT-4, Llama-3.1, Mixtral). Match to tool-use quality and cost.
3. Grounding strategy. RAG sources, retrieval method (see lesson 14), tool contracts.
4. Evaluation plan. Task success rate, tool-call correctness, off-task rate, hallucination rate on held-out dialogs.

Refuse to recommend a pure-LLM agent for any destructive action (payments, account deletion, data modification) without a structured confirmation flow. Refuse to skip the prompt-injection audit if the agent has write access to anything.
```

## Alıştırmalar

1. **Kolay.** Yukarıdaki rule-based respond'u bir kahve dükkanı sipariş bot'u için 10 pattern'le uygula. Kenar durumları test et: çift siparişler, modifikasyonlar, iptal, belirsiz niyet.
2. **Orta.** Hibrit bir FAQ + LLM fallback kur. Bir SaaS ürünü için 50 hazır FAQ girdisi, dökümantasyon sitesi üzerinde retrieval'lı LLM fallback. 100 gerçek destek sorusu üzerinde refusal oranını ve doğruluğu ölç.
3. **Zor.** Yukarıdaki agent döngüsünü üç tool ile (search, read-user-data, send-email) uygula. Prompt injection denemeleri dahil 50 test senaryosuyla bir evaluation çalıştır. Off-task oranını, başarısız görev oranını ve herhangi bir injection başarısını raporla.

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|-----------------|-----------------------|
| Niyet | Kullanıcının istediği | Kategorik etiket (book_flight, reset_password). Bir handler'a yönlendirilir. |
| Slot | Bir bilgi parçası | Bot'un ihtiyaç duyduğu parametre (tarih, varış noktası). Slot filling sorma dizisidir. |
| RAG | Retrieval artı üretim | İlgili belgeleri getir, sonra LLM'in yanıtını temellendir. |
| Tool call | Fonksiyon çağrısı | LLM, name + args ile yapılı bir çağrı yayınlar. Runtime çalıştırır, sonucu döndürür. |
| Agent döngüsü | Planla, eyle, doğrula | Görev tamamlanana kadar LLM çağrılarını tool çağrılarıyla aralayarak çalıştıran controller. |
| Prompt injection | Kullanıcı prompt'a saldırır | System prompt'unu geçersiz kılmaya çalışan kötü amaçlı girdi. |

## İleri Okuma

- [Weizenbaum (1966). ELIZA — A Computer Program For the Study of Natural Language Communication](https://web.stanford.edu/class/cs124/p36-weizenabaum.pdf) — orijinal kural tabanlı chatbot makalesi.
- [Thoppilan et al. (2022). LaMDA: Language Models for Dialog Applications](https://arxiv.org/abs/2201.08239) — Google'ın LLM agent'lar devralmadan hemen önceki geç sinirsel-chatbot makalesi.
- [Yao et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) — agent döngü desenini adlandıran makale.
- [Anthropic's guide on building effective agents](https://www.anthropic.com/research/building-effective-agents) — 2026'da hâlâ geçerli olan 2024 üretim rehberi.
- [Greshake et al. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection](https://arxiv.org/abs/2302.12173) — prompt-injection makalesi.
- [OWASP Top 10 for LLM Applications 2025 — LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — prompt injection'ı en üst güvenlik endişesi yapan sıralama.
- [AWS — Securing Amazon Bedrock Agents against Indirect Prompt Injections](https://aws.amazon.com/blogs/machine-learning/securing-amazon-bedrock-agents-a-guide-to-safeguarding-against-indirect-prompt-injections/) — Plan-Verify-Execute ve kullanıcı-onay akışları dahil pratik orkestrasyon-katmanı savunmaları.
- [EchoLeak (CVE-2025-32711)](https://www.vectra.ai/topics/prompt-injection) — dolaylı prompt injection'dan kaynaklanan kanonik sıfır-tıklamalı veri sızdırma CVE'si. Yazma erişimli agent'ların neden runtime savunmalarına ihtiyaç duyduğuna referans vaka.
