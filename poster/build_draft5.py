#!/usr/bin/env python3
"""
build_draft5.py -- Draft 5 of the trifold: 48 inches wide by 48 inches tall.

    python3 poster/build_poster_data.py     # recompute and check every number
    python3 poster/build_draft5.py          # write D5-Left, D5-Centre, D5-Right

WHAT IS NEW
-----------
1. A title area with a small drawing of where the project sits: electrodes, decoder,
   cursor, and the monitor that watches the recorded activity.
2. Under the title, a light-blue introduction in plain language. Three frames:
       THE PROBLEM      what goes wrong, and a real example of it
       WHY IT MATTERS   three ways to time the repair, and why a warning must be trusted
       THIS PROJECT     what was tested, what was found, what is not shown
   Each frame says in its heading line whether it is established science, a goal, or
   something this project showed.

WHAT MOVED, AND WHY
-------------------
Draft 4 filled its 48 inches, so the introduction takes its room from sections it
replaces or absorbs, and nothing is dropped:

    Introduction, Why it matters        left panel  -> the light-blue section
    the four headline numbers           results     -> the light-blue section
    Computational validation            centre      -> left panel
    How the bench result will be judged right panel -> under Physical validation
    the decision-rate chart             results     -> beside its discussion point
    "Also measured" (was a caption)     results     -> a discussion point

Every section's wording comes from build_draft4.py, which this file imports. The only
new sentences are the ones inside the light-blue section.

NOTHING HERE IS A PHYSICAL RESULT
---------------------------------
No apparatus exists. Photographs are grey placeholders and the bench results are blanks.
The drawings in the light-blue section are schematics, and say so.
"""
from __future__ import annotations

import build_draft4 as B
import charts as C
from build_draft4 import (BLUE, BLUE_M, BLUE_T, BODY, CAP, D, INK, INK2, INK3, MONO, ORG,
                          OUT, PH, PW_MAIN, PW_SIDE, REPO, RULE, S, SERIF, WASH, WINE, b, cap,
                          chip, finding, label, num, p, page, sec)

COL = B.COL
FRAME = 682                                   # one frame of the introduction, px
FRAME_U = int(FRAME / C.SCALE)                # the same, in chart units
GREY = "#9AA5AF"

# Figure numbers in reading order: the introduction first, then the four columns.
B.FIG.update({"drift": "1", "monitor": "2", "episode": "3", "workflow": "4", "code": "5",
              "bench": "6", "stepper": "7", "sensor": "8", "gates": "9", "verdict": "10",
              "modes": "11", "lead": "12", "fa": "13", "dfa": "14", "data": "15", "gap": "16",
              "decision": "17", "relate": "18", "experiments": "19"})
FIG = B.FIG
B.REFS = B.REFS + ["Perge et al., J. Neural Eng. 10 (2013)"]      # [7]


# ===========================================================================
# drawings (source units; charts.svg enlarges them so 17 units print at 20 pt)
# ===========================================================================
def head_right(x: float, y: float, color: str, s: float = 7) -> str:
    return f'<path d="M{x:.1f} {y:.1f} l{-s * 1.5:.1f} {-s:.1f} l0 {2 * s:.1f} Z" fill="{color}"/>'


