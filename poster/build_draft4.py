#!/usr/bin/env python3
"""
build_draft4.py -- Draft 4 of the trifold: 48 inches wide by 48 inches tall.

    python3 poster/build_poster_data.py     # recompute and check every number
    python3 poster/build_draft4.py          # write D4-Left, D4-Centre, D4-Right

THE BOARD AND THE READING ORDER
-------------------------------
Left 12 in, centre 24 in, right 12 in, all 48 in tall. The centre is laid out as
two 12 inch columns, so the board reads as four columns from left to right:

    1  left panel      the problem, the question, and the system
    2  centre, left    how it was validated: computationally, then physically,
                       each with the real material that supports it
    3  centre, right   results, data and analysis
    4  right panel     discussion, interpretation, limits, what comes next

Columns 1 and 2 are the first half: what the system is and how it was tested.
Columns 3 and 4 are the second half: what was found and what it means.

TWO TYPE SIZES, AND ONLY TWO
----------------------------
The researcher set them. Running text and headings are never under 24 pt
(BODY, 32 px). Captions, axis labels, table cells and labels inside figures may
go down to 20 pt (CAP, 27 px) and no further. The render check fails on anything
under 20 pt and counts the pieces of text that sit between 20 and 24 pt.

WHAT CAME BACK
--------------
The taller board has room for material that Drafts 2 and 3 had to leave off:
the monitor's four components, the definition of lead time on a real episode,
the acceptance gates, the experiment list, the variables, the secondary
hypothesis and the side-by-side account of what each validation can and cannot
establish.

NOTHING HERE IS A PHYSICAL RESULT
---------------------------------
No apparatus exists. Photographs are grey placeholders and the bench results
are blanks.
"""
from __future__ import annotations

import json
from pathlib import Path

import charts as C

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE / "canvas" / "project"
D = json.loads((HERE / "poster_data.json").read_text())
S = D["scalars"]
ASSETS = json.loads((HERE / "assets.json").read_text())

BODY, CAP = 32, 27                    # px: 24 pt and 20 pt at 96 px/in
C.SCALE = CAP / C.MIN_UNITS           # 17 source units print at 27 px

INK, INK2, INK3 = C.INK, C.INK2, C.INK3
RULE, GRID = C.RULE, C.GRID
BLUE, BLUE_T, BLUE_M = C.BLUE, C.BLUE_T, C.BLUE_M
ORG, ORG_T, ORG_M = C.ORG, C.ORG_T, C.ORG_M
WINE, WINE_T = C.WINE, "#F7E6EB"
WASH = "#F1F4F6"
SERIF = "'Source Serif 4', Georgia, 'Times New Roman', serif"
SANS = "'IBM Plex Sans', Arial, sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600"
         "&family=IBM+Plex+Sans:wght@400;500;600;700"
         "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap")

PH, PW_SIDE, PW_MAIN = 4608, 1152, 2304          # 48 in tall
SIDE_U = round(1040 / C.SCALE)                   # chart width, in source units, for a side panel
COL = 1068                                       # one centre column, px
COL_U = round(COL / C.SCALE)

REFS = [
    "Pun et al., Communications Biology 7 (2024)",
    "Wilson et al., Nature Biomedical Engineering (2025)",
    "Armour et al., Am. J. Public Health 106 (2016)",
    "Sendelbach &amp; Funk, AACN Adv. Crit. Care 24 (2013)",
    "Ahrens, Smoke Alarms in U.S. Home Fires, NFPA (2015)",
    "Karpowicz et al., Nature Communications 16 (2025)",
]


def minus(x: str) -> str:
    return x.replace("-", "−")


def num(v: float, nd: int = 2) -> str:
    return minus(f"{v:.{nd}f}")


# ---------------------------------------------------------------------------
# components
# ---------------------------------------------------------------------------
def page(title: str, w: int, h: int, body: str, pad: int, gap: int) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="{FONTS.replace('&', '&amp;')}">
<style>
body{{margin:0}}
</style>
</helmet>
<div style="width: {w}px; height: {h}px; box-sizing: border-box; padding: {pad}px; background: #FFFFFF; color: {INK}; font-family: {SANS}; display: flex; flex-direction: column; gap: {gap}px; overflow: hidden">
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""


def label(text: str, color: str = INK, extra: str = "") -> str:
    return (f'<div style="border-top: 4px solid {color}; padding-top: 10px; display: flex; '
            f'align-items: center; justify-content: space-between; gap: 16px">'
            f'<span style="font-family: {MONO}; font-size: {BODY}px; line-height: 40px; '
            f'font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; '
            f'color: {color}">{text}</span>{extra}</div>')


def chip(text: str, kind: str) -> str:
    st = {"done": f"background: {BLUE}; color: #FFFFFF; border: 3px solid {BLUE}",
          "todo": f"background: #FFFFFF; color: {ORG}; border: 3px dashed {ORG}"}[kind]
    return (f'<span style="{st}; font-family: {MONO}; font-size: {CAP}px; line-height: 34px; '
            f'font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; '
            f'padding: 1px 12px; border-radius: 4px; white-space: nowrap">{text}</span>')


def head(text: str, size: int = 46) -> str:
    return (f'<h2 style="margin: 0; font-family: {SERIF}; font-size: {size}px; '
            f'line-height: {round(size * 1.14)}px; font-weight: 600; color: {INK}; '
            f'text-wrap: balance">{text}</h2>')


def finding(text: str) -> str:
    return (f'<h3 style="margin: 0; font-family: {SERIF}; font-size: 40px; line-height: 46px; '
            f'font-weight: 700; color: {INK}; text-wrap: balance">{text}</h3>')


def p(html: str, color: str = INK2) -> str:
    return (f'<p style="margin: 0; font-size: {BODY}px; line-height: 42px; color: {color}; '
            f'text-wrap: pretty">{html}</p>')


def cap(n: str, text: str) -> str:
    return (f'<p style="margin: 0; font-size: {CAP}px; line-height: 36px; color: {INK2}; '
            f'text-wrap: pretty"><b style="color: {INK}; font-weight: 600">Fig. {n}.</b> '
            f'{text}</p>')


def sec(*parts: str, gap: int = 12) -> str:
    return (f'<section style="display: flex; flex-direction: column; gap: {gap}px">'
            + "".join(parts) + "</section>")


def b(text: str, color: str = INK) -> str:
    return f'<b style="color: {color}; font-weight: 600">{text}</b>'


def bullets(items: list[str]) -> str:
    return (f'<ul style="margin: 0; padding-left: 34px; display: flex; flex-direction: column; '
            f'gap: 6px">'
            + "".join(f'<li style="font-size: {BODY}px; line-height: 42px; color: {INK2}; '
                      f'text-wrap: pretty">{i}</li>' for i in items) + "</ul>")


