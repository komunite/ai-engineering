---
name: stategraph-designer
description: Bir agent görevini adlandırılmış node'lar, tipli state, reducer'lar, checkpointer ve insan interrupt'larıyla bir LangGraph StateGraph'a dönüştür.
version: 1.0.0
phase: 11
lesson: 16
tags: [langgraph, stategraph, checkpointer, interrupt, time-travel, react-agent, human-in-the-loop]
---

Agent görevi (kullanıcıya bakan hedef, mevcut tool'lar, beklenen tur sayısı, güvenlik blast radius'lu yan etkiler, durabilite gereksinimleri, hedef gecikme bütçesi) verildiğinde, şunları çıkar:

1. Node listesi. Her ayrı adımı isimlendir: LLM düşünücü, her tool çalıştırıcı, her insan inceleme adımı, herhangi bir özetleyici veya eleştirmen, herhangi bir retriever. Bir node birden fazla concern'e dokunuyorsa tasarımı reddet; böl.
2. State şeması. Her liste için bir reducer ile TypedDict (veya Pydantic) alanlar. Mesaj log'unda her zaman Annotated[list, add_messages]. Reducer'ların paralel güncellemeler altında doğru kalması için göreve özgü herhangi bir listeyi (bir plan, bir bütçe counter'ı, bir retrieved-docs listesi) mesajlardan dışarı çıkar.
3. Edge haritası. Sonraki adımın deterministik olduğu yerlerde statik edge'ler. Sadece modelin sonraki adımı seçtiği yerlerde adlandırılmış bir router fonksiyonuyla conditional edge'ler. Router fonksiyonu önceki bir node'da daha önce yapmadığın yeni bir LLM çağrısına bağlı olan herhangi bir graph'ı reddet.
4. Interrupt yerleşimi. Geri alınamaz yan etkili her node'da interrupt_before (yazmalar, silmeler, ödemeler, maliyetli dış API çağrıları). Output doğrulama ayrı bir process'te çalıştığında model node'unda interrupt_after. Herhangi bir yan etkili node'da interrupt_after reddet; o zamana kadar yan etki olmuş olur.
5. Checkpointer. Sadece testler için MemorySaver. Yeniden başlatma sonrası hayatta kalması gereken her ortam için PostgresSaver, SQLiteSaver, RedisSaver arasından seç. thread_id stratejisini (kullanıcı başına, oturum başına, konuşma başına) ve checkpoint TTL'ini teyit et.

Checkpointer olmadan bir LangGraph'ı ship etmeyi reddet. Checkpointer yoksa resume yok, time-travel yok, human-in-the-loop replay yok. add_messages olmadan bir messages alanını ship etmeyi reddet; ikinci yazma birinciyi sessizce override eder ve konuşmanın yarısı kaybolur. Her transition'ı bir planner LLM tarafından routed conditional edge olan bir graph'ı reddet; o ekstra adımlarla AutoGen'dir ve tur başına token yakar.

Örnek girdi: "Üç tool'la (lookup_order, issue_refund, send_email) Anthropic Claude üzerinde Refund-handling agent, 100 dolar üstü her iade öncesi bir insan için durmalı, sunucu yeniden başlatma sonrası devam etmeli, p95 gecikme bütçesi 8 saniye."

Örnek çıktı:
- Node'lar: agent (LLM çağrısı), lookup_tool, refund_tool, email_tool, human_review.
- State: add_messages ile messages, order_context (overwrite), refund_amount (overwrite), reviewer_decision (overwrite).
- Edge'ler: agent should_continue router'ına; branch'ler lookup_tool, refund_tool, email_tool, human_review, END. Tool node'ları agent'a geri döner.
- Interrupt'lar: refund_amount > 100 olduğunda refund_tool üzerinde interrupt_before. lookup_tool veya email_tool üzerinde interrupt yok.
- Checkpointer: thread_id "user:{user_id}:case:{case_id}" ve 30 günlük TTL ile PostgresSaver.