def chain_svg() -> str:
    """Where the project sits: the signal path of an implanted interface, and the monitor."""
    T, L, R = C.T, C.L, C.R
    W, H = 504, 176
    s = []
    # electrodes: an array seen from above
    s.append(R(16, 14, 70, 70, fill="#FFFFFF", stroke=INK, sw=2.5, rx=6))
    for i in range(5):
        for j in range(5):
            s.append(f'<circle cx="{27 + i * 12}" cy="{25 + j * 12}" r="3.4" fill="{INK}"/>')
    s.append(T(51, 106, "electrodes", 17, INK2, anchor="middle"))
    # decoder
    s.append(L(90, 49, 138, 49, INK, 2.5))
    s.append(head_right(148, 49, INK))
    s.append(R(150, 21, 132, 56, fill="#FFFFFF", stroke=INK, sw=2.5, rx=6))
    s.append(T(216, 55, "decoder", 18, INK, anchor="middle", weight=600))
    # cursor on a screen
    s.append(L(282, 49, 330, 49, INK, 2.5))
    s.append(head_right(340, 49, INK))
    s.append(R(342, 16, 96, 64, fill="#FFFFFF", stroke=INK, sw=2.5, rx=4))
    s.append(L(390, 80, 390, 90, INK, 2.5))
    s.append(L(370, 90, 410, 90, INK, 2.5))
    s.append(L(366, 62, 412, 36, INK3, 2, dash="3 5"))
    s.append(f'<circle cx="418" cy="33" r="6.5" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    s.append(f'<path d="M358 54 l0 17 l4.6 -4 l3.4 7.4 l3.4 -1.6 l-3.4 -7.2 l6 -0.4 Z" '
             f'fill="{INK}"/>')
    s.append(T(390, 110, "cursor", 17, INK2, anchor="middle"))
    # the monitor taps the recorded activity
    s.append(f'<circle cx="114" cy="49" r="4.5" fill="{BLUE}"/>')
    s.append(f'<path d="M114 49 L114 142 L146 142" fill="none" stroke="{BLUE}" '
             f'stroke-width="2.5" stroke-linejoin="round"/>')
    s.append(head_right(156, 142, BLUE))
    s.append(R(158, 114, 150, 56, fill=BLUE_T, stroke=BLUE, sw=2.5, rx=6))
    s.append(T(170, 148, "monitor", 18, BLUE, weight=600))
    s.append(L(248, 138, 300, 138, INK, 1.5, dash="4 4"))
    s.append(f'<polyline points="248,160 262,158 272,150 282,136 292,128 300,126" fill="none" '
             f'stroke="{BLUE}" stroke-width="2.5" stroke-linejoin="round"/>')
    s.append(L(308, 142, 350, 142, BLUE, 2.5))
    s.append(head_right(360, 142, BLUE))
    s.append(f'<path d="M366 162 L406 162 L386 124 Z" fill="#FFFFFF" stroke="{BLUE}" '
             f'stroke-width="2.5" stroke-linejoin="round"/>')
    s.append(T(386, 157, "!", 20, BLUE, anchor="middle", weight=700))
    s.append(T(416, 148, "warning", 18, BLUE, weight=600))
    return C.svg(W, H, s, "Signal path of an implanted brain-computer interface: electrodes, "
                 "then a decoder, then a cursor on a screen. A monitor, the subject of this "
                 "project, watches the recorded activity and raises a warning.")


