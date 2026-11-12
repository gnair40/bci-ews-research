#!/usr/bin/env python3
"""
build_draft2.py -- Draft 2 of the trifold: the "project in one minute" design.

    python3 poster/build_poster_data.py     # recompute and check every number
    python3 poster/build_draft2.py          # write Main, Left and Right .dc.html

The canvas now holds three drafts on three pages. This file builds Draft 2 and
also supplies the shared components that build_draft3.py imports. The canvas
index, canvas/project/canvas.json, is not written here: pages and positions are
arranged on the canvas itself.

THE BOARD
---------
A standard 48 x 36 inch trifold, at 96 px per inch:

    Left.dc.html     12 x 36 in   abstract, introduction, why it matters,
                                  purpose, hypothesis, engineering goal
    Main.dc.html     24 x 36 in   title, the project in four steps, how the
                                  test bench works, pictures, hardware, code
    Right.dc.html    12 x 36 in   methods compared, results and data, analysis,
                                  discussion, conclusion

THE ONE RULE ABOUT SIZE
-----------------------
Nothing on the board is smaller than 24 pt, which is 32 px here. That includes
axis numbers, captions and labels inside diagrams. `MIN` below is that floor,
and the render check in poster/README.md measures every piece of text against
it. Charts are drawn in source units and enlarged by charts.SCALE so their
smallest label lands exactly on the floor.

WHERE THE NUMBERS COME FROM
---------------------------
Every measured number is read from poster_data.json, which
build_poster_data.py recomputes and checks against the repository. Numbers
fixed by the frozen preregistration (0.1 per hour, 337 sessions) are design
constants and are written in place. Statements about other people's work carry
a reference number and are listed in REFS.

NOTHING HERE IS A PHYSICAL RESULT
---------------------------------
No apparatus exists. Photographs are grey placeholders, the physical result is
a set of blanks, and the board says so in words wherever it matters.
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

MIN = 32                               # px: 24 pt at 96 px/in
C.SCALE = MIN / C.MIN_UNITS            # 17 source units print at 32 px

INK, INK2, INK3 = C.INK, C.INK2, C.INK3
RULE, GRID = C.RULE, C.GRID
BLUE, BLUE_T, BLUE_M = C.BLUE, C.BLUE_T, C.BLUE_M
ORG, ORG_T, ORG_M = C.ORG, C.ORG_T, C.ORG_M
WINE = C.WINE
NAVY = "#0E2236"
AMBER = "#FFC55C"                      # the one accent on the dark band
MARK = "#FFE27A"                       # highlighter, for the few key findings
WASH = "#F1F4F6"
SERIF = "'Source Serif 4', Georgia, 'Times New Roman', serif"
SANS = "'IBM Plex Sans', Arial, sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600"
         "&family=IBM+Plex+Sans:wght@400;500;600;700"
         "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap")

PH, PW_SIDE, PW_MAIN = 3456, 1152, 2304

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
def page(title: str, w: int, h: int, body: str, pad: int, gap: int = 28) -> str:
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


def label(text: str, color: str = INK, rule: bool = True) -> str:
    """The standard section name a judge looks for: ABSTRACT, RESULTS, ..."""
    top = f"border-top: 4px solid {INK}; padding-top: 10px; " if rule else ""
    return (f'<div style="{top}font-family: {MONO}; font-size: {MIN}px; line-height: 40px; '
            f'font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; '
            f'color: {color}">{text}</div>')


def head(text: str, size: int = 50, color: str = INK) -> str:
    return (f'<h2 style="margin: 0; font-family: {SERIF}; font-size: {size}px; '
            f'line-height: {round(size * 1.14)}px; font-weight: 600; color: {color}; '
            f'text-wrap: balance">{text}</h2>')


def p(html: str, size: int = MIN, lh: int = 44, color: str = INK2, weight: int = 400) -> str:
    return (f'<p style="margin: 0; font-size: {size}px; line-height: {lh}px; color: {color}; '
            f'font-weight: {weight}; text-wrap: pretty">{html}</p>')


def sec(*parts: str, gap: int = 14) -> str:
    return (f'<section style="display: flex; flex-direction: column; gap: {gap}px">'
            + "".join(parts) + "</section>")


def hi(text: str) -> str:
    """Highlighter. Used on a handful of findings, never as decoration."""
    return (f'<mark style="background: {MARK}; color: {INK}; font-weight: 600; '
            f'padding: 0 6px; border-radius: 3px">{text}</mark>')


def b(text: str, color: str = INK) -> str:
    return f'<b style="color: {color}; font-weight: 600">{text}</b>'


def cap(n: str, text: str) -> str:
    return (f'<p style="margin: 0; font-size: {MIN}px; line-height: 42px; color: {INK2}; '
            f'text-wrap: pretty"><b style="color: {INK}; font-weight: 600">Fig. {n}.</b> '
            f'{text}</p>')


def status(text: str, kind: str) -> str:
    st = {
        "done": f"background: {BLUE}; color: #FFFFFF; border: 3px solid {BLUE}",
        "todo": f"background: #FFFFFF; color: {ORG}; border: 3px dashed {ORG}",
    }[kind]
    return (f'<span style="display: inline-block; {st}; font-family: {MONO}; '
            f'font-size: {MIN}px; line-height: 40px; font-weight: 600; letter-spacing: 0.04em; '
            f'text-transform: uppercase; padding: 2px 14px; border-radius: 4px; '
            f'white-space: nowrap">{text}</span>')


CAMERA = (
    '<svg aria-hidden="true" width="64" height="64" viewBox="0 0 24 24" fill="none" '
    f'stroke="{INK3}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 8h3.5l1.5-2.5h8L17.5 8H21v11H3z"/><circle cx="12" cy="13.2" r="3.6"/></svg>')


def photo(what: str, h: int, kind: str = "PHOTO TO ADD") -> str:
    """A slot for a real photograph that does not exist yet. Grey, and it says so."""
    return (f'<div style="height: {h}px; box-sizing: border-box; border: 3px dashed {INK3}; '
            f'background: {WASH}; border-radius: 6px; display: flex; flex-direction: column; '
            f'align-items: center; justify-content: center; gap: 6px; padding: 16px; '
            f'text-align: center">{CAMERA}'
            f'<span style="font-family: {MONO}; font-size: {MIN}px; line-height: 40px; '
            f'font-weight: 600; letter-spacing: 0.08em; color: {INK2}">{kind}</span>'
            f'<span style="font-size: {MIN}px; line-height: 42px; color: {INK2}">{what}</span>'
            f'</div>')


_arrow_id = [0]


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = INK2, head_: bool = True,
          dash: str | None = None, sw: int = 4) -> str:
    """One straight segment from (x1,y1) to its tip (x2,y2); horizontal or vertical."""
    _arrow_id[0] += 1
    mid = f"dc-arrow-head-filled-{_arrow_id[0]}"
    hl = 2 * sw if head_ else 0
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
            f'</marker></defs>') if head_ else ""
    me = f' marker-end="url(#{mid})"' if head_ else ""
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'style="position: absolute; left: {left}px; top: {top}px; width: {w}px; '
            f'height: {h}px; overflow: visible; fill: none; stroke: {color}; '
            f'stroke-width: {sw}; stroke-linecap: round; stroke-linejoin: round{da}">'
            f'{defs}<path d="{d}"{me}></path></svg>')


def box(x: int, y: int, w: int, h: int, html: str, look: str, color: str = INK,
        weight: int = 600) -> str:
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; '
            f'height: {h}px; box-sizing: border-box; padding: 8px 14px; display: flex; '
            f'align-items: center; justify-content: center; text-align: center; {look}; '
            f'border-radius: 8px"><span style="font-size: {MIN}px; line-height: 40px; '
            f'font-weight: {weight}; color: {color}">{html}</span></div>')


def note(x: int, y: int, w: int, text: str, align: str = "center", color: str = INK2,
         weight: int = 400) -> str:
    return (f'<div style="position: absolute; left: {x}px; top: {y}px; width: {w}px; '
            f'text-align: {align}; font-size: {MIN}px; line-height: 38px; color: {color}; '
            f'font-weight: {weight}">{text}</div>')


# ===========================================================================
# LEFT PANEL -- abstract, introduction, why it matters, purpose, hypothesis
# ===========================================================================
def quadrant() -> str:
    """Early or late, trustworthy or not: the two things that decide a warning's worth."""
    L11 = D["lead_time"]["T11"]
    over = S["false_alarms_per_hour"]["T11"] / S["budget_per_hour"]
    cell = (f"box-sizing: border-box; padding: 12px 16px; display: flex; "
            f"flex-direction: column; gap: 2px; font-size: {MIN}px; line-height: 40px; "
            f"color: {INK2}")
    name = f"font-family: {SERIF}; font-size: 42px; line-height: 48px; font-weight: 700"
    hd = (f"font-family: {MONO}; font-size: {MIN}px; line-height: 40px; font-weight: 600; "
          f"letter-spacing: 0.04em; color: {INK}; display: flex; align-items: center")
    return (
        f'<div style="display: grid; grid-template-columns: 150px minmax(0, 1fr) '
        f'minmax(0, 1fr); border: 3px solid {INK}; border-radius: 6px; overflow: hidden">'
        f'<div style="border-bottom: 3px solid {INK}"></div>'
        f'<div style="{hd}; justify-content: center; border-bottom: 3px solid {INK}; '
        f'border-left: 3px solid {INK}; padding: 6px">WARNS EARLY</div>'
        f'<div style="{hd}; justify-content: center; border-bottom: 3px solid {INK}; '
        f'border-left: 3px solid {INK}; padding: 6px">WARNS LATE</div>'
        f'<div style="{hd}; padding: 10px 14px; border-bottom: 3px solid {INK}">RARELY WRONG'
        f'</div>'
        f'<div style="{cell}; background: {MARK}; border-left: 3px solid {INK}; '
        f'border-bottom: 3px solid {INK}"><span style="{name}; color: {INK}">Useful</span>'
        f'<span style="color: {INK}">time to act before control is lost</span></div>'
        f'<div style="{cell}; border-left: 3px solid {INK}; border-bottom: 3px solid {INK}">'
        f'<span style="{name}; color: {INK}">Too late</span>the failure has already happened'
        f'</div>'
        f'<div style="{hd}; padding: 10px 14px">OFTEN WRONG</div>'
        f'<div style="{cell}; border-left: 3px solid {INK}"><span style="{name}; color: {INK}">'
        f'Ignored</span>in hospitals, 72 to 99% of monitor alarms are false [4]</div>'
        f'<div style="{cell}; border-left: 3px solid {INK}"><span style="{name}; '
        f'color: {WINE}">This monitor, so far</span><span style="color: {INK}">'
        f'{abs(L11["median_s"]):.0f} s late and {over:.0f}× its false-alarm budget</span></div>'
        f'</div>')


