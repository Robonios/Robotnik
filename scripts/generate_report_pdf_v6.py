#!/usr/bin/env python3
"""
Robotnik 1Q26 report — PDF generator.

Parses the final V6 markdown and emits a branded A4 PDF using
scripts/report_pdf_template.py (the locked design system).
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_pdf_template import (  # noqa: E402
    make_doc, styles, register_fonts,
    section_header, CoverPage,
    PAGE_W, PAGE_H, MARGIN, FRAME_W,
    INK, MUTED, YELLOW, FILL, GRID, AMBER,
    RUNNING_HEADER_TEXT,
)
from reportlab.lib.units import mm
pt = 1
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether, ListFlowable, ListItem, NextPageTemplate,
)
from reportlab.pdfgen import canvas as canvas_mod


ROOT = Path(__file__).resolve().parent.parent
SRC = Path("/Users/robertosborne-ov/Downloads/Robotnik, State of the Frontier Stack_ 1Q26 (final).md")
CHARTS_PRINT = ROOT / "data" / "exports" / "report_charts"         # 300 DPI
CHARTS_WEB   = ROOT / "data" / "exports" / "report_charts_web"     # 150 DPI
ASSETS = ROOT / "assets"
OUT_DIR = ROOT / "data" / "exports" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Module-level state: which chart directory the current build uses.
# Toggled by build_pdf() / build_pdf_web().
CHARTS = CHARTS_PRINT


# ─────────────────────────────────────────────────────────────────────
# Markdown cleaning — strip escaped chars, embedded-image lines
# ─────────────────────────────────────────────────────────────────────

def clean_markdown(text: str) -> str:
    """Undo escapes from the Google-Doc markdown export."""
    # Drop giant embedded image base64 lines (appear as base64 image references)
    text = re.sub(r"\[image\d+\]:\s*<data:image/[^>]+>", "", text)
    # Drop the image-placeholder inline references (![][image1]) — we'll re-insert.
    text = re.sub(r"!\[\]\[image\d+\]", "", text)
    # Unescape escaped punctuation (\+, \-, \&, \., \# etc.)
    text = re.sub(r"\\([\+\-&\.\#\(\)\[\]])", r"\1", text)
    return text


# ─────────────────────────────────────────────────────────────────────
# Inline markdown → HTML (for ReportLab Paragraph markup)
# ─────────────────────────────────────────────────────────────────────

def inline_md(s: str) -> str:
    """Convert markdown inline syntax to ReportLab paragraph tags.

    Uses Python-Markdown for robust parsing (handles nested bold+italic
    like ***text*** and mixed-boundary cases ***X.** rest*), then maps
    the resulting <strong>/<em> tags to ReportLab's <b>/<i>.
    """
    import markdown as _md

    s = s.strip()
    # Fence raw text so the markdown parser doesn't chomp leading whitespace.
    html = _md.markdown(s, extensions=[])
    # Strip wrapping <p>…</p> that markdown always adds
    html = re.sub(r"^<p>|</p>$", "", html.strip())
    # Remap tag names to ReportLab's set
    html = html.replace("<strong>", "<b>").replace("</strong>", "</b>")
    html = html.replace("<em>", "<i>").replace("</em>", "</i>")
    # Style inline links (markdown renders them as <a href="…">…</a>)
    html = re.sub(
        r'<a href="([^"]+)">([^<]+)</a>',
        rf'<link href="\1" color="{AMBER.hexval()}">\2</link>',
        html,
    )
    return html


# ─────────────────────────────────────────────────────────────────────
# Parser — walk the markdown, emit a list of block dicts
# ─────────────────────────────────────────────────────────────────────

def parse_blocks(md: str):
    """Yield block dicts: {'type': 'h1'|'h2'|'h3'|'p'|'ul'|'ol'|'hr'|'figure', ...}."""
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()

        # Skip empty lines
        if not ln.strip():
            i += 1
            continue

        # Headings
        if ln.startswith("# "):
            yield {"type": "h1", "text": ln[2:].strip()}
            i += 1; continue
        if ln.startswith("## "):
            yield {"type": "h2", "text": ln[3:].strip()}
            i += 1; continue
        if ln.startswith("### "):
            yield {"type": "h3", "text": ln[4:].strip()}
            i += 1; continue

        # Horizontal rule
        if re.match(r"^-{3,}\s*$", ln):
            yield {"type": "hr"}
            i += 1; continue

        # Figure caption (line like "*Figure N: ...*")
        m = re.match(r"^\*(Figure\s+\d+:?.*)\*$", ln.strip())
        if m:
            yield {"type": "caption", "text": m.group(1).strip()}
            i += 1; continue

        # Bullet lists
        if re.match(r"^\s*\*\s+", ln) or re.match(r"^\s*-\s+", ln):
            items = []
            while i < len(lines) and (
                re.match(r"^\s*\*\s+", lines[i]) or re.match(r"^\s*-\s+", lines[i])
                or (items and lines[i].startswith(("  ", "\t")) and lines[i].strip())
            ):
                item_line = re.sub(r"^\s*[\*\-]\s+", "", lines[i]).rstrip()
                if re.match(r"^\s*[\*\-]\s+", lines[i]):
                    items.append(item_line)
                else:
                    items[-1] += " " + item_line.strip()
                i += 1
            yield {"type": "ul", "items": items}
            continue

        # Numbered lists
        if re.match(r"^\s*\d+\.\s+", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]).rstrip())
                i += 1
            yield {"type": "ol", "items": items}
            continue

        # Paragraph — accumulate consecutive non-empty non-structural lines.
        # Only check for structural markers that actually start blocks; do
        # not match arbitrary leading digits (many paragraphs begin "1Q26…").
        para_lines = []
        while i < len(lines):
            cur = lines[i].rstrip()
            if not cur.strip():
                break
            if (cur.startswith("#")
                or re.match(r"^\s*\*\s+", cur)
                or re.match(r"^\s*-\s+", cur)
                or re.match(r"^\s*\d+\.\s+", cur)
                or re.match(r"^-{3,}\s*$", cur)
                or re.match(r"^\*Figure", cur.strip())):
                break
            para_lines.append(cur)
            i += 1
        if para_lines:
            yield {"type": "p", "text": " ".join(para_lines).strip()}
        else:
            # Safety: advance past any line that fell through (shouldn't happen)
            i += 1


# ─────────────────────────────────────────────────────────────────────
# Layout — turn block dicts into ReportLab flowables
# ─────────────────────────────────────────────────────────────────────

def embed_image(path: Path, width_mm: float = 150) -> Image:
    """Embed a PNG at a fixed width; preserve aspect."""
    img = Image(str(path))
    orig_w, orig_h = img.imageWidth, img.imageHeight
    target_w = width_mm * mm
    scale = target_w / orig_w
    img.drawWidth = target_w
    img.drawHeight = orig_h * scale
    img.hAlign = "CENTER"
    return img


# Figure placement rules: after which paragraph do we inject which image?
# (section_h1_text, count_of_paragraphs_after_which_to_insert) → image path + caption
FIGURE_PLACEMENTS = {
    # Executive Summary: Figure 1 after the first lede paragraph + bullets.
    # We'll insert by marker: after the "In a quarter where broad markets contracted..." line
    "exec_fig1": {
        "image": CHARTS / "chart_q1_benchmark_comparison.png",
        "caption": "Figure 1: Robotnik Composite vs Major Benchmarks — Q1 2026. "
                   "All series rebased to 100 on 31 December 2025.",
    },
    "sec2_fig2": {
        "image": CHARTS / "chart_since_inception.png",
        "caption": "Figure 2: Robotnik Composite Index — first twelve months. "
                   "Base 1,000 on 31 March 2025; close 2,003.68 on 31 March 2026.",
    },
    "sec2_fig3": {
        "image": CHARTS / "chart_q1_subindex_comparison.png",
        "caption": "Figure 3: Robotnik Sub-Indices — Q1 2026 performance. "
                   "All series rebased to 100 on 31 December 2025.",
    },
    "sec4_fig4": {
        "image": CHARTS / "chart_funding_trends.png",
        "caption": "Figure 4: Frontier Stack Monthly Funding, April 2025 – March 2026. "
                   "Stacked by sector.",
    },
    "sec4_fig5": {
        "image": CHARTS / "chart_q1_funding_breakdown.png",
        "caption": "Figure 5: Q1 2026 Funding by Sector — $46.0bn across 91 rounds.",
    },
}


# Text-match triggers for figure insertion — looks for a distinctive
# substring of the preceding paragraph; figure is inserted immediately
# after that paragraph is placed in the story.
FIGURE_TRIGGERS = [
    # (substring, figure_key)
    ("In a quarter where broad markets contracted", "exec_fig1"),
    ("closed at 2,003.68 on 31 March 2026", "sec2_fig2"),
    ("Without the cap, the figure would have been considerably higher",
     "sec2_fig3"),
    ("exceeded that annual total by", "sec4_fig4"),
    ("Materials: 9 rounds, $1.15b", "sec4_fig5"),
]


def should_insert_figure_after(text: str):
    """Given a paragraph's text, return list of figure keys to insert after it."""
    keys = []
    for substr, key in FIGURE_TRIGGERS:
        if substr in text:
            keys.append(key)
    return keys


