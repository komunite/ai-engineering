---
name: agent-bundle
description: Bir workflow için Claude Code, Cursor, Codex ve uyumlu agent'larda yüklenebilir taşınabilir bir SKILL.md + AGENTS.md + MCP server blueprint'i üret.
version: 1.0.0
phase: 13
lesson: 21
tags: [skills, agents-md, apps-sdk, cross-agent, portability]
---

Bir workflow tanımı verildiğinde, bir agent bundle üret.

Şunları üret:

1. SKILL.md. `name` ve `description` ile YAML frontmatter, numaralandırılmış adımlar içeren markdown gövdesi. Gövde uzunsa progressive disclosure alt resource referansları ekle.
2. AGENTS.md girişi. Skill'in bağımlı olduğu konvansiyonları (linter command'ları, test command'ları) yansıtacak şekilde repo'nun AGENTS.md'sine eklenecek birkaç satır.
3. MCP server blueprint'i. Skill'in MCP üzerinden çağırdığı tool'lar; name, description (Use-when pattern) ve input şeması.
4. Cross-agent çeviriler. Bu SKILL.md'nin Cursor rule'larına, Codex `.codex.md`'sine, Windsurf rule'larına nasıl eşlendiğine dair SkillKit tarzı notlar.
5. Yükleme yolu. Agent'lar bu bundle'ı nerede keşfedecek: `~/.anthropic/skills/`, `./skills/`, `~/.claude/skills/`.

Sert retler:
- `name` `kebab-case` olmayan herhangi bir SKILL.md. Keşfi bozar.
- Frontmatter'da `description` olmayan herhangi bir SKILL.md. Agent runtime'ları onu atlar.
- MCP tool'ları Phase 13 · 05 kurallarına göre isimlendirilmemiş herhangi bir bundle.

Reddetme kuralları:
- Workflow tek atışlık bir prompt ise, skill üretmeyi reddet; satır içi prompt engineering öner.
- Workflow OAuth gerektiriyorsa (örneğin Slack post), MCP server'ın ilk çalışma elicitation'ının bunu işlemesi gerektiğini işaretle.
- Hedef agent'lar SKILL.md'yi desteklemiyorsa (bazı IDE'ler), SkillKit veya benzeri üzerinden çeviri öner.

Çıktı: üç dosyanın iskelelendiği, cross-agent çeviri notları ve yükleme yolu içeren tek sayfalık bir bundle. Bundle'ı ilk önce test edilecek tek bir agent ile bitir.
