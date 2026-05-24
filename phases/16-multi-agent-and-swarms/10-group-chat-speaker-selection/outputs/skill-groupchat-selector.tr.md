---
name: groupchat-selector
description: Bir görev için AutoGen/AG2 tarzı GroupChat selector yapılandır; selector varyantını, terminasyonu ve anti-hot-speaker kurallarını adlandır.
version: 1.0.0
phase: 16
lesson: 10
tags: [multi-agent, groupchat, autogen, ag2, speaker-selection]
---

Bir görev ve agent roster'ı verildiğinde, bir GroupChat yapılandırması üret: selector seçimi, selector girdileri, terminasyon kuralları ve guardrail'lar.

Üret:

1. **Selector varyantı.** Round-robin (ucuz, adil, context-kör), LLM-seçimli (context-farkında, pahalı) ya da custom (LLM + kural tabanlı fallback).
2. **Selector girdileri.** LLM-seçimli ise: son N mesaj, agent uzmanlıkları, turn sayıları. Custom ise: açık kurallar.
3. **Terminasyon kuralları.** Maksimum round, TERMINATE token'ı, hedefe-ulaşıldı verifier'ı ya da kombinasyon.
4. **Hot-speaker önlemi.** Agent başına turn üst limiti, selector girdisindeki speaker-balance skoru, K ardışık turn sonrası zorunlu rotasyon.
5. **Context şişme önlemi.** Projeksiyon planı (rol başına scoped görünümler), özetleme checkpoint'leri, agent başına context üst limiti.
6. **Gözlemlenebilirlik.** Selector girdisini, selector seçimini, turn başına agent latency'sini logla.

Sert ret durumları:

- Selector girdisi/çıktısı loglanmayan LLM-seçimli yapılandırmalar. Hata ayıklama imkansız hale gelir.
- max_rounds üst limiti olmayan yapılandırmalar.
- Reasoning görevlerinde simetrik chat'ler (uzmanlaşma yok) — onun yerine debate (Ders 07) kullan.

Reddetme kuralları:

- Görevin bilinen bir DAG yapısı varsa, GroupChat'i reddet ve determinism için LangGraph statik graph öner.
- Görev katı denetim izleri gerektiriyorsa, GroupChat'i reddet; checkpointer'lı LangGraph öner.
- Agent sayısı 5-6'yı geçerse, düz GroupChat'i reddet ve nested grup ya da hierarchical pattern öner.

Çıktı: bir sayfalık GroupChat config brief'i. Maliyet tahminiyle kapat (LLM-seçimli her turn için bir selector çağrısı maliyeti getirir).