def left_panel() -> str:
    L11 = D["lead_time"]["T11"]
    n = S["episodes"]
    sl = S["session_level_correlation_T11"]
    span = sl["series"][-1]["trial_day"] - sl["series"][0]["trial_day"]
    fa = S["false_alarms_per_hour"]["T11"]
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
          f"but not yet built, will measure both quantities where failure times are known.",
          MIN, 43)))

    parts.append(sec(
        label("Introduction"),
        head("A decoder that fails without saying so"),
        p("Nearly 5.4 million people in the United States live with paralysis [3]. For some, "
          "an implanted brain-computer interface restores control of a cursor by intent. "
          "Software called a decoder translates the recorded activity, but the recording "
          "drifts, so decoders often need daily recalibration, and the device cannot be used "
          "freely while that happens [2].", MIN, 43),
        C.drift_line(552, 226, sl["series"], sl["failure_threshold_deg"]),
        cap("1", f"A real decoder left fixed for {span} days: cursor error by session, array "
                 f"T11. Archived data [1]."),
        gap=12))

    parts.append(sec(
        label("Why it matters"),
        head("A warning helps only if it is early and rarely wrong"),
        quadrant(),
        p("Alarms that cry wolf get switched off: nuisance alarms are the leading reason smoke "
          "alarms are disconnected [5]. Decoder research either corrects drift automatically "
          "[2, 6] or scores it and reports a correlation with performance, r = 0.93 and 0.72 "
          "[1]. No published lead time or false-alarm rate was found for such a monitor.",
          MIN, 43),
        gap=12))

    parts.append(sec(
        label("Purpose"),
        p("To measure how early a decoder-health monitor warns, and how often it warns when "
          "nothing is wrong, on test beds where the moment of failure is known in advance.",
          MIN, 43, INK)))

    parts.append(sec(
        label("Hypothesis / Engineering goal"),
        p(b("Hypothesis.") + " Measured against failure times fixed in advance, the monitor's "
          "lead time and false-alarm rate will fall outside what a deployed system could use. "
          + b("Falsified if", WINE) + " the median lead time is above zero and the 95% upper "
          "bound on false alarms is within 0.1 per hour, at the threshold that detects 80% of "
          "faults.", MIN, 43),
        p(b("Engineering goal.") + " Build the monitor, the benchmark and the test bench that "
          "make both quantities measurable. Success is a trustworthy measurement, whatever "
          "the numbers are. It is not a claim that the monitor works.", MIN, 43),
        gap=12))

    parts.append(
        f'<section style="display: flex; flex-direction: column; gap: 0; margin-top: auto">'
        + label("References")
        + "".join(f'<p style="margin: 0; font-size: {MIN}px; line-height: 40px; '
                  f'color: {INK2}; white-space: nowrap; overflow: hidden">[{i}] {r}</p>'
                  for i, r in enumerate(REFS, 1))
        + "</section>")
    return page("Left panel: abstract, introduction, purpose, hypothesis", PW_SIDE, PH,
                "\n".join(parts), 56, gap=26)


