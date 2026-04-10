#!/usr/bin/env python3
"""
Robotnik 1Q26 Report PDF Generator
====================================
Converts the markdown report to a branded PDF with dark theme,
Signal Yellow headings, embedded charts, and cover page.
"""

import re
import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    PageBreak, Table, TableStyle, Image, Flowable, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── Paths ──
ROOT = Path(__file__).resolve().parent.parent
REPORT_MD = Path("/Users/robertosborne-ov/Downloads/1Q26_STATE_OF_THE_FRONTIER_STACK_V3.md")
COVER_IMG = Path("/Users/robertosborne-ov/Downloads/ChatGPT Image Mar 14, 2026, 10_20_08 AM.png")
CHARTS_DIR = ROOT / "data" / "exports" / "report_charts"
OUTPUT_DIR = ROOT / "data" / "exports"
OUTPUT_PDF = OUTPUT_DIR / "1Q26_State_of_the_Frontier_Stack.pdf"

# ── Colours ──
VOID = HexColor('#0A0A0F')
YELLOW = HexColor('#F5D921')
TEXT = HexColor('#E0E0E0')
DIM = HexColor('#888888')
TABLE_HDR_BG = HexColor('#1A1A2E')
TABLE_ALT_BG = HexColor('#111122')
GREEN = HexColor('#4ADE80')
RED = HexColor('#F87171')
QUOTE_BG = HexColor('#111122')
BORDER = HexColor('#333333')

PAGE_W, PAGE_H = A4

# ── Styles ──
def make_styles():
    s = {}
    s['h1'] = ParagraphStyle('H1', fontName='Courier', fontSize=16, textColor=YELLOW,
                              spaceAfter=4*mm, spaceBefore=6*mm, leading=20)
    s['h2'] = ParagraphStyle('H2', fontName='Courier', fontSize=13, textColor=YELLOW,
                              spaceAfter=3*mm, spaceBefore=5*mm, leading=16)
    s['h3'] = ParagraphStyle('H3', fontName='Courier-Bold', fontSize=10, textColor=YELLOW,
                              spaceAfter=2*mm, spaceBefore=4*mm, leading=13)
    s['body'] = ParagraphStyle('Body', fontName='Helvetica', fontSize=9.5, textColor=TEXT,
                                leading=13.5, spaceAfter=2*mm, alignment=TA_LEFT)
    s['quote'] = ParagraphStyle('Quote', fontName='Courier-Oblique', fontSize=8.5, textColor=YELLOW,
                                 leading=12, leftIndent=8*mm, spaceAfter=3*mm, spaceBefore=3*mm)
    s['code'] = ParagraphStyle('Code', fontName='Courier', fontSize=7.5, textColor=TEXT,
                                leading=10, leftIndent=4*mm, rightIndent=4*mm, spaceAfter=2*mm,
                                backColor=TABLE_ALT_BG)
    s['toc'] = ParagraphStyle('TOC', fontName='Courier', fontSize=10, textColor=TEXT,
                               leading=16, spaceAfter=1*mm)
    s['caption'] = ParagraphStyle('Caption', fontName='Helvetica-Oblique', fontSize=8, textColor=DIM,
                                   spaceAfter=4*mm, spaceBefore=1*mm, alignment=TA_CENTER)
    return s

STYLES = make_styles()

# ── Page drawing callbacks ──
def draw_bg(canvas, doc):
    """Draw dark background on every page."""
    canvas.saveState()
    canvas.setFillColor(VOID)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()

def draw_cover(canvas, doc):
    """Draw cover page with image and title."""
    draw_bg(canvas, doc)
    canvas.saveState()
    # Cover image
    if COVER_IMG.exists():
        try:
            img = ImageReader(str(COVER_IMG))
            iw, ih = img.getSize()
            scale = min(PAGE_W / iw, PAGE_H / ih)
            dw, dh = iw * scale, ih * scale
            x = (PAGE_W - dw) / 2
            y = (PAGE_H - dh) / 2
            canvas.drawImage(str(COVER_IMG), x, y, dw, dh, preserveAspectRatio=True)
        except Exception:
            pass
    # Semi-transparent overlay at bottom
    canvas.setFillColor(HexColor('#0A0A0F'))
    canvas.setFillAlpha(0.75)
    canvas.rect(0, 0, PAGE_W, 120*mm, fill=1, stroke=0)
    canvas.setFillAlpha(1.0)
    # Title text
    canvas.setFont('Courier', 26)
    canvas.setFillColor(YELLOW)
    canvas.drawCentredString(PAGE_W/2, 85*mm, "STATE OF THE FRONTIER STACK")
    canvas.setFont('Courier', 20)
    canvas.drawCentredString(PAGE_W/2, 72*mm, "1Q 2026")
    canvas.setFont('Helvetica', 11)
    canvas.setFillColor(TEXT)
    canvas.drawCentredString(PAGE_W/2, 58*mm, "Robotnik Quarterly Intelligence - Inaugural Report")
    canvas.setFont('Courier', 9)
    canvas.setFillColor(DIM)
    canvas.drawCentredString(PAGE_W/2, 15*mm, "robotnik.io")
    canvas.restoreState()

