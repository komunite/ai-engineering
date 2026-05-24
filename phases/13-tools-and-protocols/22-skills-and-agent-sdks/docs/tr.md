# Skill'ler ve Agent SDK'ları — Anthropic Skills, AGENTS.md, OpenAI Apps SDK

> MCP "hangi tool'lar var" der. Skill'ler "bir görev nasıl yapılır" der. 2026 yığını ikisini katmanlar. Anthropic'in Agent Skills'i (açık standart, Aralık 2025) progressive disclosure'lı SKILL.md olarak yayınlanır. OpenAI'ın Apps SDK'sı MCP artı widget metadata'dır. AGENTS.md (şimdi 60.000+ repo'da) proje-seviyesi agent bağlamı olarak repo root'unda oturur. Bu ders her birinin neyi kapsadığını adlandırır ve agent'lar arasında seyahat eden minimal bir SKILL.md + AGENTS.md bundle inşa eder.

**Tür:** Öğrenim
**Diller:** Python (stdlib, SKILL.md parser ve loader)
**Ön koşullar:** Faz 13 · 07 (MCP sunucusu)
**Süre:** ~45 dakika

## Öğrenme Hedefleri

- Üç katmanı ayırt et: AGENTS.md (proje bağlamı), SKILL.md (yeniden kullanılabilir know-how), MCP (tool'lar).
- YAML frontmatter ve progressive disclosure ile bir SKILL.md yaz.
- Skill'leri filesystem-style olarak bir agent runtime'ına yükle.
- Bir skill'i bir MCP sunucusu ve bir AGENTS.md ile compose et, böylece bir paket Claude Code, Cursor ve Codex'te çalışsın.

## Sorun

Bir mühendis release-notes-yazma workflow'unu çok-adımlı bir prompt'a damıtır: "En son merge edilen PR'leri oku. Alana göre grupla. Her birini özetle. Takımın stiline uygun bir changelog entry yaz. Slack draft'a post et." Onu takım için bir Notion dokümanına koyar.

Şimdi bu workflow'u Claude Code, Cursor ve Codex CLI'dan kullanmak istiyor. Her agent'ın talimatları yüklemek için farklı bir yolu var: Claude Code slash-komutları, Cursor rule'ları, Codex `.codex.md`. Mühendis workflow'u üç kere kopyalar ve üç kopyayı sürdürür.

AGENTS.md ve SKILL.md birlikte bunu düzeltir:

- **AGENTS.md** repo root'unda oturur. Her uyumlu agent onu session başında okur. "Bu proje nasıl çalışır? Konvansiyonlar neler? Hangi komutlar test'leri çalıştırır?"
- **SKILL.md** taşınabilir bir bundle'dır: YAML frontmatter (name, description) + markdown body + opsiyonel resource'lar. Skill'leri destekleyen agent'lar onları isim üzerinden talep üzerine yükler.
- **MCP** (Faz 13 · 06-14) skill'in çağırması gereken tool'ları ele alır.

Üç katman, bir taşınabilir artifact.

## Kavram

### AGENTS.md (agents.md)

2025 sonunda launch oldu, Nisan 2026'da 60.000+ repo tarafından benimsendi. Repo root'unda bir dosya. Format:

```markdown
# Project: my-service

## Conventions
- TypeScript with strict mode.
- Use Pydantic for models on the Python side.
- Tests run with `pnpm test`.

## Build and run
- `pnpm dev` for local dev server.
- `pnpm build` for production bundle.
```

Agent'lar bunu session başında okur ve o proje için davranışlarını kalibre etmek için kullanır. 2026'da her coding agent AGENTS.md'yi destekler: Claude Code, Cursor, Codex, Copilot Workspace, opencode, Windsurf, Zed.

### SKILL.md formatı

Anthropic'in Agent Skills'i (Aralık 2025'te açık standart olarak yayınlandı):

```markdown
---
name: release-notes-writer
description: Write a changelog entry for the latest merged PRs following this project's style.
---

# Release notes writer

When invoked, run these steps:

1. List PRs merged since the last tag. Use `gh pr list --base main --state merged`.
2. Group by label: feature, fix, chore, docs.
3. For each PR in each group, write one line: `- <title> (#<num>)`.
4. Draft the release notes and stage them in CHANGELOG.md.

If the user says "ship", run `git tag vX.Y.Z` and `gh release create`.

## Notes

- Never include commits without a PR.
- Skip "chore" entries from the public changelog.
```

Frontmatter skill'in kimliğini bildirir. Body skill yüklendiğinde modele gösterilen prompt'tur.

### Progressive disclosure

Skill'ler agent'ın yalnızca gerektiğinde fetch ettiği sub-resource'lara referans verebilir. Örnek:

```
skills/
  release-notes-writer/
    SKILL.md
    style-guide.md
    template.md
    scripts/
      generate.sh
```

SKILL.md "stil kuralları için style-guide.md'ye bak" der. Agent style-guide.md'yi yalnızca skill aktif çalıştığında çeker. Bu, modelin ihtiyaç duymayabileceği ayrıntıyla prompt'u şişirmekten kaçınır.

### Filesystem discovery

Agent runtime'ları SKILL.md dosyaları için bilinen dizinleri tarar:

- `~/.anthropic/skills/*/SKILL.md`
- Proje `./skills/*/SKILL.md`
- `~/.claude/skills/*/SKILL.md`

Yükleme klasör adı ve frontmatter `name`'e göredir. Claude Code, Anthropic Claude Agent SDK ve SkillKit (cross-agent) hepsi bu deseni takip eder.

### Anthropic Claude Agent SDK

`@anthropic-ai/claude-agent-sdk` (TypeScript) ve `claude-agent-sdk` (Python) skill'leri session başında yükler, onları runtime'ın içinde çağrılabilir "agent'lar" olarak açar. Agent döngüsü kullanıcı çağırdığında bir skill'e dispatch eder.

### OpenAI Apps SDK

Ekim 2025'te launch oldu; doğrudan MCP üzerinde inşa edildi. OpenAI'ın önceki Connector'larını ve Custom GPT Action'larını tek bir geliştirici yüzeyi altında birleştirir. Bir Apps SDK uygulaması:

- Bir MCP sunucusu (tools, resources, prompts).
- Artı ChatGPT'nin UI'sı için widget metadata.
- Artı interaktif yüzeyler için opsiyonel bir MCP Apps `ui://` resource'u.

Aynı protokol, daha zengin UX.

### SkillKit üzerinden cross-agent portability

SkillKit gibi araçlar ve benzer cross-agent dağıtım katmanları tek bir SKILL.md'yi 32+ AI agent'ının her birinin native formatına çevirir (Claude Code, Cursor, Codex, Gemini CLI, OpenCode, vb.). Tek source of truth; birçok consumer.

### Üç katmanlı yığın

| Katman | Dosya | Yüklendiğinde | Amaç |
|-------|------|-------------|---------|
| AGENTS.md | repo root | session başı | proje-seviyesi konvansiyonlar |
| SKILL.md | skills dizini | skill çağrıldığında | yeniden kullanılabilir workflow |
| MCP sunucusu | dış process | tool'lar gerektiğinde | çağrılabilir aksiyonlar |

Üçü de compose olur: agent session başında AGENTS.md'yi okur, kullanıcı bir skill çağırır, skill'in talimatları MCP tool çağrılarını içerir, agent bir MCP client üzerinden dispatch eder.

## Kullan

`code/main.py` bir stdlib SKILL.md parser ve loader yayınlar. `./skills/` altındaki skill'leri keşfeder, YAML frontmatter artı markdown body'yi parse eder ve skill ismi ile keyed bir dict üretir. Sonra `release-notes-writer`'ı isim ile çağıran bir agent döngüsünü simüle eder.

Bakılacak şeyler:

- YAML frontmatter minimal bir stdlib parser ile parse edildi (`pyyaml` bağımlılığı yok).
- Skill body aynen saklandı; agent invocation'da onu system prompt'a prepend eder.
- Progressive disclosure, referans verilen dosyaları talep üzerine çeken bir `read_subresource` fonksiyonu üzerinden demolandı.

## Yayınla

Bu ders `outputs/skill-agent-bundle.md` üretir. Bir workflow verildiğinde, skill agent'lar arasında taşınabilir birleştirilmiş SKILL.md + AGENTS.md + MCP-server-blueprint bundle'ı üretir.

## Alıştırmalar

1. `code/main.py`'ı çalıştır. `skills/` altına ikinci bir skill ekle ve loader'ın onu aldığını doğrula.

2. Bu kurs repo'su için bir AGENTS.md yaz. Test komutlarını, stil konvansiyonlarını ve Faz 13 zihinsel modelini dahil et.

3. Takımının iç dokümanlarından bir çok-adımlı workflow'u SKILL.md'ye port et. Claude Code'da yüklendiğini doğrula.

4. Skill'i Cursor'un ve Codex'in native rule formatlarına elle çevir. Formatlar arasındaki diff'i say — bu SkillKit'in otomatikleştirdiği çeviri yüzeyidir.

5. Anthropic Agent Skills blog yazısını oku. Claude Agent SDK'sında bu dersin loader'ının ele almadığı bir feature'ı tanımla. (İpucu: agent sub-invocation.)

## Anahtar Terimler

| Terim | İnsanlar ne diyor | Gerçekte ne anlama geliyor |
|------|----------------|------------------------|
| SKILL.md | "Skill dosyası" | YAML frontmatter artı markdown body, agent runtime tarafından yüklenir |
| AGENTS.md | "Repo-root agent bağlamı" | Session başında okunan proje-seviyesi konvansiyon dosyası |
| Progressive disclosure | "Lazy-load sub-resource'lar" | Skill body yalnızca gerektiğinde çekilen dosyalara referans verir |
| Frontmatter | "Üstteki YAML bloğu" | `---` ayırıcılarda metadata (name, description) |
| Claude Agent SDK | "Anthropic'in skill runtime'ı" | `@anthropic-ai/claude-agent-sdk`, skill'leri yükler ve route'lar |
| OpenAI Apps SDK | "MCP + widget meta" | MCP artı ChatGPT UI hook'ları üzerinde inşa edilmiş OpenAI'ın dev yüzeyi |
| Skill discovery | "Filesystem tarama" | SKILL.md için bilinen dizinleri yürü, isim ile key'le |
| Cross-agent portability | "Bir skill çok agent" | SkillKit-style araçlar üzerinden bir SKILL.md'yi 32+ agent'a çevir |
| Agent Skill | "Taşınabilir know-how" | MCP'nin tool kavramının dışında yeniden kullanılabilir task template'i |
| Apps SDK | "MCP artı ChatGPT UI" | MCP üzerinde birleştirilmiş Connector'lar ve Custom GPT'ler |

## İleri Okuma

- [Anthropic — Agent Skills announcement](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — Aralık 2025 launch
- [Anthropic — Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — SKILL.md format referansı
- [OpenAI — Apps SDK](https://developers.openai.com/apps-sdk) — ChatGPT için MCP-tabanlı geliştirici platformu
- [agents.md](https://agents.md/) — AGENTS.md formatı ve benimseme listesi
- [Anthropic — anthropics/skills GitHub](https://github.com/anthropics/skills) — resmi skill örnekleri