# ===========================================================================
# CENTRE PANEL -- the entry point: title, the project in four steps, the bench
# ===========================================================================
def picto(body: str) -> str:
    return (f'<svg aria-hidden="true" width="320" height="150" viewBox="0 0 320 150" '
            f'fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" '
            f'stroke-linejoin="round" style="display: block">{body}</svg>')


def picto_problem() -> str:
    # a screen, a target, the path the user meant and the path the stale decoder drew
    return picto(
        '<rect x="20" y="10" width="230" height="124" rx="8"/>'
        f'<circle cx="208" cy="42" r="15" stroke="{AMBER}"/>'
        f'<path d="M52 110 L196 50" stroke="{AMBER}" stroke-dasharray="3 12"/>'
        '<path d="M52 110 C92 104 118 96 128 70 C134 54 122 40 104 34"/>'
        '<path d="M104 34 l22 4 l-10 6 l-2 12 z" fill="#FFFFFF" stroke-width="3"/>'
        '<path d="M272 40 v70 M272 40 l-10 12 M272 40 l10 12" stroke-width="4"/>')


def picto_idea() -> str:
    # a gauge, and a warning light that has come on
    return picto(
        '<path d="M40 118 A82 82 0 0 1 204 118"/>'
        '<path d="M122 118 L170 60" stroke-width="6"/><circle cx="122" cy="118" r="8" '
        'fill="#FFFFFF"/>'
        f'<path d="M258 28 L300 104 L216 104 Z" fill="{AMBER}" stroke="{AMBER}"/>'
        f'<path d="M258 54 V80" stroke="{NAVY}" stroke-width="7"/>'
        f'<circle cx="258" cy="93" r="4" fill="{NAVY}" stroke="{NAVY}" stroke-width="2"/>')


