#!/usr/bin/env python3
"""Generate per-lesson stub HTML pages with proper meta + OG tags.

For each lesson at phases/<phase>/<lesson>/, writes an index.html
into site/phases/<phase>/<lesson>/ containing:

  - <title>, <meta description>
  - og:title / og:description / og:image / og:url / og:type=article
  - twitter:card / twitter:title / twitter:description / twitter:image
  - canonical link
  - <noscript> + meta refresh fallback
  - JS that location.replace's to /lesson.html?path=...

Crawlers (Twitter, Slack, Facebook, Google) read the meta tags from
this stub before they would follow a redirect, so each shared link
shows the lesson-specific OG image + description. Real users see
the JS redirect and land on the SPA reader.

Run inside the Vercel build chain AFTER `cp -R phases site/phases`
so the stubs land in the deploy output:

    LOCALE=tr node site/build.js
    && python3 scripts/build_sitemap.py
    && rm -rf site/phases && cp -R phases site/phases
    && python3 scripts/build_lesson_pages.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASES_SRC = ROOT / "phases"
SITE_OUT = ROOT / "site" / "phases"  # target after Vercel `cp -R`; symlink locally
SITE_URL = os.environ.get("SITE_URL", "https://ai-muhendisligi.komunite.com.tr").rstrip("/")
OG_BASE = f"{SITE_URL}/og"

PHASE_RE = re.compile(r"^([0-9]{2})-([a-z0-9-]+)$")
LESSON_RE = re.compile(r"^([0-9]{2})-([a-z0-9-]+)$")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
TAGLINE_RE = re.compile(r"^>\s*(.+)$", re.MULTILINE)


def parse_lesson(doc: Path) -> tuple[str, str]:
    """Return (title, description). Description is the first blockquote
    or the first prose paragraph after H1."""
    if not doc.is_file():
        return ("", "")
    text = doc.read_text(encoding="utf-8")
    title_m = H1_RE.search(text)
    title = title_m.group(1).strip() if title_m else ""
    desc = ""
    tag_m = TAGLINE_RE.search(text)
    if tag_m:
        desc = tag_m.group(1).strip()
    else:
        # Fallback: first non-empty, non-heading, non-list paragraph
        body = text[title_m.end():] if title_m else text
        for chunk in body.split("\n\n"):
            line = chunk.strip()
            if not line:
                continue
            if line.startswith(("#", "-", "*", "**", "|", "```", "<", "[")):
                continue
            desc = line.split("\n")[0].strip()
            if desc:
                break
    # Truncate to a sensible meta-description length without breaking words.
    if len(desc) > 200:
        cut = desc[:200].rsplit(" ", 1)[0]
        desc = cut.rstrip(",.;:") + "…"
    return (title, desc)


PHASE_TITLE_CACHE: dict[str, str] = {}


def parse_phase_title(phase_dir: Path) -> str:
    """Return the phase H1 from README.tr.md (e.g. 'Faz 17: Altyapı ve Üretim').
    Cached per phase so we don't re-read for every lesson in the phase."""
    cached = PHASE_TITLE_CACHE.get(phase_dir.name)
    if cached is not None:
        return cached
    readme = phase_dir / "README.tr.md"
    if not readme.is_file():
        readme = phase_dir / "README.md"
    result = ""
    if readme.is_file():
        m = H1_RE.search(readme.read_text(encoding="utf-8"))
        result = m.group(1).strip() if m else ""
    PHASE_TITLE_CACHE[phase_dir.name] = result
    return result


