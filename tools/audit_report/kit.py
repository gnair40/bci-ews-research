"""Document builder helpers for the ISEF project audit report."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, KeepTogether,
                                HRFlowable, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------- palette
INK        = colors.HexColor('#12161c')
NAVY       = colors.HexColor('#17314f')
SLATE      = colors.HexColor('#3d5673')
RULE       = colors.HexColor('#c3ccd6')
FAINT      = colors.HexColor('#eef1f5')
BAND       = colors.HexColor('#f7f9fb')
HEADBG     = colors.HexColor('#17314f')
ACCENT     = colors.HexColor('#8a5a12')
GOOD       = colors.HexColor('#1d5f36')
BAD        = colors.HexColor('#8c1f24')
GREY       = colors.HexColor('#5b6672')

PAGE_W, PAGE_H = letter
LM, RM, TM, BM = 0.82*inch, 0.82*inch, 0.78*inch, 0.72*inch
AVAIL = PAGE_W - LM - RM

# ---------------------------------------------------------------- styles
def _s(name, **kw):
    base = dict(fontName='Helvetica', fontSize=9.3, leading=13.2, textColor=INK,
                spaceBefore=0, spaceAfter=0, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
 'title'   : _s('title', fontName='Helvetica-Bold', fontSize=25, leading=29,
                textColor=NAVY, alignment=TA_LEFT, spaceAfter=8),
 'subtitle': _s('subtitle', fontSize=12.5, leading=17, textColor=SLATE, spaceAfter=4),
 'tp_meta' : _s('tp_meta', fontSize=9, leading=14, textColor=GREY),
 'h1'      : _s('h1', fontName='Helvetica-Bold', fontSize=16, leading=19.5,
                textColor=NAVY, spaceBefore=0, spaceAfter=3),
 'h1num'   : _s('h1num', fontName='Helvetica-Bold', fontSize=9, leading=11,
                textColor=ACCENT, spaceAfter=2),
 'h2'      : _s('h2', fontName='Helvetica-Bold', fontSize=11.6, leading=14.5,
                textColor=NAVY, spaceBefore=13, spaceAfter=4),
 'h3'      : _s('h3', fontName='Helvetica-Bold', fontSize=9.8, leading=12.5,
                textColor=SLATE, spaceBefore=10, spaceAfter=3),
 'body'    : _s('body', alignment=TA_JUSTIFY, spaceAfter=6),
 'bullet'  : _s('bullet', alignment=TA_LEFT, spaceAfter=3.5, leftIndent=13,
                bulletIndent=3),
 'note'    : _s('note', fontSize=8.4, leading=11.6, textColor=GREY, spaceAfter=5),
 'cap'     : _s('cap', fontSize=8.1, leading=11, textColor=GREY, spaceBefore=3,
                spaceAfter=9),
 'th'      : _s('th', fontName='Helvetica-Bold', fontSize=7.9, leading=9.8,
                textColor=colors.white),
 'td'      : _s('td', fontSize=7.9, leading=9.9),
 'tdb'     : _s('tdb', fontName='Helvetica-Bold', fontSize=7.9, leading=9.9),
 'tdm'     : _s('tdm', fontName='Courier', fontSize=7.4, leading=9.6),
 'callout' : _s('callout', fontSize=9.2, leading=13, spaceAfter=0),
 'h1p'     : _s('h1p', fontName='Helvetica-Bold', fontSize=16, leading=19.5,
                textColor=NAVY, spaceBefore=0, spaceAfter=3),
 'toc1'    : _s('toc1', fontName='Helvetica-Bold', fontSize=9.6, leading=15,
                textColor=NAVY),
 'toc2'    : _s('toc2', fontSize=8.8, leading=12.6, leftIndent=16, textColor=SLATE),
 'code'    : _s('code', fontName='Courier', fontSize=7.8, leading=10.4),
 'run'     : _s('run', fontName='Helvetica-Bold', fontSize=8.6, leading=11.6,
                textColor=NAVY, spaceBefore=8, spaceAfter=2),
}

# ---------------------------------------------------------------- flowables
_seq = {'h': 0}

def H1(text, number=None):
    """Top-level section: page break, rule, number kicker, title."""
    out = [PageBreak(),
           HRFlowable(width='100%', thickness=2.2, color=NAVY, spaceAfter=5)]
    if number:
        out.append(Paragraph(number.upper(), S['h1num']))
    out.append(Paragraph(text, S['h1']))
    out.append(HRFlowable(width='100%', thickness=0.5, color=RULE, spaceBefore=4,
                          spaceAfter=10))
    return out

def H2(text):
    return [CondPageBreak(1.5*inch), Paragraph(text, S['h2'])]

def H3(text):
    return [CondPageBreak(1.1*inch), Paragraph(text, S['h3'])]

def P(text, style='body'):
    return [Paragraph(text, S[style])]

def NOTE(text):
    return [Paragraph(text, S['note'])]

def UL(items, style='bullet'):
    return [Paragraph(t, S[style], bulletText='•') for t in items]

def OL(items):
    return [Paragraph(t, S['bullet'], bulletText='%d.' % (i+1))
            for i, t in enumerate(items)]

def CAP(text):
    return [Paragraph(text, S['cap'])]

def RUNIN(text):
    return [Paragraph(text, S['run'])]

def CALLOUT(text, tone='neutral', label=None):
    """Boxed emphasis block."""
    edge = {'neutral': NAVY, 'warn': BAD, 'good': GOOD, 'flag': ACCENT}[tone]
    fill = {'neutral': FAINT, 'warn': colors.HexColor('#fbf0f0'),
            'good': colors.HexColor('#eef6f0'),
            'flag': colors.HexColor('#fdf6e9')}[tone]
    inner = []
    if label:
        inner.append(Paragraph('<font color="%s"><b>%s</b></font>'
                               % ('#' + edge.hexval()[2:], label.upper()),
                               _s('cl', fontSize=7.6, leading=10, spaceAfter=3)))
    inner.append(Paragraph(text, S['callout']))
    t = Table([[inner]], colWidths=[AVAIL])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), fill),
        ('LINEBEFORE', (0,0), (0,-1), 2.6, edge),
        ('BOX', (0,0), (-1,-1), 0.4, RULE),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    return [t, Spacer(1, 9)]

def _cell(v, sty):
    if isinstance(v, Paragraph):
        return v
    return Paragraph(str(v), S[sty])

def TBL(header, rows, widths, align=None, mono=None, caption=None,
        fs=None, repeat=True):
    """widths: fractions summing to ~1.0 of the available width."""
    if fs:
        for k in ('th', 'td', 'tdb', 'tdm'):
            S[k].fontSize = fs
            S[k].leading = fs * 1.26
    cw = [w * AVAIL for w in widths]
    mono = mono or []
    data = [[_cell(h, 'th') for h in header]] if header else []
    for r in rows:
        data.append([_cell(v, 'tdm' if i in mono else 'td')
                     for i, v in enumerate(r)])
    t = Table(data, colWidths=cw, repeatRows=1 if (header and repeat) else 0)
    st = [
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 3.4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.6),
        ('LINEBELOW', (0,0), (-1,-1), 0.3, RULE),
        ('BOX', (0,0), (-1,-1), 0.5, SLATE),
    ]
    if header:
        st += [('BACKGROUND', (0,0), (-1,0), HEADBG),
               ('LINEBELOW', (0,0), (-1,0), 0.8, NAVY),
               ('TOPPADDING', (0,0), (-1,0), 4.5),
               ('BOTTOMPADDING', (0,0), (-1,0), 4.5)]
        body0 = 1
    else:
        body0 = 0
    for i in range(body0, len(data)):
        if (i - body0) % 2 == 1:
            st.append(('BACKGROUND', (0,i), (-1,i), BAND))
    if align:
        for col, a in align.items():
            st.append(('ALIGN', (col,0), (col,-1), a))
    t.setStyle(TableStyle(st))
    if fs:
        for k, d in (('th',7.9), ('td',7.9), ('tdb',7.9), ('tdm',7.4)):
            S[k].fontSize = d
            S[k].leading = d * 1.26
    out = [t]
    if caption:
        out.append(Paragraph(caption, S['cap']))
    else:
        out.append(Spacer(1, 9))
    return out

def B(t):
    return '<b>%s</b>' % t

def M(t):
    return '<font name="Courier" size="8">%s</font>' % t

def SP(h=8):
    return [Spacer(1, h)]

def RULE_():
    return [HRFlowable(width='100%', thickness=0.5, color=RULE,
                       spaceBefore=7, spaceAfter=7)]

# ---------------------------------------------------------------- template
class AuditDoc(BaseDocTemplate):
    def __init__(self, path, **kw):
        BaseDocTemplate.__init__(self, path, pagesize=letter,
                                 leftMargin=LM, rightMargin=RM,
                                 topMargin=TM, bottomMargin=BM,
                                 title='Technical and Scientific Audit — '
                                       'BCI Decoder-Health Monitoring Project',
                                 author='Project audit', **kw)
        frame = Frame(LM, BM, AVAIL, PAGE_H - TM - BM, id='body',
                      leftPadding=0, rightPadding=0, topPadding=0,
                      bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id='plain', frames=[frame], onPage=self._blank),
            PageTemplate(id='main', frames=[frame], onPageEnd=self._chrome),
        ])
        self._section = ''

    def _blank(self, canv, doc):
        pass

    def _chrome(self, canv, doc):
        canv.saveState()
        y = PAGE_H - TM + 0.30*inch
        canv.setStrokeColor(RULE); canv.setLineWidth(0.5)
        canv.line(LM, y - 4, PAGE_W - RM, y - 4)
        canv.setFont('Helvetica', 7.2); canv.setFillColor(GREY)
        canv.drawString(LM, y, 'iBCI decoder-health monitoring '
                               '— technical & scientific audit')
        canv.drawRightString(PAGE_W - RM, y, self._section[:74])
        yb = BM - 0.30*inch
        canv.setStrokeColor(RULE)
        canv.line(LM, yb + 10, PAGE_W - RM, yb + 10)
        canv.setFont('Helvetica', 7.2); canv.setFillColor(GREY)
        canv.drawString(LM, yb, 'Repository gnair40/bci-ews-research '
                                '· HEAD 07cb392 · audited 6 September 2026')
        canv.setFont('Helvetica-Bold', 8.4); canv.setFillColor(NAVY)
        canv.drawRightString(PAGE_W - RM, yb, str(doc.page))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            st = flowable.style.name
            txt = flowable.getPlainText()
            if st == 'h1':
                self._section = txt
                self.notify('TOCEntry', (0, txt, self.page))
            elif st == 'h2':
                self.notify('TOCEntry', (1, txt, self.page))

def build(path, story):
    doc = AuditDoc(path)
    doc.multiBuild(story)
    return doc