def picto_catch() -> str:
    # a timeline: fault starts, control is lost; a warning before it and one after
    bell = ('<path d="M-17 12 Q-17 -20 0 -20 Q17 -20 17 12 L24 20 L-24 20 Z"/>'
            '<path d="M-5 28 a5 5 0 0 0 10 0" stroke-width="4"/>')
    return picto(
        '<path d="M14 120 H306"/><path d="M60 106 V134"/><path d="M228 106 V134"/>'
        '<path d="M214 106 L242 134 M242 106 L214 134" stroke-width="4"/>'
        f'<g transform="translate(144 62)" stroke="{AMBER}">{bell}</g>'
        f'<g transform="translate(284 62)" opacity="0.45">{bell}</g>')


def picto_build() -> str:
    # a sealed box with a screen and a camera, and a padlock on the start time
    return picto(
        '<rect x="14" y="26" width="196" height="108" rx="6"/>'
        '<rect x="30" y="46" width="12" height="68"/>'
        f'<path d="M44 50 L150 80 L44 110" stroke="{AMBER}" stroke-width="3" '
        f'stroke-dasharray="4 9"/>'
        '<rect x="152" y="66" width="34" height="28" rx="4"/>'
        f'<rect x="244" y="66" width="56" height="48" rx="6" stroke="{AMBER}"/>'
        f'<path d="M256 66 V52 a16 16 0 0 1 32 0 V66" stroke="{AMBER}"/>'
        f'<circle cx="272" cy="90" r="5" fill="{AMBER}" stroke="{AMBER}" stroke-width="2"/>')


def step(n: int, tag: str, art: str, title: str, text: str) -> str:
    return (f'<div style="display: flex; flex-direction: column; gap: 10px">'
            f'<div style="display: flex; align-items: center; gap: 14px">'
            f'<span style="width: 56px; height: 56px; flex: none; border-radius: 50%; '
            f'background: {AMBER}; color: {NAVY}; font-family: {SERIF}; font-size: 38px; '
            f'font-weight: 700; display: flex; align-items: center; justify-content: center">'
            f'{n}</span><span style="font-family: {MONO}; font-size: {MIN}px; '
            f'line-height: 40px; font-weight: 600; letter-spacing: 0.08em; color: {AMBER}">'
            f'{tag}</span></div>{art}'
            f'<span style="font-family: {SERIF}; font-size: 46px; line-height: 52px; '
            f'font-weight: 700; color: #FFFFFF">{title}</span>'
            f'<span style="font-size: {MIN}px; line-height: 43px; color: #DDE5EC">{text}</span>'
            f'</div>')


def sofar(big: str, text: str, todo: bool = False) -> str:
    edge = f"border-top: 4px dashed {AMBER}" if todo else f"border-top: 4px solid {AMBER}"
    return (f'<div style="{edge}; padding-top: 10px; display: flex; flex-direction: column; '
            f'gap: 2px"><span style="font-family: {SERIF}; font-size: 84px; line-height: 90px; '
            f'font-weight: 700; color: {AMBER}; white-space: nowrap">{big}</span>'
            f'<span style="font-size: {MIN}px; line-height: 42px; color: #FFFFFF">{text}</span>'
            f'</div>')


