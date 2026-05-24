#!/usr/bin/env python3
"""Generate site/llms.txt per the llmstxt.org proposal.

Produces a markdown-formatted index of the curriculum at /llms.txt
so AI agents and LLM crawlers can read a structured site summary
without scraping every page. Format:

    # Project name
    > One-line summary
    Optional body paragraph(s)
    ## Section
    - [Link Name](URL): optional description

Phase titles and taglines are pulled from phases/<phase>/README.tr.md
so the file stays in sync as content evolves.

Run from the repo root (or via vercel.json's buildCommand):

    python3 scripts/build_llms_txt.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://ai-muhendisligi.komunite.com.tr"
GH_BASE = "https://github.com/komunite/ai-engineering"
UPSTREAM = "https://github.com/rohitg00/ai-engineering-from-scratch"

H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
TAGLINE_RE = re.compile(r"^>\s*(.+)$", re.MULTILINE)
PHASE_DIR_RE = re.compile(r"^(\d{2})-")


def phase_info(phase_dir: Path) -> tuple[str, str]:
    """Return (title, tagline). Title is README.tr.md H1, tagline is the first blockquote."""
    readme = phase_dir / "README.tr.md"
    if not readme.is_file():
        readme = phase_dir / "README.md"
    if not readme.is_file():
        return (phase_dir.name, "")
    text = readme.read_text(encoding="utf-8")
    title_m = H1_RE.search(text)
    tagline_m = TAGLINE_RE.search(text)
    title = title_m.group(1).strip() if title_m else phase_dir.name
    tagline = tagline_m.group(1).strip() if tagline_m else ""
    return (title, tagline)


def main() -> int:
    phases_src = sorted(
        d for d in (ROOT / "phases").iterdir()
        if d.is_dir() and PHASE_DIR_RE.match(d.name)
    )

    lines = [
        "# Sıfırdan Yapay Zeka Mühendisliği",
        "",
        "> 20 faz, 435 ders, ~320 saatlik açık kaynak Türkçe yapay zeka mühendisliği müfredatı. Matematiksel temellerden üretim altyapısına. MIT lisanslı.",
        "",
        "Bu site, `rohitg00/ai-engineering-from-scratch` upstream curriculum'ının Komünite tarafından Türkçeleştirilmiş ve bağımsız sürdürülen versiyonudur. Her ders kendi makinende çalışan bir çıktı üretir: bir model, bir prompt, bir araç ya da bir agent. Python, TypeScript, Rust, Julia.",
        "",
        "## Temel Sayfalar",
        "",
        f"- [Ana sayfa]({BASE}/): Curriculum'a giriş, müfredat akışı ve faz haritası",
        f"- [Ders kataloğu]({BASE}/catalog.html): 435 dersin filtrelenebilir tam listesi (faz, tür, dil, durum)",
        f"- [Yol haritası]({BASE}/prereqs.html): Etkileşimli faz ön koşul grafiği",
        f"- [Sözlük]({BASE}/glossary.html): Yapay zeka mühendisliğinde 83 terim — Türkçe-İngilizce karşılıkları",
        "",
        "## Fazlar",
        "",
    ]

    for phase_dir in phases_src:
        title, tagline = phase_info(phase_dir)
        url = f"{BASE}/phases/{phase_dir.name}/"
        if tagline:
            lines.append(f"- [{title}]({url}): {tagline}")
        else:
            lines.append(f"- [{title}]({url})")

    lines.extend([
        "",
        "## Repo ve Katkı",
        "",
        f"- [GitHub kaynağı]({GH_BASE}): Tüm ders dosyaları, kod örnekleri ve site kaynağı",
        f"- [ROADMAP]({GH_BASE}/blob/main/ROADMAP.tr.md): Her faz ve dersin durumu, tahmini süreler",
        f"- [CONTRIBUTING]({GH_BASE}/blob/main/CONTRIBUTING.tr.md): Katkı rehberi (Türkçe çeviri, terim, UX)",
        f"- [FORKING]({GH_BASE}/blob/main/FORKING.tr.md): Repo'yu kendi takımın/okulun için fork etme rehberi",
        f"- [CHANGELOG]({GH_BASE}/blob/main/CHANGELOG.tr.md): Sürüm geçmişi ve önemli değişiklikler",
        "",
        "## Optional",
        "",
        f"- [Upstream (İngilizce)]({UPSTREAM}): Rohit Ghumare'nin orijinal İngilizce müfredatı",
        f"- [Sözlük (İngilizce)]({BASE}/glossary/terms.md): Sözlük terimlerinin İngilizce orijinalleri",
        f"- [Sitemap]({BASE}/sitemap.xml): SEO sitemap.xml (439 URL)",
        f"- [Lisans]({GH_BASE}/blob/main/LICENSE): MIT",
        "",
    ])

    out = ROOT / "site" / "llms.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"llms.txt: {len(phases_src)} phases, {out.stat().st_size} bytes → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
