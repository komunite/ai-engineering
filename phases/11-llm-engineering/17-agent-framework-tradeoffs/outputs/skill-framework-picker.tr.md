---
name: framework-picker
description: Bir agent görevi için soyutlamayı problem şekline eşleyerek LangGraph, CrewAI, AutoGen, Agno veya düz Python seç.
version: 1.0.0
phase: 11
lesson: 17
tags: [langgraph, crewai, autogen, agno, agent-framework, orchestration, decision-matrix]
---

Görev açıklaması (problem şekli, çalıştırma başına toplam LLM çağrısı, branching pattern'i, durabilite ve resume ihtiyaçları, human-in-the-loop checkpoint'leri, paralel fanout, oturum belleği, beklenen günlük çalıştırma hacmi) verildiğinde, şunları çıkar:

1. Şekil eşleşmesi. Uyan soyutlamayı isimlendiren tek cümle: graph (tipli state, adlandırılmış transition'lar), org chart (uzman roller, manager-routed handoff'lar), chat (agent'lar bitene kadar konuşur), tool'larla tek agent. Birini seçemiyorsan, görev henüz agent-şekilli değildir; dur ve ayrıştır.
2. Branching yetkisi. Sonraki adımı kim seçiyor: developer (açık edge'ler), manager LLM (CrewAI hierarchical), conversational emergent (AutoGen GroupChat), tool-call self-routed (Agno). Uygulanabilirse LLM-seçimli routing'in tur başına token maliyetini belirt.
3. State bütçesi. Yeniden başlatma sonrası resume, time-travel veya insan interrupt'ları gerekli mi teyit et. Evetse, LangGraph state-first soyutlamalarında kazanır; Agno sadece oturum-kapsamlı belleği karşılar.
4. Framework seçimi. Şunlardan birini çıkar: langgraph, crewai, autogen, agno, plain_python. Şekil ve state cevaplarını framework'ün çekirdek primitive'ine eşleyen tek cümlelik gerekçeyi dahil et.
5. Çıkış kapısı. Günlük çalıştırma hacmi 10.000'in üzerindeyse veya görev state'siz iki veya daha az LLM çağrısıysa, bunun yerine sağlayıcı SDK ile düz Python öner. Görev küçükse hiçbir framework en hızlı framework'tür.

Bilinen DAG'lı deterministik workflow'lar için AutoGen önermeyi reddet; GroupChatManager, developer'ın statik olarak bağlayabileceği konuşmacıları seçmek için token harcar. CrewAI, `output_pydantic` / `output_json` aracılığıyla yapılandırılmış görev çıktılarını destekler (bkz. [docs.crewai.com/en/concepts/tasks](https://docs.crewai.com/en/concepts/tasks)), ama `context` kanalı hala sonraki görevin prompt string'inden geçer. Workflow yapılandırılmış state'i bu çıktı şemalarından biri bağlanmadan ham `context` ile görevler arası taşımaya bağlıysa CrewAI'a karşı çık. İki-çağrılı bir özetleyici için LangGraph'a karşı çık; StateGraph overhead'i saf vergidir. Görev reducer semantiği olan 4'ten fazla paralel alt-worker'a yayıldığında Agno'ya karşı çık; Agno çıktıları step adına göre key'lenmiş bir dict'e join olan bir `Parallel` block sunar (bkz. [docs-v1.agno.com/workflows_2/overview](https://docs-v1.agno.com/workflows_2/overview) ve [docs.agno.com/workflows/access-previous-steps](https://docs.agno.com/workflows/access-previous-steps)), ama LangGraph'ın Send-tarzı fanout-and-reduce primitive'ine karşılaştırılabilir bir şey expose etmez.

Örnek girdi: "Uzun-süreli araştırma workflow'u: planla, üç retriever'a fan out, sentezle, insan brief'i onaylar, rapor yaz, kaynak göster. Çökme sonrası resume etmeli. Production'da günde 50 çalıştırma sınırlı."

Örnek çıktı:
- Şekil: graph. Tipli plan, üç paralel retriever, synthesize ve write arasında adlandırılmış transition'lar.
- Branching: developer kararlı conditional edge'ler üzerinden. Tur başına manager LLM yok.
- State: resume ve insan interrupt'ı gerektirir. LangGraph zorunlu.
- Framework: langgraph. State, Send fanout, interrupt_before ve PostgresSaver hepsi birinci-sınıf.
- Çıkış kapısı: uygulanabilir değil. Günde 50 çalıştırma düz-Python eşiğinin altında ve workflow framework'süz bırakılamayacak kadar state-ağırlıklı.