def table(heads: list[str], rows: list[list[str]], widths: list[str]) -> str:
    th = "".join(
        f'<th style="width: {w}; text-align: left; padding: 4px 10px; font-size: {CAP}px; '
        f'line-height: 34px; font-weight: 600; color: {INK}; background: {WASH}; '
        f'border-bottom: 3px solid {INK}; vertical-align: bottom">{h}</th>'
        for h, w in zip(heads, widths))
    body = "".join(
        "<tr>" + "".join(
            f'<td style="padding: 4px 10px; font-size: {CAP}px; line-height: 35px; '
            f'color: {INK2}; border-bottom: 1.5px solid {RULE}; vertical-align: top">{c}</td>'
            for c in r) + "</tr>" for r in rows)
    return (f'<table style="width: 100%; border-collapse: collapse; table-layout: fixed; '
            f'font-family: {SANS}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>')


CAMERA = (
    '<svg aria-hidden="true" width="56" height="56" viewBox="0 0 24 24" fill="none" '
    f'stroke="{INK3}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 8h3.5l1.5-2.5h8L17.5 8H21v11H3z"/><circle cx="12" cy="13.2" r="3.6"/></svg>')


def photo(what: str, h: int, kind: str = "PHOTO TO ADD") -> str:
    return (f'<div style="height: {h}px; box-sizing: border-box; border: 3px dashed {INK3}; '
            f'background: {WASH}; border-radius: 6px; display: flex; flex-direction: column; '
            f'align-items: center; justify-content: center; gap: 4px; padding: 12px; '
            f'text-align: center">{CAMERA}'
            f'<span style="font-family: {MONO}; font-size: {CAP}px; line-height: 34px; '
            f'font-weight: 600; letter-spacing: 0.08em; color: {INK2}">{kind}</span>'
            f'<span style="font-size: {CAP}px; line-height: 35px; color: {INK2}">{what}</span>'
            f'</div>')


_arrow_id = [0]


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = INK2, sw: int = 4) -> str:
    """One straight arrow from (x1,y1) to its tip (x2,y2); horizontal or vertical."""
    _arrow_id[0] += 1
    mid = f"dc-arrow-head-filled-{_arrow_id[0]}"
    hl = 2 * sw
    horiz = y1 == y2
    n = abs(x2 - x1) if horiz else abs(y2 - y1)
    if horiz:
        left, top, w, h = min(x1, x2), y1 - 4, n, 8
        d = f"M 0 4 L {n - hl} 4" if x2 > x1 else f"M {n} 4 L {hl} 4"
    else:
        left, top, w, h = x1 - 4, min(y1, y2), 8, n
        d = f"M 4 0 L 4 {n - hl}" if y2 > y1 else f"M 4 {n} L 4 {hl}"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'style="position: absolute; left: {left}px; top: {top}px; width: {w}px; '
            f'height: {h}px; overflow: visible; fill: none; stroke: {color}; '
            f'stroke-width: {sw}; stroke-linecap: round; stroke-linejoin: round">'
            f'<defs><marker id="{mid}" orient="auto" markerWidth="5" markerHeight="5" refX="2" '
            f'refY="2" overflow="visible"><path d="M0 0 L4 2 L0 4 Z" fill="{color}" '
            f'stroke="none" style="stroke: none; fill: {color}; fill: context-stroke"/>'
            f'</marker></defs><path d="{d}" marker-end="url(#{mid})"></path></svg>')


def box(x: int, y: int, w: int, h: int, html: str, look: str, color: str = INK) -> str:
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; '
            f'height: {h}px; box-sizing: border-box; padding: 6px 12px; display: flex; '
            f'align-items: center; justify-content: center; text-align: center; {look}; '
            f'border-radius: 8px"><span style="font-size: {CAP}px; line-height: 34px; '
            f'font-weight: 600; color: {color}">{html}</span></div>')


def note(x: int, y: int, w: int, text: str, align: str = "center", color: str = INK2,
         weight: int = 400) -> str:
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; '
            f'text-align: {align}; font-size: {CAP}px; line-height: 34px; color: {color}; '
            f'font-weight: {weight}">{text}</div>')


def refs_block() -> str:
    return (f'<section style="display: flex; flex-direction: column; gap: 0; margin-top: auto">'
            + label("References")
            + "".join(f'<p style="margin: 0; font-size: {CAP}px; line-height: 36px; '
                      f'color: {INK2}; white-space: nowrap; overflow: hidden">[{i}] {r}</p>'
                      for i, r in enumerate(REFS, 1))
            + "</section>")


# ===========================================================================
# COLUMN 1 (left panel) -- the problem, the question, the system
# ===========================================================================
def quadrant() -> str:
    L11 = D["lead_time"]["T11"]
    over = S["false_alarms_per_hour"]["T11"] / S["budget_per_hour"]
    cell = (f"box-sizing: border-box; padding: 10px 16px; display: flex; "
            f"flex-direction: column; gap: 2px; font-size: {CAP}px; line-height: 35px; "
            f"color: {INK2}")
    name = f"font-family: {SERIF}; font-size: 40px; line-height: 46px; font-weight: 700"
    hd = (f"font-family: {MONO}; font-size: {CAP}px; line-height: 34px; font-weight: 600; "
          f"letter-spacing: 0.04em; color: {INK}; display: flex; align-items: center")
    edge = f"3px solid {INK}"
    return (
        f'<div style="display: grid; grid-template-columns: 138px minmax(0, 1fr) '
        f'minmax(0, 1fr); border: {edge}; border-radius: 6px; overflow: hidden">'
        f'<div style="border-bottom: {edge}"></div>'
        f'<div style="{hd}; justify-content: center; border-bottom: {edge}; '
        f'border-left: {edge}; padding: 6px">WARNS EARLY</div>'
        f'<div style="{hd}; justify-content: center; border-bottom: {edge}; '
        f'border-left: {edge}; padding: 6px">WARNS LATE</div>'
        f'<div style="{hd}; padding: 10px 14px; border-bottom: {edge}">RARELY WRONG</div>'
        f'<div style="{cell}; background: {BLUE_T}; border-left: {edge}; '
        f'border-bottom: {edge}"><span style="{name}; color: {INK}">Useful</span>'
        f'<span style="color: {INK}">time to act before control is lost</span></div>'
        f'<div style="{cell}; border-left: {edge}; border-bottom: {edge}">'
        f'<span style="{name}; color: {INK}">Too late</span>the failure has already happened'
        f'</div>'
        f'<div style="{hd}; padding: 10px 14px">OFTEN WRONG</div>'
        f'<div style="{cell}; border-left: {edge}"><span style="{name}; color: {INK}">Ignored'
        f'</span>in hospitals, 72 to 99% of monitor alarms are false [4]</div>'
        f'<div style="{cell}; border-left: {edge}"><span style="{name}; color: {WINE}">'
        f'This monitor, so far</span><span style="color: {INK}">'
        f'{abs(L11["median_s"]):.0f} s late and {over:.0f}× its false-alarm budget</span></div>'
        f'</div>')