def render_stub(phase_slug: str, lesson_slug: str, lesson_path: str,
                title: str, desc: str, phase_title: str = "") -> str:
    full_title = f"{title} — Sıfırdan Yapay Zeka Mühendisliği" if title else "Ders — Sıfırdan Yapay Zeka Mühendisliği"
    canonical = f"{SITE_URL}/phases/{phase_slug}/{lesson_slug}/"
    og_image = f"{OG_BASE}/{phase_slug}/{lesson_slug}.jpg"
    spa_url = f"/lesson.html?path={lesson_path}"
    # Escape attribute values; JS uses single-quoted literal which is safe
    # because lesson_path is a known slug (no quotes).
    t = escape(full_title, quote=True)
    d = escape(desc or full_title, quote=True)

    # JSON-LD: LearningResource for the lesson itself, plus a BreadcrumbList
    # so search engines can render breadcrumb navigation in rich results.
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LearningResource",
                "name": full_title,
                "description": desc or full_title,
                "url": canonical,
                "image": og_image,
                "inLanguage": "tr-TR",
                "learningResourceType": "Lesson",
                "isPartOf": {"@id": f"{SITE_URL}/#course"},
                "provider": {
                    "@type": "EducationalOrganization",
                    "name": "Komünite",
                    "url": "https://komunite.com.tr/",
                },
                "isAccessibleForFree": True,
                "license": "https://opensource.org/licenses/MIT",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Ana Sayfa", "item": f"{SITE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": phase_title or phase_slug, "item": f"{SITE_URL}/catalog.html"},
                    {"@type": "ListItem", "position": 3, "name": title or "Ders", "item": canonical},
                ],
            },
        ],
    }
    jsonld_str = json.dumps(jsonld, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <link rel="canonical" href="{canonical}">

  <meta property="og:type" content="article">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="Sıfırdan Yapay Zeka Mühendisliği">
  <meta property="og:locale" content="tr_TR">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{t}">
  <meta name="twitter:description" content="{d}">
  <meta name="twitter:image" content="{og_image}">

  <script type="application/ld+json">
{jsonld_str}
  </script>

  <meta http-equiv="refresh" content="0; url={spa_url}">
  <script>
    // Crawlers don't run this; they stay on this stub and read meta tags.
    // Browsers replace immediately so the URL doesn't pollute history.
    location.replace('{spa_url}');
  </script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='%23fafaf5'/><rect x='2' y='2' width='28' height='28' fill='none' stroke='%233553ff' stroke-width='1.2'/><text x='6' y='22' font-size='14' font-family='monospace' fill='%233553ff'>AI</text></svg>">
  <style>
    body {{
      font-family: ui-sans-serif, system-ui, sans-serif;
      max-width: 560px;
      margin: 96px auto;
      padding: 0 20px;
      color: #1a1a1a;
      line-height: 1.5;
    }}
    a {{ color: #3553ff; }}
  </style>
</head>
<body>
  <h1>{escape(title) if title else "Ders"}</h1>
  <p>{escape(desc) if desc else ""}</p>
  <p>Otomatik yönlendiriliyor. Yönlendirilmediyseniz <a href="{spa_url}">buraya tıklayın</a>.</p>
</body>
</html>
"""


def iter_lessons():
    for phase_dir in sorted(PHASES_SRC.iterdir()):
        if not phase_dir.is_dir() or not PHASE_RE.match(phase_dir.name):
            continue
        for lesson_dir in sorted(phase_dir.iterdir()):
            if not lesson_dir.is_dir() or not LESSON_RE.match(lesson_dir.name):
                continue
            if not (lesson_dir / "docs").is_dir():
                continue
            yield phase_dir, lesson_dir


def main() -> int:
    # If SITE_OUT is a symlink (local dev), follow it. On Vercel after
    # `cp -R phases site/phases`, it's a real directory.
    target_base = SITE_OUT
    if target_base.is_symlink():
        target_base = target_base.resolve()

    count = 0
    for phase_dir, lesson_dir in iter_lessons():
        doc = lesson_dir / "docs" / "tr.md"
        if not doc.exists():
            doc = lesson_dir / "docs" / "en.md"
        title, desc = parse_lesson(doc)
        phase_title = parse_phase_title(phase_dir)
        lesson_path = f"phases/{phase_dir.name}/{lesson_dir.name}"
        html = render_stub(phase_dir.name, lesson_dir.name, lesson_path, title, desc, phase_title)
        out_dir = target_base / phase_dir.name / lesson_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        count += 1
    sys.stdout.write(f"lesson stubs: {count} index.html files\n  base={target_base}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
