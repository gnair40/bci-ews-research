#!/usr/bin/env python3
"""
charts.py -- the poster's charts, as inline SVG.

ONE VISUAL SYSTEM, TWO STATES
-----------------------------
    measured   solid marks, drawn from poster_data.json. Blue: the computational
               phase. Orange is reserved for the physical phase and no orange
               mark exists yet, because no physical measurement exists yet.

    planned    the SAME axes, hatched and empty, drawn from the frozen
               preregistration: reference lines, units, planned sample sizes,
               and nothing else.

A planned chart never contains a data mark. The only things drawn inside one
are quantities fixed by the design before any recording: the zero line, the
0.1-per-hour budget, the severity levels, the decision rates, and the
rule-of-three bound, which is arithmetic and not a result.

When a physical result exists, its chart is redrawn in the measured state with
the same function the computational chart uses. Nothing is edited by hand.
"""
from __future__ import annotations

import math

INK, INK2, INK3 = "#101A24", "#33414D", "#55626E"
RULE, GRID = "#B9C3CC", "#E2E7EB"
BLUE, BLUE_M, BLUE_T = "#1B5A8E", "#86ABCD", "#E4EDF6"
ORG, ORG_M, ORG_T = "#B24E0A", "#E9C3A0", "#FDF3E9"
WINE = "#8C1D3B"
SANS = "IBM Plex Sans, Arial, sans-serif"
MONO = "IBM Plex Mono, Consolas, monospace"
TICK = 18
LABEL = 19
# Charts are drawn in "source units" and displayed SCALE times larger. The
# builder sets SCALE so that the smallest label, 17 units, prints at 32 px,
# which is 24 pt on a 96 px/in sheet. Nothing on the board may be smaller.
SCALE = 1.0
MIN_UNITS = 17


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def T(x, y, s, size=TICK, fill=INK2, anchor="start", weight=400, rot=None, family=SANS,
      spacing=None):
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{tr}>'
            f'{esc(s)}</text>')