def draw_normal(canvas, doc):
    """Draw dark bg + header/footer on content pages."""
    draw_bg(canvas, doc)
    canvas.saveState()
    # Header
    canvas.setFont('Courier', 7)
    canvas.setFillColor(DIM)
    canvas.drawString(20*mm, PAGE_H - 15*mm, "STATE OF THE FRONTIER STACK - 1Q 2026")
    canvas.drawRightString(PAGE_W - 20*mm, PAGE_H - 15*mm, str(doc.page))
    # Footer
    canvas.drawCentredString(PAGE_W/2, 10*mm, "robotnik.io")
    # Header line
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, PAGE_H - 17*mm, PAGE_W - 20*mm, PAGE_H - 17*mm)
    canvas.restoreState()

# ── Custom flowables ──
class QuoteBlock(Flowable):
    """Robotnik pull quote with yellow left border."""
    def __init__(self, text, width):
        Flowable.__init__(self)
        self.text = text
        self.max_width = width
        self._p = Paragraph(text, STYLES['quote'])
        self._p.wrap(width - 12*mm, 9999)
        self.height = self._p.height + 6*mm

    def wrap(self, aw, ah):
        self._p.wrap(aw - 12*mm, ah)
        self.height = self._p.height + 6*mm
        self.width = aw
        return (aw, self.height)

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(QUOTE_BG)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(YELLOW)
        c.rect(0, 0, 1.5*mm, self.height, fill=1, stroke=0)
        c.restoreState()
        self._p.drawOn(self.canv, 5*mm, 3*mm)