def add_figure(story, key, st):
    fig = FIGURE_PLACEMENTS.get(key)
    if not fig: return
    # Rewrite path to point at whichever chart directory the current
    # build is using (300 DPI print vs 150 DPI web).
    img_path = CHARTS / fig["image"].name
    if not img_path.exists():
        return
    story.append(Spacer(1, 6))
    story.append(embed_image(img_path, width_mm=150))
    story.append(Paragraph(fig["caption"], st["caption"]))
    story.append(Spacer(1, 4))


# ─────────────────────────────────────────────────────────────────────
# Block → flowable mappers
# ─────────────────────────────────────────────────────────────────────

SECTION_NUMBERS = {
    "Section 1: The Dependency Chain": 1,
    "Section 2: The Robotnik Index": 2,
    "Section 3: Sector Briefings": 3,
    "Section 4: Funding Intelligence": 4,
    "Section 5: The Robotnik Platform": 5,
    "Section 6: Implications and Risks": 6,
}

TOC_ITEMS = [
    ("Opening Transmission", 2),
    ("About the Author", 3),
    ("Executive Summary", 4),
    ("Section 1 · The Dependency Chain", 7),
    ("Section 2 · The Robotnik Index", 13),
    ("Section 3 · Sector Briefings", 16),
    ("Section 4 · Funding Intelligence", 22),
    ("Section 5 · The Robotnik Platform", 25),
    ("Section 6 · Implications and Risks", 27),
    ("Closing Transmission", 30),
    ("Appendix A · Methodology", 32),
    ("Appendix B · Sources", 34),
    ("Glossary", 36),
    ("Disclaimer", 38),
]