def comp(name: str, meaning: str) -> str:
    return (f'<div style="box-sizing: border-box; border: 2.5px solid {BLUE}; '
            f'background: {BLUE_T}; border-radius: 4px; padding: 6px 12px; display: flex; '
            f'flex-direction: column"><span style="font-family: {MONO}; font-size: {CAP}px; '
            f'line-height: 34px; font-weight: 600; color: {BLUE}">{name}</span>'
            f'<span style="font-size: {CAP}px; line-height: 33px; color: {INK2}">{meaning}'
            f'</span></div>')


CHEV = (f'<svg aria-hidden="true" width="24" height="44" viewBox="0 0 24 44" fill="none" '
        f'stroke="{INK2}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M6 6 L18 22 L6 38"/></svg>')


def monitor_fig() -> str:
    io = (f'box-sizing: border-box; border: 2.5px solid {INK}; border-radius: 4px; '
          f'padding: 8px 12px; display: flex; flex-direction: column; justify-content: center; '
          f'font-size: {CAP}px; line-height: 33px; color: {INK2}')
    grid = ('<div style="flex: 1; display: grid; grid-template-columns: repeat(2, '
            'minmax(0, 1fr)); gap: 8px">'
            + comp("level", "total activity has moved")
            + comp("silence", "channels have gone quiet")
            + comp("dispersion", "channels drift apart, total unchanged")
            + comp("profile", "shape across channels has changed") + "</div>")
    return ('<div style="display: flex; align-items: stretch; gap: 8px">'
            f'<div style="width: 196px; {io}"><b style="color: {INK}; font-weight: 600">'
            f'384 channels</b>activity in each 30 s window</div>'
            f'<div style="display: flex; align-items: center">{CHEV}</div>' + grid
            + f'<div style="display: flex; align-items: center">{CHEV}</div>'
            f'<div style="width: 190px; {io}"><b style="color: {INK}; font-weight: 600">'
            f'Risk score</b>largest component, cause named</div></div>')


def left_panel() -> str:
    L11 = D["lead_time"]["T11"]
    n = S["episodes"]
    sl = S["session_level_correlation_T11"]
    span = sl["series"][-1]["trial_day"] - sl["series"][0]["trial_day"]
    fa = S["false_alarms_per_hour"]["T11"]
    ep = D["median_episode"]
    day = ep["block"].split("/")[1].replace("day_", "")
    parts = []

    parts.append(sec(
        label("Abstract"),
        p(f"Brain-computer interface decoders lose accuracy as the recorded signal drifts. A "
          f"monitor could warn before control is lost, but no accepted test shows whether such "
          f"a warning comes early enough or is right often enough. This project builds that "
          f"test. On archived recordings from two implanted arrays, with {n['T11'] + n['T5']:,} "
          f"planted faults whose start times were sealed in advance, the monitor detected "
          f"faults that counting activity misses, yet warned a median "
          f"{abs(L11['median_s']):.0f} s after decoding failed and gave {fa:.2f} false alarms "
          f"per hour against a budget of 0.1. A preregistered optical test bench, specified "
          f"but not yet built, will measure both quantities where failure times are known.")))

    parts.append(sec(
        label("Introduction"),
        head("A decoder that fails without saying so"),
        p("Nearly 5.4 million people in the United States live with paralysis [3]. For some, "
          "an implanted brain-computer interface restores control of a cursor by intent. "
          "Software called a decoder translates the recorded activity, but the recording "
          "drifts, so decoders often need daily recalibration, and the device cannot be used "
          "freely while that happens [2]."),
        C.drift_line(SIDE_U, 212, sl["series"], sl["failure_threshold_deg"]),
        cap("1", f"A real decoder left fixed for {span} days: median cursor error by session, "
                 f"array T11. Archived data [1].")))

    parts.append(sec(
        label("Why it matters"),
        head("A warning helps only if it is early and rarely wrong"),
        quadrant(),
        p("Alarms that cry wolf get switched off: nuisance alarms are the leading reason smoke "
          "alarms are disconnected [5]. Existing decoder research corrects drift automatically "
          "[2, 6], or scores it and reports a correlation with performance, r = 0.93 and 0.72 "
          "[1]. No published lead time or false-alarm rate was found for such a monitor.")))

    parts.append(sec(
        label("Purpose"),
        p("To measure how early a decoder-health monitor warns, and how often it warns when "
          "nothing is wrong, on test beds where the moment of failure is known in advance.",
          INK)))

    parts.append(sec(
        label("Hypothesis / Engineering goal"),
        p(b("Primary hypothesis.") + " Measured against failure times fixed in advance, with "
          "enough fault-free recording to bound the rate, the monitor's lead time and "
          "false-alarm rate fall outside what a deployed system could use. "
          + b("Falsified if", WINE) + " the median lead time is above zero and the 95% upper "
          "bound on false alarms is within 0.1 per hour, at the threshold that detects 80% of "
          "faults."),
        p(b("Secondary hypothesis.") + " A monitor can reach the correlation with performance "
          "that the field reports as evidence (r above 0.7) while those two quantities say it "
          "is unusable. Inconclusive if no correlation measure reaches 0.70."),
        p(b("Engineering goal.") + " Build the monitor, the benchmark and the test bench that "
          "make both quantities measurable. Success is a trustworthy measurement, whatever "
          "the numbers are. It is not a claim that the monitor works."),
        cap_plain("Predictions and sample sizes were frozen on 24 September 2026, before any "
                  "bench data existed (commit f4dda04)."),
        gap=10))

    parts.append(sec(
        label("The system"),
        head("One monitor, used unchanged in both validations"),
        monitor_fig(),
        cap("2", "The monitor, decoder-guard: four named components in place of one opaque "
                 "number (scripts/22_decoder_guard.py)."),
        bullets([
            "It is fitted on healthy windows only. It never sees the decoder output, the task, "
            "the performance number or a fault label.",
            "It works in log space, so a uniform gain change becomes a shift and separates "
            "from a change in shape across channels.",
            "A warning needs the risk score to stay above its threshold, not touch it once."]),
        gap=12))

    parts.append(sec(
        label("What is measured"),
        C.episode_compact(ep, SIDE_U, 236),
        cap("3", f"One archived episode (array T11, day {day}, gain drift), chosen by rule as "
                 f"the first whose lead time equals the median. A: the fault begins, at a time "
                 f"sealed in advance. B: decoding fails, its error 10° above the healthy "
                 f"baseline. C: the monitor warns. Lead time is B minus C, so a negative value "
                 f"means the warning came too late. Detection delay, C minus A, is what the "
                 f"bench adds."),
        gap=10))
    return page("Draft 4, left panel: the problem and the system", PW_SIDE, PH,
                "\n".join(parts), 56, gap=24)


def cap_plain(text: str) -> str:
    return (f'<p style="margin: 0; font-size: {CAP}px; line-height: 36px; color: {INK3}; '
            f'text-wrap: pretty">{text}</p>')