# ── Markdown parser ──
def escape_xml(text):
    """Escape XML special chars but preserve our tags."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def md_inline(text):
    """Convert markdown inline formatting to ReportLab XML."""
    # Escape first
    text = escape_xml(text)
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    # Italic *text* (not at start of line for pull quotes)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    # Inline code `text`
    text = re.sub(r'`([^`]+)`', r'<font face="Courier" size="8">\1</font>', text)
    # Links [text](url) → just text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text

def parse_table(lines):
    """Parse markdown table lines into data."""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip('|').split('|')]
        # Skip separator rows
        if all(re.match(r'^[-:]+$', c) for c in cells):
            continue
        rows.append(cells)
    return rows

def build_table(rows, avail_width):
    """Build a ReportLab Table from parsed rows."""
    if not rows: return None
    ncols = max(len(r) for r in rows)
    # Pad rows
    for r in rows:
        while len(r) < ncols:
            r.append('')

    # Convert to Paragraphs
    cell_style = ParagraphStyle('Cell', fontName='Courier', fontSize=7.5, textColor=TEXT, leading=10)
    hdr_style = ParagraphStyle('Hdr', fontName='Courier-Bold', fontSize=7.5, textColor=YELLOW, leading=10)

    data = []
    for i, row in enumerate(rows):
        style = hdr_style if i == 0 else cell_style
        data.append([Paragraph(md_inline(c), style) for c in row])

    col_width = avail_width / ncols
    t = Table(data, colWidths=[col_width]*ncols)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HDR_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    # Alternating row colours
    for i in range(1, len(data)):
        bg = TABLE_ALT_BG if i % 2 == 0 else VOID
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_cmds))
    return t

def parse_markdown(md_text, avail_width):
    """Parse markdown into ReportLab flowables."""
    story = []
    lines = md_text.split('\n')
    i = 0
    in_code = False
    code_lines = []
    table_lines = []
    first_h1 = True

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                # End code block
                code_text = '<br/>'.join(escape_xml(l) for l in code_lines)
                story.append(Paragraph(code_text, STYLES['code']))
                story.append(Spacer(1, 2*mm))
                code_lines = []
                in_code = False
            else:
                # Flush any pending table
                if table_lines:
                    rows = parse_table(table_lines)
                    t = build_table(rows, avail_width)
                    if t: story.append(t)
                    story.append(Spacer(1, 2*mm))
                    table_lines = []
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # Table rows
        if line.strip().startswith('|') and '|' in line.strip()[1:]:
            table_lines.append(line)
            i += 1
            continue
        else:
            # Flush pending table
            if table_lines:
                rows = parse_table(table_lines)
                t = build_table(rows, avail_width)
                if t: story.append(t)
                story.append(Spacer(1, 2*mm))
                table_lines = []

        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped == '---' or stripped == '***':
            story.append(HRFlowable(width='100%', color=BORDER, thickness=0.5, spaceBefore=3*mm, spaceAfter=3*mm))
            i += 1
            continue

        # Chart placeholders
        chart_match = re.search(r'\*?\[CHART:\s*(\S+)\]\*?', stripped)
        if chart_match:
            chart_file = chart_match.group(1)
            chart_path = CHARTS_DIR / chart_file
            if chart_path.exists():
                img = Image(str(chart_path), width=avail_width, height=avail_width*0.5)
                img.hAlign = 'CENTER'
                story.append(Spacer(1, 3*mm))
                story.append(img)
                story.append(Paragraph(chart_file.replace('.png','').replace('_',' ').title(), STYLES['caption']))
            else:
                story.append(Paragraph(f'[Chart: {chart_file} - to be inserted]', STYLES['caption']))
            i += 1
            continue

        # Headings
        if stripped.startswith('# ') and not stripped.startswith('## '):
            if not first_h1:
                story.append(PageBreak())
            first_h1 = False
            text = md_inline(stripped[2:])
            story.append(Paragraph(text.upper(), STYLES['h1']))
            story.append(HRFlowable(width='100%', color=YELLOW, thickness=1, spaceAfter=4*mm))
            i += 1
            continue

        if stripped.startswith('### '):
            text = md_inline(stripped[4:])
            story.append(Paragraph(text, STYLES['h3']))
            i += 1
            continue

        if stripped.startswith('## '):
            text = md_inline(stripped[3:])
            story.append(Paragraph(text, STYLES['h2']))
            i += 1
            continue

        # Pull quotes (Robotnik voice)
        if stripped.startswith('>'):
            quote_text = md_inline(stripped.lstrip('> '))
            story.append(QuoteBlock(quote_text, avail_width))
            i += 1
            continue

        # Bullet points
        if stripped.startswith('- ') or stripped.startswith('* '):
            bullet_text = md_inline(stripped[2:])
            bullet_style = ParagraphStyle('Bullet', parent=STYLES['body'], leftIndent=6*mm,
                                           bulletIndent=2*mm, bulletFontName='Helvetica',
                                           bulletFontSize=9, bulletColor=YELLOW)
            story.append(Paragraph(bullet_text, bullet_style, bulletText='\u2022'))
            i += 1
            continue

        # Numbered list
        num_match = re.match(r'^(\d+)\.\s+(.+)', stripped)
        if num_match:
            num = num_match.group(1)
            text = md_inline(num_match.group(2))
            num_style = ParagraphStyle('Num', parent=STYLES['body'], leftIndent=6*mm, bulletIndent=0)
            story.append(Paragraph(text, num_style, bulletText=f'{num}.'))
            i += 1
            continue

        # Regular paragraph
        text = md_inline(stripped)
        if text.strip():
            story.append(Paragraph(text, STYLES['body']))

        i += 1

    # Flush remaining table
    if table_lines:
        rows = parse_table(table_lines)
        t = build_table(rows, avail_width)
        if t: story.append(t)

    return story


def main():
    print("=" * 60)
    print("ROBOTNIK REPORT PDF GENERATOR")
    print("=" * 60)

    # Read markdown
    md_text = REPORT_MD.read_text(encoding='utf-8')
    print(f"Markdown: {len(md_text)} chars, {md_text.count(chr(10))} lines")

    # Setup document
    margin_lr = 20*mm
    margin_tb = 25*mm
    frame_w = PAGE_W - 2*margin_lr
    frame_h = PAGE_H - 2*margin_tb

    # Content frame (smaller top margin for header)
    content_frame = Frame(margin_lr, margin_tb, frame_w, PAGE_H - margin_tb - 20*mm,
                          id='content')

    # Cover frame — small, just to hold a spacer
    cover_frame = Frame(margin_lr, margin_tb, frame_w, 50*mm, id='coverframe')

    cover_template = PageTemplate(id='cover', frames=[cover_frame], onPage=draw_cover)
    normal_template = PageTemplate(id='normal', frames=[content_frame], onPage=draw_normal)

    doc = BaseDocTemplate(str(OUTPUT_PDF), pagesize=A4,
                          leftMargin=margin_lr, rightMargin=margin_lr,
                          topMargin=margin_tb, bottomMargin=margin_tb,
                          title="State of the Frontier Stack - 1Q 2026",
                          author="Robotnik")

    doc.addPageTemplates([cover_template, normal_template])

    # Build story
    from reportlab.platypus.doctemplate import NextPageTemplate
    story = []

    # Cover page
    story.append(Spacer(1, 10*mm))
    story.append(NextPageTemplate('normal'))
    story.append(PageBreak())

    # Parse markdown content
    print("Parsing markdown...")
    content = parse_markdown(md_text, frame_w)
    story.extend(content)

    # Build PDF
    print(f"Building PDF ({len(story)} flowables)...")
    doc.build(story)

    size = os.path.getsize(OUTPUT_PDF)
    print(f"\nOutput: {OUTPUT_PDF} ({size/1024/1024:.1f} MB)")
    print("=" * 60)


if __name__ == '__main__':
    main()