def discover_toc_page_numbers(pdf_path):
    """Walk a built PDF, find first page of each section AFTER the TOC.

    The Contents page itself lists every section title, so naïvely
    searching for marker substrings would collapse every entry onto
    the TOC page. We detect the TOC page first and start the search
    on the following page.
    """
    import fitz
    doc = fitz.open(pdf_path)

    # Locate TOC page by looking for "Contents\n" at the top of a page
    toc_page_idx = 0
    for i, page in enumerate(doc):
        txt = page.get_text()
        # Contents page: the word "Contents" appears with multiple TOC entries
        if "Contents" in txt and "Opening Transmission" in txt \
           and "About the Author" in txt and "Section 1" in txt:
            toc_page_idx = i
            break

    # Markers chosen to appear UNIQUELY on each section opener page —
    # i.e. as the large H1 title, not as inline references elsewhere.
    # Markers are matched in document order with a monotonic page cursor
    # so that false matches earlier in the doc can't steal a section's slot.
    markers_in_order = [
        ("Opening Transmission",                 "TRANSMISSION FROM ROBOTNIK"),
        ("About the Author",                     "About the Author"),
        ("Executive Summary",                    "Executive Summary"),
        ("Section 1 · The Dependency Chain",     "The Dependency Chain"),
        ("Section 2 · The Robotnik Index",       "The Robotnik Index"),
        ("Section 3 · Sector Briefings",         "Sector Briefings"),
        ("Section 4 · Funding Intelligence",     "Funding Intelligence"),
        ("Section 5 · The Robotnik Platform",    "The Robotnik Platform"),
        ("Section 6 · Implications and Risks",   "Implications and Risks"),
        # Transmission markers: Closing uses the same "TRANSMISSION FROM
        # ROBOTNIK" banner as Opening — so we use the H1 title text instead.
        ("Closing Transmission",                 "Tovarishchi"),
        # Appendix / Glossary / Disclaimer H1 titles use · separator
        ("Appendix A · Methodology",             "Appendix A · Methodology"),
        ("Appendix B · Sources",                 "Appendix B · Sources"),
        ("Glossary",                             "Glossary"),
        ("Disclaimer",                           "Disclaimer"),
    ]

    result = {}
    cursor = 0  # lowest page index to search from — advances monotonically
    for name, marker in markers_in_order:
        # Opening Transmission and About the Author appear BEFORE the TOC,
        # so cursor for them starts at 0.
        # All others must come AFTER the TOC page.
        lo = 0 if name in ("Opening Transmission", "About the Author") \
             else max(cursor, toc_page_idx + 1)
        for i in range(lo, len(doc)):
            txt = doc[i].get_text()
            if marker in txt:
                result[name] = i + 1
                cursor = i  # next marker can't appear earlier than this page
                break
    doc.close()
    return result


