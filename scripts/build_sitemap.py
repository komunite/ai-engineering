#!/usr/bin/env python3
"""Generate site/sitemap.xml from filesystem.

Lists static pages (/, /catalog.html, /glossary.html, /prereqs.html)
plus every lesson under phases/<phase>/<lesson>/ as
/lesson.html?path=phases/<phase>/<lesson>.

The site URL is read from the SITE_URL env var; defaults to the
production domain.

Run:
    python3 scripts/build_sitemap.py            # write site/sitemap.xml
    SITE_URL=https://example.com python3 scripts/build_sitemap.py
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PHASES_DIR = ROOT / "phases"
OUTPUT = ROOT / "site" / "sitemap.xml"
SITE_URL = os.environ.get("SITE_URL", "https://ai-muhendisligi.komunite.com.tr").rstrip("/")

PHASE_RE = re.compile(r"^[0-9]{2}-[a-z0-9-]+$")
LESSON_RE = re.compile(r"^[0-9]{2}-[a-z0-9-]+$")

# Static pages (path, changefreq, priority)
STATIC_PAGES = [
    ("/", "weekly", "1.0"),
    ("/catalog.html", "weekly", "0.8"),
    ("/glossary.html", "monthly", "0.7"),
    ("/prereqs.html", "monthly", "0.7"),
]


def find_lesson_paths() -> list[str]:
    """Return sorted list of phases/<phase>/<lesson> paths that have
    a docs/ folder (the marker of a real lesson)."""
    paths: list[str] = []
    if not PHASES_DIR.is_dir():
        return paths
    for phase_dir in sorted(PHASES_DIR.iterdir()):
        if not phase_dir.is_dir() or not PHASE_RE.match(phase_dir.name):
            continue
        for lesson_dir in sorted(phase_dir.iterdir()):
            if not lesson_dir.is_dir() or not LESSON_RE.match(lesson_dir.name):
                continue
            if not (lesson_dir / "docs").is_dir():
                continue
            paths.append(f"phases/{phase_dir.name}/{lesson_dir.name}")
    return paths


def build_xml(lesson_paths: list[str]) -> str:
    today = date.today().isoformat()
    out: list[str] = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for path, freq, prio in STATIC_PAGES:
        out.append("  <url>")
        out.append(f"    <loc>{escape(SITE_URL + path)}</loc>")
        out.append(f"    <lastmod>{today}</lastmod>")
        out.append(f"    <changefreq>{freq}</changefreq>")
        out.append(f"    <priority>{prio}</priority>")
        out.append("  </url>")
    for lesson in lesson_paths:
        # Use the pretty URL (stub HTML lives at phases/<phase>/<lesson>/)
        # so crawlers index the rich-meta page, not the SPA query-string URL.
        url = f"{SITE_URL}/{lesson}/"
        out.append("  <url>")
        out.append(f"    <loc>{escape(url)}</loc>")
        out.append(f"    <lastmod>{today}</lastmod>")
        out.append("    <changefreq>monthly</changefreq>")
        out.append("    <priority>0.6</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    out.append("")
    return "\n".join(out)


def main() -> int:
    lesson_paths = find_lesson_paths()
    xml = build_xml(lesson_paths)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(xml, encoding="utf-8")
    sys.stdout.write(
        f"sitemap: {OUTPUT.relative_to(ROOT)}\n"
        f"  base={SITE_URL}\n"
        f"  static={len(STATIC_PAGES)} lessons={len(lesson_paths)} "
        f"total={len(STATIC_PAGES) + len(lesson_paths)}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
