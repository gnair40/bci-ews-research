#!/usr/bin/env python3
"""
build_poster.py -- assemble the three trifold panels from poster_data.json.

    python3 poster/build_poster_data.py     # recompute and check every number
    python3 poster/build_poster.py          # write poster/canvas/project/*.dc.html

THE BOARD
---------
A standard 48 x 36 inch trifold, at 96 px per inch:

    Left.dc.html     12 x 36 in   1152 x 3456 px   problem, question, approach
    Main.dc.html     24 x 36 in   2304 x 3456 px   title, architecture, evidence
    Right.dc.html    12 x 36 in   1152 x 3456 px   physical design and protocol

WHAT IS HAND-WRITTEN AND WHAT IS NOT
------------------------------------
The words, tables and diagrams below are written here by hand, from the
repository's documents. Every number that comes from a stored result is NOT
typed here: it is read from poster_data.json, which build_poster_data.py
recomputes and checks. If a sentence below needs a measured number, it takes it
from `D`, so the poster cannot disagree with the data it summarises.

Numbers fixed by the frozen preregistration (the 0.1 per hour budget, 101
sessions, 36.1 degrees) are design constants, not results, and are written in
place. scripts/77_cross_reference.py checks those against the code.

NOTHING HERE IS A PHYSICAL RESULT
---------------------------------
No apparatus exists. Every chart of the physical phase is drawn in its planned
state, and each one says so on its face.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import charts as C

HERE = Path(__file__).resolve().parent
OUT = HERE / "canvas" / "project"
D = json.loads((HERE / "poster_data.json").read_text())
S = D["scalars"]

INK, INK2, INK3 = C.INK, C.INK2, C.INK3
RULE, GRID = C.RULE, C.GRID
BLUE, BLUE_T, BLUE_M = C.BLUE, C.BLUE_T, C.BLUE_M
ORG, ORG_T, ORG_M = C.ORG, C.ORG_T, C.ORG_M
WINE, WINE_T = C.WINE, "#F7E6EB"
TEAL, TEAL_T = "#0D6B5D", "#E0F1ED"
WASH = "#F3F5F7"
SERIF = "'Source Serif 4', Georgia, 'Times New Roman', serif"
SANS = "'IBM Plex Sans', Arial, sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600"
         "&family=IBM+Plex+Sans:wght@400;500;600;700"
         "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap")

PH, PW_SIDE, PW_MAIN = 3456, 1152, 2304


def minus(x: str) -> str:
    return x.replace("-", "−")


def num(v: float, nd: int = 2) -> str:
    return minus(f"{v:.{nd}f}")


# ---------------------------------------------------------------------------
# small components
# ---------------------------------------------------------------------------
def page(title: str, w: int, h: int, body: str, pad: int, gap: int = 24) -> str:
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


def kicker(text: str, color: str = INK3) -> str:
    return (f'<div style="font-family: {MONO}; font-size: 19px; line-height: 24px; '
            f'font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; '
            f'color: {color}">{text}</div>')


def h2(n: str, text: str, size: int = 42) -> str:
    return (f'<div style="display: flex; align-items: baseline; gap: 16px; '
            f'border-top: 3px solid {INK}; padding-top: 12px">'
            f'<span style="font-family: {MONO}; font-size: 20px; font-weight: 500; '
            f'color: {INK3}">{n}</span>'
            f'<h2 style="margin: 0; font-family: {SERIF}; font-size: {size}px; '
            f'line-height: 1.12; font-weight: 600; color: {INK}; text-wrap: balance">{text}</h2>'
            f'</div>')


def p(html: str, size: int = 25, lh: int = 35, color: str = INK2, weight: int = 400) -> str:
    return (f'<p style="margin: 0; font-size: {size}px; line-height: {lh}px; color: {color}; '
            f'font-weight: {weight}; text-wrap: pretty">{html}</p>')


def sec(*parts: str, gap: int = 16) -> str:
    return (f'<section style="display: flex; flex-direction: column; gap: {gap}px">'
            + "".join(parts) + "</section>")


def chip(text: str, kind: str) -> str:
    st = {
        "measured": f"background: {BLUE}; color: #FFFFFF; border: 2px solid {BLUE}",
        "complete": f"background: {INK}; color: #FFFFFF; border: 2px solid {INK}",
        "frozen": f"background: {TEAL}; color: #FFFFFF; border: 2px solid {TEAL}",
        "planned": f"background: #FFFFFF; color: {ORG}; border: 2px dashed {ORG}",
        "none": f"background: #FFFFFF; color: {INK2}; border: 2px dashed {INK3}",
    }[kind]
    return (f'<span style="display: inline-block; {st}; font-family: {MONO}; font-size: 17px; '
            f'line-height: 22px; font-weight: 600; letter-spacing: 0.06em; '
            f'text-transform: uppercase; padding: 3px 10px; border-radius: 4px; '
            f'white-space: nowrap">{text}</span>')


def cap(n: str, title: str, text: str = "", size: int = 20) -> str:
    return (f'<p style="margin: 0; font-size: {size}px; line-height: {size + 8}px; '
            f'color: {INK2}; text-wrap: pretty"><b style="color: {INK}">Fig. {n}. {title}</b> '
            f'{text}</p>')


def src(text: str) -> str:
    return (f'<span style="font-family: {MONO}; font-size: 16px; color: {INK3}">{text}</span>')


def b(text: str, color: str = INK) -> str:
    return f'<b style="color: {color}; font-weight: 600">{text}</b>'


def table(head: list[str], rows: list[list[str]], widths: list[str], size: int = 20,
          lh: int = 27, pad: str = "8px 10px") -> str:
    th = "".join(
        f'<th style="width: {w}; text-align: left; padding: {pad}; font-size: {size - 2}px; '
        f'line-height: {lh - 3}px; font-weight: 600; color: {INK}; background: {WASH}; '
        f'border-bottom: 2px solid {INK}; vertical-align: bottom">{h}</th>'
        for h, w in zip(head, widths))
    body = ""
    for r in rows:
        body += "<tr>" + "".join(
            f'<td style="padding: {pad}; font-size: {size}px; line-height: {lh}px; '
            f'color: {INK2}; border-bottom: 1px solid {RULE}; vertical-align: top">{c}</td>'
            for c in r) + "</tr>"
    return (f'<table style="width: 100%; border-collapse: collapse; table-layout: fixed; '
            f'font-family: {SANS}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>')


CAMERA_GLYPH = (
    '<svg aria-hidden="true" width="44" height="44" viewBox="0 0 24 24" fill="none" '
    f'stroke="{INK3}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 8h3.5l1.5-2.5h8L17.5 8H21v11H3z"/><circle cx="12" cy="13.2" r="3.6"/></svg>')


def photo(n: int, what: str, h: int = 168) -> str:
    """A slot for a photograph that does not exist yet. Grey, never orange or blue."""
    return (f'<div style="height: {h}px; box-sizing: border-box; border: 2px dashed {INK3}; '
            f'background: {WASH}; border-radius: 4px; display: flex; flex-direction: column; '
            f'align-items: center; justify-content: center; gap: 4px; padding: 10px; '
            f'text-align: center">{CAMERA_GLYPH}'
            f'<span style="font-family: {MONO}; font-size: 16px; font-weight: 600; '
            f'letter-spacing: 0.08em; color: {INK2}">PHOTO SLOT {n}</span>'
            f'<span style="font-size: 18px; line-height: 23px; color: {INK2}">{what}</span>'
            f'</div>')


# ---------------------------------------------------------------------------
# diagram primitives: separate placed elements, one small svg per straight arrow
# ---------------------------------------------------------------------------
_arrow_id = [0]


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = INK2, head: bool = True,
          dash: str | None = None, sw: int = 3) -> str:
    """One straight segment from (x1,y1) to its tip (x2,y2); horizontal or vertical."""
    _arrow_id[0] += 1
    mid = f"dc-arrow-head-filled-{_arrow_id[0]}"
    hl = 2 * sw if head else 0
    horiz = y1 == y2
    n = abs(x2 - x1) if horiz else abs(y2 - y1)
    if horiz:
        left, top, w, h = min(x1, x2), y1 - 4, n, 8
        d = f"M 0 4 L {n - hl} 4" if x2 > x1 else f"M {n} 4 L {hl} 4"
    else:
        left, top, w, h = x1 - 4, min(y1, y2), 8, n
        d = f"M 4 0 L 4 {n - hl}" if y2 > y1 else f"M 4 {n} L 4 {hl}"
    da = f"; stroke-dasharray: {dash}" if dash else ""
    defs = (f'<defs><marker id="{mid}" orient="auto" markerWidth="5" markerHeight="5" '
            f'refX="2" refY="2" overflow="visible"><path d="M0 0 L4 2 L0 4 Z" fill="{color}" '
            f'stroke="none" style="stroke: none; fill: {color}; fill: context-stroke"/>'
            f'</marker></defs>') if head else ""
    me = f' marker-end="url(#{mid})"' if head else ""
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'style="position: absolute; left: {left}px; top: {top}px; width: {w}px; '
            f'height: {h}px; overflow: visible; fill: none; stroke: {color}; '
            f'stroke-width: {sw}; stroke-linecap: round; stroke-linejoin: round{da}">'
            f'{defs}<path d="{d}"{me}></path></svg>')


def card(x: int, y: int, w: int, h: int, title: str, lines: str, kind: str,
         mono: bool = False, tsize: int = 22) -> str:
    look = {
        "soft": f"background: {BLUE_T}; border: 2px solid {BLUE}",
        "phys": f"background: {ORG_T}; border: 2px solid {ORG}",
        "seal": f"background: {TEAL_T}; border: 2px solid {TEAL}",
        "fault": f"background: {WINE_T}; border: 2px solid {WINE}",
        "fixed": f"background: #FFFFFF; border: 2px solid {INK}",
        "out": f"background: {INK}; border: 2px solid {INK}",
        "data": f"background: {WASH}; border: 2px dashed {INK3}",
    }[kind]
    tcol = {"soft": BLUE, "phys": ORG, "seal": TEAL, "fault": WINE, "fixed": INK,
            "out": "#FFFFFF", "data": INK}[kind]
    lcol = "#E6EBEF" if kind == "out" else INK2
    fam = MONO if mono else SANS
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; '
            f'height: {h}px; box-sizing: border-box; padding: 10px 12px; display: flex; '
            f'align-items: center; justify-content: center; text-align: center; {look}; '
            f'border-radius: 6px"><span style="font-size: 18px; line-height: 23px; '
            f'color: {lcol}"><b style="font-family: {fam}; font-size: {tsize}px; '
            f'line-height: 28px; font-weight: 600; color: {tcol}">{title}</b><br>{lines}</span>'
            f'</div>')


def note(x: int, y: int, w: int, text: str, align: str = "center", color: str = INK2,
         size: int = 17) -> str:
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; '
            f'text-align: {align}; font-size: {size}px; line-height: {size + 5}px; '
            f'color: {color}">{text}</div>')


# ===========================================================================
# LEFT PANEL -- problem, question, hypothesis, the monitor, the computational build
# ===========================================================================
def tile(title: str, body: str, color: str) -> str:
    return (f'<div style="flex: 1; box-sizing: border-box; border: 2px solid {INK}; '
            f'border-radius: 4px; padding: 16px 18px; display: flex; flex-direction: column; '
            f'gap: 6px"><span style="font-family: {SERIF}; font-size: 31px; line-height: 36px; '
            f'font-weight: 600; color: {color}">{title}</span>'
            f'<span style="font-size: 22px; line-height: 30px; color: {INK2}">{body}</span></div>')


def claim(label: str, text: str, falsified: str) -> str:
    return (f'<div style="display: flex; flex-direction: column; gap: 8px">'
            f'<div style="display: flex; gap: 12px; align-items: baseline">'
            f'<span style="font-family: {MONO}; font-size: 18px; font-weight: 600; '
            f'letter-spacing: 0.06em; text-transform: uppercase; color: {INK}; '
            f'white-space: nowrap">{label}</span></div>'
            + p(text, 24, 33, INK)
            + f'<p style="margin: 0; font-size: 21px; line-height: 29px; color: {INK2}">'
              f'<b style="color: {WINE}; font-weight: 600">Falsified if</b> {falsified}</p></div>')


def comp(name: str, meaning: str) -> str:
    return (f'<div style="box-sizing: border-box; border: 2px solid {BLUE}; background: {BLUE_T}; '
            f'border-radius: 4px; padding: 8px 12px; display: flex; flex-direction: column">'
            f'<span style="font-family: {MONO}; font-size: 20px; line-height: 26px; '
            f'font-weight: 600; color: {BLUE}">{name}</span>'
            f'<span style="font-size: 18px; line-height: 23px; color: {INK2}">{meaning}</span>'
            f'</div>')


CHEV = (f'<svg aria-hidden="true" width="22" height="40" viewBox="0 0 22 40" fill="none" '
        f'stroke="{INK2}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M5 6 L17 20 L5 34"/></svg>')


def bullet(html: str, size: int = 22, lh: int = 30) -> str:
    return (f'<li style="font-size: {size}px; line-height: {lh}px; color: {INK2}; '
            f'text-wrap: pretty">{html}</li>')


def bullets(items: list[str], size: int = 22, lh: int = 30) -> str:
    return (f'<ul style="margin: 0; padding-left: 26px; display: flex; flex-direction: column; '
            f'gap: 6px">' + "".join(bullet(i, size, lh) for i in items) + "</ul>")


def left_panel() -> str:
    ep = D["median_episode"]
    L11 = D["lead_time"]["T11"]
    day = ep["block"].split("/")[1].replace("day_", "")
    parts = [kicker("Panel 1 of 3 &middot; Problem, question, approach")]

    parts.append(sec(
        h2("01", "A decoder fails quietly"),
        p("An intracortical brain-computer interface turns recorded neural activity into "
          "cursor movement through software called a decoder. Over weeks the recording "
          "changes: electrodes drift and neurons drop out. The decoder keeps producing "
          "confident output from a signal it was not trained on, until it has to be "
          "recalibrated, which is slow and disruptive [4]. Methods exist to correct the "
          "drift. A warning that it has begun, early enough to act on, has no agreed test.")))

    parts.append(sec(
        h2("02", "Two quantities decide whether a warning is usable"),
        '<div style="display: flex; gap: 18px">'
        + tile("Lead time", "Seconds from the first warning to the moment decoding "
               "performance crosses its failure level. Positive means the warning came "
               "first.", INK)
        + tile("False-alarm rate", "Warnings per hour while nothing is wrong. Budget fixed "
               "in advance: 0.1 per hour.", INK)
        + "</div>",
        p("The published state of the art validates a decoder-health monitor by its "
          "correlation with performance, r = 0.93 and 0.72 [1]. Neither quantity above has "
          "been reported for a monitor of this class: both need a recorded moment at which "
          "degradation began, and archived recordings do not contain one.", 23, 32)))

    parts.append(sec(
        h2("03", "Research question"),
        f'<p style="margin: 0; font-family: {SERIF}; font-size: 33px; line-height: 43px; '
        f'font-weight: 400; color: {INK}; text-wrap: pretty">How early, and at what cost in '
        f'false alarms, can a decoder-health monitor warn that a sensor array is degrading? '
        f'Does the correlation-based validation now in use support the claims made from it?</p>'))

    parts.append(sec(
        h2("04", "Hypotheses, frozen before any physical data"),
        claim("Primary: a measurement",
              "For this class of monitor, lead time and false-alarm rate are measurable. "
              "Measured against onsets fixed in advance, with enough fault-free recording to "
              "bound the rate, they fall outside what a deployed system could use.",
              "the median lead time is above zero and the 95% upper bound on the false-alarm "
              "rate is within 0.1 per hour, at the threshold needed for 80% detection."),
        claim("Secondary: a comparison",
              "A monitor can reach the correlation with performance that the field reports as "
              "evidence (r above 0.7) while those two quantities say it is unusable.",
              "r is above 0.7 together with a positive median lead time and a false-alarm "
              "rate within budget. Inconclusive if no correlation measure reaches 0.70."),
        '<div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap">'
        + chip("Preregistration frozen 24 Sep 2026", "frozen")
        + src("commit f4dda04 &middot; physical/docs/09_PREREGISTRATION.md") + "</div>",
        gap=14))

    parts.append(sec(
        C.episode_trace(ep, 1040, 392),
        cap("1", "One archived episode, scored.",
            f"Array T11, day {day}, gain-drift fault. Chosen by rule: the first test episode "
            f"whose lead time equals the median of all {L11['n_detected']} detected faults, so "
            f"it is the typical case and not the best one. Lead time is failure minus warning. "
            f"Detection delay, warning minus onset, is the quantity the physical phase adds, "
            f"measured against an onset sealed before each recording."),
        gap=8))

    grid = ('<div style="flex: 1; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); '
            'gap: 8px">'
            + comp("level", "total activity has moved")
            + comp("silence", "channels have gone quiet")
            + comp("dispersion", "channels drift apart, total unchanged")
            + comp("profile", "shape across channels has changed") + "</div>")
    io = (f'box-sizing: border-box; border: 2px solid {INK}; border-radius: 4px; '
          f'padding: 10px 12px; display: flex; flex-direction: column; justify-content: center; '
          f'font-size: 18px; line-height: 24px; color: {INK2}')
    parts.append(sec(
        h2("05", "The monitor: decoder-guard"),
        '<div style="display: flex; align-items: stretch; gap: 10px">'
        f'<div style="width: 196px; {io}"><b style="font-size: 20px; color: {INK}">384 channels'
        f'</b>log activity in each 30 s window, one window every 5 s</div>'
        f'<div style="display: flex; align-items: center">{CHEV}</div>' + grid +
        f'<div style="display: flex; align-items: center">{CHEV}</div>'
        f'<div style="width: 212px; {io}"><b style="font-size: 20px; color: {INK}">Risk score'
        f'</b>largest component, cause named; warning needs dwell and hysteresis</div></div>',
        cap("2", "Four named components instead of one opaque number.",
            "Source: scripts/22_decoder_guard.py."),
        bullets([
            "Fitted on healthy windows only. It never sees the decoder output, the task, the "
            "performance number or a fault label.",
            "Works in log space: a uniform gain change becomes an additive shift and separates "
            "from a change in shape across channels.",
            "The physical analysis imports this detector and its warning logic unmodified, so "
            "a difference between phases cannot come from a retuned monitor."]),
        gap=12))

    e, c = S["decoder_error_deg"], S["decoder_chance_deg"]
    n = S["episodes"]
    parts.append(sec(
        h2("06", "Computational phase: grading built first"),
        table(["Component", "What was built"], [
            [b("Recordings"), "Pun et al. 2024, public and de-identified [1, 2]. Two implanted "
             "arrays, labelled T11 and T5 by the source researchers. No participants were "
             "recruited for this project."],
            [b("Constructed faults"), f"{n['T11'] + n['T5']:,} episodes ({n['T11']:,} on T11, "
             f"{n['T5']} on T5): four fault types, three rates, three severities. Onsets drawn "
             f"and sealed under SHA-256 before any detector existed."],
            [b("Reference decoder"), f"Ridge regression, fitted once and frozen. Median error "
             f"{e['T11']:.1f}° against {c['T11']:.1f}° measured chance (T11); {e['T5']:.1f}° "
             f"against {c['T5']:.1f}° (T5). Used for grading only."],
            [b("Evaluation harness"), "Lead time and false-alarm rate reported as a pair. Five "
             "gates, silence first. Fit, validation and test split by block; test read once."],
            [b("Earlier phase"), "Early-warning-signal theory [3] under a frozen design: "
             "negative. The indicator rose faster during healthy performance than overall."],
        ], ["24%", "76%"], size=20, lh=27),
        gap=12))

    refs = [
        "[1] Pun, T. K., et al. (2024). Measuring instability in chronic human intracortical "
        "neural recordings toward stable, long-term brain-computer interfaces. "
        "<i>Communications Biology, 7</i>. doi:10.1038/s42003-024-06784-4",
        "[2] Pun, T. K., et al. (2024). Data from [1]. Dryad. doi:10.5061/dryad.n2z34tn5s",
        "[3] Scheffer, M., et al. (2009). Early-warning signals for critical transitions. "
        "<i>Nature, 461</i>, 53&ndash;59.",
        "[4] Swanson, E., et al. (2026). Recalibration of implantable brain-computer "
        "interfaces to enable long-term independent use: a systematic review. "
        "<i>J. Neural Engineering, 23</i>(3).",
    ]
    parts.append(
        f'<section style="display: flex; flex-direction: column; gap: 5px; '
        f'border-top: 1px solid {RULE}; padding-top: 12px; margin-top: auto">'
        + "".join(f'<p style="margin: 0; font-size: 17px; line-height: 23px; color: {INK2}">'
                  f'{r}</p>' for r in refs)
        + f'<p style="margin: 4px 0 0; font-size: 17px; line-height: 23px; color: {INK2}">'
          f'Code, data pipeline and dated research log: '
          f'<span style="font-family: {MONO}">github.com/gnair40/bci-ews-research</span></p>'
          f'</section>')
    return page("Left panel: problem, question, approach", PW_SIDE, PH, "\n".join(parts), 56)


# ===========================================================================
# CENTRE PANEL -- title, the two validations, the signal chain, the figure wall
# ===========================================================================
def status_row(kind_chip: str, text: str) -> str:
    return (f'<div style="display: flex; gap: 14px; align-items: flex-start">'
            f'<div style="width: 218px; flex: none; padding-top: 2px">{kind_chip}</div>'
            f'<span style="font-size: 21px; line-height: 28px; color: {INK2}">{text}</span></div>')


def title_block() -> str:
    key = lambda sw, t: (f'<div style="display: flex; gap: 10px; align-items: center">{sw}'
                         f'<span style="font-size: 18px; line-height: 22px; color: {INK2}">{t}'
                         f'</span></div>')
    sw_m = f'<span style="width: 34px; height: 20px; background: {BLUE}; flex: none"></span>'
    sw_p = (f'<span style="width: 30px; height: 16px; flex: none; border: 2px dashed {ORG}; '
            f'background: repeating-linear-gradient(45deg, {ORG_T}, {ORG_T} 6px, {ORG_M} 6px, '
            f'{ORG_M} 9px)"></span>')
    sw_f = (f'<span style="width: 30px; height: 16px; flex: none; border: 2px dashed {INK3}; '
            f'background: {WASH}"></span>')
    left = (
        '<div style="flex: 1; display: flex; flex-direction: column; gap: 14px">'
        + kicker("Research poster &middot; draft of 12 November 2026 &middot; "
                 "physical results pending")
        + f'<h1 style="margin: 0; font-family: {SERIF}; font-size: 100px; line-height: 1.04; '
          f'font-weight: 700; letter-spacing: -0.012em; color: {INK}">Seeing Failure Before It '
          f'Shows</h1>'
        + f'<p style="margin: 0; font-family: {SERIF}; font-size: 38px; line-height: 47px; '
          f'color: {INK2}; text-wrap: balance">Building and validating a decoder-health monitor '
          f'for neural interfaces, in two phases: on archived intracortical recordings, and on '
          f'a controlled optical apparatus</p>'
        + f'<p style="margin: 6px 0 0; font-size: 26px; line-height: 34px; color: {INK}">'
          f'<b style="font-weight: 600">Gayathri Nair</b> &middot; Central Bucks High School '
          f'South &middot; [CATEGORY] &middot; [FAIR AND YEAR]</p></div>')
    right = (
        f'<div style="width: 800px; flex: none; box-sizing: border-box; border: 2px solid {INK}; '
        f'border-radius: 4px; padding: 14px 20px; display: flex; flex-direction: column; '
        f'gap: 9px">'
        + f'<span style="font-family: {MONO}; font-size: 18px; font-weight: 600; '
          f'letter-spacing: 0.08em; text-transform: uppercase; color: {INK}">Status of the work'
          f'</span>'
        + status_row(chip("Complete", "complete"),
                     "<b style=\"font-weight: 600; color: " + INK + "\">Computational "
                     "validation.</b> Two archived arrays; 102 headline numbers recomputed "
                     "by script.")
        + status_row(chip("Frozen, not built", "frozen"),
                     "<b style=\"font-weight: 600; color: " + INK + "\">Physical validation."
                     "</b> Specified, coded, preregistered 24 Sep 2026. No apparatus exists "
                     "yet.")
        + status_row(chip("None recorded", "none"),
                     "<b style=\"font-weight: 600; color: " + INK + "\">Physical measurements."
                     "</b> Every physical chart here is an empty template.")
        + f'<div style="display: flex; gap: 18px; flex-wrap: wrap; border-top: 1px solid '
          f'{RULE}; padding-top: 9px">'
        + key(sw_m, "measured, from stored data") + key(sw_p, "planned, no data yet")
        + key(sw_f, "photo to be taken") + "</div></div>")
    return (f'<header style="display: flex; gap: 48px; align-items: flex-end">{left}{right}'
            f'</header>')


def compare_fig() -> str:
    n = S["episodes"]
    ff = S["fault_free_episodes"]
    rows = [
        ("Signal source",
         "Archived intracortical recordings from two implanted arrays (T11, T5), binned at "
         "20 ms.",
         "384 screen patches imaged by a camera at 50 frames per second in a sealed enclosure. "
         "One frame stands in for one 20 ms bin."),
        ("Degradation",
         "Injected into the recordings in software: four fault types, three rates, three "
         "severities.",
         "Imposed on the apparatus, optically (ND 0.6 filter, rotation stage) or in software: "
         "four types at severity 0.25, 0.5 and 1.0, plus faults nobody designed (P-5)."),
        ("Onset ground truth",
         f"Drawn and sealed before any detector existed: {n['T11'] + n['T5']:,} episodes.",
         "Drawn by program and sealed with SHA-256 before each recording starts."),
        ("Fault-free record",
         f"{ff['T11']} + {ff['T5']} episodes, about 1.4 h. Too little to bound a rate of 0.1 "
         f"per hour.",
         "101 sessions, about 8.4 h, of which about 4 h are held out. Recorded unattended."),
        ("Produces",
         "AUC by fault type; lead time; false alarms per hour at the operating point; five "
         "gate results; a decision-rate curve.",
         "Lead time and detection delay; false-alarm rate with a 95% bound; detection by type "
         "and severity; silence-gate rate; correlation; decision-rate curve in four "
         "configurations."),
        ("Establishes",
         "The monitor separates faults that activity counting cannot. At the 0.1 per hour "
         "budget no configuration is deployable, and the cause is measured.",
         "Whether the late warning and the restless risk score persist on a non-biological "
         "system with known onsets, and whether the numbers depend on the apparatus."),
        ("Cannot establish",
         "A bounded false-alarm rate. Agreement beyond two arrays, which disagree on several "
         "questions.",
         "Clinical performance. A camera in a sealed box is not an implanted electrode array."),
    ]
    cell = (f'padding: 6px 16px; font-size: 21px; line-height: 27px; color: {INK2}; '
            f'border-bottom: 1px solid {RULE}')
    out = ['<div style="display: grid; grid-template-columns: minmax(0, 1fr) 300px '
           'minmax(0, 1fr); border: 2px solid ' + INK + '; border-radius: 4px; '
           'overflow: hidden">']
    out.append(
        f'<div style="padding: 14px 16px; background: {BLUE}; display: flex; '
        f'align-items: center; justify-content: space-between; gap: 12px">'
        f'<span style="font-family: {SERIF}; font-size: 32px; font-weight: 600; '
        f'color: #FFFFFF">Computational validation</span>'
        f'<span style="font-family: {MONO}; font-size: 17px; font-weight: 600; '
        f'letter-spacing: 0.06em; color: #FFFFFF">COMPLETE</span></div>'
        f'<div style="padding: 10px 12px; background: {INK}; display: flex; '
        f'align-items: center; justify-content: center; text-align: center; '
        f'font-family: {MONO}; font-size: 17px; line-height: 22px; font-weight: 600; '
        f'letter-spacing: 0.06em; color: #FFFFFF">ONE MONITOR, UNCHANGED</div>'
        f'<div style="padding: 14px 16px; background: {ORG}; display: flex; '
        f'align-items: center; justify-content: space-between; gap: 12px">'
        f'<span style="font-family: {SERIF}; font-size: 32px; font-weight: 600; '
        f'color: #FFFFFF">Physical validation</span>'
        f'<span style="font-family: {MONO}; font-size: 17px; font-weight: 600; '
        f'letter-spacing: 0.06em; color: #FFFFFF">PREREGISTERED, NOT EXECUTED</span></div>')
    for i, (lab, a, c) in enumerate(rows):
        last = "border-bottom: none; " if i == len(rows) - 1 else ""
        out.append(
            f'<div style="{cell}; {last}background: #FFFFFF">{a}</div>'
            f'<div style="{cell}; {last}background: {WASH}; text-align: center; '
            f'font-weight: 600; color: {INK}; display: flex; align-items: center; '
            f'justify-content: center; border-left: 1px solid {RULE}; '
            f'border-right: 1px solid {RULE}">{lab}</div>'
            f'<div style="{cell}; {last}background: #FFFFFF">{c}</div>')
    out.append("</div>")
    shared = (
        f'<div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; '
        f'font-size: 20px; line-height: 26px; color: {INK2}">'
        f'<b style="font-weight: 600; color: {INK}">Held identical in both phases:</b>'
        + "".join(f'<span style="border: 1.5px solid {INK3}; border-radius: 4px; '
                  f'padding: 2px 10px; white-space: nowrap">{t}</span>' for t in (
                      "decoder-guard monitor", "30 s window, 5 s step",
                      "warning state machine", "0.1 per hour budget",
                      "frozen ridge decoder", "lead time and false alarms as a pair"))
        + "</div>")
    open_q = (
        f'<div style="display: grid; grid-template-columns: 250px repeat(3, minmax(0, 1fr)); '
        f'gap: 0; border: 2px solid {INK}; border-radius: 4px; overflow: hidden">'
        f'<div style="background: {INK}; color: #FFFFFF; padding: 12px 16px; font-family: '
        f'{SERIF}; font-size: 25px; line-height: 30px; font-weight: 600; display: flex; '
        f'align-items: center">Open until both are read together</div>'
        + "".join(
            f'<div style="padding: 10px 16px; font-size: 21px; line-height: 28px; '
            f'color: {INK2}; border-left: 1px solid {RULE}">{t}</div>' for t in (
                "Whether the late warning belongs to neural recordings or to the monitoring "
                "method itself " + src("PP-2, PP-3"),
                "How large the false-alarm rate is once enough fault-free recording exists "
                "to bound it " + src("PP-1"),
                "Whether deciding less often helps: on archived data T11 rises and T5 falls "
                + src("PP-7, PP-9")))
        + "</div>")
    return sec(
        "".join(out), shared, open_q,
        cap("3", "Two validations of one monitor.",
            "Each phase supplies what the other cannot. Left column from reports/ and "
            "data/processed/; right column from the frozen preregistration."),
        gap=12)


def grid_thumb() -> str:
    cells = "".join(
        f'<rect x="{c * 4 + 0.5}" y="{r * 4 + 0.5}" width="3" height="3" fill="{ORG_M}"/>'
        for r in range(16) for c in range(24))
    return (f'<svg aria-hidden="true" width="96" height="64" viewBox="0 0 96 64" '
            f'style="position: absolute; left: 309px; top: 166px; width: 96px; height: 64px; '
            f'background: #FFFFFF; border: 1.5px solid {ORG}">{cells}</svg>')


def chain_fig() -> str:
    y1, hh = 40, 120
    xs = [0, 253, 506, 759, 1012, 1265, 1518, 1771, 2006]
    ws = [208, 208, 208, 208, 208, 208, 208, 190, 170]
    cards = [
        ("stimulus.py", "24 × 16 patch grid, modulation depth 0.00211", "soft", True),
        ("Display", "384 independent patches, fixed manual brightness", "phys", False),
        ("Sealed enclosure", "matte black, light-tight optical path", "phys", False),
        ("Camera", "50 frames per second, exposure and gain fixed", "phys", False),
        ("capture.py", "frames and timestamps, raw files never modified", "soft", True),
        ("Frozen decoder", "ridge, fitted once on fault-free sessions", "soft", False),
        ("monitor.py", "30 s window every 5 s, one risk score each", "soft", True),
        ("Threshold", "fixed on held-out fault-free sessions", "fixed", False),
        ("Warning", "time of first warning", "out", False),
    ]
    el = []
    # arrows first, then cards, then labels (paint order = click order)
    for i in range(len(xs) - 1):
        el.append(arrow(xs[i] + ws[i], y1 + hh // 2, xs[i + 1] - 1, y1 + hh // 2))
    y2, h2_ = 236, 100
    el.append(arrow(300, y2 + h2_ // 2, 399, y2 + h2_ // 2, TEAL))            # plan -> fault
    el.append(arrow(610, y2, 610, y1 + hh + 1, WINE))                           # optical fault
    el.append(arrow(1116, y2, 1116, y1 + hh + 1, WINE))                         # software fault
    el.append(arrow(1180, y2 + h2_ // 2, 1264, y2 + h2_ // 2, WINE))            # onset -> score
    el.append(arrow(1369, y1 + hh, 1369, y2 - 1))                               # failure time
    el.append(arrow(2091, y1 + hh, 2091, y2 - 1))                               # warning time
    for (t, l, k, m), x, w in zip(cards, xs, ws):
        el.append(card(x, y1, w, hh, t, l, k, mono=m, tsize=21 if m else 22))
    el.append(card(0, y2, 300, h2_, "draw_onset.py",
                   "onset, type and severity drawn, then sealed with SHA-256", "seal", True, 21))
    el.append(card(400, y2, 780, h2_, "Fault imposed at the sealed onset",
                   "optical: ND 0.6 filter, rotation stage (acts on the light path)<br>"
                   "software: gain drift, channel dropout (acts on recorded frames)", "fault"))
    el.append(card(1265, y2, 911, h2_, "Scoring against the sealed onset",
                   "lead time = failure time − warning time (positive: the warning came first)"
                   "<br>detection delay = warning time − sealed onset", "fixed"))
    el.append(grid_thumb())
    el.append(note(412, 176, 96, "24 × 16<br>= 384", "left", ORG))
    el.append(note(306, y2 + 20, 90, "plan", "center", TEAL))
    el.append(note(622, 186, 130, "light path", "left", WINE))
    el.append(note(1128, 186, 130, "frames", "left", WINE))
    el.append(note(1180, y2 + 20, 86, "onset", "center", WINE))
    el.append(note(1381, 176, 380, "failure time: decoding error crosses<br>its failure level",
                   "left"))
    el.append(note(1890, 186, 190, "warning time", "right"))
    el.append(note(759, 8, 208, "1 frame = one 20 ms bin", "center", ORG))
    el.append(note(1448, 8, 348, "same code as the neural analysis", "center", BLUE))
    host = (f'<div style="position: relative; width: 2192px; height: 340px">'
            + "".join(el) + "</div>")
    legend = (
        '<div style="display: flex; gap: 26px; flex-wrap: wrap; align-items: center">'
        + "".join(
            f'<div style="display: flex; gap: 8px; align-items: center">'
            f'<span style="width: 26px; height: 18px; flex: none; {st}"></span>'
            f'<span style="font-size: 18px; line-height: 22px; color: {INK2}">{t}</span></div>'
            for st, t in (
                (f"background: {BLUE_T}; border: 2px solid {BLUE}", "software process"),
                (f"background: {ORG_T}; border: 2px solid {ORG}", "physical component"),
                (f"background: {TEAL_T}; border: 2px solid {TEAL}", "sealed before recording"),
                (f"background: {WINE_T}; border: 2px solid {WINE}", "imposed fault"),
                (f"background: #FFFFFF; border: 2px solid {INK}", "fixed rule or constant")))
        + "</div>")
    return sec(
        host, legend,
        cap("4", "Signal chain of the apparatus.",
            "A known direction is encoded across 384 patches, imaged, decoded by a decoder "
            "that is never refitted, and watched by the monitor. The fault path degrades the "
            "signal, and its sealed onset is the ground truth each warning is scored "
            "against. Specified, not yet built."),
        gap=10)


def stat(big: str, text: str, ref: str) -> str:
    return (f'<div style="box-sizing: border-box; border-top: 4px solid {BLUE}; '
            f'padding: 10px 0 0; display: flex; flex-direction: column; gap: 4px">'
            f'<span style="font-family: {SERIF}; font-size: 50px; line-height: 54px; '
            f'font-weight: 700; color: {BLUE}; white-space: nowrap">{big}</span>'
            f'<span style="font-size: 20px; line-height: 27px; color: {INK2}">{text}</span>'
            f'<span style="font-family: {MONO}; font-size: 15px; color: {INK3}">{ref}</span>'
            f'</div>')


def stat_strip() -> str:
    v = D["fault_mode_auc"]["values"]
    g = [v[a]["decoder_guard"][i] for a in ("T11", "T5") for i in (2, 3)]
    k = [v[a]["mean_activity"][i] for a in ("T11", "T5") for i in (2, 3)]
    f = S["funnel"]
    sep = S["task_change_separation"]
    sc = D["session_scatter"]
    tiles = [
        stat(f"{min(g):.2f} to {max(g):.2f}",
             f"AUC on the two faults that leave total activity unchanged. Counting activity "
             f"scores {min(k):.2f} to {max(k):.2f}.", "claim C02, C15"),
        stat(f"{sep['658']:.1f}× and {sep['665']:.0f}×",
             "separation between a change of task and a real fault, on two days. A task "
             "change is not mistaken for a fault.", "claim C05"),
        stat(f"{f['all_gates']} of {f['run']}",
             f"configurations pass all five gates. {f['positive_lead']} reach a positive "
             f"median lead time; {f['met_budget']} meet the budget; none stays silent.",
             "claim C03"),
        stat(f"{S['lag1_pooled']['T11']:.3f}",
             f"lag-1 autocorrelation of the risk score within a faulted session (T11; "
             f"{S['lag1_pooled']['T5']:.3f} on T5): about one independent measurement.",
             "claim C04, C18"),
        stat(f"{S['auc_needed_at_budget']['T11']:.3f}",
             f"session AUC needed at one decision per session inside the budget (T11; "
             f"{S['auc_needed_at_budget']['T5']:.3f} on T5). Achieved: "
             f"{S['auc_session']['T11']:.3f} and {S['auc_session']['T5']:.3f}.",
             "reports/OPERATING_POINT_BOUND.md"),
        stat(f"{sc['auc_min']:.2f} to {sc['auc_max']:.2f}",
             f"monitor AUC by session across {sc['n_sessions']} sessions of T11, tracking "
             f"that day's decoder error (ρ = {num(sc['spearman_rho'], 3)}, preregistered).",
             "claim C08, C09"),
    ]
    return sec(
        f'<div style="display: flex; align-items: baseline; gap: 16px; border-top: 3px solid '
        f'{INK}; padding-top: 12px"><h2 style="margin: 0; font-family: {SERIF}; '
        f'font-size: 42px; line-height: 1.12; font-weight: 600; color: {INK}">Computational '
        f'findings, each recomputed from stored results</h2></div>',
        '<div style="display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); '
        'gap: 26px">' + "".join(tiles) + "</div>", gap=14)


def pair(n: str, title: str, dv: str, m_svg: str, m_note: str, p_svg: str, p_note: str) -> str:
    def side(label_chip: str, where: str, svg_: str, note_: str, edge: str) -> str:
        return (f'<div style="flex: 1; min-width: 0; display: flex; flex-direction: column; '
                f'gap: 6px; border-top: {edge}; padding-top: 8px">'
                f'<div style="display: flex; gap: 10px; align-items: center">{label_chip}'
                f'<span style="font-size: 17px; line-height: 22px; color: {INK2}">{where}'
                f'</span></div>{svg_}'
                f'<p style="margin: 0; font-size: 18px; line-height: 23px; color: {INK2}; '
                f'text-wrap: pretty">{note_}</p></div>')
    return (
        f'<div style="box-sizing: border-box; border: 1.5px solid {RULE}; border-radius: 4px; '
        f'padding: 10px 18px 12px; display: flex; flex-direction: column; gap: 6px">'
        f'<div style="display: flex; align-items: baseline; justify-content: space-between; '
        f'gap: 12px"><h3 style="margin: 0; font-family: {SERIF}; font-size: 30px; '
        f'line-height: 36px; font-weight: 600; color: {INK}">Fig. {n}. {title}</h3>'
        f'<span style="font-family: {MONO}; font-size: 16px; color: {INK3}; '
        f'white-space: nowrap">{dv}</span></div>'
        f'<div style="display: flex; gap: 28px">'
        + side(chip("Measured", "measured"), "archived neural recordings", m_svg, m_note,
               f"4px solid {BLUE}")
        + side(chip("Planned", "planned"), "optical apparatus", p_svg, p_note,
               f"4px dashed {ORG}")
        + "</div></div>")


NAMES = {"RATE_LOSS": ("Overall signal loss", "total activity falls"),
         "CHANNEL_DROPOUT": ("Channel dropout", "channels go silent"),
         "GAIN_DRIFT": ("Gain drift", "total unchanged"),
         "GEOMETRY_ROTATION": ("Geometric rotation", "total unchanged")}


def wall() -> str:
    W, H = 500, 296
    L11, L5 = D["lead_time"]["T11"], D["lead_time"]["T5"]
    ci = L11["ci95_s"]
    dvf = D["detection_vs_fa"]
    sl = S["session_level_correlation_T11"]
    pr = D["decision_rate"]["paired"]["participants"]
    a, t5 = pr["T11"]["own_range"], pr["T5"]["own_range"]
    pct = lambda x: minus(f"{x * 100:+.1f}")
    cards = [
        pair("5", "Lead time", "DV1 &middot; P-3",
             C.lead_dots(W, H, L11["leads_s"], L11["median_s"]),
             f"T11: {L11['n_detected']} of {L11['n_degraded']} faults detected. Median "
             f"{num(L11['median_s'], 0)} s (95% CI {num(ci[0], 0)} to {num(ci[1], 0)}); "
             f"{L11['fraction_negative'] * 100:.0f}% warned late, "
             f"{L11['fraction_positive'] * 100:.0f}% early. T5: {L5['n_detected']} of "
             f"{L5['n_degraded']}, median {num(L5['median_s'], 0)} s.",
             C.lead_planned(W, H, "lead"),
             "PP-3 predicts a median at or below 0 s; falsified by a positive median whose "
             "95% interval excludes zero. Detection delay is reported beside it."),
        pair("6", "False alarms and silence", "DV2, DV4 &middot; P-2",
             C.fa_measured(W, H, S["false_alarms_per_hour"], S["budget_per_hour"],
                           S["silence_fault_free_fraction"], S["fault_free_episodes"]),
             f"Rates at the operating point chosen on validation data. Only "
             f"{S['fault_free_episodes']['T11']} + {S['fault_free_episodes']['T5']} episodes, "
             f"about 1.4 h, are genuinely fault-free.",
             C.fa_planned(W, H, "fa"),
             "PP-1: rate above 0.1 per hour. PP-2: over 10% of fault-free sessions trend. "
             "The curve is arithmetic (3 ÷ hours), not data: zero alarms would be reported as "
             "untested, not as a pass."),
        pair("7", "Detection against false alarms", "DV3 &middot; P-2, P-3",
             C.dfa_measured(W, H, dvf["curves"], {"T11": dvf["best_inside_budget_T11"],
                                                  "T5": dvf["best_inside_budget_T5"]}),
             "The warning threshold swept over its whole range. Detection is high only where "
             "false alarms run at several per hour.",
             C.dfa_planned(W, H, "dfa"),
             "Same axes. The curve is read at the budget line: a usable monitor reaches the "
             "80% target to the left of it."),
        pair("8", "Detection by fault type and severity", "DV3 &middot; IV3, IV4",
             C.mode_dumbbell(W, H, D["fault_mode_auc"]["values"], D["fault_mode_auc"]["modes"],
                             NAMES),
             "The monitor wins on the two faults that conserve total activity and loses on "
             "overall signal loss, on both arrays. Descriptive: no interval is attached.",
             C.severity_planned(W, H, "sev", ["Overall signal loss", "Channel dropout",
                                             "Per-channel gain drift", "Geometric rotation"]),
             "PP-6: detection at severity 1.0 exceeds detection at 0.25. If not, PP-1 to "
             "PP-5 are reported but not read as being about degradation."),
        pair("9", "Monitor score against decoding performance", "DV5 &middot; P-4",
             C.scatter_measured(W, H, sl["series"], sl["failure_threshold_deg"]),
             f"{sl['n_sessions']} sessions of T11. Spearman ρ: raw {num(sl['raw'], 3)}; time "
             f"trend removed {num(sl['partial'], 3)}; first differences {num(sl['diff'], 3)}. "
             f"Exploratory, not preregistered.",
             C.scatter_planned(W, H, "sc"),
             "PP-4: at least one of the three measures reaches 0.70 in magnitude. PP-5: raw "
             "exceeds partial. Published for comparison: 0.93 and 0.72 [1]."),
        pair("10", "How often the monitor decides", "P-6 &middot; co-primary",
             C.decision_measured(W, H, D["decision_rate"]["curves"]),
             f"At a 10% false-flag rate, paired test. T11: {pct(a['change'])} points (95% CI "
             f"{pct(a['ci95'][0])} to {pct(a['ci95'][1])}; not established). T5: "
             f"{pct(t5['change'])} points ({pct(t5['ci95'][0])} to {pct(t5['ci95'][1])}; "
             f"established).",
             C.decision_planned(W, H, "dr"),
             "PP-7: at least +10 points at one decision per session. PP-9: the same sign in "
             "all four configurations. Re-scored from the same recordings."),
    ]
    head = (
        f'<div style="display: flex; align-items: baseline; gap: 16px; border-top: 3px solid '
        f'{INK}; padding-top: 12px"><h2 style="margin: 0; font-family: {SERIF}; '
        f'font-size: 42px; line-height: 1.12; font-weight: 600; color: {INK}">The same six '
        f'quantities, measured and to be measured</h2></div>'
        )
    return sec(head,
               '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); '
               'gap: 20px">' + "".join(cards) + "</div>", gap=12)


def main_panel() -> str:
    return page("Centre panel: architecture and evidence", PW_MAIN, PH,
                "\n".join([title_block(), compare_fig(), chain_fig(), stat_strip(), wall()]),
                56)


# ===========================================================================
# RIGHT PANEL -- the physical validation: apparatus, protocol, gates, design
# ===========================================================================
def apparatus_svg() -> str:
    T, Ln, R = C.T, C.L, C.R
    W, H = 1040, 350
    s = []
    s.append(T(40, 22, "Sealed enclosure: cardboard, at least 40 × 30 × 30 cm", 19, INK,
               weight=600))
    s.append(T(40, 44, "matte black lining, taped seams, darkness verified by measurement "
               "(gate G-a)", 17, INK2))
    # enclosure: outline plus an inner band for the matte lining (little ink, reads as a box)
    s.append(R(40, 56, 760, 236, fill="#FFFFFF", stroke=INK, sw=3))
    s.append(R(48, 64, 744, 220, fill="none", stroke="#39424B", sw=8))
    # light path
    s.append(f'<path d="M92 104 L632 177 L92 250 Z" fill="{ORG_T}" stroke="{ORG_M}" '
             f'stroke-width="2" stroke-dasharray="8 6"/>')
    # display
    s.append(R(70, 100, 22, 154, fill=ORG_T, stroke=ORG, sw=3))
    for i in range(1, 8):
        s.append(Ln(92, 100 + i * 19.25, 86, 100 + i * 19.25, ORG, 1.5))
    s.append(T(110, 94, "Display", 19, ORG, weight=600))
    s.append(T(184, 94, "384 patches (24 × 16), brightness fixed", 17, INK2))
    # filter
    s.append(R(556, 126, 8, 102, fill=WINE_T, stroke=WINE, sw=2.5, dash="6 4"))
    s.append(T(548, 252, "ND 0.6 gel filter slides into the light path:", 17, WINE,
               anchor="end"))
    s.append(T(548, 273, "optical signal-loss fault", 17, WINE, anchor="end", weight=600))
    # camera on its stage
    s.append(R(640, 159, 40, 36, fill=ORG_T, stroke=ORG, sw=3, rx=3))
    s.append(R(630, 169, 10, 16, fill=ORG, stroke=ORG, sw=1))
    s.append(Ln(660, 195, 660, 246, INK, 4))
    s.append(R(626, 246, 68, 12, fill=WINE_T, stroke=WINE, sw=2.5, rx=2))
    s.append(T(784, 94, "Camera Module 3", 19, ORG, anchor="end", weight=600))
    s.append(T(784, 116, "50 fps, fixed exposure", 17, INK2, anchor="end"))
    s.append(T(704, 240, "rotation", 17, WINE))
    s.append(T(704, 260, "stage", 17, WINE))
    # cable aperture and computer
    s.append(R(795, 168, 10, 18, fill="#FFFFFF", stroke=INK, sw=1.5))
    s.append(Ln(680, 177, 850, 177, BLUE, 3))
    s.append(T(740, 168, "ribbon", 17, BLUE, anchor="middle"))
    s.append(T(812, 104, "taped cable", 17, INK2))
    s.append(T(812, 124, "aperture", 17, INK2))
    s.append(Ln(826, 130, 804, 164, INK2, 1.5))
    s.append(R(850, 138, 182, 84, fill=BLUE_T, stroke=BLUE, sw=3, rx=4))
    s.append(T(941, 164, "Raspberry Pi 4", 19, BLUE, anchor="middle", weight=600))
    s.append(T(941, 186, "stimulus.py", 17, INK2, anchor="middle", family=C.MONO))
    s.append(T(941, 208, "capture.py", 17, INK2, anchor="middle", family=C.MONO))
    s.append(Ln(980, 222, 980, 244, INK2, 2))
    s.append(R(850, 244, 182, 50, fill="#FFFFFF", stroke=INK2, sw=2, rx=4))
    s.append(T(941, 265, "DHT22 sensor", 18, INK, anchor="middle", weight=600))
    s.append(T(941, 285, "room temperature", 17, INK2, anchor="middle"))
    # HDMI
    s.append(f'<path d="M850 200 L826 200 L826 316 L81 316 L81 254" fill="none" '
             f'stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>')
    s.append(T(450, 340, "HDMI: the computer draws the patch grid on the display", 17, BLUE,
               anchor="middle"))
    return C.svg(W, H, s, "Side view of the apparatus. A display at one end of a sealed "
                 "matte black enclosure faces a camera at the other. A neutral density filter "
                 "can slide into the light path, and the camera sits on a rotation stage. A "
                 "Raspberry Pi outside drives the display and reads the camera.")


def step(n: str, title: str, text: str, status: str, kind: str) -> str:
    return (f'<div style="box-sizing: border-box; border: 1.5px solid {RULE}; '
            f'border-radius: 4px; padding: 10px 12px; display: flex; flex-direction: column; '
            f'gap: 4px"><div style="display: flex; gap: 8px; align-items: baseline">'
            f'<span style="font-family: {MONO}; font-size: 22px; font-weight: 600; '
            f'color: {INK}">{n}</span>'
            f'<span style="font-size: 20px; line-height: 25px; font-weight: 600; color: {INK}">'
            f'{title}</span></div>'
            f'<span style="font-size: 17px; line-height: 22px; color: {INK2}; flex: 1">{text}'
            f'</span><div>{chip(status, kind)}</div></div>')


def var_list(title: str, color: str, items: list[tuple[str, str]]) -> str:
    rows = "".join(
        f'<div style="display: flex; gap: 10px; align-items: baseline; padding: 5px 0; '
        f'border-bottom: 1px solid {RULE}"><span style="font-family: {MONO}; font-size: 17px; '
        f'font-weight: 600; color: {INK}; width: 44px; flex: none">{k}</span>'
        f'<span style="font-size: 19px; line-height: 25px; color: {INK2}">{v}</span></div>'
        for k, v in items)
    return (f'<div style="flex: 1; min-width: 0; display: flex; flex-direction: column">'
            f'<div style="font-size: 20px; line-height: 26px; font-weight: 600; color: {color}; '
            f'border-bottom: 2px solid {INK}; padding-bottom: 4px">{title}</div>{rows}</div>')


BLANK = (f'<span style="display: inline-block; width: 100%; height: 24px; box-sizing: '
         f'border-box; border-bottom: 2px dashed {ORG}"></span>')
BOXES = (f'<span style="display: inline-flex; gap: 8px; align-items: center; font-size: 17px; '
         f'color: {INK2}; white-space: nowrap"><span style="width: 18px; height: 18px; '
         f'box-sizing: border-box; border: 2px solid {INK}"></span>pass'
         f'<span style="width: 18px; height: 18px; box-sizing: border-box; border: 2px solid '
         f'{INK}; margin-left: 6px"></span>fail</span>')


def right_panel() -> str:
    parts = [kicker("Panel 3 of 3 &middot; Physical validation: design and protocol")]

    photos = ('<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); '
              'gap: 10px">'
              + photo(1, "Assembled enclosure, lid sealed", 106)
              + photo(2, "Raspberry Pi 4 and Camera Module 3", 106)
              + photo(3, "Interior: lining, display, camera mount", 106)
              + photo(4, "Patch grid as the camera sees it", 106)
              + photo(5, "Bench check B-2: dark frame", 106)
              + photo(6, "Unattended overnight recording", 106) + "</div>")
    parts.append(sec(
        h2("07", "A sealed optical loop with a known input", 38),
        p("Archived recordings supply neither a recorded onset nor enough fault-free hours. "
          "An apparatus does: failures start at sealed moments and it records unattended. No "
          "person is measured.", 21, 28),
        apparatus_svg(),
        cap("11", "Apparatus, side view, as specified.",
            "Nothing shown has been built. Computer placement and display-to-camera distance "
            "are not fixed by the repository."),
        photos, gap=10))

    steps = ('<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); '
             'gap: 8px">'
             + step("0", "Software check", "self-test and dry run on synthetic input",
                    "Rehearsed", "measured")
             + step("1", "Procure", "four critical parts, about 110 USD", "Not started",
                    "planned")
             + step("2", "Computer", "card, libraries, camera ribbon, wiring",
                    "Not started", "planned")
             + step("3", "Enclosure", "lining, display, camera mount, seal",
                    "Not started", "planned")
             + step("4", "Checks and gates", "B-0 to B-7, G-a to G-e; halt if G-e fails",
                    "Not started", "planned")
             + step("5", "Preregister", "predictions and sample sizes frozen",
                    "Done 24 Sep 2026", "frozen")
             + step("6", "Record", "seal each plan first; 337 sessions, about 28 h",
                    "Not started", "planned")
             + step("7", "Analyse", "three disjoint groups, fixed criteria",
                    "Not started", "planned")
             + "</div>")
    parts.append(sec(
        h2("08", "Protocol: the order is enforced by the programs", 38),
        steps,
        cap("12", "Experimental workflow.",
            "run_session.py refuses to record a session that has no sealed plan."),
        gap=10))

    gates = table(
        ["Gate", "Must hold before any experiment is read", "Check", "Measured", "Result"],
        [[b("G-a"), "light-tight: mean pixel below 2, maximum below 5 (of 255)",
          src("darkframe"), BLANK, BOXES],
         [b("G-b"), "intact: under 1% late frames, 5% dead channels, 1% clipped",
          src("frames"), BLANK, BOXES],
         [b("G-c"), "display-to-camera delay agrees across three recordings",
          src("lag"), BLANK, BOXES],
         [b("G-d"), "sub-level signal survives: over 0.02, on over 80% of channels",
          src("dither"), BLANK, BOXES],
         [b("G-e"), "decoding margin within 6° of 36.1° (neural: 90.7° − 54.6°)",
          src("margin"), BLANK, BOXES]],
        ["7%", "55%", "11%", "11%", "16%"], size=19, lh=25, pad="6px 8px")
    parts.append(sec(
        h2("09", "Acceptance gates: no result is read before these pass", 38),
        p("On an apparatus that is too easy, a monitor has nothing to detect. Modulation "
          "depth is tuned until the decoder is as far above chance as the neural decoder was; "
          "if it cannot be, the phase stops.", 20, 27),
        gates, gap=10))

    parts.append(sec(
        h2("10", "Variables", 38),
        '<div style="display: flex; gap: 22px">'
        + var_list("Changed (independent)", ORG, [
            ("IV1", "onset time: drawn at random, sealed"),
            ("IV2", "degradation present or absent"),
            ("IV3", "type: signal loss, dropout, gain drift, rotation"),
            ("IV4", "severity: 0, 0.25, 0.5, 1.0"),
            ("IV5", "decision rate: 720 per hour to 1 per session")])
        + var_list("Measured (dependent)", ORG, [
            ("DV1", "lead time (s)"),
            ("DV2", "false alarms per fault-free hour"),
            ("DV3", "detection rate at a stated false-alarm rate"),
            ("DV4", "silence-gate pass rate"),
            ("DV5", "correlation with performance, raw and detrended")])
        + "</div>",
        p(b("Held fixed:") + " 30 s window and 5 s step; ridge decoder fitted once; camera "
          "exposure and gain; screen brightness; modulation depth after calibration; ambient "
          "light (sealed and verified); camera position.", 19, 26),
        gap=10))

    exps = table(
        ["", "Measures", "Sessions", "Recording"],
        [[b("P-1"), "calibration: the difficulty match (gate G-e)", "5 or more", "25 min"],
         [b("P-2"), "false-alarm rate and silence, fault-free sessions", "101", "8.4 h"],
         [b("P-3"), "lead time and detection from a sealed onset", "101", "8.4 h"],
         [b("P-4"), "correlation against usability", "0", "analysis"],
         [b("P-5"), "faults nobody designed, imposed by hand", "10", "50 min"],
         [b("P-6"), "decision-rate curve, re-scored from P-2 and P-3", "0", "analysis"],
         [b("P-7"), "three more configurations: exposure, patch size, 96 channels", "120",
          "about 10 h"],
         [b("All"), b("planned; none recorded"), b("337"), b("about 28 h")]],
        ["9%", "55%", "17%", "19%"], size=19, lh=25, pad="5px 8px")
    parts.append(sec(
        h2("11", "Seven experiments, sizes frozen in advance", 38),
        exps,
        C.configs_planned(1040, 184, "cfg"),
        cap("13", "Apparatus configurations (P-7), planned.",
            "PP-10: lead time differs by over 10 s, or false alarms by over twofold."),
        gap=10))

    parts.append(sec(
        h2("12", "Limits of inference, stated in advance", 38),
        bullets([
            "A camera in a sealed box is not an implanted array. A false-alarm rate measured "
            "here is not an estimate of the clinical rate.",
            "Matching the decoding margin makes the problem comparably hard. It does not make "
            "the noise, the drift mechanism or the failure modes comparable.",
            "One apparatus, one room, one family of monitor. P-7 narrows that objection and "
            "does not close it. The computational results rest on two arrays that disagree."],
            20, 27),
        gap=10))

    L11, L5 = D["lead_time"]["T11"], D["lead_time"]["T5"]
    f = S["funnel"]
    field = (f'<span style="display: inline-block; width: 120px; height: 22px; box-sizing: '
             f'border-box; border-bottom: 2px dashed {ORG}; vertical-align: baseline"></span>')
    box = (f'<span style="display: inline-block; width: 18px; height: 18px; box-sizing: '
           f'border-box; border: 2px solid {INK}; vertical-align: -2px; margin-right: 6px">'
           f'</span>')
    parts.append(sec(
        h2("13", "Conclusions", 38),
        f'<div style="box-sizing: border-box; border-top: 4px solid {BLUE}; padding-top: 8px; '
        f'display: flex; flex-direction: column; gap: 6px">'
        + f'<div>{chip("Computational: established", "measured")}</div>'
        + p(f"The monitor detects faults that counting activity cannot and does not mistake a "
            f"task change for a fault. It is not deployable at the budget: {f['all_gates']} of "
            f"{f['run']} configurations pass, the median warning arrives "
            f"{abs(L11['median_s']):.0f} s (T11) and {abs(L5['median_s']):.0f} s (T5) after "
            f"the failure, and the risk score is never quiet within a session.",
            20, 27, INK)
        + "</div>"
        f'<div style="box-sizing: border-box; border: 2px dashed {ORG}; border-radius: 4px; '
        f'padding: 10px 14px; display: flex; flex-direction: column; gap: 8px; '
        f'margin-top: 4px">'
        + f'<div>{chip("Physical: to be written after analysis", "planned")}</div>'
        + f'<p style="margin: 0; font-size: 20px; line-height: 32px; color: {INK2}">Median '
          f'lead time {field} s (95% CI {field}). False-alarm rate {field} per hour (95% '
          f'upper bound {field}). Strongest correlation {field}.</p>'
        + f'<p style="margin: 0; font-size: 20px; line-height: 28px; color: {INK2}">'
          f'Preregistered verdict: &nbsp;{box}supported &nbsp;&nbsp;{box}falsified '
          f'&nbsp;&nbsp;{box}inconclusive &nbsp;&nbsp;{box}halted at gate G-e</p>'
        + "</div>",
        gap=8))
    return page("Right panel: physical validation design", PW_SIDE, PH, "\n".join(parts), 56,
                gap=20)


# ===========================================================================
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    boards = {
        "Main.dc.html": {"x": PW_SIDE + 80, "y": 0, "w": PW_MAIN, "h": PH,
                         "title": "Centre panel, 24 x 36 in"},
        "Left.dc.html": {"x": 0, "y": 0, "w": PW_SIDE, "h": PH,
                         "title": "Left panel, 12 x 36 in"},
        "Right.dc.html": {"x": PW_SIDE + 80 + PW_MAIN + 80, "y": 0, "w": PW_SIDE, "h": PH,
                          "title": "Right panel, 12 x 36 in"},
    }
    index_path = OUT / "canvas.json"
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if index_path.exists():          # keep the creation stamp across rebuilds
        created = json.loads(index_path.read_text())["createdOnFiles"]["at"]
    index = {
        "v": 3,
        "createdOnFiles": {"v": 1, "at": created},
        "title": "Decoder-Health Monitor Trifold Poster",
        "launch": {"view": "canvas"},
        "pages": [],
        "boards": boards,
        "order": ["Main.dc.html", "Left.dc.html", "Right.dc.html"],
        "notes": {
            "board": {"x": 0, "y": -300, "kind": "title1", "maxW": 4768,
                      "text": "Trifold, 48 x 36 in: left 12 in, centre 24 in, right 12 in"},
        },
        "designSystems": [],
    }
    index_path.write_text(json.dumps(index, indent=1))
    for name, fn in (("Main.dc.html", main_panel), ("Left.dc.html", left_panel),
                     ("Right.dc.html", right_panel)):
        html = fn()
        markup = html[html.index("<x-dc>"):html.index("</x-dc>")]
        if "{{" in markup or "}}" in markup:
            raise SystemExit(f"{name}: a doubled brace would be read as a template hole")
        if "—" in html:
            raise SystemExit(f"{name}: contains an em dash")
        (OUT / name).write_text(html)
        print(f"wrote {(OUT / name).relative_to(HERE.parent)}  ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