def hero() -> str:
    v = D["fault_mode_auc"]["values"]
    g = [v[a]["decoder_guard"][i] for a in ("T11", "T5") for i in (2, 3)]
    k = [v[a]["mean_activity"][i] for a in ("T11", "T5") for i in (2, 3)]
    L11 = D["lead_time"]["T11"]
    fa = S["false_alarms_per_hour"]["T11"]
    steps = (
        step(1, "THE PROBLEM", picto_problem(), "The decoder goes stale",
             "An implant lets a paralysed person move a cursor by intent. The brain signal "
             "drifts, and the decoder goes wrong without saying so.")
        + step(2, "THE IDEA", picto_idea(), "Add a warning light",
               "A monitor watches the signal itself and warns before control is lost, so the "
               "user recalibrates only when it is needed.")
        + step(3, "THE CATCH", picto_catch(), "Test the warning",
               "A warning is only useful if it comes early and is rarely wrong. For this kind "
               "of monitor, neither had been measured.")
        + step(4, "THIS PROJECT", picto_build(), "Build the test",
               "One monitor and two test beds where the moment of failure is fixed in "
               "advance: brain recordings with planted faults, and a camera-and-screen "
               "bench."))
    found = (
        sofar(f"{min(g):.2f} to {max(g):.2f}",
              f"score for spotting faults that plain activity counting scores "
              f"{min(k):.2f} to {max(k):.2f} on (0.5 is a coin flip)")
        + sofar(f"{abs(L11['median_s']):.0f} s late",
                "the typical warning arrives after decoding has already failed")
        + sofar(f"{fa / S['budget_per_hour']:.0f}× too often",
                f"{fa:.2f} false alarms per hour, against a budget of 0.1")
        + sofar("Next", "the test bench: designed, coded and preregistered. Not yet built.",
                todo=True))
    grid = ("display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 40px")
    return (
        f'<section style="background: {NAVY}; border-radius: 10px; padding: 28px 44px 32px; '
        f'display: flex; flex-direction: column; gap: 18px">'
        f'<div style="font-family: {MONO}; font-size: {MIN}px; line-height: 40px; '
        f'font-weight: 600; letter-spacing: 0.12em; color: #FFFFFF">THE WHOLE PROJECT IN ONE '
        f'MINUTE</div>'
        f'<div style="{grid}">{steps}</div>'
        f'<div style="font-family: {MONO}; font-size: {MIN}px; line-height: 40px; '
        f'font-weight: 600; letter-spacing: 0.08em; color: {AMBER}; border-top: 2px solid '
        f'#3B5068; padding-top: 18px">RESULT SO FAR, MEASURED ON ARCHIVED BRAIN RECORDINGS'
        f'</div>'
        f'<div style="{grid}">{found}</div></section>')


def title_block() -> str:
    return (
        '<header style="display: flex; flex-direction: column; gap: 10px">'
        f'<h1 style="margin: 0; font-family: {SERIF}; font-size: 138px; line-height: 144px; '
        f'font-weight: 700; letter-spacing: -0.014em; color: {INK}; white-space: nowrap">'
        f'Seeing Failure Before It Shows</h1>'
        f'<p style="margin: 0; font-family: {SERIF}; font-size: 48px; line-height: 58px; '
        f'color: {INK2}; text-wrap: balance">An early-warning monitor for brain-computer '
        f'interface decoders, and the test bench that shows whether its warnings can be '
        f'trusted</p>'
        f'<p style="margin: 4px 0 0; font-size: 36px; line-height: 44px; color: {INK}">'
        f'<b style="font-weight: 600">Gayathri Nair</b> &middot; Central Bucks High School '
        f'South &middot; [CATEGORY] &middot; [FAIR AND YEAR]</p></header>')


def bench_svg() -> str:
    """Side view of the test bench, in source units (17 units print at 32 px)."""
    T, Ln, R = C.T, C.L, C.R
    W, H = 700, 292
    s = [T(30, 24, "sealed dark box", 18, INK, weight=600)]
    s.append(R(30, 34, 474, 208, fill="#FFFFFF", stroke=INK, sw=2.5))
    s.append(R(36, 40, 462, 196, fill="none", stroke="#39424B", sw=6))
    s.append(f'<path d="M70 66 L418 140 L70 214 Z" fill="{ORG_T}" stroke="{ORG_M}" '
             f'stroke-width="1.5" stroke-dasharray="6 5"/>')
    s.append(R(54, 62, 16, 156, fill=ORG_T, stroke=ORG, sw=2.5))
    s.append(T(82, 60, "screen", 18, ORG, weight=600))
    s.append(R(330, 96, 7, 88, fill="#F7E6EB", stroke=WINE, sw=2, dash="5 4"))
    s.append(T(333, 210, "filter", 18, WINE, anchor="middle", weight=600))
    s.append(R(426, 126, 32, 28, fill=ORG_T, stroke=ORG, sw=2.5, rx=3))
    s.append(R(418, 133, 8, 14, fill=ORG, stroke=ORG, sw=1))
    s.append(Ln(442, 154, 442, 196, INK, 3))
    s.append(R(416, 196, 52, 10, fill="#F7E6EB", stroke=WINE, sw=2, rx=2))
    s.append(T(442, 228, "camera", 18, ORG, anchor="middle", weight=600))
    s.append(Ln(458, 140, 560, 140, BLUE, 2.5))
    s.append(R(499, 133, 8, 14, fill="#FFFFFF", stroke=INK, sw=1.2))
    s.append(R(560, 104, 130, 72, fill=BLUE_T, stroke=BLUE, sw=2.5, rx=4))
    s.append(T(625, 136, "Raspberry", 18, BLUE, anchor="middle", weight=600))
    s.append(T(625, 158, "Pi 4", 18, BLUE, anchor="middle", weight=600))
    s.append(f'<path d="M600 176 L600 268 L62 268 L62 218" fill="none" stroke="{BLUE}" '
             f'stroke-width="2.5" stroke-linejoin="round"/>')
    for n, x, y in ((1, 62, 88), (2, 442, 104), (5, 333, 78)):
        s.append(f'<circle cx="{x}" cy="{y}" r="15" fill="{INK}" stroke="#FFFFFF" '
                 f'stroke-width="2"/>')
        s.append(T(x, y + 6.5, str(n), 18, "#FFFFFF", anchor="middle", weight=700))
    return C.svg(W, H, s, "Side view of the test bench: a screen at one end of a sealed dark "
                 "box faces a camera at the other. A filter can slide into the light path and "
                 "the camera sits on a rotation stage. A Raspberry Pi outside drives the "
                 "screen and records the camera.")


