#!/usr/bin/env python3
"""
build_pptx.py -- export every poster draft to an editable PowerPoint file.

    python3 poster/pptx/build_pptx.py            # all five drafts
    python3 poster/pptx/build_pptx.py draft5     # one draft

Writes poster/export/trifold-draftN-<size>.pptx. Each file is ONE slide the size of
the whole board, with the three panels side by side:

    Drafts 1 to 3    48 x 36 inches      Drafts 4 and 5    48 x 48 inches

HOW IT WORKS
------------
1. render_check/preview.py turns each published artboard into a plain web page.
2. pptx/extract.js opens that page in a browser and lists every piece of text, box,
   line and chart element with the position the browser gave it.
3. This file writes that list as PowerPoint objects:
       paragraphs   -> text boxes whose text can be edited and re-wraps
       labels       -> small text boxes, one per line, at their exact place
       boxes, rules -> rectangles and lines
       charts       -> rectangles, circles, lines and freeforms, grouped per chart
       wiring       -> pictures (they are pictures on the poster too)

So nothing is redrawn or retyped: the PowerPoint file is the published board, read
back from the browser. What does NOT carry over exactly is listed in poster/README.md.

NEEDS
-----
Python with python-pptx, and Node with Playwright. The fonts (IBM Plex Sans, IBM Plex
Mono, Source Serif 4) must be installed on whatever computer opens the file, or
PowerPoint substitutes its own and the text shifts.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
POSTER = HERE.parent
RENDER = POSTER / "render_check" / "out"
WORK = HERE / "_work"
EXPORT = POSTER / "export"

PX = 9525                                    # EMU per CSS pixel at 96 px per inch
PANELS = [(0, 1152), (1152, 2304), (3456, 1152)]          # left, centre, right: offset, width
DRAFTS = {
    "draft1": ("Draft 1", 3456, ["D1-Left", "D1-Centre", "D1-Right"]),
    "draft2": ("Draft 2", 3456, ["Left", "Main", "Right"]),
    "draft3": ("Draft 3", 3456, ["D3-Left", "D3-Centre", "D3-Right"]),
    "draft4": ("Draft 4", 4608, ["D4-Left", "D4-Centre", "D4-Right"]),
    "draft5": ("Draft 5", 4608, ["D5-Left", "D5-Centre", "D5-Right"]),
}
FAMILIES = {"IBM Plex Sans", "IBM Plex Mono", "Source Serif 4"}
ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}
DASH = {"dashed": MSO_LINE.DASH, "dash": MSO_LINE.DASH, "sysDash": MSO_LINE.SQUARE_DOT,
        "dotted": MSO_LINE.ROUND_DOT, "sysDot": MSO_LINE.ROUND_DOT}
NOTES = ("Exported from the poster canvas by poster/pptx/build_pptx.py. Text is editable; "
         "each chart is one group (ungroup it to edit its parts). Fonts: IBM Plex Sans, "
         "IBM Plex Mono and Source Serif 4, free from Google Fonts. Without them PowerPoint "
         "substitutes other fonts and the text will shift.")


def E(v: float) -> int:
    return int(round(v * PX))


def face(family: str, weight: int) -> tuple[str, bool]:
    """PowerPoint has only 'bold' or not, so the in-between weights go by family name."""
    if family not in FAMILIES:
        return family, weight >= 600
    if weight >= 650:
        return family, True
    if weight >= 550:
        return family + " SemiBold", False
    if weight >= 450:
        return family + " Medium", False
    return family, False


def set_alpha(holder, a: float) -> None:
    if a >= 0.995:
        return
    clr = holder.find(".//" + qn("a:srgbClr"))
    if clr is not None:
        etree.SubElement(clr, qn("a:alpha")).set("val", str(int(round(a * 100000))))


def paint(shp, fill, patt, line) -> None:
    """Fill and outline. The theme's own shape style is removed first, so nothing is inherited."""
    style = shp._element.find(qn("p:style"))
    if style is not None:
        shp._element.remove(style)
    if patt:
        shp.fill.background()
        sp = shp._element.spPr
        no = sp.find(qn("a:noFill"))
        pf = etree.Element(qn("a:pattFill"))
        pf.set("prst", "ltUpDiag")
        etree.SubElement(etree.SubElement(pf, qn("a:fgClr")), qn("a:srgbClr")).set("val", patt["fg"])
        etree.SubElement(etree.SubElement(pf, qn("a:bgClr")), qn("a:srgbClr")).set("val", patt["bg"])
        no.addprevious(pf)
        sp.remove(no)
    elif fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(fill["hex"])
        set_alpha(shp._element.spPr.find(qn("a:solidFill")), fill.get("a", 1))
    else:
        shp.fill.background()
    stroke(shp, line)