def build_story(toc_pages: dict | None = None):
    """Main builder — returns a flowables story for doc.build().

    If toc_pages is provided (a dict of {section_name: page_number}),
    the Contents page uses those numbers. Otherwise, the stale defaults
    in TOC_ITEMS are used (first-pass build).
    """
    register_fonts()
    st = styles()
    story = []

    # ── Cover page: use default first template (cover) for page 1 ──
    # We push a tiny Spacer on the cover frame so page 1 exists, then
    # switch templates before the page-break so page 2 uses transmission.
    story.append(Spacer(1, 1))
    story.append(NextPageTemplate("transmission"))
    story.append(PageBreak())
    story.append(Paragraph("TRANSMISSION FROM ROBOTNIK", st["transmission_header"]))
    story.append(Spacer(1, 18))

    raw = clean_markdown(SRC.read_text())

    # Extract just the Opening Transmission block
    opening_text = _extract_section(raw, "# Transmission from Robotnik",
                                     next_header="# About the Author")
    meta_style = ParagraphStyle(
        "transmission_meta",
        fontName="Mulish-Italic",
        fontSize=10,
        leading=10 * 1.35,
        textColor=MUTED,
        alignment=TA_LEFT,
        spaceAfter=0,
    )
    for para in _split_paras(opening_text):
        stripped = para.strip()
        if stripped.startswith("— ROBOTNIK"):
            story.append(Spacer(1, 10))
            story.append(Paragraph(inline_md(para), st["transmission_signoff"]))
        # Compact metadata block: Origin / Relay date / Clearance — render
        # as tight italic grey lines rather than full paragraphs.
        elif re.match(r"^\*(Origin|Relay date|Clearance):", stripped):
            # Strip the outer markdown italic markers and render
            meta_text = stripped.strip("*").strip()
            story.append(Paragraph(meta_text, meta_style))
        else:
            story.append(Paragraph(inline_md(para), st["transmission"]))
    story.append(PageBreak())

    # ── About the Author ──
    story.append(NextPageTemplate("body"))
    story.append(Paragraph("About the Author", st["h1"]))
    author_text = _extract_section(raw, "# About the Author", "# Contents")
    for para in _split_paras(author_text):
        story.append(Paragraph(inline_md(para), st["body"]))
    story.append(PageBreak())

    # ── Contents ──
    story.append(Paragraph("Contents", st["h1"]))
    story.append(Spacer(1, 10))
    for name, default_page in TOC_ITEMS:
        page = (toc_pages or {}).get(name, default_page)
        # Dot-leader line: name ........... page
        dots = "." * max(3, 80 - len(name) - len(str(page)))
        line = f'<font color="#6B7280">{dots}</font>'
        story.append(Paragraph(
            f'{name} {line} {page}',
            st["toc_entry"],
        ))
    story.append(PageBreak())

    # ── Executive Summary ──
    story.append(Paragraph("Executive Summary", st["h1"]))
    exec_text = _extract_section(raw, "# Executive Summary", "# Section 1:")
    _emit_section_body(story, exec_text, st, lede_first=True)
    story.append(PageBreak())

    # ── Sections 1–6 ──
    section_bounds = [
        ("# Section 1:", "# Section 2:", "Section 1: The Dependency Chain", 1),
        ("# Section 2:", "# Section 3:", "Section 2: The Robotnik Index", 2),
        ("# Section 3:", "# Section 4:", "Section 3: Sector Briefings", 3),
        ("# Section 4:", "# Section 5:", "Section 4: Funding Intelligence", 4),
        ("# Section 5:", "# Section 6:", "Section 5: The Robotnik Platform", 5),
        ("# Section 6:", "# Closing Transmission", "Section 6: Implications and Risks", 6),
    ]
    for idx, (start, end, title, num) in enumerate(section_bounds):
        # Section header on new page
        title_short = title.split(": ", 1)[1] if ": " in title else title
        for f in section_header(num, title_short, st):
            story.append(f)
        story.append(Spacer(1, 8))
        body = _extract_section(raw, start, end)
        body = re.sub(r"^# Section \d+: [^\n]+\n", "", body, count=1)
        _emit_section_body(story, body, st)
        # After the LAST section (Section 6), the next page should be the
        # Closing Transmission → switch to the transmission template BEFORE
        # the page break so the new page lands on the right template.
        if idx == len(section_bounds) - 1:
            story.append(NextPageTemplate("transmission"))
        story.append(PageBreak())

    # ── Closing Transmission ──
    # NextPageTemplate("transmission") already set above; this page uses it.
    story.append(Paragraph("TRANSMISSION FROM ROBOTNIK", st["transmission_header"]))
    closing_text = _extract_section(raw, "# Closing Transmission", "# Appendices")
    closing_paras = _split_paras(closing_text)
    for j, para in enumerate(closing_paras):
        # The last paragraph (the ROBOTNIK sign-off block) always ends the
        # transmission; switch templates BEFORE the page break that follows.
        if para.strip().startswith("***ROBOTNIK**") or para.strip().startswith("**ROBOTNIK"):
            story.append(Spacer(1, 10))
            story.append(Paragraph(inline_md(para), st["transmission_signoff"]))
        else:
            story.append(Paragraph(inline_md(para), st["transmission"]))
    # Switch back to body template for the appendix pages
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # ── Appendix A: Methodology ──
    story.append(Paragraph("Appendix A · Methodology", st["h1"]))
    a_text = _extract_section(raw, "## Appendix A: Methodology", "## Appendix B: Sources")
    a_text = re.sub(r"^## Appendix A: Methodology\n", "", a_text, count=1)
    _emit_section_body(story, a_text, st)
    story.append(PageBreak())

    # ── Appendix B: Sources ──
    story.append(Paragraph("Appendix B · Sources", st["h1"]))
    b_text = _extract_section(raw, "## Appendix B: Sources", "# Glossary")
    b_text = re.sub(r"^## Appendix B: Sources\n", "", b_text, count=1)
    _emit_section_body(story, b_text, st)
    story.append(PageBreak())

    # ── Glossary ──
    story.append(Paragraph("Glossary", st["h1"]))
    g_text = _extract_section(raw, "# Glossary", "# Disclaimer")
    g_text = re.sub(r"^# Glossary\n", "", g_text, count=1)
    _emit_section_body(story, g_text, st)
    story.append(PageBreak())

    # ── Disclaimer ──
    story.append(Paragraph("Disclaimer", st["h1"]))
    d_text = _extract_section(raw, "# Disclaimer", None)
    d_text = re.sub(r"^# Disclaimer\n", "", d_text, count=1)
    _emit_section_body(story, d_text, st)

    return story