def mechanism_svg() -> str:
    """Why the recording a decoder was fitted to does not stay the same [7]. A schematic."""
    T, L, R = C.T, C.L, C.R
    W, H = FRAME_U, 116

    def state(ox: float, later: bool) -> list[str]:
        o = [R(ox, 22, 112, 74, fill="#FFFFFF", stroke=RULE, sw=1.5, rx=4)]
        cx = ox + (64 if later else 56)
        tip = 66 if not later else 62                       # a worn tip is blunter
        if later:
            # where the electrode was, and the tissue that has formed round it
            o.append(f'<path d="M{ox + 52} 23 L{ox + 52} 58 L{ox + 56} 66 L{ox + 60} 58 '
                     f'L{ox + 60} 23" fill="none" stroke="{INK3}" stroke-width="1.5" '
                     f'stroke-dasharray="4 3"/>')
            o.append(f'<path d="M{cx - 10} 23 L{cx - 10} 58 Q{cx} 78 {cx + 10} 58 L{cx + 10} 23" '
                     f'fill="none" stroke="{GREY}" stroke-width="5" stroke-linejoin="round"/>')
        o.append(f'<path d="M{cx - 4} 22.8 L{cx - 4} 56 L{cx} {tip} L{cx + 4} 56 L{cx + 4} 22.8 Z" '
                 f'fill="{INK}"/>')
        cells = [(ox + 26, 70, 9), (ox + 90, 60, 9), (ox + 66, 84, 8)]
        for k, (x, y, r) in enumerate(cells):
            quiet = later and k == 0
            if not quiet:
                o.append(L(cx, tip, x, y, BLUE_M, 2 if not (later and k == 2) else 1.2))
        for k, (x, y, r) in enumerate(cells):
            if later and k == 0:
                o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" stroke="{INK3}" '
                         f'stroke-width="2" stroke-dasharray="4 3"/>')
            else:
                o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{BLUE}"/>')
        return o

    s = [T(56, 15, "at fitting", 17, INK, anchor="middle", weight=600),
         T(196, 15, "weeks later", 17, INK, anchor="middle", weight=600)]
    s += state(0, False)
    s.append(L(117, 59, 128, 59, INK2, 2.5))
    s.append(head_right(137, 59, INK2, 6))
    s += state(140, True)
    s.append(T(0, 112, "schematic, not to scale", 17, INK2))
    # what changed, keyed by the same marks as the drawing
    lx, tx = 266, 290
    s.append(T(lx, 15, "what changes [7]", 17, INK, weight=600))
    rows = ["array shifts", "tissue reacts", "neurons change", "parts wear"]
    for i, name in enumerate(rows):
        y = 38 + i * 21
        if i == 0:
            s.append(L(lx + 4, y - 9, lx + 4, y + 7, INK3, 1.5, dash="4 3"))
            s.append(L(lx + 12, y - 9, lx + 12, y + 7, INK, 4))
        elif i == 1:
            s.append(f'<circle cx="{lx + 8}" cy="{y - 1}" r="6" fill="none" stroke="{GREY}" '
                     f'stroke-width="4.5"/>')
        elif i == 2:
            s.append(f'<circle cx="{lx + 8}" cy="{y - 1}" r="7" fill="#FFFFFF" stroke="{INK3}" '
                     f'stroke-width="2" stroke-dasharray="4 3"/>')
        else:
            s.append(f'<path d="M{lx + 4} {y - 10} L{lx + 4} {y + 2} L{lx + 8} {y + 6} '
                     f'L{lx + 12} {y + 2} L{lx + 12} {y - 10} Z" fill="{INK}"/>')
        s.append(T(tx, y + 5, name, 17, INK2))
    return C.svg(W, H, s, "Schematic of one electrode among three neurons, when the decoder "
                 "is fitted and weeks later. Later the electrode has shifted, tissue has "
                 "formed around it, one neuron is no longer picked up, and the tip is worn.")


def repairs_svg() -> str:
    """Three ways to time the same repair. The third is the goal and has not been shown."""
    T, L, R = C.T, C.L, C.R
    W, H = FRAME_U, 118
    x0, x1 = 6, W - 6
    s = []

    def sq(x: float, y: float) -> str:
        return R(x - 6, y - 6, 12, 12, fill=INK, stroke="#FFFFFF", sw=1.5)

    # 1. on a schedule
    s.append(T(0, 14, "on a schedule: every day, pausing use [2]", 17, INK, weight=600))
    s.append(L(x0, 27, x1, 27, BLUE, 5))
    for k in range(7):
        s.append(sq(x0 + 30 + k * (x1 - x0 - 60) / 6, 27))
    # 2. after the failure
    s.append(T(0, 55, "after failure: control is lost first", 17, INK, weight=600))
    s.append(L(x0, 68, 190, 68, BLUE, 5))
    s.append(L(190, 68, 300, 68, WINE, 8))
    s.append(L(300, 68, x1, 68, BLUE, 5))
    s.append(f'<circle cx="190" cy="68" r="7.5" fill="{WINE}" stroke="#FFFFFF" '
             f'stroke-width="1.5"/>')
    s.append(sq(300, 68))
    # 3. when warned
    s.append(T(0, 96, "when warned: before control is lost (goal)", 17, BLUE, weight=600))
    s.append(L(x0, 109, x1, 109, BLUE, 5))
    s.append(f'<path d="M132 117 L150 117 L141 100 Z" fill="#FFFFFF" stroke="{BLUE}" '
             f'stroke-width="2.5" stroke-linejoin="round"/>')
    s.append(sq(176, 109))
    return C.svg(W, H, s, "Three timelines of the same repair. On a schedule: seven repairs "
                 "at even intervals. After failure: a stretch without control, then one "
                 "repair. When warned: a warning, then one repair, and no stretch without "
                 "control.")