def L(x1, y1, x2, y2, stroke=INK, w=1.5, dash=None, cap="butt"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{w}" stroke-linecap="{cap}"{d}/>')


def R(x, y, w, h, fill="none", stroke="none", sw=1, rx=0, dash=None, op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' opacity="{op}"' if op is not None else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')


def lin(d0, d1, r0, r1):
    return lambda v: r0 + (v - d0) / (d1 - d0) * (r1 - r0)


def logs(d0, d1, r0, r1):
    a, b = math.log10(d0), math.log10(d1)
    return lambda v: r0 + (math.log10(v) - a) / (b - a) * (r1 - r0)


def svg(W, H, body, label):
    dw, dh = round(W * SCALE), round(H * SCALE)
    return (f'<svg role="img" aria-label="{esc(label)}" width="{dw}" height="{dh}" '
            f'viewBox="0 0 {W} {H}" style="display: block; width: {dw}px; height: {dh}px">'
            + "".join(body) + "</svg>")


def hatch(uid, x, y, w, h):
    """The planned state: a pale hatched field with a dashed orange edge."""
    return (f'<defs><pattern id="hatch-{uid}" width="16" height="16" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="16" height="16" fill="{ORG_T}"/>'
            f'<line x1="0" y1="0" x2="0" y2="16" stroke="{ORG_M}" stroke-width="3"/>'
            f'</pattern></defs>'
            + R(x, y, w, h, fill=f"url(#hatch-{uid})", stroke=ORG, sw=2, dash="10 7"))


def tag(cx, cy, line1, line2=None, w=None):
    """The label every planned chart carries, so an empty chart cannot be misread."""
    w = w or max(len(line1) * 12.4 + 40, (len(line2) * 8.9 + 40) if line2 else 0)
    h = 74 if line2 else 46
    out = [R(cx - w / 2, cy - h / 2, w, h, fill="#FFFFFF", stroke=ORG, sw=2, rx=6)]
    out.append(T(cx, cy - (8 if line2 else -6), line1, size=18, fill=ORG, anchor="middle",
                 weight=600, spacing="0.06em"))
    if line2:
        out.append(T(cx, cy + 20, line2, size=17, fill=INK2, anchor="middle"))
    return "".join(out)


def frame(x0, y0, x1, y1):
    return L(x0, y1, x1, y1, RULE, 1.5) + L(x0, y0, x0, y1, RULE, 1.5)


# ---------------------------------------------------------------------------
# Fig. 1 -- one archived episode: risk over time with onset, failure, warning
# ---------------------------------------------------------------------------
def episode_trace(ep, W=1040, H=400, win_s=30.0, step_s=5.0):
    x0, x1, y0, y1 = 78, W - 24, 86, H - 62
    t = [i * step_s + win_s for i in range(len(ep["risk"]))]     # window END time
    X = lin(t[0], t[-1], x0, x1)
    ymax = 120.0
    Y = lin(0, ymax, y1, y0)
    b = []
    for v in (0, 40, 80, 120):
        b.append(L(x0, Y(v), x1, Y(v), GRID, 1))
        b.append(T(x0 - 10, Y(v) + 6, f"{v}", anchor="end"))
    for s in range(60, 301, 60):
        b.append(L(X(s), y1, X(s), y1 + 7, RULE, 1.5))
        b.append(T(X(s), y1 + 28, f"{s}", anchor="middle"))
    b.append(frame(x0, y0, x1, y1))
    b.append(T(x0 + (x1 - x0) / 2, H - 8, "time at the end of each 30 s window (s); "
               "one window every 5 s", size=LABEL, anchor="middle"))
    b.append(T(20, y0 + (y1 - y0) / 2, "risk score", size=LABEL, anchor="middle", rot=-90))
    # WARN threshold
    th = ep["warn_threshold"]
    b.append(L(x0, Y(th), x1, Y(th), INK, 1.5, dash="7 5"))
    b.append(T(x1 - 4, Y(th) - 8, f"warning threshold {th:.1f}", size=17, fill=INK,
               anchor="end"))
    # the three moments
    t_on = ep["onset_w"] * step_s                    # the fault's own start time
    t_fail = ep["crossing_w"] * step_s + win_s
    t_warn = ep["warn_w"] * step_s + win_s
    b.append(R(X(t_fail), y0, X(t_warn) - X(t_fail), y1 - y0, fill=BLUE_T))
    pts = " ".join(f"{X(a):.1f},{Y(min(v, ymax)):.1f}" for a, v in zip(t, ep["risk"]))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{BLUE}" stroke-width="4" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    for tx, col, dash in ((t_on, WINE, None), (t_fail, INK, None), (t_warn, BLUE, None)):
        b.append(L(X(tx), y0 - 6, X(tx), y1, col, 3))
    b.append(T(X(t_on) - 8, y0 - 46, "fault onset", size=18, fill=WINE, anchor="end",
               weight=600))
    b.append(T(X(t_on) - 8, y0 - 24, "sealed in advance", size=17, fill=WINE, anchor="end"))
    b.append(T(X(t_fail) - 8, y0 + 22, "decoding fails", size=18, fill=INK, anchor="end",
               weight=600))
    b.append(T(X(t_fail) - 8, y0 + 44, "error +10° over", size=17, fill=INK2, anchor="end"))
    b.append(T(X(t_fail) - 8, y0 + 64, "healthy baseline", size=17, fill=INK2, anchor="end"))
    b.append(T(X(t_warn) + 8, y0 + 22, "monitor warns", size=18, fill=BLUE, weight=600))
    # lead-time bracket
    by = y0 - 26
    b.append(L(X(t_fail), by, X(t_warn), by, INK, 2))
    b.append(L(X(t_fail), by - 7, X(t_fail), by + 7, INK, 2))
    b.append(L(X(t_warn), by - 7, X(t_warn), by + 7, INK, 2))
    b.append(T(X(t_warn) + 10, by - 16, f"lead time = {ep['lead_s']:+.0f} s".replace("-", "−"),
               size=22, fill=INK, weight=700))
    b.append(T(X(t_warn) + 10, by + 8, "the warning came after the failure", size=17,
               fill=INK2))
    return svg(W, H, b, f"Risk score over one archived episode. The fault starts at "
               f"{t_on:.0f} seconds, decoding fails at {t_fail:.0f} seconds and the "
               f"monitor warns at {t_warn:.0f} seconds, a lead time of {ep['lead_s']:.0f} "
               f"seconds.")


# ---------------------------------------------------------------------------
# Fig. 5 -- lead time. One dot per detected fault.
# ---------------------------------------------------------------------------
def lead_dots(W, H, leads, median, xlim=(-180, 140), top=54, label_gap=8, label_dy=56):
    """`top` is the empty band above the plot; `label_gap` and `label_dy` place the median
    label clear of its line and of the dots. The defaults reproduce the earlier drafts."""
    x0, x1, y0, y1 = 28, W - 20, top, H - 60
    X = lin(xlim[0], xlim[1], x0, x1)
    counts: dict[float, int] = {}
    for v in leads:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    pitch = min((y1 - y0 - 6) / top, (X(5) - X(0)) * 1.02)
    r = pitch / 2 - 0.6
    b = [R(x0, y0, X(0) - x0, y1 - y0, fill="#F3F5F7")]
    b.append(T(x0 + 10, y0 + 24, "warning after the failure", size=17, fill=INK2))
    b.append(T(x1 - 6, y0 + 24, "warning first", size=17, fill=INK2, anchor="end"))
    for v, n in sorted(counts.items()):
        fill = INK if v == 0 else (BLUE if v < 0 else "#FFFFFF")
        for k in range(n):
            b.append(f'<circle cx="{X(v):.1f}" cy="{y1 - r - 2 - k * pitch:.1f}" r="{r:.1f}" '
                     f'fill="{fill}" stroke="{BLUE if v > 0 else fill}" stroke-width="1.6"/>')
    b.append(L(x0, y1, x1, y1, RULE, 1.5))
    b.append(L(X(0), y0 - 8, X(0), y1 + 7, INK, 2.5))
    for v in range(-180, 141, 60):
        b.append(L(X(v), y1, X(v), y1 + 7, RULE, 1.5))
        b.append(T(X(v), y1 + 28, f"{v:+d}".replace("-", "−") if v else "0", anchor="middle",
                   weight=700 if v == 0 else 400, fill=INK if v == 0 else INK2))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "lead time (s); one dot per detected fault",
               size=LABEL, anchor="middle"))
    b.append(L(X(median), y0 + 34, X(median), y1, BLUE, 2, dash="6 5"))
    b.append(T(X(median) - label_gap, y0 + label_dy,
               f"median {median:+.0f} s".replace("-", "−"),
               size=18,
               fill=BLUE, anchor="end", weight=700))
    return svg(W, H, b, f"Dot plot of {len(leads)} lead times. The median is {median:.0f} "
               f"seconds, left of zero.")