def _extract_section(raw: str, start_marker: str, next_header=None) -> str:
    """Extract the body BELOW a section heading, excluding the heading line itself."""
    start = raw.find(start_marker)
    if start < 0:
        return ""
    # Advance past the entire heading line so callers don't re-render it as body.
    nl = raw.find("\n", start)
    if nl >= 0:
        start = nl + 1
    if next_header is None:
        return raw[start:]
    end = raw.find(next_header, start)
    return raw[start:end] if end > 0 else raw[start:]


def _split_paras(text: str):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _emit_section_body(story, body_text, st, lede_first=False):
    """Walk blocks within a section body and emit flowables."""
    # Strip first heading (already placed as H1)
    blocks = list(parse_blocks(body_text))
    emitted_lede = not lede_first
    for blk in blocks:
        t = blk["type"]
        if t == "h1":
            # Nested H1 inside a section — shouldn't happen. Downgrade to H2.
            story.append(Paragraph(inline_md(blk["text"]), st["h2"]))
        elif t == "h2":
            story.append(Paragraph(inline_md(blk["text"]), st["h2"]))
        elif t == "h3":
            story.append(Paragraph(inline_md(blk["text"]), st["h3"]))
        elif t == "hr":
            story.append(HRFlowable(
                width="100%", thickness=0.5, color=GRID,
                spaceBefore=6, spaceAfter=6,
            ))
        elif t == "caption":
            # Figure captions are regenerated from our figure_placements;
            # drop inline markdown captions to avoid duplicates.
            continue
        elif t == "ul":
            items = [
                ListItem(Paragraph(inline_md(item), st["bullet"]),
                         leftIndent=14, bulletColor=INK)
                for item in blk["items"]
            ]
            story.append(ListFlowable(
                items, bulletType="bullet", bulletChar="•",
                bulletFontName="Mulish", bulletFontSize=8,
                leftIndent=14, bulletIndent=2,
                spaceBefore=2, spaceAfter=10,
            ))
        elif t == "ol":
            items = [
                ListItem(Paragraph(inline_md(item), st["bullet"]),
                         leftIndent=18, bulletColor=INK)
                for item in blk["items"]
            ]
            story.append(ListFlowable(
                items, bulletType="1",
                bulletFontName="Mulish-Medium", bulletFontSize=10.5,
                leftIndent=18, bulletIndent=2,
                spaceBefore=2, spaceAfter=10,
            ))
        elif t == "p":
            txt = blk["text"]
            style = st["lede"] if (lede_first and not emitted_lede) else st["body"]
            emitted_lede = True
            story.append(Paragraph(inline_md(txt), style))
            # Figure insertion — after selected paragraphs
            for key in should_insert_figure_after(txt):
                add_figure(story, key, st)