# ===========================================================================
# the title area
# ===========================================================================
def title_block() -> str:
    sw = lambda st: f'<span style="width: 34px; height: 22px; flex: none; {st}"></span>'
    key = lambda s_, t: (f'<span style="display: inline-flex; gap: 10px; align-items: center; '
                         f'font-size: {CAP}px; line-height: 34px; color: {INK2}">{s_}{t}</span>')
    return (
        f'<header style="border-top: 6px solid {INK}; padding-top: 10px; display: flex; '
        f'gap: 44px; align-items: center">'
        f'<div style="flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px">'
        f'<h1 style="margin: 0; font-family: {SERIF}; font-size: 104px; line-height: 104px; '
        f'font-weight: 700; letter-spacing: -0.014em; color: {INK}; white-space: nowrap">'
        f'Seeing Failure Before It Shows</h1>'
        f'<p style="margin: 0; font-family: {SERIF}; font-size: 36px; line-height: 44px; '
        f'color: {INK2}; text-wrap: balance">An early-warning monitor for brain-computer '
        f'interface decoders, validated on archived brain recordings and on a purpose-built '
        f'optical test bench</p>'
        f'<div style="margin-top: 6px; border-top: 2px solid {RULE}; padding-top: 6px; '
        f'font-size: 32px; line-height: 40px; color: {INK}">'
        f'<b style="font-weight: 600">Gayathri Nair</b> &middot; Central Bucks High School '
        f'South &middot; [CATEGORY] &middot; [FAIR AND YEAR]</div>'
        f'<div style="display: flex; gap: 26px; flex-wrap: wrap">'
        + key(sw(f"background: {BLUE}"), "measured on archived recordings")
        + key(sw(f"border: 3px dashed {ORG}; box-sizing: border-box"), "planned on the bench")
        + key(sw(f"border: 3px dashed {INK3}; background: {WASH}; box-sizing: border-box"),
              "photo to add")
        + "</div></div>"
        f'<div style="flex: none">{chain_svg()}</div></header>')


# ===========================================================================
# the light-blue introduction
# ===========================================================================
def tagline(n: int, name: str, status: str) -> str:
    """Step number, what the frame is about, and how far the claim in it goes."""
    return (f'<div style="display: flex; align-items: center; gap: 12px; font-family: {MONO}; '
            f'font-size: {CAP}px; line-height: 36px; letter-spacing: 0.03em; '
            f'text-transform: uppercase; color: {INK2}">'
            f'<span style="width: 36px; height: 36px; flex: none; border-radius: 50%; '
            f'background: {BLUE}; color: #FFFFFF; font-family: {B.SANS}; font-weight: 700; '
            f'letter-spacing: 0; display: flex; align-items: center; justify-content: center">'
            f'{n}</span><span><b style="color: {BLUE}; font-weight: 600">{name}</b> &middot; '
            f'{status}</span></div>')


def frame(*parts: str) -> str:
    return ('<div style="min-width: 0; display: flex; flex-direction: column; gap: 10px">'
            + "".join(parts) + "</div>")