def lead_planned(W, H, uid):
    x0, x1, y0, y1 = 28, W - 20, 54, H - 60
    X = lin(-180, 140, x0, x1)
    b = [hatch(uid, x0, y0, x1 - x0, y1 - y0)]
    b.append(L(x0, y1, x1, y1, RULE, 1.5))
    b.append(L(X(0), y0 - 8, X(0), y1 + 7, INK, 2.5))
    b.append(T(X(0), y1 + 28, "0", anchor="middle", weight=700, fill=INK))
    b.append(T(x0 + 4, y1 + 28, "← warning after the failure", size=17))
    b.append(T(x1 - 4, y1 + 28, "warning first →", size=17, anchor="end"))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "lead time (s); one dot per detected session",
               size=LABEL, anchor="middle"))
    b.append(tag(x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2, "AWAITING MEASUREMENT",
                 "101 degraded sessions planned"))
    return svg(W, H, b, "Empty template for the lead-time distribution of the physical "
               "phase, with zero marked. No data.")


# ---------------------------------------------------------------------------
# Fig. 6 -- false-alarm rate against the budget, and the silence gate
# ---------------------------------------------------------------------------
def fa_measured(W, H, rates, budget, silence, n_ff):
    b = []
    x0, x1 = 64, W - 24
    X = logs(0.03, 10, x0, x1)
    ya, yb = 34, 112
    for v in (0.1, 1, 10):
        b.append(L(X(v), ya, X(v), yb, GRID, 1))
        b.append(T(X(v), yb + 24, f"{v:g}", anchor="middle",
                   weight=700 if v == budget else 400))
    b.append(L(x0, yb, x1, yb, RULE, 1.5))
    b.append(L(X(budget), ya - 14, X(budget), yb + 6, INK, 2.5, dash="7 5"))
    b.append(T(X(budget) + 8, ya - 4, "budget 0.1 /h", size=17, fill=INK, weight=600))
    for part, y in (("T11", ya + 30), ("T5", ya + 62)):
        v = rates[part]
        b.append(T(x0 - 12, y + 6, part, anchor="end", weight=600, fill=INK))
        b.append(L(X(budget), y, X(v), y, BLUE_M, 5))
        b.append(f'<circle cx="{X(v):.1f}" cy="{y}" r="11" fill="{BLUE}"/>')
        if v >= 1:
            b.append(T(X(v) - 18, y - 12, f"{v:.2f} /h, {v / budget:.0f}× the budget", size=18,
                       fill=INK, anchor="end", weight=600))
        else:
            b.append(T(X(v) + 18, y + 6, f"{v:.3f} /h, {v / budget:.1f}×", size=18, fill=INK,
                       weight=600))
    b.append(T(x0 + (x1 - x0) / 2, yb + 47, "false alarms per hour (log scale)", size=LABEL,
               anchor="middle"))
    S = lin(0, 1, x0, x1)
    yc = yb + 82
    b.append(T(x0, yc - 8, "fault-free episodes whose risk score trends", size=LABEL - 1,
               fill=INK2))
    for i, part in enumerate(("T11", "T5")):
        y = yc + 2 + i * 30
        f = silence[part]
        b.append(T(x0 - 12, y + 18, part, anchor="end", weight=600, fill=INK))
        b.append(R(x0, y, x1 - x0, 24, fill="#EEF1F4"))
        b.append(R(x0, y, S(f) - x0, 24, fill=BLUE))
        k = round(f * n_ff[part])
        b.append(T(S(f) - 10, y + 18, f"{f * 100:.1f}%  ({k} of {n_ff[part]})", size=17,
                   fill="#FFFFFF", anchor="end", weight=600))
    yd = yc + 2 + 2 * 30 - 6
    b.append(L(S(0.10), yc - 2, S(0.10), yd + 6, INK, 2.5, dash="7 5"))
    b.append(T(S(0.10) + 8, yd + 22, "gate: at most 10%", size=17, fill=INK, weight=600))
    return svg(W, H, b, "False alarms per hour: 3.41 for T11 and 0.225 for T5 against a "
               "budget of 0.1. Fault-free episodes with a trending risk score: 76.5 percent "
               "and 100 percent against a gate of 10 percent.")