# ===========================================================================
# CENTRE PANEL -- title, then column 2 (validation) and column 3 (results)
# ===========================================================================
def title_block() -> str:
    sw = lambda st: f'<span style="width: 34px; height: 22px; flex: none; {st}"></span>'
    key = lambda s_, t: (f'<span style="display: inline-flex; gap: 10px; align-items: center; '
                         f'font-size: {CAP}px; line-height: 34px; color: {INK2}">{s_}{t}</span>')
    return (
        '<header style="display: flex; flex-direction: column; gap: 8px">'
        f'<h1 style="margin: 0; font-family: {SERIF}; font-size: 138px; line-height: 144px; '
        f'font-weight: 700; letter-spacing: -0.014em; color: {INK}; white-space: nowrap">'
        f'Seeing Failure Before It Shows</h1>'
        f'<p style="margin: 0; font-family: {SERIF}; font-size: 46px; line-height: 56px; '
        f'color: {INK2}; text-wrap: balance">An early-warning monitor for brain-computer '
        f'interface decoders, validated on archived brain recordings and on a purpose-built '
        f'optical test bench</p>'
        f'<div style="display: flex; align-items: center; justify-content: space-between; '
        f'gap: 24px; flex-wrap: wrap; margin-top: 4px">'
        f'<span style="font-size: 36px; line-height: 44px; color: {INK}">'
        f'<b style="font-weight: 600">Gayathri Nair</b> &middot; Central Bucks High School '
        f'South &middot; [CATEGORY] &middot; [FAIR AND YEAR]</span>'
        f'<span style="display: inline-flex; gap: 26px">'
        + key(sw(f"background: {BLUE}"), "measured on archived recordings")
        + key(sw(f"border: 3px dashed {ORG}; box-sizing: border-box"), "planned on the bench")
        + key(sw(f"border: 3px dashed {INK3}; background: {WASH}; box-sizing: border-box"),
              "photo to add")
        + "</span></div></header>")


# ---- column 2: validation ---------------------------------------------------
def rail(steps: list[tuple[str, str]], color: str) -> str:
    """A numbered sequence down a line: the order things happen in."""
    out = [f'<div style="position: relative; display: flex; flex-direction: column; '
           f'gap: 10px"><div style="position: absolute; left: 22px; top: 24px; bottom: 24px; '
           f'width: 4px; background: {color}"></div>']
    for i, (t, d) in enumerate(steps, 1):
        out.append(
            f'<div style="position: relative; display: flex; gap: 16px; align-items: '
            f'flex-start"><span style="width: 48px; height: 48px; flex: none; '
            f'border-radius: 50%; background: {color}; color: #FFFFFF; font-size: 30px; '
            f'font-weight: 700; display: flex; align-items: center; justify-content: center">'
            f'{i}</span><span style="font-size: {CAP}px; line-height: 35px; color: {INK2}">'
            f'<b style="font-size: {BODY}px; line-height: 40px; color: {INK}; '
            f'font-weight: 600">{t}</b><br>{d}</span></div>')
    out.append("</div>")
    return "".join(out)


def code_block(path: str, want: list[str], dedent: int) -> str:
    """Lines copied from a repository file. The build stops if they are no longer there."""
    have = [ln[dedent:] if ln.startswith(" " * dedent) else ln
            for ln in (REPO / path).read_text().splitlines()]
    for ln in want:
        if ln not in have:
            raise SystemExit(f"the code shown on the poster is no longer in {path}: {ln!r}")
    esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = "".join(
        f'<div style="white-space: pre-wrap; padding-left: 2ch; text-indent: -2ch; '
        f'color: {INK3 if ln.lstrip().startswith("#") else INK}">{esc(ln)}</div>'
        for ln in want)
    return (f'<div style="box-sizing: border-box; background: {WASH}; border: 2px solid '
            f'{RULE}; border-radius: 6px; overflow: hidden; font-family: {MONO}; '
            f'font-size: {CAP}px; line-height: 35px; font-weight: 500">'
            f'<div style="background: {INK}; color: #FFFFFF; padding: 4px 16px">{path}</div>'
            f'<div style="padding: 10px 16px">{lines}</div></div>')


def output_block() -> str:
    line = lambda t, c: f'<div style="white-space: pre-wrap; color: {c}">{t}</div>'
    return (f'<div style="box-sizing: border-box; background: {WASH}; border: 2px solid '
            f'{RULE}; border-radius: 6px; overflow: hidden; font-family: {MONO}; '
            f'font-size: {CAP}px; line-height: 35px; font-weight: 500">'
            f'<div style="background: {INK}; color: #FFFFFF; padding: 4px 16px">output</div>'
            f'<div style="padding: 10px 16px">'
            + line("$ python3 scripts/31_verify_claims.py", INK3)
            + line("All 102 headline claims match the data files.", INK)
            + line("$ python3 poster/build_poster_data.py", INK3)
            + line("PASS -- every recomputed value matches its stored headline.", INK)
            + "</div></div>")


def bench_svg() -> str:
    """Side view of the test bench, in source units."""
    T, Ln, R = C.T, C.L, C.R
    W, H = COL_U, 268
    k = W / 700                                   # drawn for 700 units, fitted to the column
    X = lambda v: v * k
    s = [T(X(30), 22, "sealed dark box", 18, INK, weight=600)]
    s.append(R(X(30), 32, X(474), 196, fill="#FFFFFF", stroke=INK, sw=2.5))
    s.append(R(X(36), 38, X(462), 184, fill="none", stroke="#39424B", sw=6))
    s.append(f'<path d="M{X(70):.1f} 62 L{X(418):.1f} 130 L{X(70):.1f} 198 Z" '
             f'fill="{ORG_T}" stroke="{ORG_M}" stroke-width="1.5" stroke-dasharray="6 5"/>')
    s.append(R(X(54), 58, X(16), 144, fill=ORG_T, stroke=ORG, sw=2.5))
    s.append(T(X(82), 58, "screen", 18, ORG, weight=600))
    s.append(R(X(330), 90, 7, 80, fill=WINE_T, stroke=WINE, sw=2, dash="5 4"))
    s.append(T(X(330) + 3, 196, "filter", 18, WINE, anchor="middle", weight=600))
    s.append(R(X(426), 116, X(32), 28, fill=ORG_T, stroke=ORG, sw=2.5, rx=3))
    s.append(R(X(418), 123, X(8), 14, fill=ORG, stroke=ORG, sw=1))
    s.append(Ln(X(442), 144, X(442), 182, INK, 3))
    s.append(R(X(416), 182, X(52), 10, fill=WINE_T, stroke=WINE, sw=2, rx=2))
    s.append(T(X(442), 214, "camera", 18, ORG, anchor="middle", weight=600))
    s.append(Ln(X(458), 130, X(560), 130, BLUE, 2.5))
    s.append(R(X(499), 123, X(8), 14, fill="#FFFFFF", stroke=INK, sw=1.2))
    s.append(R(X(560), 94, X(130), 72, fill=BLUE_T, stroke=BLUE, sw=2.5, rx=4))
    s.append(T(X(625), 126, "Raspberry", 18, BLUE, anchor="middle", weight=600))
    s.append(T(X(625), 148, "Pi 4", 18, BLUE, anchor="middle", weight=600))
    s.append(f'<path d="M{X(600):.1f} 166 L{X(600):.1f} 250 L{X(62):.1f} 250 L{X(62):.1f} 202" '
             f'fill="none" stroke="{BLUE}" stroke-width="2.5" stroke-linejoin="round"/>')
    for n, x, y in ((1, 62, 84), (2, 442, 96), (5, 333, 70)):
        s.append(f'<circle cx="{X(x):.1f}" cy="{y}" r="14" fill="{INK}" stroke="#FFFFFF" '
                 f'stroke-width="2"/>')
        s.append(T(X(x), y + 6, str(n), 17, "#FFFFFF", anchor="middle", weight=700))
    return C.svg(W, H, s, "Side view of the test bench: a screen at one end of a sealed dark "
                 "box faces a camera at the other. A filter can slide into the light path and "
                 "the camera sits on a rotation stage. A Raspberry Pi outside drives the "
                 "screen and records the camera.")