def quadrant_compact() -> str:
    """The four outcomes of a warning. The details are in the sentence under it."""
    edge = f"2.5px solid {INK}"
    hd = (f"font-family: {MONO}; font-size: {CAP}px; line-height: 34px; font-weight: 600; "
          f"letter-spacing: 0.03em; color: {INK}; display: flex; align-items: center; "
          f"box-sizing: border-box")
    cell = (f"background: #FFFFFF; box-sizing: border-box; padding: 10px 14px; display: flex; "
            f"align-items: center; font-family: {SERIF}; font-size: 34px; line-height: 40px; "
            f"font-weight: 700")
    return (
        f'<div style="display: grid; grid-template-columns: 148px minmax(0, 1fr) '
        f'minmax(0, 1fr); border: {edge}; border-radius: 6px; overflow: hidden; '
        f'background: #FFFFFF">'
        f'<div style="border-bottom: {edge}"></div>'
        f'<div style="{hd}; justify-content: center; padding: 4px; border-left: {edge}; '
        f'border-bottom: {edge}">WARNS EARLY</div>'
        f'<div style="{hd}; justify-content: center; padding: 4px; border-left: {edge}; '
        f'border-bottom: {edge}">WARNS LATE</div>'
        f'<div style="{hd}; padding: 6px 12px; border-bottom: {edge}">RARELY WRONG</div>'
        f'<div style="{cell}; color: {BLUE}; border-left: {edge}; border-bottom: {edge}">'
        f'Useful</div>'
        f'<div style="{cell}; color: {INK}; border-left: {edge}; border-bottom: {edge}">'
        f'Too late</div>'
        f'<div style="{hd}; padding: 6px 12px">OFTEN WRONG</div>'
        f'<div style="{cell}; color: {INK}; border-left: {edge}">Ignored</div>'
        f'<div style="{cell}; color: {WINE}; border-left: {edge}">This monitor, so far</div>'
        f'</div>')


def stat(big: str, text: str) -> str:
    return (f'<div style="border-top: 5px solid {BLUE}; padding-top: 4px; display: flex; '
            f'flex-direction: column"><span style="font-family: {SERIF}; font-size: 50px; '
            f'line-height: 56px; font-weight: 700; color: {BLUE}; white-space: nowrap">{big}'
            f'</span><span style="font-size: {CAP}px; line-height: 35px; color: {INK2}">{text}'
            f'</span></div>')


def introduction() -> str:
    sl = S["session_level_correlation_T11"]
    span = sl["series"][-1]["trial_day"] - sl["series"][0]["trial_day"]
    v = D["fault_mode_auc"]["values"]
    g = [v[a]["decoder_guard"][i] for a in ("T11", "T5") for i in (2, 3)]
    k = [v[a]["mean_activity"][i] for a in ("T11", "T5") for i in (2, 3)]
    L11 = D["lead_time"]["T11"]
    fa = S["false_alarms_per_hour"]
    f = S["funnel"]
    n = S["episodes"]

    header = (
        f'<div style="display: flex; align-items: baseline; justify-content: space-between; '
        f'gap: 24px"><span style="font-family: {MONO}; font-size: {BODY}px; line-height: 40px; '
        f'font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: {BLUE}">'
        f'Introduction: start here</span>'
        f'<span style="font-family: {MONO}; font-size: {CAP}px; line-height: 34px; '
        f'letter-spacing: 0.03em; text-transform: uppercase; color: {INK2}">Nearly 5.4 million '
        f'people in the United States live with paralysis [3]</span></div>'
        f'<h2 style="margin: 0; font-family: {SERIF}; font-size: 48px; line-height: 54px; '
        f'font-weight: 600; color: {INK}; text-wrap: balance">A decoder left unchanged worked '
        f'for about two months, then failed (Fig. {FIG["drift"]}). This project tests whether '
        f'such a failure can be seen coming, early enough and reliably enough to act on.</h2>')

    what = frame(
        tagline(1, "The problem", "established science"),
        finding("A decoder tuned to yesterday"),
        mechanism_svg(),
        C.drift_compact(FRAME_U, 124, sl["series"], sl["failure_threshold_deg"]),
        cap(FIG["drift"], f"Real data [1], array T11: median cursor error by session, one "
                          f"decoder kept for {span} days."),
        p("In research trials, people with paralysis steer a cursor by intent: implanted "
          "electrodes record brain activity and software called a decoder translates it "
          "[1]. The recording keeps changing [7]. The decoder still expects the old pattern, "
          "so control degrades, and nothing tells the user."))

    why = frame(
        tagline(2, "Why it matters", "not yet shown"),
        finding("Three ways to time the repair"),
        repairs_svg(),
        quadrant_compact(),
        p("A warning would not stop the drift. It would let the repair happen only when "
          "needed, before control is lost. But a warning has to be trusted: in hospitals 72 "
          "to 99% of monitor alarms are false [4], and nuisance alarms are the leading "
          "reason smoke alarms are disconnected [5]."))

    how = frame(
        tagline(3, "This project", "shown on archived data"),
        finding("How early, and how often wrong"),
        p("Earlier work corrects drift automatically [2, 6], or scores it and reports a "
          "correlation with performance, r = 0.93 and 0.72 [1]. No published lead time or "
          f"false-alarm rate was found. This project plants {n['T11'] + n['T5']:,} faults in "
          "real recordings at start times sealed in advance, then measures both."),
        '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); '
        'gap: 10px 28px">'
        + stat(f"{min(g):.2f} to {max(g):.2f}",
               f"detection score; counting scores {min(k):.2f} to {max(k):.2f}")
        + stat(f"{abs(L11['median_s']):.0f} s late",
               "the typical warning follows the failure")
        + stat(f"{fa['T11'] / S['budget_per_hour']:.0f}× too often",
               f"{fa['T11']:.2f} false alarms per hour; the budget is 0.1")
        + stat(f"{f['all_gates']} of {f['run']}",
               "monitor configurations pass all five gates")
        + "</div>",
        p(b("Not shown or claimed:") + " a warning reliable enough to act on, or any "
          "benefit to a user."))

    return (f'<section style="background: {BLUE_T}; border-top: 6px solid {BLUE}; '
            f'padding: 12px 32px 14px; display: flex; flex-direction: column; gap: 10px">'
            + header
            + '<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); '
              'gap: 40px; align-items: start">' + what + why + how + "</div></section>")