def fa_planned(W, H, uid, budget=0.1, frozen_h=4.0):
    b = []
    x0, x1 = 78, W - 24
    ya, yb = 34, 148
    Xh = lin(0, 32, x0, x1)
    Yr = logs(0.03, 10, yb, ya)
    b.append(hatch(uid, x0, ya, x1 - x0, yb - ya))
    for v in (0.1, 1, 10):
        b.append(T(x0 - 12, Yr(v) + 6, f"{v:g}", anchor="end",
                   weight=700 if v == budget else 400))
    for hh in (0, 10, 20, 30):
        b.append(L(Xh(hh), yb, Xh(hh), yb + 7, RULE, 1.5))
        b.append(T(Xh(hh), yb + 28, f"{hh}", anchor="middle"))
    b.append(frame(x0, ya, x1, yb))
    b.append(L(x0, Yr(budget), x1, Yr(budget), INK, 2.5, dash="7 5"))
    b.append(T(x0 + 10, Yr(budget) + 21, "budget 0.1 /h", size=17, fill=INK, weight=600))
    # rule of three: arithmetic, not a result
    pts = " ".join(f"{Xh(h / 10):.1f},{Yr(3 / (h / 10)):.1f}" for h in range(3, 321)
                   if 3 / (h / 10) <= 10)
    b.append(f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="2"/>')
    px, py = Xh(frozen_h), Yr(3 / frozen_h)
    b.append(L(px, py, px + 30, py - 18, INK, 1.5))
    b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="#FFFFFF" stroke="{INK}" '
             f'stroke-width="2.5"/>')
    b.append(T(px + 36, py - 30, f"frozen campaign: about {frozen_h:.0f} h held out;", size=17,
               fill=INK))
    b.append(T(px + 36, py - 8, f"zero alarms would bound it at {3 / frozen_h:.2f} /h",
               size=17, fill=INK))
    b.append(f'<circle cx="{Xh(30):.1f}" cy="{Yr(0.1):.1f}" r="7" fill="#FFFFFF" '
             f'stroke="{INK}" stroke-width="2.5"/>')
    b.append(T(Xh(30) - 12, Yr(0.1) + 21, "30 h reaches the budget", size=17, fill=INK,
               anchor="end"))
    b.append(T(x0 + (x1 - x0) / 2, yb + 50, "held-out fault-free recording (h)", size=LABEL,
               anchor="middle"))
    b.append(T(22, ya + (yb - ya) / 2, "alarms per hour", size=LABEL - 1, anchor="middle",
               rot=-90))
    S = lin(0, 1, x0, x1)
    yc = yb + 82
    b.append(T(x0, yc - 8, "fault-free sessions whose risk score trends", size=LABEL - 1,
               fill=INK2))
    b.append(hatch(uid + "b", x0, yc + 2, x1 - x0, 24))
    b.append(L(S(0.10), yc - 4, S(0.10), yc + 32, INK, 2.5, dash="7 5"))
    b.append(T(S(0.10) + 8, yc + 50, "gate: at most 10%", size=17, fill=INK, weight=600))
    b.append(T(x1, yc + 50, "of 101 sessions", size=17, fill=INK2, anchor="end"))
    return svg(W, H, b, "Empty template for the physical false-alarm rate. The only line "
               "drawn is arithmetic: the 95 percent upper bound that zero alarms would give "
               "after a number of held-out hours. No data.")


# ---------------------------------------------------------------------------
# Fig. 7 -- detection against false alarms per hour
# ---------------------------------------------------------------------------
def _dfa_axes(W, H, x0, x1, y0, y1):
    X = logs(0.05, 20, x0, x1)
    Y = lin(0, 1, y1, y0)
    b = []
    for v in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        b.append(T(x0 - 10, Y(v) + 6, f"{v * 100:.0f}", anchor="end"))
    for v in (0.1, 1, 10):
        b.append(L(X(v), y1, X(v), y1 + 7, RULE, 1.5))
        b.append(T(X(v), y1 + 28, f"{v:g}", anchor="middle",
                   weight=700 if v == 0.1 else 400))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "false alarms per hour (log scale)", size=LABEL,
               anchor="middle"))
    b.append(T(20, y0 + (y1 - y0) / 2, "faults detected (%)", size=LABEL, anchor="middle",
               rot=-90))
    return X, Y, b


def _dfa_refs(X, Y, x0, x1, y0, y1):
    b = [L(X(0.1), y0 - 10, X(0.1), y1, INK, 2.5, dash="7 5"),
         T(X(0.1) + 8, y0 + 22, "budget 0.1 /h", size=17, fill=INK, weight=600),
         L(x0, Y(0.8), x1, Y(0.8), INK, 1.5, dash="2 5"),
         T(X(0.1) + 8, Y(0.8) + 22, "target: 80% detected", size=17, fill=INK)]
    return b