def legend_line(n: int, html: str) -> str:
    return (f'<div style="display: flex; gap: 12px; align-items: baseline; font-size: {CAP}px; '
            f'line-height: 36px; color: {INK2}"><span style="width: 34px; height: 34px; '
            f'flex: none; border-radius: 50%; background: {INK}; color: #FFFFFF; '
            f'font-weight: 700; display: inline-flex; align-items: center; '
            f'justify-content: center; align-self: center">{n}</span><span>{html}</span></div>')


STEPPER = [("#E8453A", "pin 2 &middot; 5 V", "+"), ("#3C4248", "pin 9 &middot; GND", "&minus;"),
           ("#F08A2A", "pin 11 &middot; GPIO 17", "IN1"),
           ("#F0D32A", "pin 13 &middot; GPIO 27", "IN2"),
           ("#2FA84F", "pin 15 &middot; GPIO 22", "IN3"),
           ("#2E7BD4", "pin 16 &middot; GPIO 23", "IN4")]
SENSOR = [("#F0D32A", "pin 7 &middot; GPIO 4", "DATA"), ("#E8453A", "pin 1 &middot; 3.3 V", "VCC"),
          ("#3C4248", "pin 9 &middot; GND", "GND")]


def pins(rows: list[tuple[str, str, str]], cols: int) -> str:
    cell = f"font-size: {CAP}px; line-height: 36px; color: {INK2}; white-space: nowrap"
    return (f'<div style="display: grid; grid-template-columns: repeat({cols}, '
            f'minmax(0, 1fr)); column-gap: 20px">'
            + "".join(
                f'<div style="display: flex; align-items: center; gap: 10px; {cell}">'
                f'<span style="width: 36px; height: 20px; flex: none; background: {c}; '
                f'border-radius: 3px"></span>{pin} &rarr; <b style="color: {INK}; '
                f'font-weight: 600">{to}</b></div>' for c, pin, to in rows)
            + "</div>")


def stepper_fig() -> str:
    iw, ih = COL, round(COL * 450 / 1664)
    return (f'<div style="position: relative; width: {iw}px; height: {ih + 34}px">'
            f'<img src="{ASSETS["wiring-stepper-unlabelled.svg"]}" alt="Raspberry Pi 4 wired '
            f'to a ULN2003 driver board and a 28BYJ-48 stepper motor by six coloured jumper '
            f'wires" style="position: absolute; left: 0; top: 0; width: {iw}px; '
            f'height: {ih}px">'
            + note(14, ih - 6, 330, "Raspberry Pi 4", "left", INK, 600)
            + note(500, ih - 6, 300, "driver board", "center", INK, 600)
            + note(760, ih - 6, 300, "stepper motor", "center", INK, 600) + "</div>"
            + pins(STEPPER, 3))


def sensor_fig() -> str:
    iw = 520
    ih = round(iw * 390 / 1080)
    return (f'<div style="width: {iw}px; flex: none; display: flex; flex-direction: column; '
            f'gap: 6px"><div style="position: relative; width: {iw}px; height: {ih + 30}px">'
            f'<img src="{ASSETS["wiring-dht22-unlabelled.svg"]}" alt="Raspberry Pi 4 header '
            f'wired to a DHT22 temperature sensor by three jumper wires" style="position: '
            f'absolute; left: 0; top: 0; width: {iw}px; height: {ih}px">'
            + note(10, ih - 8, 220, "Raspberry Pi 4", "left", INK, 600)
            + note(300, ih - 8, 220, "DHT22 sensor", "right", INK, 600) + "</div>"
            + pins(SENSOR, 1) + "</div>")


BLANK = (f'<span style="display: inline-block; width: 100%; height: 28px; box-sizing: '
         f'border-box; border-bottom: 3px dashed {ORG}"></span>')
TICKS = (f'<span style="display: inline-flex; gap: 8px; align-items: center; white-space: '
         f'nowrap"><span style="width: 22px; height: 22px; box-sizing: border-box; '
         f'border: 2.5px solid {INK}"></span>pass<span style="width: 22px; height: 22px; '
         f'box-sizing: border-box; border: 2.5px solid {INK}; margin-left: 8px"></span>fail'
         f'</span>')


