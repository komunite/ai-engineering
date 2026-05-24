#!/usr/bin/env python3
"""Generate per-lesson Open Graph images (1280x640 JPG).

Reads the template at scripts/og_template.html, fills it with lesson
metadata, runs headless Chrome to screenshot the result, and writes a
high-quality JPG to site/og/<phase-dir>/<lesson-dir>.jpg.

Usage:
    # Preview a single lesson (Phase 0 / Lesson 01)
    python3 scripts/build_og.py --preview 00 01

    # Build all lessons (after the design is approved)
    python3 scripts/build_og.py --all

Headless Chrome must be available on the system. On macOS this script
looks for Google Chrome.app first, then falls back to `chromium`/`chrome`
on PATH.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image
except ImportError:
    sys.stderr.write("Pillow not installed. Run: pip3 install --user Pillow\n")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "og_template.html"
STATIC_TEMPLATE = ROOT / "scripts" / "og_template_static.html"
OUTPUT_BASE = ROOT / "site" / "og"

# Static pages get hard-coded copy; this keeps them out of any data file
# so the OG generation has zero runtime dependency on data.js.
STATIC_PAGES = [
    {
        "slug": "home",
        "eyebrow": "ANA SAYFA",
        "title": "Sıfırdan\nYapay Zeka\nMühendisliği",
        "tagline": "435 ders. 20 faz. Her algoritma; tek bir framework import edilmeden önce matematiğinden başlanarak kuruluyor.",
        "meta_left": "FIG_000 · MÜFREDAT V1.0 · 2026",
        "meta_right": "AÇIK KAYNAK · MIT",
        "footer_left": "PYTHON · TYPESCRIPT · RUST · JULIA",
    },
    {
        "slug": "catalog",
        "eyebrow": "DERS KATALOĞU",
        "title": "Ders Kataloğu",
        "tagline": "20 fazdaki tüm 435 ders. Faz, tür ve dil ile filtrele; tek tıkla aç.",
        "meta_left": "FIG_C00 · KATALOG · 2026",
        "meta_right": "AÇIK KAYNAK · MIT",
        "footer_left": "20 FAZ · 435 DERS · 4 DİL",
    },
    {
        "slug": "glossary",
        "eyebrow": "YAPAY ZEKA SÖZLÜĞÜ",
        "title": "Yapay Zeka Sözlüğü",
        "tagline": "İnsanların söylediği şey ile gerçekte ne anlama geldiği. Her terim, lafı dolandırmadan tanımlanıyor.",
        "meta_left": "FIG_G00 · SÖZLÜK · 2026",
        "meta_right": "AÇIK KAYNAK · MIT",
        "footer_left": "83 TERİM",
    },
    {
        "slug": "prereqs",
        "eyebrow": "YOL HARİTASI",
        "title": "Yol Haritası",
        "tagline": "20 fazın etkileşimli ön koşul haritası. Bir faza tıkla, neye dayandığını ve ileride neyin kapısını açtığını gör.",
        "meta_left": "FIG_R00 · YOL HARİTASI · 2026",
        "meta_right": "AÇIK KAYNAK · MIT",
        "footer_left": "20 FAZ · BAĞIMLILIK GRAFİĞİ",
    },
]

PHASE_RE = re.compile(r"^([0-9]{2})-([a-z0-9-]+)$")
LESSON_RE = re.compile(r"^([0-9]{2})-([a-z0-9-]+)$")
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
TAGLINE_RE = re.compile(r"^>\s*(.+)$", re.MULTILINE)
TYPE_RE = re.compile(r"\*\*Tür:\*\*\s*(\S+)")
LANGS_RE = re.compile(r"\*\*Diller:\*\*\s*(.+)")


def find_chrome() -> str:
    """Locate a usable headless-capable Chromium binary."""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "chromium",
        "chrome",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        which = shutil.which(c)
        if which:
            return which
    sys.stderr.write("Chrome / Chromium not found. Install Google Chrome.\n")
    sys.exit(2)


def parse_phase_readme(readme: Path) -> str:
    """Phase name = first H1 minus 'Faz N: ' prefix, uppercased."""
    if not readme.is_file():
        return "BİLİNMEYEN FAZ"
    text = readme.read_text(encoding="utf-8")
    m = H1_RE.search(text)
    if not m:
        return "BİLİNMEYEN FAZ"
    title = m.group(1).strip()
    title = re.sub(r"^Faz\s+\d+:\s*", "", title, flags=re.IGNORECASE)
    return title.upper()


def parse_lesson_doc(doc: Path) -> dict[str, str]:
    """Extract title (H1), tagline (first blockquote), type, languages."""
    out = {"title": "", "tagline": "", "type": "", "langs": ""}
    if not doc.is_file():
        return out
    text = doc.read_text(encoding="utf-8")
    m = H1_RE.search(text)
    if m:
        out["title"] = m.group(1).strip()
    m = TAGLINE_RE.search(text)
    if m:
        out["tagline"] = m.group(1).strip()
    m = TYPE_RE.search(text)
    if m:
        out["type"] = m.group(1).strip()
    m = LANGS_RE.search(text)
    if m:
        out["langs"] = m.group(1).strip()
    return out


def title_class(title: str) -> str:
    """Pick a CSS modifier so long titles still fit on the canvas.

    Multi-line titles (using \\n) are sized by the longest single line so
    a 3-line hero like "Sıfırdan / Yapay Zeka / Mühendisliği" still gets
    the default large display size.
    """
    longest = max((len(line) for line in title.split("\n")), default=0)
    if longest > 28:
        return "very-long"
    if longest > 18:
        return "long"
    return ""


def render_langs(langs_raw: str) -> str:
    """Comma-separated languages → uppercase tokens with blueprint separators."""
    if not langs_raw or langs_raw.strip() in ("—", "-", ""):
        return "&mdash;"
    parts = [p.strip() for p in langs_raw.split(",") if p.strip()]
    parts = [escape(p.upper()) for p in parts]
    return ('<span class="lang-sep">·</span>'.join(parts))


def render_html(meta: dict[str, str]) -> str:
    html = TEMPLATE.read_text(encoding="utf-8")
    title = meta.get("title", "Ders")
    replacements = {
        "{{PHASE_NUM_PAD}}": meta["phase_num"].zfill(2),
        "{{LESSON_NUM_PAD}}": meta["lesson_num"].zfill(2),
        "{{PHASE_NAME_UPPER}}": escape(meta["phase_name"]),
        "{{TYPE}}": escape(meta.get("type", "YAPIM").upper()),
        "{{TITLE}}": escape(title),
        "{{TITLE_CLASS}}": title_class(title),
        "{{TAGLINE}}": escape(meta.get("tagline", "")),
        "{{LANGS_HTML}}": render_langs(meta.get("langs", "")),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    return html


def screenshot(chrome: str, html: str, dest_png: Path) -> None:
    """Render the HTML in headless Chrome and write a 1280x640 PNG."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_html = Path(tmp) / "card.html"
        tmp_html.write_text(html, encoding="utf-8")
        cmd = [
            chrome,
            "--headless=new",
            "--hide-scrollbars",
            "--disable-gpu",
            "--no-sandbox",
            "--force-device-scale-factor=1",
            "--window-size=1280,640",
            # Give async webfont loads (VT323 in particular) time to settle
            # before Chrome snaps the screenshot. Without this Chrome captures
            # the FOUT state and the title falls back to the system mono font,
            # silently breaking the hero-H1 / homepage-H1 match.
            "--virtual-time-budget=4000",
            "--run-all-compositor-stages-before-draw",
            f"--screenshot={dest_png}",
            f"file://{tmp_html}",
        ]
        # Suppress Chrome's verbose stderr unless something actually fails.
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not dest_png.exists():
            sys.stderr.write(result.stderr)
            raise RuntimeError(f"Chrome screenshot failed (exit {result.returncode})")