def dfa_measured(W, H, curves, inside):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    X, Y, b = _dfa_axes(W, H, x0, x1, y0, y1)
    for v in (0.2, 0.4, 0.6, 0.8, 1.0):
        b.append(L(x0, Y(v), x1, Y(v), GRID, 1))
    b.append(frame(x0, y0, x1, y1))
    for part, dash, col in (("T11", None, BLUE), ("T5", "9 6", "#0E3A5E")):
        pts = [(f, d) for f, d in curves[part] if 0.05 <= f <= 20]
        s = " ".join(f"{X(f):.1f},{Y(d):.1f}" for f, d in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        b.append(f'<polyline points="{s}" fill="none" stroke="{col}" stroke-width="3.5" '
                 f'stroke-linejoin="round"{da}/>')
    b += _dfa_refs(X, Y, x0, x1, y0, y1)
    lx, ly = X(0.1) + 8, Y(0.8) + 22
    b.append(T(lx, ly + 30, "detected inside the budget:", size=17, fill=INK, weight=600))
    b.append(T(lx, ly + 52, f"{inside['T11'] * 100:.1f}% (T11), {inside['T5'] * 100:.1f}% (T5)",
               size=17, fill=INK, weight=600))
    gx, gy = x1 - 196, y0 + 16
    b.append(L(gx, gy, gx + 40, gy, BLUE, 3.5))
    b.append(T(gx + 48, gy + 6, "T11", size=17, fill=INK, weight=600))
    b.append(f'<line x1="{gx + 100}" y1="{gy}" x2="{gx + 140}" y2="{gy}" '
             f'stroke="#0E3A5E" stroke-width="3.5" stroke-dasharray="9 6"/>')
    b.append(T(gx + 148, gy + 6, "T5", size=17, fill=INK, weight=600))
    return svg(W, H, b, "Detection against false alarms per hour for T11 and T5. Inside the "
               "0.1 per hour budget, detection is near zero on both.")


def dfa_planned(W, H, uid):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    X, Y, b = _dfa_axes(W, H, x0, x1, y0, y1)
    b.insert(0, hatch(uid, x0, y0, x1 - x0, y1 - y0))
    b.append(frame(x0, y0, x1, y1))
    b += _dfa_refs(X, Y, x0, x1, y0, y1)
    b.append(tag(x0 + (x1 - x0) * 0.56, y0 + (y1 - y0) * 0.68, "AWAITING MEASUREMENT",
                 "swept on held-out sessions"))
    return svg(W, H, b, "Empty template for detection against false alarms per hour in the "
               "physical phase, with the budget and the 80 percent target marked. No data.")


# ---------------------------------------------------------------------------
# Fig. 8 -- detection by fault type (measured) and by type and severity (planned)
# ---------------------------------------------------------------------------
def mode_dumbbell(W, H, values, modes, names):
    """Four fault types, two arrays each, on ONE axis so the pattern can be compared."""
    b = []
    x0, x1 = 232, W - 122
    y0, y1 = 52, H - 62
    X = lin(0.3, 0.9, x0, x1)
    group = (y1 - y0) / len(modes)
    for v in (0.3, 0.5, 0.7, 0.9):
        b.append(L(X(v), y0 - 6, X(v), y1, GRID if v != 0.5 else INK, 1 if v != 0.5 else 2,
                   dash=None if v != 0.5 else "7 5"))
        b.append(T(X(v), y1 + 26, f"{v:.1f}", anchor="middle",
                   weight=700 if v == 0.5 else 400, fill=INK if v == 0.5 else INK2))
    b.append(T(X(0.5), y0 - 14, "chance", size=17, fill=INK, anchor="middle", weight=600))
    # column heads double as the legend
    c1, c2 = x1 + 40, x1 + 96
    b.append(f'<circle cx="{c1}" cy="{y0 - 20}" r="8" fill="{BLUE}"/>')
    b.append(R(c2 - 7, y0 - 27, 14, 14, fill="#FFFFFF", stroke=INK, sw=2.5))
    b.append(T(c1 - 4, y0 - 36, "monitor", size=17, fill=BLUE, anchor="middle", weight=600))
    b.append(T(c2, y0 - 36, "count", size=17, fill=INK2, anchor="middle", weight=600))
    for gi, m in enumerate(modes):
        gy = y0 + group * gi
        if gi:
            b.append(L(0, gy, W, gy, GRID, 1))
        a, c = names[m]
        b.append(T(0, gy + group / 2 - 4, a, size=18, fill=INK, weight=600))
        b.append(T(0, gy + group / 2 + 16, c, size=17, fill=INK2))
        for pi, part in enumerate(("T11", "T5")):
            y = gy + group / 2 + (pi - 0.5) * 21
            g = values[part]["decoder_guard"][gi]
            k = values[part]["mean_activity"][gi]
            b.append(T(x0 - 12, y + 6, part, size=17, fill=INK2, anchor="end"))
            b.append(L(X(min(g, k)), y, X(max(g, k)), y, BLUE_M, 4))
            b.append(R(X(k) - 7, y - 7, 14, 14, fill="#FFFFFF", stroke=INK, sw=2.5))
            b.append(f'<circle cx="{X(g):.1f}" cy="{y:.1f}" r="8" fill="{BLUE}"/>')
            b.append(T(c1, y + 6, f"{g:.2f}", size=17, fill=BLUE, weight=700, anchor="middle"))
            b.append(T(c2, y + 6, f"{k:.2f}", size=17, fill=INK2, anchor="middle"))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "window-level AUC", size=LABEL, anchor="middle"))
    return svg(W, H, b, "AUC by fault type for the monitor and for counting activity, on two "
               "arrays. The monitor wins on the two faults that leave total activity "
               "unchanged and loses on overall signal loss.")


def severity_planned(W, H, uid, types):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    Y = lin(0, 1, y1, y0)
    Xs = lin(0, 1.1, x0, x1)
    b = [hatch(uid, x0, y0, x1 - x0, y1 - y0)]
    for v in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        b.append(T(x0 - 10, Y(v) + 6, f"{v * 100:.0f}", anchor="end"))
    b.append(frame(x0, y0, x1, y1))
    for v, lab in ((0.25, "0.25"), (0.5, "0.5"), (1.0, "1.0")):
        b.append(L(Xs(v), y0, Xs(v), y1 + 7, INK3, 1.5, dash="3 5"))
        b.append(T(Xs(v), y1 + 28, lab, anchor="middle", weight=600, fill=INK))
    b.append(T(x0, y1 + 28, "0", anchor="middle"))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "severity of the imposed fault", size=LABEL,
               anchor="middle"))
    b.append(T(20, y0 + (y1 - y0) / 2, "faults detected (%)", size=LABEL, anchor="middle",
               rot=-90))
    # marker shapes are fixed now, so the measured chart needs no redesign
    lx, ly = x0 + 16, y0 + 18
    b.append(R(lx - 8, ly - 10, 252, 26 * len(types) + 12, fill="#FFFFFF", stroke=RULE))
    for i, name in enumerate(types):
        y = ly + 8 + i * 26
        cx = lx + 10
        if i == 0:
            b.append(f'<circle cx="{cx}" cy="{y}" r="7" fill="none" stroke="{ORG}" '
                     f'stroke-width="2.5"/>')
        elif i == 1:
            b.append(R(cx - 7, y - 7, 14, 14, stroke=ORG, sw=2.5))
        elif i == 2:
            b.append(f'<path d="M{cx} {y - 9} L{cx + 9} {y + 7} L{cx - 9} {y + 7} Z" '
                     f'fill="none" stroke="{ORG}" stroke-width="2.5"/>')
        else:
            b.append(f'<path d="M{cx} {y - 9} L{cx + 9} {y} L{cx} {y + 9} L{cx - 9} {y} Z" '
                     f'fill="none" stroke="{ORG}" stroke-width="2.5"/>')
        b.append(T(cx + 20, y + 6, name, size=17, fill=INK))
    b.append(tag(x0 + (x1 - x0) / 2 + 20, y0 + (y1 - y0) * 0.81, "AWAITING MEASUREMENT",
                 "with 95% intervals"))
    return svg(W, H, b, "Empty template for detection against fault severity, one series "
               "per fault type. No data.")