def validation_column() -> str:
    n = S["episodes"]
    e, c = S["decoder_error_deg"], S["decoder_chance_deg"]
    parts = []
    parts.append(sec(
        label("Computational validation", BLUE, chip("complete", "done")),
        p("Archived recordings do not say when a failure began, so the failures were built: "
          "faults planted in real recordings at start times sealed before any detector "
          "existed, graded by a decoder that is never refitted."),
        rail([
            ("Archived recordings", "two implanted arrays, T11 and T5; public and "
             "de-identified [1]. No participants were recruited."),
            ("Planted faults", f"{n['T11'] + n['T5']:,} episodes ({n['T11']:,} + {n['T5']}): "
             f"four fault types, three rates, three severities; start times sealed with "
             f"SHA-256."),
            ("Frozen reference decoder", f"ridge regression, fitted once: {e['T11']:.1f}° "
             f"error against {c['T11']:.1f}° chance (T11), {e['T5']:.1f}° against "
             f"{c['T5']:.1f}° (T5). Grades only."),
            ("The monitor", "sees only recorded activity; a risk score every 5 s from the "
             "last 30 s."),
            ("Scoring harness", "lead time and false alarms as a pair; five gates; test data "
             "read once."),
        ], BLUE),
        cap("4", "The computational workflow (scripts/17 to scripts/22). The grading was "
                 "built and committed before the monitor existed, so the measure could not be "
                 "chosen to flatter it."),
        code_block("scripts/21_score_report.py", [
            "# A warning raised before the fault even started is not prescience, it is a",
            "# false alarm that happens to sit in a positive episode. Counting it as a",
            "# very early detection would be the most flattering possible error.",
            "if warn_w < onset_w:",
            '    return {"false_alarm": True, "warn_w": warn_w, "lead_s": np.nan, '
            '"detected": False}',
        ], 4),
        output_block(),
        cap("5", "Real code and real output. A warning before the fault begins is scored as a "
                 "false alarm, never as an early catch. Every headline number is recomputed "
                 "from the data files by script."),
        gap=12))

    parts.append(sec(
        label("Physical validation", ORG, chip("preregistered, not built", "todo")),
        p("Archived data cannot supply a recorded start time or enough fault-free hours. A "
          "bench can: its faults begin at sealed moments and it records unattended. The "
          "apparatus is the subject; no person is measured."),
        bench_svg(),
        '<div style="display: flex; flex-direction: column; gap: 2px">'
        + legend_line(1, b("Screen:") + " 384 patches whose brightness encodes a known "
                         "direction.")
        + legend_line(2, b("Camera:") + " films them at 50 frames a second, in the dark.")
        + legend_line(3, b("Decoder:") + " fitted once on fault-free sessions, then frozen.")
        + legend_line(4, b("Monitor:") + " the same code as on the brain recordings.")
        + legend_line(5, b("Fault", WINE) + ": filter, rotation or software; begins at a "
                         "sealed moment.")
        + legend_line(6, b("Scoring:") + " each warning against that sealed moment.")
        + "</div>",
        cap("6", "The optical test bench as specified. Nothing shown is built yet. Parts: "
                 "Raspberry Pi 4, Camera Module 3, display, cardboard enclosure, ND 0.6 "
                 "filter, stepper motor and driver, DHT22 sensor."),
        stepper_fig(),
        cap("7", "Breadboard view: wiring of the rotation stage. Pin numbers are read from "
                 "rig/motor.py and checked on every run. The motor takes 5 V, never 3.3 V."),
        f'<div style="display: flex; gap: 28px; align-items: stretch">{sensor_fig()}'
        f'<div style="flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px">'
        + photo("Raspberry Pi 4, camera and wiring", 200)
        + cap("8", "Left: breadboard view of the room-temperature sensor. Only the DATA pin "
                   "is fixed by the repository (rig/logtemp.py); VCC and GND are a "
                   "recommendation.")
        + "</div></div>",
        '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); '
        'gap: 16px">'
        + photo("the assembled bench, sealed", 196)
        + photo("inside: screen and camera", 196)
        + photo("a recording session", 196, "SCREENSHOT TO ADD") + "</div>",
        table(["Gate", "Must hold before any result is read", "Measured", "Result"],
              [[b("G-a"), "light-tight: mean pixel below 2, max below 5 (of 255)", BLANK, TICKS],
               [b("G-b"), "under 1% late frames, 5% dead channels, 1% clipped", BLANK, TICKS],
               [b("G-c"), "screen-to-camera delay agrees over 3 runs", BLANK, TICKS],
               [b("G-d"), "sub-level signal on over 80% of channels", BLANK, TICKS],
               [b("G-e"), "margin within 6° of the neural value, 36.1°", BLANK, TICKS]],
              ["9%", "55%", "14%", "22%"]),
        cap("9", "Acceptance gates, blank until the bench exists. If G-e cannot be met the "
                 "phase stops and reports that."),
        gap=12))
    return (f'<div style="width: {COL}px; flex: none; display: flex; flex-direction: column; '
            f'gap: 22px">' + "".join(parts) + "</div>")


# ---- column 3: results, data, analysis --------------------------------------
def key(big: str, text: str) -> str:
    return (f'<div style="border-top: 5px solid {BLUE}; padding-top: 6px; display: flex; '
            f'flex-direction: column"><span style="font-family: {SERIF}; font-size: 72px; '
            f'line-height: 80px; font-weight: 700; color: {BLUE}; white-space: nowrap">{big}'
            f'</span><span style="font-size: {CAP}px; line-height: 35px; color: {INK2}">{text}'
            f'</span></div>')


def chart(title: str, svg_: str, n: str, caption: str) -> str:
    return (f'<div style="display: flex; flex-direction: column; gap: 6px">'
            + finding(title) + svg_ + cap(n, caption) + "</div>")