def png_to_jpg(src_png: Path, dest_jpg: Path, quality: int = 90) -> None:
    img = Image.open(src_png).convert("RGB")
    # Hard-resize to exact 1280x640 in case Chrome added DPR scaling.
    if img.size != (1280, 640):
        img = img.resize((1280, 640), Image.LANCZOS)
    dest_jpg.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest_jpg, "JPEG", quality=quality, optimize=True, progressive=True)


def render_static_html(page: dict[str, str]) -> str:
    html = STATIC_TEMPLATE.read_text(encoding="utf-8")
    title = page["title"]
    replacements = {
        "{{META_LEFT}}": escape(page["meta_left"]),
        "{{META_RIGHT}}": escape(page["meta_right"]),
        "{{EYEBROW}}": escape(page["eyebrow"]),
        "{{TITLE}}": escape(title),
        "{{TITLE_CLASS}}": title_class(title),
        "{{TAGLINE}}": escape(page["tagline"]),
        "{{FOOTER_LEFT}}": escape(page["footer_left"]),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    return html


def build_static(chrome: str, page: dict[str, str]) -> Path:
    html = render_static_html(page)
    out_jpg = OUTPUT_BASE / f"{page['slug']}.jpg"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpf:
        tmp_png = Path(tmpf.name)
    try:
        screenshot(chrome, html, tmp_png)
        png_to_jpg(tmp_png, out_jpg)
    finally:
        if tmp_png.exists():
            tmp_png.unlink()
    return out_jpg


def build_one(chrome: str, phase_dir: Path, lesson_dir: Path) -> Path | None:
    """Render the OG card for a single lesson; return the output path."""
    phase_match = PHASE_RE.match(phase_dir.name)
    lesson_match = LESSON_RE.match(lesson_dir.name)
    if not phase_match or not lesson_match:
        return None
    # Prefer the Turkish doc; fall back to English so the script never silently
    # ships an empty title for un-translated lessons.
    doc = lesson_dir / "docs" / "tr.md"
    if not doc.exists():
        doc = lesson_dir / "docs" / "en.md"
    parsed = parse_lesson_doc(doc)
    phase_name = parse_phase_readme(phase_dir / "README.tr.md")
    if phase_name == "BİLİNMEYEN FAZ":
        phase_name = parse_phase_readme(phase_dir / "README.md")
    meta = {
        "phase_num": phase_match.group(1),
        "lesson_num": lesson_match.group(1),
        "phase_name": phase_name,
        **parsed,
    }
    html = render_html(meta)
    out_jpg = OUTPUT_BASE / phase_dir.name / f"{lesson_dir.name}.jpg"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpf:
        tmp_png = Path(tmpf.name)
    try:
        screenshot(chrome, html, tmp_png)
        png_to_jpg(tmp_png, out_jpg)
    finally:
        if tmp_png.exists():
            tmp_png.unlink()
    return out_jpg


def iter_lessons() -> Iterable[tuple[Path, Path]]:
    phases_root = ROOT / "phases"
    for phase_dir in sorted(phases_root.iterdir()):
        if not phase_dir.is_dir() or not PHASE_RE.match(phase_dir.name):
            continue
        for lesson_dir in sorted(phase_dir.iterdir()):
            if not lesson_dir.is_dir() or not LESSON_RE.match(lesson_dir.name):
                continue
            yield phase_dir, lesson_dir


def main() -> int:
    p = argparse.ArgumentParser(description="Generate per-lesson OG images.")
    p.add_argument("--preview", nargs=2, metavar=("PHASE", "LESSON"),
                   help="Build a single lesson by zero-padded numbers, e.g. 00 01")
    p.add_argument("--all", action="store_true", help="Build every lesson")
    p.add_argument("--static", action="store_true",
                   help="Build OG images for the 4 static pages (home, catalog, glossary, prereqs)")
    p.add_argument("--workers", type=int, default=4,
                   help="Parallel Chrome workers for --all (default: 4)")
    args = p.parse_args()

    chrome = find_chrome()

    if args.preview:
        phase_num, lesson_num = args.preview
        phases_root = ROOT / "phases"
        phase_dir = next(
            (d for d in phases_root.iterdir() if d.name.startswith(f"{phase_num.zfill(2)}-")),
            None,
        )
        if not phase_dir:
            sys.stderr.write(f"Phase {phase_num} not found.\n")
            return 3
        lesson_dir = next(
            (d for d in phase_dir.iterdir() if d.name.startswith(f"{lesson_num.zfill(2)}-")),
            None,
        )
        if not lesson_dir:
            sys.stderr.write(f"Lesson {lesson_num} not found in {phase_dir.name}.\n")
            return 3
        out = build_one(chrome, phase_dir, lesson_dir)
        print(f"wrote: {out.relative_to(ROOT) if out else '(none)'}")
        return 0

    if args.static:
        for page in STATIC_PAGES:
            out = build_static(chrome, page)
            print(f"wrote: {out.relative_to(ROOT)}")
        return 0

    if args.all:
        lessons = list(iter_lessons())
        total = len(lessons)
        print(f"rendering {total} lessons with {args.workers} worker(s)...")
        count = 0
        errors = 0

        def task(pair):
            return build_one(chrome, pair[0], pair[1])

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(task, pair): pair for pair in lessons}
            for fut in as_completed(futures):
                pair = futures[fut]
                try:
                    out = fut.result()
                    if out:
                        count += 1
                except Exception as e:
                    errors += 1
                    sys.stderr.write(f"FAIL {pair[0].name}/{pair[1].name}: {e}\n")
                if (count + errors) % 20 == 0:
                    print(f"  {count + errors}/{total} done (ok={count}, fail={errors})")
        print(f"done: {count} lesson(s){' — ' + str(errors) + ' error(s)' if errors else ''}")
        return 1 if errors else 0

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