# ─────────────────────────────────────────────────────────────────────
# Cover drawing — done via a canvas hook because it's not a Flowable
# ─────────────────────────────────────────────────────────────────────

# Find cover background image
def find_cover_bg():
    for candidate in [
        ASSETS / "cover" / "cosmonaut-bg.png",
        ROOT / "cosmonaut-bg.png",
    ]:
        if candidate.exists():
            return candidate
    return None


class _CoverHookDoc:
    """Wraps a BaseDocTemplate to draw cover content on page 1."""
    def __init__(self, doc, cover):
        self.doc = doc
        self.cover = cover


def _build_once(out_path, toc_pages=None):
    """Single build pass."""
    doc = make_doc(out_path)
    cover_bg = find_cover_bg()
    cover = CoverPage(background_path=cover_bg)
    def on_first_page(canvas, d):
        cover.draw_on(canvas)
    for tmpl in doc.pageTemplates:
        if tmpl.id == "cover":
            tmpl.onPage = on_first_page
            break
    doc.build(build_story(toc_pages=toc_pages))
    return doc


def build_pdf(out_path):
    """Two-pass build so the Contents page has correct page numbers."""
    tmp = Path(str(out_path) + ".pass1.pdf")
    _build_once(tmp)                               # first pass (stale TOC)
    toc_pages = discover_toc_page_numbers(tmp)     # scan for real page numbers
    _build_once(out_path, toc_pages=toc_pages)     # second pass (correct TOC)
    try:
        tmp.unlink()
    except OSError:
        pass
    return out_path


def _build_both():
    """Build print (300 DPI charts) + web (150 DPI charts) PDFs."""
    global CHARTS

    # Print version (default 300 DPI charts)
    CHARTS = CHARTS_PRINT
    print_out = OUT_DIR / "1Q26_State_of_the_Frontier_Stack.pdf"
    build_pdf(print_out)
    print_size = print_out.stat().st_size
    print(f"✓ Print : {print_out.name}  ({print_size/1024:.1f} KB, {print_size/(1024*1024):.2f} MB)")

    # Web version (150 DPI charts)
    CHARTS = CHARTS_WEB
    web_out = OUT_DIR / "1Q26_State_of_the_Frontier_Stack_web.pdf"
    build_pdf(web_out)
    web_size = web_out.stat().st_size
    print(f"✓ Web   : {web_out.name}  ({web_size/1024:.1f} KB, {web_size/(1024*1024):.2f} MB)")
    print(f"  Reduction: {(1 - web_size/print_size)*100:.1f}%")


if __name__ == "__main__":
    print(f"Source: {SRC}")
    print(f"Output dir: {OUT_DIR}")
    _build_both()