def stroke(shp, line) -> None:
    style = shp._element.find(qn("p:style"))
    if style is not None:
        shp._element.remove(style)
    if not line:
        shp.line.fill.background()
        return
    shp.line.color.rgb = RGBColor.from_string(line["c"]["hex"])
    shp.line.width = Emu(max(E(line["w"]), 3175))
    if DASH.get(line.get("dash")):
        shp.line.dash_style = DASH[line["dash"]]
    ln = shp.line._get_or_add_ln()
    set_alpha(ln, line["c"].get("a", 1))
    if line.get("arrow"):
        etree.SubElement(ln, qn("a:tailEnd")).set("type", "triangle")


def style_run(run, r) -> None:
    name, bold = face(r["f"], r["wt"])
    f = run.font
    f.name = name
    f.size = Pt(round(r["s"] * 0.75 * r.get("fit", 1), 2))
    if bold:
        f.bold = True
    if r.get("it"):
        f.italic = True
    f.color.rgb = RGBColor.from_string(r["c"])
    rpr = run._r.get_or_add_rPr()
    if r.get("ls"):
        rpr.set("spc", str(int(round(r["ls"] * 75))))
    if r.get("hl"):                          # highlighter, as a property of the words themselves
        hl = etree.Element(qn("a:highlight"))
        etree.SubElement(hl, qn("a:srgbClr")).set("val", r["hl"])
        rpr.find(qn("a:latin")).addprevious(hl)


def text_box(cont, x, y, w, h, wrap: bool, anchor):
    tb = cont.add_textbox(E(x), E(y), max(E(w), PX), max(E(h), PX))
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    return tb, tf