def numbered(n: int, text: str) -> str:
    return (f'<div style="display: flex; gap: 16px; align-items: flex-start">'
            f'<span style="width: 52px; height: 52px; flex: none; border-radius: 50%; '
            f'background: {INK}; color: #FFFFFF; font-size: 34px; font-weight: 700; '
            f'display: flex; align-items: center; justify-content: center; margin-top: 2px">'
            f'{n}</span><span style="font-size: {MIN}px; line-height: 42px; color: {INK2}">'
            f'{text}</span></div>')


def how_it_works() -> str:
    steps = "".join((
        numbered(1, "The " + b("screen") + " shows 384 patches whose brightness encodes a "
                    "known direction."),
        numbered(2, "A " + b("camera") + " films them at 50 frames a second, in the dark."),
        numbered(3, "A " + b("decoder") + ", fitted once and then frozen, reads the direction "
                    "back from the video."),
        numbered(4, "The " + b("monitor") + " scores risk every 5 s from the last 30 s of "
                    "signal."),
        numbered(5, "A " + b("fault", WINE) + " begins at a moment drawn and " + hi("sealed "
                    "before recording") + "."),
        numbered(6, "Each warning is " + b("scored") + " against that sealed moment: how "
                    "early, and how many false alarms."),
    ))
    return sec(
        label("Materials and methods"),
        head("How the test bench works"),
        f'<div style="display: flex; gap: 40px; align-items: flex-start">'
        f'<div style="flex: none">{bench_svg()}</div>'
        f'<div style="flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px">'
        f'{steps}</div></div>',
        cap("2", "The bench as specified; nothing shown is built yet. 1, 2 and 5 are marked on "
                 "the drawing; 3, 4 and 6 run on the recording afterwards. Parts: Raspberry "
                 "Pi 4, Camera Module 3, display, cardboard enclosure, ND 0.6 filter, stepper "
                 "motor, DHT22 sensor."),
        gap=12)


def pictures() -> str:
    return sec(
        label("Pictures"),
        '<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); '
        'gap: 22px">'
        + photo("the assembled test bench, sealed", 244)
        + photo("inside: screen, light path, camera", 244)
        + photo("Raspberry Pi 4, camera and wiring", 244)
        + photo("a recording session running", 244, "SCREENSHOT TO ADD") + "</div>", gap=12)


WIRES = [("#E8453A", "pin 2 &middot; 5 V", "+"), ("#3C4248", "pin 9 &middot; ground", "&minus;"),
         ("#F08A2A", "pin 11 &middot; GPIO 17", "IN1"),
         ("#F0D32A", "pin 13 &middot; GPIO 27", "IN2"),
         ("#2FA84F", "pin 15 &middot; GPIO 22", "IN3"),
         ("#2E7BD4", "pin 16 &middot; GPIO 23", "IN4")]


def hardware(local: bool = False) -> str:
    name = "wiring-stepper-unlabelled.svg"
    src_ = f"../../assets/{name}" if local else ASSETS[name]
    iw, ih = 1210, 327                      # 1664 x 450 drawing, scaled to fit
    host = (
        f'<div style="position: relative; width: {iw}px; height: 372px; flex: none">'
        f'<img src="{src_}" alt="Raspberry Pi 4 wired to a ULN2003 driver board and a 28BYJ-48 '
        f'stepper motor by six coloured jumper wires" style="position: absolute; left: 0; '
        f'top: 0; width: {iw}px; height: {ih}px">'
        + note(20, 326, 380, "Raspberry Pi 4", "left", INK, 600)
        + note(590, 326, 300, "driver board", "center", INK, 600)
        + note(880, 326, 320, "stepper motor", "center", INK, 600)
        + "</div>")
    td = (f"padding: 3px 12px; font-size: {MIN}px; line-height: 42px; color: {INK2}; "
          f"border-bottom: 1.5px solid {RULE}")
    rows = "".join(
        f'<tr><td style="{td}; width: 60px"><span style="display: inline-block; width: 44px; '
        f'height: 22px; background: {c}; border-radius: 3px; vertical-align: -2px"></span></td>'
        f'<td style="{td}">{pin}</td><td style="{td}; font-weight: 600; color: {INK}">{to}</td>'
        f'</tr>' for c, pin, to in WIRES)
    th = (f"padding: 3px 12px; font-size: {MIN}px; line-height: 42px; font-weight: 600; "
          f"color: {INK}; text-align: left; border-bottom: 3px solid {INK}")
    tbl = (f'<table style="flex: 1; border-collapse: collapse; font-family: {SANS}">'
           f'<thead><tr><th style="{th}">wire</th><th style="{th}">from the Pi</th>'
           f'<th style="{th}">to the driver</th></tr></thead><tbody>{rows}</tbody></table>')
    return sec(
        label("Hardware: wiring the rotation stage"),
        f'<div style="display: flex; gap: 40px; align-items: flex-start">{host}{tbl}</div>',
        cap("3", "The repository's wiring diagram, relabelled at poster size. Pin numbers are "
                 "read from rig/motor.py and checked on every run by "
                 "scripts/81_hardware_pins.py. The motor takes 5 V, never 3.3 V."),
        gap=12)