def results_column() -> str:
    v = D["fault_mode_auc"]["values"]
    g = [v[a]["decoder_guard"][i] for a in ("T11", "T5") for i in (2, 3)]
    k = [v[a]["mean_activity"][i] for a in ("T11", "T5") for i in (2, 3)]
    L11, L5 = D["lead_time"]["T11"], D["lead_time"]["T5"]
    ci = L11["ci95_s"]
    fa = S["false_alarms_per_hour"]
    f = S["funnel"]
    dvf = D["detection_vs_fa"]
    sil, nff = S["silence_fault_free_fraction"], S["fault_free_episodes"]
    pr = D["decision_rate"]["paired"]["participants"]
    a, t5 = pr["T11"]["own_range"], pr["T5"]["own_range"]
    pct = lambda x: minus(f"{x * 100:+.1f}")
    sc = D["session_scatter"]
    sep = S["task_change_separation"]
    names = {"RATE_LOSS": ("Signal loss", "total falls"),
             "CHANNEL_DROPOUT": ("Dropout", "channels go silent"),
             "GAIN_DRIFT": ("Gain drift", "total unchanged"),
             "GEOMETRY_ROTATION": ("Rotation", "total unchanged")}
    W = COL_U
    numbers = (
        '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); '
        'gap: 14px 32px">'
        + key(f"{min(g):.2f} to {max(g):.2f}",
              f"detection score on faults where counting activity scores {min(k):.2f} to "
              f"{max(k):.2f}")
        + key(f"{abs(L11['median_s']):.0f} s late",
              "the typical warning arrives after decoding has already failed")
        + key(f"{fa['T11'] / S['budget_per_hour']:.0f}× too often",
              f"{fa['T11']:.2f} false alarms per hour against a budget of 0.1")
        + key(f"{f['all_gates']} of {f['run']}",
              "monitor configurations pass all five acceptance gates")
        + "</div>")
    data = table(
        ["Measured", "Array T11", "Array T5", "Needed"],
        [["Faults detected", f"{L11['n_detected']} of {L11['n_degraded']}",
          f"{L5['n_detected']} of {L5['n_degraded']}", "80%"],
         ["Median lead time", f"{num(L11['median_s'], 0)} s", f"{num(L5['median_s'], 0)} s",
          "above 0 s"],
         ["False alarms per hour", f"{fa['T11']:.2f}", f"{fa['T5']:.3f}", "at most 0.1"],
         ["Fault-free episodes drifting", f"{sil['T11'] * 100:.1f}%", f"{sil['T5'] * 100:.0f}%",
          "at most 10%"],
         ["Session score (AUC)", f"{S['auc_session']['T11']:.3f}",
          f"{S['auc_session']['T5']:.3f}", f"{S['auc_needed_at_budget']['T11']:.3f}"],
         ["Risk autocorrelation, lag 1", f"{S['lag1_pooled']['T11']:.3f}",
          f"{S['lag1_pooled']['T5']:.3f}", "near 0"],
         ],
        ["40%", "21%", "21%", "18%"])
    parts = [
        sec(label("Results and data", BLUE, chip("archived recordings", "done")), numbers,
            gap=12),
        chart("It sees faults that counting misses",
              C.mode_dumbbell(W, 290, v, D["fault_mode_auc"]["modes"], names), "10",
              "Detection score by fault type. Filled: the monitor. Open: counting activity. "
              "It wins where total activity is unchanged and loses on plain signal loss, as "
              "designed."),
        chart("But the warning comes after the failure",
              C.lead_dots(W, 166, L11["leads_s"], L11["median_s"], top=16, label_gap=12, label_dy=46), "11",
              f"One dot per detected fault, array T11 ({L11['n_detected']} of "
              f"{L11['n_degraded']}). Median {num(L11['median_s'], 0)} s, 95% CI "
              f"{num(ci[0], 0)} to {num(ci[1], 0)}: {L11['fraction_negative'] * 100:.0f}% late, "
              f"{L11['fraction_positive'] * 100:.0f}% early."),
        chart("And it warns far too often",
              C.fa_measured(W, 278, fa, S["budget_per_hour"], sil, nff), "12",
              f"False alarms per hour against the budget, and how often the risk score drifts "
              f"when nothing is wrong ({nff['T11']} + {nff['T5']} fault-free episodes)."),
        chart("No threshold fixes both at once",
              C.dfa_measured(W, 228, dvf["curves"], {"T11": dvf["best_inside_budget_T11"],
                                                     "T5": dvf["best_inside_budget_T5"]}),
              "13", "Sweeping the warning threshold: detection is high only where false "
                    "alarms run at several per hour."),
        sec(label("Data"), data,
            cap("14", f"Also measured: a change of task is not mistaken for a fault "
                      f"({sep['658']:.1f}× and {sep['665']:.0f}× separation), and accuracy by "
                      f"session ranges {sc['auc_min']:.2f} to {sc['auc_max']:.2f}, tracking "
                      f"that day's decoder error (ρ = {num(sc['spearman_rho'], 3)})."),
            gap=10),
        sec(label("Analysis"),
            finding("Why: one measurement, 720 decisions"),
            p(f"Risk scores within a session are near-copies of each other, so 720 decisions "
              f"an hour rest on about one independent measurement. Deciding once per session "
              f"would still need a score of {S['auc_needed_at_budget']['T11']:.3f}."),
            C.auc_gap(W, 122, S["auc_session"], S["auc_needed_at_budget"]),
            cap("15", "Session score reached on each array against the score needed to stay "
                      "inside the false-alarm budget."),
            gap=8),
        chart("Deciding less often: the arrays disagree",
              C.decision_measured(W, 232, D["decision_rate"]["curves"]), "16",
              f"Detection against how often the monitor decides, at a 10% false-flag rate. "
              f"T11 {pct(a['change'])} points (not established); T5 {pct(t5['change'])} "
              f"points (established)."),
    ]
    return (f'<div style="width: {COL}px; flex: none; display: flex; flex-direction: column; '
            f'gap: 16px">' + "".join(parts) + "</div>")


def centre_panel() -> str:
    return page("Draft 4, centre panel: validation and results", PW_MAIN, PH,
                title_block()
                + '\n<div style="display: flex; gap: 56px; align-items: flex-start">'
                + validation_column() + results_column() + "</div>", 56, gap=30)


# ===========================================================================
# COLUMN 4 (right panel) -- discussion and interpretation
# ===========================================================================
def point(lead: str, text: str) -> str:
    return (f'<p style="margin: 0; font-size: {BODY}px; line-height: 42px; color: {INK2}; '
            f'text-wrap: pretty"><b style="color: {INK}; font-weight: 600">{lead}</b> {text}'
            f'</p>')


def relate() -> str:
    """What each validation supplies, and what it cannot: the two read as one argument."""
    n = S["episodes"]
    ff = S["fault_free_episodes"]
    rows = [
        ("Signal", "two implanted arrays, 20 ms bins",
         "384 screen patches at 50 frames a second"),
        ("Faults", "planted in software: 4 types, 3 rates, 3 severities",
         "optical or software: 4 types, 3 severities, plus faults nobody designed"),
        ("Start time", f"sealed before any detector existed ({n['T11'] + n['T5']:,} episodes)",
         "sealed with SHA-256 before each recording"),
        ("Fault-free record", f"{ff['T11']} + {ff['T5']} episodes, about 1.4 h",
         "101 sessions, about 8.4 h, 4 h held out"),
        ("Establishes", "the monitor sees real faults, and is not deployable at the budget",
         "whether that persists without biology, with known start times"),
        ("Cannot establish", "a bounded false-alarm rate; agreement beyond two arrays",
         "clinical performance: a camera is not an implant"),
    ]
    cell = (f"padding: 6px 12px; font-size: {CAP}px; line-height: 35px; color: {INK2}; "
            f"border-top: 1.5px solid {RULE}")
    out = [f'<div style="display: grid; grid-template-columns: 172px minmax(0, 1fr) '
           f'minmax(0, 1fr); border: 3px solid {INK}; border-radius: 6px; overflow: hidden">'
           f'<div></div>'
           f'<div style="padding: 6px 12px; background: {BLUE}; color: #FFFFFF; '
           f'font-size: {CAP}px; line-height: 35px; font-weight: 600">Computational: done</div>'
           f'<div style="padding: 6px 12px; background: {ORG}; color: #FFFFFF; '
           f'font-size: {CAP}px; line-height: 35px; font-weight: 600">Physical: planned</div>']
    for lab, x, y in rows:
        out.append(f'<div style="{cell}; font-weight: 600; color: {INK}">{lab}</div>'
                   f'<div style="{cell}">{x}</div><div style="{cell}">{y}</div>')
    out.append("</div>")
    return "".join(out)


def verdict_tree() -> str:
    L11 = D["lead_time"]["T11"]
    q = f"background: #FFFFFF; border: 3px solid {INK}"
    bad = f"background: {WINE_T}; border: 3px solid {WINE}"
    good = f"background: {BLUE_T}; border: 3px solid {BLUE}"
    el = [
        arrow(520, 42, 639, 42), arrow(260, 84, 260, 143),
        arrow(520, 198, 639, 198), arrow(260, 252, 260, 311),
        box(0, 0, 520, 84, "Median lead time above 0 s?", q),
        box(640, 0, 400, 84, "Not usable: too late", bad, WINE),
        box(0, 144, 520, 108, "False-alarm upper bound within 0.1 per hour?", q),
        box(640, 156, 400, 84, "Not usable: too noisy", bad, WINE),
        box(0, 312, 520, 84, "Usable: hypothesis falsified", good, BLUE),
        note(540, 2, 80, "no", "center", INK, 600),
        note(540, 158, 80, "no", "center", INK, 600),
        note(276, 96, 80, "yes", "left", INK, 600),
        note(276, 264, 80, "yes", "left", INK, 600),
        note(640, 90, 400, f"archived data: {abs(L11['median_s']):.0f} s late", "center",
             BLUE, 600),
        note(640, 318, 400, "bench result:", "left", ORG, 600),
        f'<div style="position: absolute; left: 640px; top: 358px; width: 400px; height: 36px; '
        f'box-sizing: border-box; border-bottom: 3px dashed {ORG}"></div>',
    ]
    return (f'<div style="position: relative; width: 1040px; height: 398px">'
            + "".join(el) + "</div>")