# ---------------------------------------------------------------------------
# Fig. 9 -- monitor score against decoding performance
# ---------------------------------------------------------------------------
def scatter_measured(W, H, series, fail_deg):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    X = lin(1.05, 0.30, x0, x1)          # similarity falls to the right: more drift
    Y = lin(0, 130, y1, y0)
    b = []
    for v in (0, 40, 80, 120):
        b.append(L(x0, Y(v), x1, Y(v), GRID, 1))
        b.append(T(x0 - 10, Y(v) + 6, f"{v}", anchor="end"))
    for v in (1.0, 0.8, 0.6, 0.4):
        b.append(L(X(v), y1, X(v), y1 + 7, RULE, 1.5))
        b.append(T(X(v), y1 + 28, f"{v:.1f}", anchor="middle"))
    b.append(frame(x0, y0, x1, y1))
    b.append(L(x0, Y(fail_deg), x1, Y(fail_deg), INK, 2, dash="7 5"))
    b.append(T(x0 + 8, Y(fail_deg) - 8, f"failure level {fail_deg:.1f}°", size=17, fill=INK,
               weight=600))
    for s in series:
        b.append(f'<circle cx="{X(s["cosine_to_first_session"]):.1f}" '
                 f'cy="{Y(s["median_error_deg"]):.1f}" r="10" fill="{BLUE}" '
                 f'stroke="#FFFFFF" stroke-width="2"/>')
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "drift measure: similarity to session 1",
               size=LABEL, anchor="middle"))
    b.append(T(x1 - 4, y1 - 10, "more drift →", size=17, fill=INK2, anchor="end"))
    b.append(T(20, y0 + (y1 - y0) / 2, "median decoding error (°)", size=LABEL,
               anchor="middle", rot=-90))
    return svg(W, H, b, f"Scatter of {len(series)} sessions: decoding error rises as the "
               "monitor's drift measure falls.")


def scatter_planned(W, H, uid):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    b = [hatch(uid, x0, y0, x1 - x0, y1 - y0), frame(x0, y0, x1, y1)]
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "monitor's risk score, per session", size=LABEL,
               anchor="middle"))
    b.append(T(20, y0 + (y1 - y0) / 2, "median decoding error (°)", size=LABEL,
               anchor="middle", rot=-90))
    b.append(tag(x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2, "AWAITING MEASUREMENT",
                 "one point per recorded session"))
    return svg(W, H, b, "Empty template for monitor score against decoding error in the "
               "physical phase. No data.")


# ---------------------------------------------------------------------------
# Fig. 10 -- detection against how often the monitor decides
# ---------------------------------------------------------------------------
def _dr_axes(W, H, x0, x1, y0, y1, ticks):
    X = logs(9, 900, x0, x1)             # fewer decisions to the left
    Y = lin(0.3, 1.0, y1, y0)
    b = []
    for v in (0.4, 0.6, 0.8, 1.0):
        b.append(T(x0 - 10, Y(v) + 6, f"{v * 100:.0f}", anchor="end"))
    for v in ticks:
        b.append(L(X(v), y1, X(v), y1 + 7, RULE, 1.5))
        b.append(T(X(v), y1 + 28, f"{v:g}", anchor="middle"))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "decisions per hour (log scale; fewer to the left)",
               size=LABEL, anchor="middle"))
    b.append(T(20, y0 + (y1 - y0) / 2, "faults detected (%)", size=LABEL, anchor="middle",
               rot=-90))
    return X, Y, b


def decision_measured(W, H, curves):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    X, Y, b = _dr_axes(W, H, x0, x1, y0, y1, (13, 27, 65, 120, 240, 720))
    for v in (0.4, 0.6, 0.8, 1.0):
        b.append(L(x0, Y(v), x1, Y(v), GRID, 1))
    b.append(frame(x0, y0, x1, y1))
    for part, col, dx, dash in (("T11", BLUE, -5, None), ("T5", "#0E3A5E", 5, "9 6")):
        c = curves[part]
        for q in c:
            x = X(q["per_hour"]) + dx
            b.append(L(x, Y(q["lo"]), x, Y(q["hi"]), col, 2))
            b.append(L(x - 5, Y(q["lo"]), x + 5, Y(q["lo"]), col, 2))
            b.append(L(x - 5, Y(q["hi"]), x + 5, Y(q["hi"]), col, 2))
        s = " ".join(f"{X(q['per_hour']) + dx:.1f},{Y(q['detection']):.1f}" for q in c)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        b.append(f'<polyline points="{s}" fill="none" stroke="{col}" stroke-width="3.5"{da}/>')
        for q in c:
            x, y = X(q["per_hour"]) + dx, Y(q["detection"])
            if part == "T11":
                b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}"/>')
            else:
                b.append(R(x - 6.5, y - 6.5, 13, 13, fill="#FFFFFF", stroke=col, sw=2.5))
    b.append(T(X(13) + 16, Y(0.966) - 12, "T11", size=18, fill=BLUE, weight=700))
    b.append(T(X(27) - 16, Y(0.683) + 28, "T5", size=18, fill="#0E3A5E", weight=700,
               anchor="end"))
    return svg(W, H, b, "Detection against decisions per hour with 95 percent intervals. "
               "On T11 detection rises as the monitor decides less often; on T5 it falls.")


