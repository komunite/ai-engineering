---
name: otel-genai-instrumentation
description: OTel GenAI span'larını uçtan uca emit etmek için bir agent codebase'i için instrumentation planı üret.
version: 1.0.0
phase: 13
lesson: 19
tags: [otel, observability, gen-ai, tracing]
---

Bir agent codebase (LLM çağrıları, tool dispatch, MCP client, alt agent'lar) verildiğinde, bir OTel GenAI instrumentation planı üret.

Şunları üret:

1. Span hiyerarşisi. Root `agent.invoke_agent` (INTERNAL) ve çocuklar: `llm.chat` (CLIENT), `tool.execute` (INTERNAL), `mcp.call` (CLIENT), `subagent.invoke` (INTERNAL).
2. Span başına attribute checklist'i. `gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.*`, `gen_ai.tool.name`, `gen_ai.agent.name`.
3. Propagation kuralı. Her uzak çağrıya W3C traceparent inject et; MCP stdio için ara alan olarak `_meta.traceparent` kullan.
4. İçerik yakalama policy'si. Varsayılan kapalı; hangi env var'ın etkinleştirdiğini belgele; PII risklerini adlandır.
5. Exporter seçimi. Jaeger / Tempo / Langfuse / Phoenix / Datadog / Honeycomb; tel olarak OTLP.

Sert retler:
- MCP ya da alt agent sınırları boyunca trace propagation eksik herhangi bir plan.
- Varsayılan olarak içerik yakalama açık olan herhangi bir plan. Prompt'ları ve PII'yi sızdırır.
- `gen_ai.` ya da açık vendor prefix'i olmadan keyfi özel attribute'lar emit eden herhangi bir plan.

Reddetme kuralları:
- Codebase yerleşik OTel auto-instrumentation içeren bir framework kullanıyorsa (Pydantic AI, LangGraph, AgentOps), önce framework kancasını öner.
- Exporter backend on-prem ise ve ekibin SRE desteği yoksa, managed bir backend öner.
- Kullanıcı prod debug için içerik yakalamak isterse, tipli bir consent policy'si ve PII redaksiyon pipeline'ı olmadan reddet.

Çıktı: span hiyerarşisi, span başına attribute checklist'i, propagation kuralı, içerik yakalama policy'si ve exporter seçimi içeren tek sayfalık bir plan. Alarm verilecek en önemli metrikle bitir (tipik olarak p95 `gen_ai.client.operation.duration`).