def right_panel() -> str:
    L11 = D["lead_time"]["T11"]
    fa = S["false_alarms_per_hour"]["T11"]
    blank = (f'<span style="display: inline-block; width: 140px; height: 34px; box-sizing: '
             f'border-box; border-bottom: 3px dashed {ORG}; vertical-align: baseline"></span>')
    parts = []
    parts.append(sec(
        label("Discussion"),
        head("What the results mean"),
        point("The monitor carries real information.", "It beats plain counting on exactly "
              "the faults counting cannot see, on both arrays (Fig. 10). It also does not "
              "mistake a change of task for a fault."),
        point("A real signal is not yet a usable warning.", f"It comes "
              f"{abs(L11['median_s']):.0f} s late and {fa / S['budget_per_hour']:.0f} times "
              f"too often (Figs 11 to 13). The binding problem is not detection but silence: "
              f"the risk score is never quiet during healthy use."),
        point("The cause is measured, not guessed.", "One session holds about one "
              "independent measurement, so neither a different threshold nor averaging "
              "rescues it (Fig. 15)."),
        point("One question stays open.", "Deciding less often helps on one array and hurts "
              "on the other (Fig. 16). Two arrays cannot settle it."),
        gap=12))

    parts.append(sec(
        label("How the two validations relate"),
        relate(),
        cap("17", "Each validation supplies what the other cannot. Held identical in both: "
                  "the monitor, the 30 s window and 5 s step, the warning logic, the 0.1 per "
                  "hour budget and the frozen decoder, so a difference between them cannot "
                  "come from a retuned monitor."),
        p(b("Open until both are read together:") + " whether the late warning belongs to "
          "brain recordings or to the method itself; how large the false-alarm rate is once "
          "there is enough fault-free recording to bound it; and whether deciding less often "
          "helps."),
        gap=12))

    parts.append(sec(
        label("How the bench result will be judged"),
        verdict_tree(),
        cap("18", "Fixed before any recording. A result is read only after the five "
                  "acceptance gates pass (Fig. 9)."),
        gap=10))

    parts.append(sec(
        label("Limitations"),
        bullets([
            "A camera in a sealed box is not an implanted array. A false-alarm rate measured "
            "on the bench is not an estimate of a clinical rate.",
            "Matching the decoding difficulty makes the problem comparably hard. It does not "
            "make the noise, the drift or the failure modes the same.",
            "Two arrays, which disagree on several questions; one bench, one room, one "
            "family of monitor.",
            "About 4 held-out fault-free hours cannot show a rate below 0.75 per hour. "
            "Reaching the 0.1 budget needs about 30 h."]),
        gap=10))

    parts.append(sec(
        label("Broader significance"),
        p("The two questions, how early and how often wrong, are not specific to brain "
          "implants. They apply to any many-channel sensor that drifts and is watched by a "
          "statistic, and the bench is one instance of that class. What carries over is the "
          "test: failures whose start times are sealed in advance, and timing and false "
          "alarms reported together. No clinical benefit is claimed."),
        gap=10))

    parts.append(sec(
        label("Future directions"),
        table(["", "Planned bench experiment", "Sessions", "Recording"],
              [[b("P-1"), "calibration: match decoding difficulty", "5 or more", "25 min"],
               [b("P-2"), "false-alarm rate and silence, fault-free", "101", "8.4 h"],
               [b("P-3"), "lead time from a sealed start time", "101", "8.4 h"],
               [b("P-4"), "correlation against usability", "0", "analysis"],
               [b("P-5"), "faults nobody designed, by hand", "10", "50 min"],
               [b("P-6"), "decision-rate curve, re-scored", "0", "analysis"],
               [b("P-7"), "three more bench configurations", "120", "about 10 h"],
               [b("All"), b("none recorded yet"), b("337"), b("about 28 h")]],
              ["9%", "55%", "17%", "19%"]),
        cap("19", "The seven planned experiments, sizes frozen in advance. Changed: start "
                  "time, fault present or absent, fault type, severity (0.25, 0.5, 1.0), "
                  "decision rate. Measured: lead time, false-alarm rate, detection rate, "
                  "silence, correlation with performance. Held fixed: window, decoder, camera "
                  "exposure, screen brightness, modulation depth, ambient light, geometry."),
        gap=10))

    box_ = (f'<span style="width: 24px; height: 24px; flex: none; box-sizing: border-box; '
            f'border: 2.5px solid {INK}; margin-left: 10px"></span>')
    parts.append(sec(
        label("Conclusion"),
        p("On archived recordings the monitor detects real faults, but it warns too late and "
          "too often to be relied on, and the cause is measured. The bench will show whether "
          "that belongs to brain recordings or to the method.", INK),
        # The blanks are the quantities the frozen verdict (Fig. 18) is read from, no others.
        f'<div style="font-size: {BODY}px; line-height: 50px; color: {INK2}; '
        f'border: 3px dashed {ORG}; border-radius: 6px; padding: 8px 16px">'
        f'<b style="color: {ORG}; font-weight: 600">Bench result, to be measured</b><br>'
        f'median lead time {blank} s, 95% CI {blank} to {blank}<br>'
        f'false alarms {blank} per hour, upper bound {blank}<br>'
        f'<span style="display: inline-flex; gap: 12px; align-items: center; '
        f'flex-wrap: wrap">verdict (Fig. 18): {box_}too late {box_}too noisy {box_}usable'
        f'</span></div>',
        gap=10))
    parts.append(refs_block())
    return page("Draft 4, right panel: discussion and interpretation", PW_SIDE, PH,
                "\n".join(parts), 56, gap=22)


# ===========================================================================
def main() -> int:
    for name, fn in (("D4-Centre.dc.html", centre_panel), ("D4-Left.dc.html", left_panel),
                     ("D4-Right.dc.html", right_panel)):
        html = fn()
        markup = html[html.index("<x-dc>"):html.index("</x-dc>")]
        if "{{" in markup or "}}" in markup:
            raise SystemExit(f"{name}: a doubled brace would be read as a template hole")
        if "—" in html:
            raise SystemExit(f"{name}: contains an em dash")
        (OUT / name).write_text(html)
        print(f"wrote {(OUT / name).relative_to(REPO)}  ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