def decision_planned(W, H, uid):
    x0, x1, y0, y1 = 78, W - 20, 28, H - 62
    X, Y, b = _dr_axes(W, H, x0, x1, y0, y1, (12, 27, 65, 120, 240, 720))
    b.insert(0, hatch(uid, x0, y0, x1 - x0, y1 - y0))
    b.append(frame(x0, y0, x1, y1))
    b.append(L(X(12), y0, X(12), y1, INK, 1.5, dash="2 5"))
    b.append(T(X(12) + 8, y1 - 10, "1 per session", size=17, fill=INK, weight=600))
    lx, ly = x0 + 36, y0 + 10
    b.append(R(lx - 10, ly - 2, x1 - lx, 58, fill="#FFFFFF", stroke=RULE))
    labs = ("A  baseline", "B  exposure ×2", "C  patch 24", "D  96 channels")
    for i, lab in enumerate(labs):
        x = lx + (i % 2) * 178
        y = ly + 14 + (i // 2) * 26
        b.append(L(x, y, x + 34, y, ORG, 3, dash=(None, "9 6", "2 6", "14 5 2 5")[i]))
        b.append(T(x + 42, y + 6, lab, size=17, fill=INK))
    b.append(tag(x0 + (x1 - x0) / 2 + 16, y0 + (y1 - y0) * 0.66, "AWAITING MEASUREMENT",
                 "same recordings, re-scored"))
    return svg(W, H, b, "Empty template for the decision-rate curve in the physical phase, "
               "one line per apparatus configuration. No data.")


# ---------------------------------------------------------------------------
# Fig. 13 -- lead time and false-alarm rate across apparatus configurations
# ---------------------------------------------------------------------------
def configs_planned(W, H, uid):
    b = []
    half = (W - 40) / 2
    for k, (title, unit) in enumerate((("median lead time", "s"),
                                       ("false alarms per hour", "/h"))):
        x0 = 150 + k * (half + 20) - (0 if k == 0 else 96)
        x0 = 150 if k == 0 else half + 70
        x1 = (half - 6) if k == 0 else W - 16
        y0, y1 = 34, H - 38
        b.append(hatch(f"{uid}{k}", x0, y0, x1 - x0, y1 - y0))
        b.append(T(x0, y0 - 14, f"{title} ({unit}), 95% interval", size=17, fill=INK,
                   weight=600))
        rowh = (y1 - y0) / 4
        for i, lab in enumerate("ABCD"):
            y = y0 + rowh * (i + 0.5)
            if k == 0:
                b.append(T(0, y + 6, ("A  baseline", "B  exposure ×2", "C  patch 24",
                                      "D  96 channels")[i], size=17, fill=INK))
            b.append(L(x0, y, x1, y, "#FFFFFF", 2))
        mid = x0 + (x1 - x0) * (0.5 if k == 0 else 0.22)
        b.append(L(mid, y0 - 4, mid, y1 + 6, INK, 2.5, dash=None if k == 0 else "7 5"))
        b.append(T(mid, y1 + 28, "0" if k == 0 else "budget 0.1", size=17, fill=INK,
                   weight=700, anchor="middle"))
    return svg(W, H, b, "Empty template comparing four apparatus configurations on median "
               "lead time and false-alarm rate. No data.")


# ---------------------------------------------------------------------------
# Introduction -- one decoder left fixed for 142 days (real, archived)
# ---------------------------------------------------------------------------
def drift_line(W, H, series, fail_deg):
    x0, x1, y0, y1 = 66, W - 18, 20, H - 56
    d0 = series[0]["trial_day"]
    X = lin(0, 150, x0, x1)
    Y = lin(0, 130, y1, y0)
    b = [R(x0, y0, x1 - x0, Y(fail_deg) - y0, fill="#F7E6EB")]
    for v in (0, 40, 80, 120):
        b.append(L(x0, Y(v), x1, Y(v), GRID, 1))
        b.append(T(x0 - 10, Y(v) + 6, f"{v}", anchor="end"))
    for v in (0, 50, 100, 150):
        b.append(L(X(v), y1, X(v), y1 + 7, RULE, 1.5))
        b.append(T(X(v), y1 + 27, f"{v}", anchor="middle"))
    b.append(frame(x0, y0, x1, y1))
    b.append(L(x0, Y(fail_deg), x1, Y(fail_deg), INK, 2, dash="7 5"))
    b.append(T(x0 + 10, y0 + 22, "above the dashed line: failure", size=17, fill=WINE,
               weight=600))
    b.append(T(x0 + 10, y0 + 43, "(twice the day-1 error)", size=17, fill=INK2))
    pts = [(X(q["trial_day"] - d0), Y(q["median_error_deg"])) for q in series]
    b.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
             + f'" fill="none" stroke="{BLUE}" stroke-width="3" stroke-linejoin="round"/>')
    for (x, y), q in zip(pts, series):
        over = q["median_error_deg"] > fail_deg
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{WINE if over else BLUE}" '
                 f'stroke="#FFFFFF" stroke-width="2"/>')
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "days since the first session", size=LABEL,
               anchor="middle"))
    b.append(T(18, y0 + (y1 - y0) / 2, "cursor error (°)", size=LABEL, anchor="middle",
               rot=-90))
    return svg(W, H, b, f"Median cursor error by session over {series[-1]['trial_day'] - d0} "
               "days with a fixed decoder. Error stays near 20 to 35 degrees, then rises above "
               "the failure level to around 100 degrees.")