def real_code() -> str:
    """Five lines copied from scripts/21_score_report.py, checked against the file."""
    want = [
        "# A warning raised before the fault even started is not prescience, it is a",
        "# false alarm that happens to sit in a positive episode. Counting it as a",
        "# very early detection would be the most flattering possible error.",
        "if warn_w < onset_w:",
        '    return {"false_alarm": True, "warn_w": warn_w, "lead_s": np.nan, '
        '"detected": False}',
    ]
    source = (REPO / "scripts" / "21_score_report.py").read_text().splitlines()
    have = [ln[4:] if ln.startswith("    ") else ln for ln in source]
    for ln in want:
        if ln not in have:
            raise SystemExit("the code shown on the poster is no longer in "
                             f"scripts/21_score_report.py: {ln!r}")
    esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = "".join(
        f'<div style="white-space: pre; color: {INK3 if ln.startswith("#") else INK}">'
        f'{esc(ln)}</div>' for ln in want)
    code = (f'<div style="flex: none; box-sizing: border-box; background: {WASH}; '
            f'border: 2px solid {RULE}; border-radius: 6px; padding: 16px 22px; '
            f'font-family: {MONO}; font-size: {MIN}px; line-height: 42px; font-weight: 500">'
            f'{lines}</div>')
    side = (f'<div style="flex: 1; min-width: 0; display: flex; flex-direction: column; '
            f'gap: 6px; font-size: {MIN}px; line-height: 42px; color: {INK2}">'
            f'<span>{hi("A warning before the fault starts is a false alarm")}, never an '
            f'early catch.</span><span style="font-family: {MONO}; color: {INK}; '
            f'font-weight: 500">All 102 headline claims match the data files.</span></div>')
    return sec(
        label("Real code and real output"),
        f'<div style="display: flex; gap: 32px; align-items: stretch">{code}{side}</div>',
        gap=12)


def main_panel(local: bool = False) -> str:
    return page("Centre panel: the project in one minute", PW_MAIN, PH,
                "\n".join([title_block(), hero(), how_it_works(), pictures(),
                           hardware(local), real_code()]), 56, gap=24)


# ===========================================================================
# RIGHT PANEL -- methods compared, results and data, analysis, discussion
# ===========================================================================
def compare() -> str:
    n = S["episodes"]
    cell = (f"padding: 8px 14px; font-size: {MIN}px; line-height: 40px; color: {INK2}; "
            f"border-top: 1.5px solid {RULE}")
    lab = f"{cell}; font-weight: 600; color: {INK}"
    rows = [
        ("Signal", "two implanted arrays [1]", "384 screen patches, filmed"),
        ("Faults", f"{n['T11'] + n['T5']:,} planted in software",
         "optical and software, 337 sessions"),
        ("Start time", "sealed before any detector existed", "sealed before each recording"),
    ]
    out = [f'<div style="display: grid; grid-template-columns: 178px minmax(0, 1fr) '
           f'minmax(0, 1fr); border: 3px solid {INK}; border-radius: 6px; overflow: hidden">']
    out.append(
        f'<div></div>'
        f'<div style="padding: 8px 14px; background: {BLUE}; color: #FFFFFF; '
        f'font-size: {MIN}px; line-height: 40px; font-weight: 600">Archived brain recordings'
        f'</div>'
        f'<div style="padding: 8px 14px; background: {ORG}; color: #FFFFFF; '
        f'font-size: {MIN}px; line-height: 40px; font-weight: 600">Optical test bench</div>')
    for a, x, y in rows:
        out.append(f'<div style="{lab}">{a}</div><div style="{cell}">{x}</div>'
                   f'<div style="{cell}">{y}</div>')
    out.append(f'<div style="{lab}">Status</div>'
               f'<div style="{cell}; color: {BLUE}; font-weight: 600">complete, re-checked'
               f'</div><div style="{cell}; color: {ORG}; font-weight: 600">not built yet</div>')
    out.append("</div>")
    return "".join(out)


def finding(text: str) -> str:
    return (f'<h3 style="margin: 0; font-family: {SERIF}; font-size: 44px; line-height: 50px; '
            f'font-weight: 700; color: {INK}">{text}</h3>')


