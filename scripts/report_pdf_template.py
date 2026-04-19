"""
Robotnik Quarterly Report — PDF Template
========================================
Locked visual template for branded PDF production of Robotnik's
quarterly reports (1Q26 and every future quarter).

Design system locked in brief:
  - Fonts: Space Grotesk (headings), Mulish (body + numbers)
  - A4 portrait, 25mm margins (opening-transmission page gets 30mm)
  - White background, ink #1A1F2B, Robotnik yellow #F5D921 accent only
  - Running header (top-right, grey) + page number (bottom-right, grey)
  - Section headers open with Robotnik-yellow rule + "SECTION N" eyebrow

Build a PDF by constructing `ReportBuilder(out_path)`, pushing flowables
onto its story via the `add_*` helpers, and calling `builder.build()`.
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
pt = 1  # ReportLab's internal unit is the point — no separate alias needed
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvas_mod
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Image, PageBreak, Table, TableStyle, KeepTogether, ListFlowable,
    ListItem, HRFlowable, NextPageTemplate,
)


# ─────────────────────────────────────────────────────────────────────
# Palette (locked — do not alter without brand approval)
# ─────────────────────────────────────────────────────────────────────

INK    = HexColor("#1A1F2B")
MUTED  = HexColor("#6B7280")
PAPER  = HexColor("#FFFFFF")
FILL   = HexColor("#F8F9FA")
YELLOW = HexColor("#F5D921")
GRID   = HexColor("#E5E7EB")
AMBER  = HexColor("#D97706")

SECTOR_COLOURS = {
    "semiconductor": HexColor("#60A5FA"),
    "robotics":      HexColor("#6EE7B7"),
    "space":         HexColor("#F87171"),
    "materials":     HexColor("#A78BFA"),
}


# ─────────────────────────────────────────────────────────────────────
# Font registration — static weights from /assets/fonts/static/
# ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts" / "static"

# Font name → TTF file. Names are what we use in Paragraph styles.
_FONT_MAP = {
    "Mulish":                FONT_DIR / "Mulish-Regular.ttf",
    "Mulish-Medium":         FONT_DIR / "Mulish-Medium.ttf",
    "Mulish-Bold":           FONT_DIR / "Mulish-Bold.ttf",
    "Mulish-Italic":         FONT_DIR / "Mulish-Italic.ttf",
    "Mulish-BoldItalic":     FONT_DIR / "Mulish-BoldItalic.ttf",
    "SpaceGrotesk-Medium":   FONT_DIR / "SpaceGrotesk-Medium.ttf",
    "SpaceGrotesk-SemiBold": FONT_DIR / "SpaceGrotesk-SemiBold.ttf",
    "SpaceGrotesk-Bold":     FONT_DIR / "SpaceGrotesk-Bold.ttf",
}

_fonts_registered = False

def register_fonts():
    """Register all Robotnik report fonts. Idempotent."""
    global _fonts_registered
    if _fonts_registered:
        return
    for name, path in _FONT_MAP.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing font: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    # Font family registration — lets <b>, <i>, <em>, <strong> map correctly
    # within Paragraph markup.
    pdfmetrics.registerFontFamily(
        "Mulish",
        normal="Mulish",
        bold="Mulish-Bold",
        italic="Mulish-Italic",
        boldItalic="Mulish-BoldItalic",
    )
    _fonts_registered = True


# ─────────────────────────────────────────────────────────────────────
# Page geometry
# ─────────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
MARGIN = 25 * mm               # standard body page
OT_MARGIN = 30 * mm             # opening / closing transmission pages

FRAME_W = PAGE_W - 2 * MARGIN
FRAME_H = PAGE_H - 2 * MARGIN


# ─────────────────────────────────────────────────────────────────────
# Paragraph styles — body, headings, captions
# ─────────────────────────────────────────────────────────────────────

def _styles():
    """Returns a dict of named ParagraphStyles. Call after register_fonts()."""
    register_fonts()

    body = ParagraphStyle(
        "body",
        fontName="Mulish",
        fontSize=10.5,
        leading=10.5 * 1.55,
        textColor=INK,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        hyphenationLang="en_GB",
    )

    lede = ParagraphStyle(
        "lede",
        parent=body,
        fontName="Mulish-Medium",
        fontSize=12,
        leading=12 * 1.55,
        spaceAfter=12,
    )

    body_ragged = ParagraphStyle(
        "body_ragged",
        parent=body,
        alignment=TA_LEFT,
    )

    caption = ParagraphStyle(
        "caption",
        fontName="Mulish-Italic",
        fontSize=9,
        leading=9 * 1.3,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=12,
    )

    h1 = ParagraphStyle(
        "h1",
        fontName="SpaceGrotesk-Bold",
        fontSize=28,
        leading=28 * 1.15,
        textColor=INK,
        spaceBefore=0,
        spaceAfter=20,
        alignment=TA_LEFT,
    )

    eyebrow = ParagraphStyle(
        "eyebrow",
        fontName="SpaceGrotesk-Medium",
        fontSize=10,
        leading=10 * 1.2,
        textColor=MUTED,
        spaceBefore=12,
        spaceAfter=4,
        alignment=TA_LEFT,
    )

    h2 = ParagraphStyle(
        "h2",
        fontName="SpaceGrotesk-SemiBold",
        fontSize=18,
        leading=18 * 1.2,
        textColor=INK,
        spaceBefore=24,
        spaceAfter=12,
        alignment=TA_LEFT,
        keepWithNext=1,
    )

    h3 = ParagraphStyle(
        "h3",
        fontName="SpaceGrotesk-Medium",
        fontSize=13,
        leading=13 * 1.25,
        textColor=INK,
        spaceBefore=16,
        spaceAfter=8,
        alignment=TA_LEFT,
        keepWithNext=1,
    )

    # Opening / Closing transmission narrative body
    transmission = ParagraphStyle(
        "transmission",
        fontName="Mulish",
        fontSize=11,
        leading=11 * 1.7,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=12,
    )

    transmission_header = ParagraphStyle(
        "transmission_header",
        fontName="SpaceGrotesk-Medium",
        fontSize=10,
        leading=10 * 1.2,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=30,
    )

    transmission_signoff = ParagraphStyle(
        "transmission_signoff",
        fontName="Mulish-Italic",
        fontSize=10,
        leading=10 * 1.4,
        textColor=MUTED,
        alignment=TA_RIGHT,
        spaceBefore=24,
    )

    # List item
    bullet = ParagraphStyle(
        "bullet",
        parent=body,
        leftIndent=14,
        bulletIndent=2,
        spaceAfter=4,
    )

    # Contents
    toc_entry = ParagraphStyle(
        "toc_entry",
        fontName="Mulish-Medium",
        fontSize=11,
        leading=11 * 1.6,
        textColor=INK,
        alignment=TA_LEFT,
        spaceAfter=2,
    )

    # Appendix / disclaimer body (slightly smaller)
    small = ParagraphStyle(
        "small",
        parent=body,
        fontSize=9.5,
        leading=9.5 * 1.55,
        spaceAfter=6,
    )

    return dict(
        body=body, body_ragged=body_ragged, lede=lede, caption=caption,
        h1=h1, h2=h2, h3=h3, eyebrow=eyebrow,
        transmission=transmission,
        transmission_header=transmission_header,
        transmission_signoff=transmission_signoff,
        bullet=bullet,
        toc_entry=toc_entry,
        small=small,
    )


# ─────────────────────────────────────────────────────────────────────
# Page templates — cover / transmission / body
# ─────────────────────────────────────────────────────────────────────

RUNNING_HEADER_TEXT = "Robotnik · 1Q26 State of the Frontier Stack"


def _draw_running_chrome(canvas, doc, show_header=True, show_page_number=True):
    """Stamp running header + page number on body pages."""
    canvas.saveState()
    canvas.setFillColor(MUTED)
    canvas.setFont("Mulish", 9)
    if show_header:
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 15 * mm,
                               RUNNING_HEADER_TEXT)
    if show_page_number:
        canvas.drawRightString(PAGE_W - MARGIN, 12 * mm, str(doc.page))
    canvas.restoreState()


def _on_body(canvas, doc):
    _draw_running_chrome(canvas, doc, show_header=True, show_page_number=True)


def _on_transmission(canvas, doc):
    # No header, no page number (per brief: cover + opening transmission skip)
    pass


def _on_cover(canvas, doc):
    # Cover drawing handled by separate CoverFlowable — this is just
    # a blank background setup so the frame doesn't render the header.
    pass


def _build_templates():
    body_frame = Frame(
        MARGIN, MARGIN, FRAME_W, FRAME_H,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="body",
    )
    # Narrower frame for transmission pages
    ot_frame = Frame(
        OT_MARGIN, OT_MARGIN, PAGE_W - 2 * OT_MARGIN, PAGE_H - 2 * OT_MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="ot",
    )
    cover_frame = Frame(
        0, 0, PAGE_W, PAGE_H,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="cover",
    )
    return [
        PageTemplate(id="cover", frames=[cover_frame], onPage=_on_cover),
        PageTemplate(id="transmission", frames=[ot_frame], onPage=_on_transmission),
        PageTemplate(id="body", frames=[body_frame], onPage=_on_body),
    ]


# ─────────────────────────────────────────────────────────────────────
# Flowable: section header block (rule + eyebrow + title)
# ─────────────────────────────────────────────────────────────────────

def section_header(section_num, title, styles):
    """Return flowables for a section opener: yellow rule + eyebrow + title."""
    flows = []
    flows.append(HRFlowable(
        width=60 * pt, thickness=2, color=YELLOW,
        spaceBefore=0, spaceAfter=12, hAlign="LEFT",
    ))
    flows.append(Paragraph(
        f'<font color="#6B7280"><b>SECTION&#160;{section_num}</b></font>',
        ParagraphStyle(
            "eyebrow_inline", fontName="SpaceGrotesk-Medium",
            fontSize=10, textColor=MUTED, alignment=TA_LEFT,
            spaceBefore=0, spaceAfter=4, leading=12,
        ),
    ))
    flows.append(Paragraph(title, styles["h1"]))
    return flows


# ─────────────────────────────────────────────────────────────────────
# Flowable: cover page
# ─────────────────────────────────────────────────────────────────────

class CoverPage:
    """Builds cover page flowables. Renders as a sequence of drawing commands
    onto a full-page frame — cover is intentionally not paragraph-flowed."""

    def __init__(self, background_path, quarter_label="1Q26", month_year="April 2026"):
        self.background_path = background_path
        self.quarter = quarter_label
        self.month_year = month_year

    def draw_on(self, canvas):
        # Full-bleed background image
        if self.background_path and Path(self.background_path).exists():
            try:
                canvas.drawImage(
                    str(self.background_path), 0, 0,
                    width=PAGE_W, height=PAGE_H,
                    preserveAspectRatio=False, mask="auto",
                )
            except Exception:
                pass

        # 15% darkening overlay
        canvas.saveState()
        canvas.setFillColorRGB(0, 0, 0, alpha=0.15)
        canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        canvas.restoreState()

        # Top-left wordmark
        canvas.saveState()
        canvas.setFillColor(YELLOW)
        canvas.setFont("SpaceGrotesk-Bold", 32)
        canvas.drawString(40 * pt, PAGE_H - 50 * pt - 24, "ROBOTNIK")

        # Subtitle
        canvas.setFillColorRGB(1, 1, 1)
        canvas.setFont("SpaceGrotesk-Medium", 14)
        canvas.drawString(40 * pt, PAGE_H - 90 * pt - 14,
                          "STATE OF THE FRONTIER STACK")

        # Big quarter label — lower-right quadrant
        canvas.setFillColor(YELLOW)
        canvas.setFont("SpaceGrotesk-Bold", 96)
        q_text = self.quarter
        q_width = canvas.stringWidth(q_text, "SpaceGrotesk-Bold", 96)
        canvas.drawString(PAGE_W - q_width - 40 * pt, PAGE_H * 0.42, q_text)

        # Tagline bottom-left
        canvas.setFillColorRGB(1, 1, 1)
        canvas.setFont("Mulish", 12)
        canvas.drawString(40 * pt, 40 * pt + 30,
                          "The quarterly intelligence report on semiconductors,")
        canvas.drawString(40 * pt, 40 * pt + 14,
                          "robotics, space, and critical materials.")

        # Footer
        canvas.setFont("Mulish-Medium", 10)
        canvas.drawString(40 * pt, 20 * pt, "robotnik.world")
        canvas.drawRightString(PAGE_W - 40 * pt, 20 * pt, self.month_year)
        canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────

def make_doc(out_path, title="Robotnik 1Q26 State of the Frontier Stack"):
    """Returns a configured BaseDocTemplate ready for .build(story)."""
    register_fonts()
    doc = BaseDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=title,
        author="Robotnik",
        subject="Quarterly Report",
        creator="Robotnik (report_pdf_template.py)",
    )
    doc.addPageTemplates(_build_templates())
    return doc


# Export the style dict for consumers
STYLES = None

def styles():
    global STYLES
    if STYLES is None:
        STYLES = _styles()
    return STYLES