# ---------------------------------------------------------------------------
# Analysis -- the score the monitor reached, and the score it would need
# ---------------------------------------------------------------------------
def auc_gap(W, H, achieved, needed):
    x0, x1 = 20, W - 20
    X = lin(0.5, 1.0, x0, x1)
    y = H - 46
    b = [R(X(max(achieved.values())), y - 16, X(min(needed.values())) - X(max(achieved.values())),
           32, fill="#F7E6EB")]
    b.append(L(x0, y, x1, y, RULE, 2))
    for v in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        b.append(L(X(v), y - 6, X(v), y + 6, RULE, 1.5))
        b.append(T(X(v), y + 30, f"{v:.1f}", anchor="middle",
                   weight=700 if v == 0.5 else 400, fill=INK if v == 0.5 else INK2))
    b.append(T(X(0.5), y - 54, "coin flip", size=17, fill=INK2, anchor="start"))
    b.append(L(X(0.5), y - 46, X(0.5), y - 8, INK2, 1.5, dash="4 4"))
    for part, dy in (("T11", -54), ("T5", -54)):
        v = achieved[part]
        b.append(f'<circle cx="{X(v):.1f}" cy="{y}" r="10" fill="{BLUE}" stroke="#FFFFFF" '
                 f'stroke-width="2"/>')
        b.append(T(X(v), y + dy + 22, f"{v:.3f}", size=18, fill=BLUE, anchor="middle",
                   weight=700))
        b.append(T(X(v), y + dy, part, size=17, fill=BLUE, anchor="middle"))
    n = min(needed.values())
    b.append(L(X(n), y - 62, X(n), y + 8, INK, 3))
    b.append(T(X(n) - 10, y - 54, "needed", size=17, fill=INK, anchor="end", weight=600))
    b.append(T(X(n) - 10, y - 32, f"{n:.3f}", size=18, fill=INK, anchor="end", weight=700))
    mid = (X(max(achieved.values())) + X(n)) / 2
    b.append(T(mid, y + 6, "the gap", size=17, fill=WINE, anchor="middle", weight=600))
    return svg(W, H, b, f"Session score reached, {achieved['T11']:.3f} and "
               f"{achieved['T5']:.3f}, against the {n:.3f} needed at one decision per session.")


# ---------------------------------------------------------------------------
# One archived episode, for a narrow column: events lettered, explained in the caption
# ---------------------------------------------------------------------------
def episode_compact(ep, W, H, win_s=30.0, step_s=5.0):
    x0, x1, y0, y1 = 62, W - 18, 46, H - 54
    t = [i * step_s + win_s for i in range(len(ep["risk"]))]     # window END time
    X = lin(t[0], t[-1], x0, x1)
    ymax = 120.0
    Y = lin(0, ymax, y1, y0)
    b = []
    for v in (0, 40, 80, 120):
        b.append(L(x0, Y(v), x1, Y(v), GRID, 1))
        b.append(T(x0 - 10, Y(v) + 6, f"{v}", anchor="end"))
    for s in range(60, 301, 60):
        b.append(L(X(s), y1, X(s), y1 + 7, RULE, 1.5))
        b.append(T(X(s), y1 + 27, f"{s}", anchor="middle"))
    b.append(frame(x0, y0, x1, y1))
    b.append(T(x0 + (x1 - x0) / 2, H - 6, "time at the end of each 30 s window (s)", size=LABEL,
               anchor="middle"))
    b.append(T(18, y0 + (y1 - y0) / 2, "risk score", size=LABEL, anchor="middle", rot=-90))
    th = ep["warn_threshold"]
    b.append(L(x0, Y(th), x1, Y(th), INK, 1.5, dash="7 5"))
    b.append(T(x1 - 4, Y(th) + 22, "warning threshold", size=17, fill=INK, anchor="end"))
    t_on = ep["onset_w"] * step_s
    t_fail = ep["crossing_w"] * step_s + win_s
    t_warn = ep["warn_w"] * step_s + win_s
    b.append(R(X(t_fail), y0, X(t_warn) - X(t_fail), y1 - y0, fill=BLUE_T))
    pts = " ".join(f"{X(a):.1f},{Y(min(v, ymax)):.1f}" for a, v in zip(t, ep["risk"]))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{BLUE}" stroke-width="3.5" '
             f'stroke-linejoin="round" stroke-linecap="round"/>')
    for tx, col, letter in ((t_on, WINE, "A"), (t_fail, INK, "B"), (t_warn, BLUE, "C")):
        b.append(L(X(tx), y0 - 8, X(tx), y1, col, 2.5))
        b.append(f'<circle cx="{X(tx):.1f}" cy="{y0 - 22}" r="13" fill="{col}"/>')
        b.append(T(X(tx), y0 - 16, letter, size=17, fill="#FFFFFF", anchor="middle", weight=700))
    b.append(T(X(t_warn) + 22, y0 - 16, f"lead time = {ep['lead_s']:+.0f} s".replace("-", "−"),
               size=19, fill=INK, weight=700))
    return svg(W, H, b, f"Risk score over one archived episode. The fault starts at "
               f"{t_on:.0f} seconds, decoding fails at {t_fail:.0f} seconds and the monitor "
               f"warns at {t_warn:.0f} seconds, a lead time of {ep['lead_s']:.0f} seconds.")