def verdict_tree() -> str:
    """How the bench result will be read, as fixed in the preregistration."""
    L11 = D["lead_time"]["T11"]
    q = f"background: #FFFFFF; border: 3px solid {INK}"
    bad = f"background: #F7E6EB; border: 3px solid {WINE}"
    good = f"background: {MARK}; border: 3px solid {INK}"
    el = [
        arrow(520, 46, 639, 46), arrow(260, 92, 260, 157),
        arrow(520, 222, 639, 222), arrow(260, 286, 260, 345),
        box(0, 0, 520, 92, "Median lead time above 0 s?", q),
        box(640, 0, 400, 92, "Not usable: too late", bad, WINE),
        box(0, 158, 520, 128, "False-alarm upper bound within 0.1 per hour?", q),
        box(640, 176, 400, 92, "Not usable: too noisy", bad, WINE),
        box(0, 346, 520, 92, "Usable: hypothesis falsified", good),
        note(540, 4, 80, "no", "center", INK, 600),
        note(540, 180, 80, "no", "center", INK, 600),
        note(276, 104, 80, "yes", "left", INK, 600),
        note(276, 294, 80, "yes", "left", INK, 600),
        note(640, 100, 400, f"archived data: {abs(L11['median_s']):.0f} s late", "center",
             BLUE, 600),
        note(640, 352, 400, "bench result:", "left", ORG, 600),
        f'<div style="position: absolute; left: 640px; top: 396px; width: 400px; height: 40px; '
        f'box-sizing: border-box; border-bottom: 3px dashed {ORG}"></div>',
    ]
    return (f'<div style="position: relative; width: 1040px; height: 440px">'
            + "".join(el) + "</div>")


def bullets(items: list[str]) -> str:
    return (f'<ul style="margin: 0; padding-left: 34px; display: flex; flex-direction: column; '
            f'gap: 8px">'
            + "".join(f'<li style="font-size: {MIN}px; line-height: 42px; color: {INK2}; '
                      f'text-wrap: pretty">{i}</li>' for i in items) + "</ul>")


def right_panel() -> str:
    L11 = D["lead_time"]["T11"]
    ci = L11["ci95_s"]
    f = S["funnel"]
    fa = S["false_alarms_per_hour"]
    blank = (f'<span style="display: inline-block; width: 150px; height: 34px; box-sizing: '
             f'border-box; border-bottom: 3px dashed {ORG}; vertical-align: baseline"></span>')
    parts = []

    parts.append(sec(
        label("Methods: two test beds, one monitor"),
        compare(), gap=12))

    names = {"RATE_LOSS": ("Signal loss", "total falls"),
             "CHANNEL_DROPOUT": ("Dropout", "channels go silent"),
             "GAIN_DRIFT": ("Gain drift", "total unchanged"),
             "GEOMETRY_ROTATION": ("Rotation", "total unchanged")}
    parts.append(sec(
        label("Results and data"),
        finding("It sees faults that counting misses"),
        C.mode_dumbbell(552, 286, D["fault_mode_auc"]["values"], D["fault_mode_auc"]["modes"],
                        names),
        cap("4", "Detection score by fault type. Filled: monitor. Open: counting."),
        finding("But the warning comes late, and too often"),
        C.lead_dots(552, 232, L11["leads_s"], L11["median_s"]),
        cap("5", f"Each dot is one detected fault (array T11, {L11['n_detected']} of "
                 f"{L11['n_degraded']}). Median {num(L11['median_s'], 0)} s, 95% CI "
                 f"{num(ci[0], 0)} to {num(ci[1], 0)}. False alarms: "
                 + hi(f"{fa['T11']:.2f} per hour against a budget of 0.1") + "."),
        gap=10))

    parts.append(sec(
        label("Analysis"),
        p(f"Risk scores inside one session are near-copies of each other (lag\u20111 "
          f"autocorrelation {S['lag1_pooled']['T11']:.3f}), so 720 decisions an hour rest on "
          f"about one independent measurement. {f['all_gates']} of {f['run']} monitor "
          f"configurations pass all five gates.", MIN, 42),
        verdict_tree(),
        cap("6", "How the bench result will be judged, fixed in advance."),
        gap=10))

    parts.append(sec(
        label("Discussion"),
        bullets([
            b("Shown so far") + ", on archived recordings only: the results above.",
            b("Not shown yet:") + " anything on the bench. " + b("Not claimed:") + " any "
            "clinical rate or benefit to patients.",
            b("Limits:") + " two arrays that sometimes disagree, one bench, one family of "
            "monitor.",
            b("Next:") + " build the bench, pass five acceptance gates, record 337 "
            "sessions."]),
        gap=10))

    parts.append(sec(
        label("Conclusion"),
        p("On archived recordings the monitor " + hi("detects real faults but warns too late "
          "and too often") + " to be relied on. The bench will show whether that belongs to "
          "brain recordings or to the method.", MIN, 42, INK),
        f'<p style="margin: 0; font-size: {MIN}px; line-height: 50px; color: {INK2}; '
        f'border: 3px dashed {ORG}; border-radius: 6px; padding: 8px 16px">'
        f'<b style="color: {ORG}; font-weight: 600">Bench, to be measured:</b> lead time '
        f'{blank} s, false alarms {blank} per hour.</p>',
        gap=10))
    return page("Right panel: methods, results, analysis, conclusion", PW_SIDE, PH,
                "\n".join(parts), 56, gap=22)


# ===========================================================================
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
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