# ===========================================================================
# the three panels
# ===========================================================================
def column(parts: list[str], gap: int) -> str:
    return (f'<div style="width: {COL}px; flex: none; display: flex; flex-direction: column; '
            f'gap: {gap}px">' + "".join(parts) + "</div>")


def left_panel() -> str:
    parts = [B.s_abstract(), B.s_purpose(), B.s_hypothesis(), B.s_system(), B.s_measured(H=220),
             B.s_computational()]
    return page("Draft 5, left panel: the question, the system, the computational test",
                PW_SIDE, PH, "\n".join(parts), 56, gap=22)


def centre_panel() -> str:
    data, _ = B.data_parts()
    validation = column([B.s_physical(), B.s_verdict()], 22)
    results = column([
        sec(label("Results and data", BLUE, chip("archived recordings", "done"))),
        B.r_modes(), B.r_lead(), B.r_fa(), B.r_dfa(),
        sec(label("Data"), data,
            cap(FIG["data"], f"The measured values behind Figs {FIG['modes']} to "
                             f"{FIG['dfa']}."), gap=10),
        B.r_analysis()], 10)
    return page("Draft 5, centre panel: introduction, the bench, the results", PW_MAIN, PH,
                title_block() + "\n" + introduction()
                + '\n<div style="display: flex; gap: 56px; align-items: flex-start">'
                + validation + results + "</div>", 56, gap=14)


def right_panel() -> str:
    _, also = B.data_parts()
    pts = B.discussion_points()
    parts = [
        sec(label("Discussion"), B.head("What the results mean"), pts[0],
            B.point("Also measured:", also), *pts[1:],
            B.r_decision(W=B.SIDE_U, H=206), gap=12),
        B.s_relate(), B.s_limits(), B.s_broader(), B.s_future(), B.s_conclusion(),
        B.refs_block()]
    return page("Draft 5, right panel: discussion and interpretation", PW_SIDE, PH,
                "\n".join(parts), 56, gap=22)


def main() -> int:
    for name, fn in (("D5-Centre.dc.html", centre_panel), ("D5-Left.dc.html", left_panel),
                     ("D5-Right.dc.html", right_panel)):
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