def add_flow(cont, it, ox: float) -> None:
    """A paragraph block. More than one line: PowerPoint wraps it, with a little slack."""
    x, y, w, h, al = it["x"] + ox, it["y"], it["w"], it["h"], it["al"]
    one = it["lines"] <= 1
    if not one:
        d = min(12.0, max(4.0, w * 0.012))
        if al == "center":
            x, w = x - d / 2, w + d
        elif al == "right":
            x, w = x - d, w + d
        else:
            w += d
    tb, tf = text_box(cont, x, y, w, h, not one, MSO_ANCHOR.TOP)
    for i, runs in enumerate(it["paras"]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ALIGN[al]
        lh = max([r.get("lh", 0) for r in runs] + [0]) or it.get("lh", 0)
        if lh:
            p.line_spacing = Pt(round(lh * 0.75, 2))
        for r in runs:
            run = p.add_run()
            run.text = r["t"]
            style_run(run, r)


def add_frag(cont, it, ox: float) -> None:
    """One line of text at an exact place: a label, a number on a chart, a table heading."""
    tb, tf = text_box(cont, it["x"] + ox, it["y"], it["w"], it["h"], False, MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = ALIGN[it["al"]]
    run = p.add_run()
    run.text = it["t"]
    style_run(run, it)
    if it.get("rot"):
        tb.rotation = it["rot"]


def add_item(cont, it, ox: float, images) -> None:
    k = it["k"]
    if k == "flow":
        add_flow(cont, it, ox)
    elif k == "frag":
        add_frag(cont, it, ox)
    elif k in ("rect", "round", "ellipse"):
        w, h = max(it["w"], 0.5), max(it["h"], 0.5)
        kind = {"rect": MSO_SHAPE.RECTANGLE, "round": MSO_SHAPE.ROUNDED_RECTANGLE,
                "ellipse": MSO_SHAPE.OVAL}[k]
        shp = cont.add_shape(kind, E(it["x"] + ox), E(it["y"]), max(E(w), PX), max(E(h), PX))
        if k == "round":
            shp.adjustments[0] = min(0.5, it["rad"] / min(w, h))
        paint(shp, it.get("fill"), it.get("patt"), it.get("line"))
    elif k == "line":
        c = cont.add_connector(MSO_CONNECTOR.STRAIGHT, E(it["x1"] + ox), E(it["y1"]),
                               E(it["x2"] + ox), E(it["y2"]))
        ln = dict(it["line"])
        if ln.get("arrow"):                  # the drawn line stops short of its arrowhead's tip
            dx, dy = it["x2"] - it["x1"], it["y2"] - it["y1"]
            n = (dx * dx + dy * dy) ** 0.5 or 1.0
            c.end_x = E(it["x2"] + ox + dx / n * 2 * ln["w"])
            c.end_y = E(it["y2"] + dy / n * 2 * ln["w"])
        stroke(c, ln)
    elif k == "poly":
        pts = [(E(px + ox), E(py)) for px, py in it["pts"]]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        if len(pts) == 2 or max(xs) - min(xs) < PX or max(ys) - min(ys) < PX:
            if it.get("line"):               # a straight run: a line, which PowerPoint handles better
                c = cont.add_connector(MSO_CONNECTOR.STRAIGHT, *pts[0], *pts[-1])
                ln = dict(it["line"])
                if ln.get("arrow"):
                    dx, dy = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
                    n = (dx * dx + dy * dy) ** 0.5 or 1.0
                    c.end_x = int(pts[-1][0] + dx / n * 2 * E(ln["w"]))
                    c.end_y = int(pts[-1][1] + dy / n * 2 * E(ln["w"]))
                stroke(c, ln)
            return
        fb = cont.build_freeform(pts[0][0], pts[0][1], scale=1.0)
        fb.add_line_segments(pts[1:], close=bool(it.get("closed")))
        shp = fb.convert_to_shape()
        line = dict(it["line"]) if it.get("line") else None
        if line:
            line["arrow"] = False
        paint(shp, it.get("fill"), it.get("patt"), line)
    elif k == "img":
        pic = cont.add_picture(images[it["id"]]["png"], E(it["x"] + ox), E(it["y"]),
                               E(it["w"]), E(it["h"]))
        if it.get("alt"):
            pic._element.nvPicPr.cNvPr.set("descr", it["alt"])


def letters(text: str) -> Counter:
    """Every letter, digit and symbol, counted; spaces dropped (the board's own text has
    none between neighbouring labels, so words cannot be compared directly)."""
    return Counter(re.sub(r"\s+", "", text.lower()))


def all_text(shapes) -> str:
    out = []
    for shp in shapes:
        if shp.shape_type == 6:                       # a group: look inside it
            out.append(all_text(shp.shapes))
        elif shp.has_text_frame:
            out.append(shp.text_frame.text)
    return " ".join(out)


def check_text(out: Path, panels: list[dict]) -> int:
    """Open the file that was just written and count its characters against the board's.

    Every letter, digit and symbol on the three panels must be in the PowerPoint file
    the same number of times, and nothing extra. Capitals are ignored, because labels
    the board prints in capitals are stored in lower case. This is what shows no text
    was lost on the way."""
    want = Counter()
    for data in panels:
        want += letters(data["text"])
    have = letters(all_text(Presentation(out).slides[0].shapes))
    if want != have:
        missing, extra = want - have, have - want
        raise SystemExit(f"{out.name}: the text does not match the board.\n"
                         f"  missing: {dict(missing.most_common(12))}\n"
                         f"  extra:   {dict(extra.most_common(12))}")
    return sum(want.values())


def extract(key: str) -> list[dict]:
    _, height, names = DRAFTS[key]
    WORK.mkdir(exist_ok=True)
    out = []
    for name, (_, width) in zip(names, PANELS):
        js = WORK / f"{name}.json"
        subprocess.run(["node", str(HERE / "extract.js"), str(RENDER), name, str(width),
                        str(height), str(js), str(WORK / "img")], check=True)
        out.append(json.loads(js.read_text()))
    return out


def build(key: str) -> Path:
    title, height, names = DRAFTS[key]
    panels = extract(key)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(48), Emu(height * PX)
    prs.core_properties.title = f"Seeing Failure Before It Shows: trifold poster, {title}"
    prs.core_properties.author = "Gayathri Nair"
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    shapes = slide.shapes
    shapes.turbo_add_enabled = True
    count = {}
    for (ox, _), data, name in zip(PANELS, panels, names):
        groups = {}
        for it in data["items"]:
            g = it.get("g")
            if g is None:
                cont = shapes
            else:
                if g not in groups:
                    grp = shapes.add_group_shape()
                    label = data["groups"].get(str(g), "") or "drawing"
                    grp.name = f"{name} figure {g}: {label}"[:120]
                    groups[g] = grp
                cont = groups[g].shapes
            add_item(cont, it, ox, data["images"])
            count[it["k"]] = count.get(it["k"], 0) + 1
    # every object gets its own number; groups and the slide numbered them separately
    for i, el in enumerate(slide.shapes._spTree.iter(qn("p:cNvPr")), start=2):
        el.set("id", str(i))
    slide.notes_slide.notes_text_frame.text = NOTES
    EXPORT.mkdir(exist_ok=True)
    size = f"48x{height // 96}in"
    out = EXPORT / f"trifold-{key}-{size}.pptx"
    prs.save(out)
    n = check_text(out, panels)
    print(f"wrote {out.relative_to(POSTER.parent)}  {size}  "
          + ", ".join(f"{v} {k}" for k, v in sorted(count.items()))
          + f"  | all {n:,} characters match the board")
    return out


def main() -> int:
    keys = sys.argv[1:] or list(DRAFTS)
    subprocess.run([sys.executable, str(POSTER / "render_check" / "preview.py")], check=True)
    for key in keys:
        build(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
