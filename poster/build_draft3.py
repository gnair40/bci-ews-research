#!/usr/bin/env python3
"""
build_draft3.py -- Draft 3 of the trifold: the data and its analysis in the centre.

    python3 poster/build_poster_data.py     # recompute and check every number
    python3 poster/build_draft3.py          # write D3-Left, D3-Centre, D3-Right

WHAT CHANGED FROM DRAFT 2, AND WHY
----------------------------------
The researcher's review of Draft 2: the method took the centre and the data and
analysis were pushed to one side; the dark navy band and the yellow highlighter
did not belong with the rest of the board.

So here:

    left     abstract, introduction, why it matters, purpose, hypothesis,
             and a compact materials-and-methods block
    centre   title, then RESULTS, DATA and ANALYSIS: five real charts and the
             numbers they support
    right    DISCUSSION of those results, the conclusion, then pictures,
             hardware and references

The palette is the first draft's: white, ink, blue for what was measured,
orange for what is still to be measured. Nothing dark, nothing yellow.

The 24 pt floor from Draft 2 is kept. Components are shared with
build_draft2.py; only the layout and the colour of emphasis differ.
"""
from __future__ import annotations

import build_draft2 as B
import charts as C

D, S = B.D, B.S
INK, INK2, INK3, RULE = B.INK, B.INK2, B.INK3, B.RULE
BLUE, BLUE_T, ORG, WINE = B.BLUE, B.BLUE_T, B.ORG, B.WINE
SERIF, SANS, MONO, MIN = B.SERIF, B.SANS, B.MONO, B.MIN
label, head, p, sec, cap, b, photo, num = (B.label, B.head, B.p, B.sec, B.cap, B.b, B.photo,
                                           B.num)

# Emphasis in this draft is a pale blue ground, not a yellow one. The shared
# components read these names when they are called, so setting them here is
# enough to recolour the quadrant, the verdict tree and every highlight.
B.MARK = BLUE_T


def finding(text: str) -> str:
    return (f'<h3 style="margin: 0; font-family: {SERIF}; font-size: 44px; line-height: 50px; '
            f'font-weight: 700; color: {INK}; text-wrap: balance">{text}</h3>')


# ===========================================================================
# LEFT -- the question, and a compact account of the method
# ===========================================================================
def bench_narrow() -> str:
    """The test bench, drawn to fit a 12 inch panel. Source units: 17 print at 32 px."""
    T, Ln, R = C.T, C.L, C.R
    W, H = 552, 250
    s = [T(14, 22, "sealed dark box", 18, INK, weight=600)]
    s.append(R(14, 32, 372, 178, fill="#FFFFFF", stroke=INK, sw=2.5))
    s.append(R(20, 38, 360, 166, fill="none", stroke="#39424B", sw=6))
    s.append(f'<path d="M52 62 L300 121 L52 180 Z" fill="{B.ORG_T}" stroke="{B.ORG_M}" '
             f'stroke-width="1.5" stroke-dasharray="6 5"/>')
    s.append(R(36, 58, 16, 126, fill=B.ORG_T, stroke=ORG, sw=2.5))
    s.append(T(62, 58, "screen", 18, ORG, weight=600))
    s.append(R(214, 86, 7, 70, fill="#F7E6EB", stroke=WINE, sw=2, dash="5 4"))
    s.append(T(217, 180, "filter", 18, WINE, anchor="middle", weight=600))
    s.append(R(308, 107, 32, 28, fill=B.ORG_T, stroke=ORG, sw=2.5, rx=3))
    s.append(R(300, 114, 8, 14, fill=ORG, stroke=ORG, sw=1))
    s.append(Ln(324, 135, 324, 166, INK, 3))
    s.append(R(298, 166, 52, 10, fill="#F7E6EB", stroke=WINE, sw=2, rx=2))
    s.append(T(324, 196, "camera", 18, ORG, anchor="middle", weight=600))
    s.append(Ln(340, 121, 418, 121, BLUE, 2.5))
    s.append(R(381, 114, 8, 14, fill="#FFFFFF", stroke=INK, sw=1.2))
    s.append(R(418, 86, 122, 70, fill=BLUE_T, stroke=BLUE, sw=2.5, rx=4))
    s.append(T(479, 117, "Raspberry", 18, BLUE, anchor="middle", weight=600))
    s.append(T(479, 139, "Pi 4", 18, BLUE, anchor="middle", weight=600))
    s.append(f'<path d="M450 156 L450 232 L44 232 L44 184" fill="none" stroke="{BLUE}" '
             f'stroke-width="2.5" stroke-linejoin="round"/>')
    return C.svg(W, H, s, "Side view of the test bench: a screen at one end of a sealed dark "
                 "box faces a camera at the other, with a filter that can slide into the light "
                 "path. A Raspberry Pi outside drives the screen and records the camera.")


def left_panel() -> str:
    L11 = D["lead_time"]["T11"]
    n = S["episodes"]
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
          MIN, 42)))
    parts.append(sec(
        label("Introduction"),
        p("Nearly 5.4 million people in the United States live with paralysis [3]. For some, "
          "an implanted brain-computer interface restores control of a cursor by intent. Its "
          "decoder goes wrong as the recording drifts, so decoders often need daily "
          "recalibration, and the device cannot be used freely while that happens [2].",
          MIN, 42), gap=12))
    parts.append(sec(
        label("Why it matters"),
        head("A warning helps only if it is early and rarely wrong", 46),
        B.quadrant(),
        p("Alarms that cry wolf get switched off: nuisance alarms are the leading reason "
          "smoke alarms are disconnected [5]. Existing work corrects drift automatically "
          "[2, 6] or reports that a drift score correlates with performance [1]. No published "
          "lead time or false-alarm rate was found for such a monitor.", MIN, 42),
        gap=12))
    parts.append(sec(
        label("Purpose"),
        p("To measure how early a decoder-health monitor warns, and how often it warns when "
          "nothing is wrong, on test beds where the moment of failure is known in advance.",
          MIN, 42, INK)))
    parts.append(sec(
        label("Hypothesis / Engineering goal"),
        p(b("Hypothesis.") + " Measured against failure times fixed in advance, lead time and "
          "false-alarm rate will fall outside what a deployed system could use. "
          + b("Falsified if", WINE) + " the median lead time is above zero and the 95% upper "
          "bound on false alarms is within 0.1 per hour.", MIN, 42),
        p(b("Engineering goal.") + " Build the monitor, the benchmark and the test bench that "
          "make both measurable. Success is a trustworthy measurement, not a claim that the "
          "monitor works.", MIN, 42),
        gap=10))
    parts.append(sec(
        label("Materials and methods"),
        B.compare(),
        bench_narrow(),
        cap("1", "The optical test bench as specified; not built yet. A fault begins at a "
                 "moment sealed before recording, and each warning is scored against it. "
                 "Parts: Raspberry Pi 4, Camera Module 3, display, enclosure, ND 0.6 filter, "
                 "stepper motor, DHT22 sensor."),
        gap=12))
    return B.page("Draft 3, left panel: question and method", B.PW_SIDE, B.PH,
                  "\n".join(parts), 56, gap=22)


# ===========================================================================
# CENTRE -- results, data and analysis
# ===========================================================================
def recolour(svg_: str) -> str:
    """The step pictures were drawn white on dark. Here they are ink on white."""
    return (svg_.replace('stroke="#FFFFFF"', f'stroke="{INK}"')
                .replace('fill="#FFFFFF"', f'fill="{INK}"')
                .replace('width="320" height="150"', 'width="256" height="120"'))


def step(n: int, art: str, title: str, text: str) -> str:
    return (f'<div style="display: flex; flex-direction: column; gap: 6px">{recolour(art)}'
            f'<div style="display: flex; align-items: center; gap: 12px">'
            f'<span style="width: 50px; height: 50px; flex: none; border-radius: 50%; '
            f'background: {INK}; color: #FFFFFF; font-family: {SERIF}; font-size: 34px; '
            f'font-weight: 700; display: flex; align-items: center; justify-content: center">'
            f'{n}</span><span style="font-family: {SERIF}; font-size: 42px; line-height: 48px; '
            f'font-weight: 700; color: {INK}; white-space: nowrap">{title}</span></div>'
            f'<span style="font-size: {MIN}px; line-height: 41px; color: {INK2}">{text}</span>'
            f'</div>')


def one_minute() -> str:
    amber, navy = B.AMBER, B.NAVY
    B.AMBER, B.NAVY = BLUE, "#FDFEFF"       # accent and knock-out for a white ground
    try:
        steps = (
            step(1, B.picto_problem(), "The decoder goes stale",
                 "The brain signal drifts and the decoder goes wrong without saying so.")
            + step(2, B.picto_idea(), "Add a warning light",
                   "A monitor should warn before control is lost.")
            + step(3, B.picto_catch(), "Test the warning",
                   "It must be early and rarely wrong. Neither had been measured.")
            + step(4, B.picto_build(), "Build the test",
                   "Two test beds where the moment of failure is known in advance."))
    finally:
        B.AMBER, B.NAVY = amber, navy
    return sec(
        label("The project in one minute"),
        f'<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); '
        f'gap: 36px">{steps}</div>', gap=12)


def key(big: str, text: str) -> str:
    return (f'<div style="border-top: 5px solid {BLUE}; padding-top: 8px; display: flex; '
            f'flex-direction: column; gap: 2px"><span style="font-family: {SERIF}; '
            f'font-size: 86px; line-height: 92px; font-weight: 700; color: {BLUE}; '
            f'white-space: nowrap">{big}</span><span style="font-size: {MIN}px; '
            f'line-height: 41px; color: {INK2}">{text}</span></div>')


def chart_card(title: str, svg_: str, n: str, caption: str) -> str:
    return (f'<div style="min-width: 0; display: flex; flex-direction: column; gap: 8px">'
            + finding(title) + svg_ + cap(n, caption) + "</div>")


def centre_panel() -> str:
    v = D["fault_mode_auc"]["values"]
    g = [v[a]["decoder_guard"][i] for a in ("T11", "T5") for i in (2, 3)]
    k = [v[a]["mean_activity"][i] for a in ("T11", "T5") for i in (2, 3)]
    L11, L5 = D["lead_time"]["T11"], D["lead_time"]["T5"]
    ci = L11["ci95_s"]
    fa = S["false_alarms_per_hour"]
    f = S["funnel"]
    dvf = D["detection_vs_fa"]
    pr = D["decision_rate"]["paired"]["participants"]
    a, t5 = pr["T11"]["own_range"], pr["T5"]["own_range"]
    pct = lambda x: B.minus(f"{x * 100:+.1f}")
    names = {"RATE_LOSS": ("Signal loss", "total falls"),
             "CHANNEL_DROPOUT": ("Dropout", "channels go silent"),
             "GAIN_DRIFT": ("Gain drift", "total unchanged"),
             "GEOMETRY_ROTATION": ("Rotation", "total unchanged")}
    W, H = 552, 286
    two = "display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 44px"

    numbers = (
        f'<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); '
        f'gap: 36px">'
        + key(f"{min(g):.2f} to {max(g):.2f}",
              f"detection score on faults that plain counting scores {min(k):.2f} to "
              f"{max(k):.2f} on; 0.5 is a coin flip")
        + key(f"{abs(L11['median_s']):.0f} s late",
              "the typical warning arrives after decoding has already failed")
        + key(f"{fa['T11'] / S['budget_per_hour']:.0f}× too often",
              f"{fa['T11']:.2f} false alarms per hour against a budget of 0.1")
        + key(f"{f['all_gates']} of {f['run']}",
              "monitor configurations pass all five acceptance gates")
        + "</div>")

    row1 = (f'<div style="{two}">'
            + chart_card("It sees faults that counting misses",
                         C.mode_dumbbell(W, H, v, D["fault_mode_auc"]["modes"], names), "2",
                         "Detection score by fault type on two arrays. Filled: the monitor. "
                         "Open: counting activity.")
            + chart_card("But the warning comes after the failure",
                         C.lead_dots(W, H, L11["leads_s"], L11["median_s"]), "3",
                         f"One dot per detected fault, array T11 ({L11['n_detected']} of "
                         f"{L11['n_degraded']}). Median {num(L11['median_s'], 0)} s, 95% CI "
                         f"{num(ci[0], 0)} to {num(ci[1], 0)}.")
            + "</div>")
    row2 = (f'<div style="{two}">'
            + chart_card("And it warns far too often",
                         C.fa_measured(W, H, fa, S["budget_per_hour"],
                                       S["silence_fault_free_fraction"],
                                       S["fault_free_episodes"]), "4",
                         "False alarms per hour against the budget, and how often the risk "
                         "score drifts when nothing is wrong.")
            + chart_card("No threshold fixes both at once",
                         C.dfa_measured(W, H, dvf["curves"],
                                        {"T11": dvf["best_inside_budget_T11"],
                                         "T5": dvf["best_inside_budget_T5"]}), "5",
                         "Sweeping the warning threshold: detection is high only where false "
                         "alarms run at several per hour.")
            + "</div>")
    why = (f'<div style="min-width: 0; display: flex; flex-direction: column; gap: 10px">'
           + finding("Why: one measurement, 720 decisions")
           + p(f"Risk scores within a session are near-copies of each other (lag‑1 "
               f"autocorrelation {S['lag1_pooled']['T11']:.3f}), so 720 decisions an hour rest "
               f"on about one independent measurement. Even deciding once per session would "
               f"need a score of {S['auc_needed_at_budget']['T11']:.3f}.", MIN, 42)
           + C.auc_gap(W, 128, S["auc_session"], S["auc_needed_at_budget"])
           + cap("6", "Session score reached on each array, against the score needed to stay "
                      "inside the false-alarm budget.")
           + "</div>")
    rate = chart_card(
        "Deciding less often: the two arrays disagree",
        C.decision_measured(W, 292, D["decision_rate"]["curves"]), "7",
        f"Detection against how often the monitor decides. T11 {pct(a['change'])} points "
        f"(not established); T5 {pct(t5['change'])} points (established).")
    return B.page(
        "Draft 3, centre panel: results, data and analysis", B.PW_MAIN, B.PH,
        "\n".join([
            B.title_block(),
            one_minute(),
            sec(label("Results and data: measured on archived brain recordings"), numbers,
                gap=14),
            row1, row2,
            sec(label("Analysis"), f'<div style="{two}">{why}{rate}</div>', gap=12),
        ]), 56, gap=22)


# ===========================================================================
# RIGHT -- discussion of the data, conclusion, pictures, hardware
# ===========================================================================
def point(lead: str, text: str) -> str:
    return (f'<p style="margin: 0; font-size: {MIN}px; line-height: 42px; color: {INK2}; '
            f'text-wrap: pretty"><b style="color: {INK}; font-weight: 600">{lead}</b> {text}'
            f'</p>')


def hardware_narrow() -> str:
    name = "wiring-stepper-unlabelled.svg"
    iw, ih = 1040, 281
    host = (f'<div style="position: relative; width: {iw}px; height: 322px">'
            f'<img src="{B.ASSETS[name]}" alt="Raspberry Pi 4 wired to a ULN2003 driver board '
            f'and a 28BYJ-48 stepper motor by six coloured jumper wires" style="position: '
            f'absolute; left: 0; top: 0; width: {iw}px; height: {ih}px">'
            + B.note(14, 280, 330, "Raspberry Pi 4", "left", INK, 600)
            + B.note(480, 280, 300, "driver board", "center", INK, 600)
            + B.note(740, 280, 300, "stepper motor", "center", INK, 600) + "</div>")
    cell = f"font-size: {MIN}px; line-height: 44px; color: {INK2}; white-space: nowrap"
    pins = "".join(
        f'<div style="display: flex; align-items: center; gap: 12px; {cell}">'
        f'<span style="width: 40px; height: 22px; flex: none; background: {c}; '
        f'border-radius: 3px"></span>{pin.replace("ground", "GND")} &rarr; '
        f'<b style="color: {INK}; font-weight: 600">{to}</b></div>' for c, pin, to in B.WIRES)
    return (host + f'<div style="display: grid; grid-template-columns: repeat(2, '
                   f'minmax(0, 1fr)); column-gap: 24px">{pins}</div>')


def right_panel() -> str:
    L11 = D["lead_time"]["T11"]
    fa = S["false_alarms_per_hour"]["T11"]
    blank = (f'<span style="display: inline-block; width: 140px; height: 34px; box-sizing: '
             f'border-box; border-bottom: 3px dashed {ORG}; vertical-align: baseline"></span>')
    parts = []
    parts.append(sec(
        label("Discussion"),
        head("What the data mean", 46),
        point("The monitor carries real information.", "It beats plain counting on exactly "
              "the faults counting cannot see, on both arrays (Fig. 2)."),
        point("A real signal is not yet a usable warning.", f"It comes "
              f"{abs(L11['median_s']):.0f} s late and {fa / S['budget_per_hour']:.0f} times "
              f"too often (Figs 3 to 5)."),
        point("The cause is measured, not guessed.", "One session holds about one "
              "independent measurement, so no threshold or averaging rescues it (Fig. 6)."),
        point("One question stays open.", "Deciding less often helps on one array and hurts "
              "on the other (Fig. 7). Two arrays cannot settle it."),
        gap=12))
    parts.append(sec(
        label("What is shown, and what is not"),
        B.bullets([
            b("Shown") + ", on archived recordings only: Figs 2 to 7.",
            b("Not shown yet:") + " anything on the test bench. " + b("Not claimed:")
            + " any clinical rate or benefit to patients.",
            b("Limits:") + " two arrays, one bench, one family of monitor."]),
        B.verdict_tree(),
        cap("8", "How the bench result will be judged, fixed before any recording."),
        gap=12))
    parts.append(sec(
        label("Conclusion"),
        p("On archived recordings the monitor " + B.hi("detects real faults but warns too "
          "late and too often") + " to be relied on. The bench will show whether that belongs "
          "to brain recordings or to the method.", MIN, 42, INK),
        f'<p style="margin: 0; font-size: {MIN}px; line-height: 48px; color: {INK2}; '
        f'border: 3px dashed {ORG}; border-radius: 6px; padding: 6px 16px">'
        f'<b style="color: {ORG}; font-weight: 600">Bench, to be measured:</b> lead time '
        f'{blank} s, false alarms {blank} per hour.</p>',
        gap=10))
    parts.append(sec(
        label("Next steps"),
        B.bullets([
            "Build the bench and pass five acceptance gates before any result is read.",
            "Record 337 sessions, each with its fault time sealed first.",
            "Report lead time and false alarms together, whatever they are."]),
        gap=10))
    parts.append(sec(
        label("Pictures and hardware"),
        '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); '
        'gap: 16px">'
        + photo("the assembled test bench", 186)
        + photo("inside: screen and camera", 186)
        + photo("Raspberry Pi 4 and wiring", 186)
        + photo("a recording session", 186, "SCREENSHOT TO ADD") + "</div>",
        hardware_narrow(),
        cap("9", "Wiring of the rotation stage: the repository's diagram, relabelled. Pins "
                 "are read from rig/motor.py."),
        gap=12))
    parts.append(
        f'<section style="display: flex; flex-direction: column; gap: 0; margin-top: auto">'
        + label("References")
        + "".join(f'<p style="margin: 0; font-size: {MIN}px; line-height: 39px; '
                  f'color: {INK2}; white-space: nowrap; overflow: hidden">[{i}] {r}</p>'
                  for i, r in enumerate(B.REFS, 1))
        + "</section>")
    return B.page("Draft 3, right panel: discussion and conclusion", B.PW_SIDE, B.PH,
                  "\n".join(parts), 56, gap=20)


def main() -> int:
    for name, fn in (("D3-Centre.dc.html", centre_panel), ("D3-Left.dc.html", left_panel),
                     ("D3-Right.dc.html", right_panel)):
        html = fn()
        markup = html[html.index("<x-dc>"):html.index("</x-dc>")]
        if "{{" in markup or "}}" in markup:
            raise SystemExit(f"{name}: a doubled brace would be read as a template hole")
        if "—" in html:
            raise SystemExit(f"{name}: contains an em dash")
        for banned, why in ((B.NAVY, "the navy band"), ("#FFE27A", "the yellow highlighter"),
                            (B.AMBER, "the amber accent")):
            if banned.lower() in html.lower():
                raise SystemExit(f"{name}: still contains {why} ({banned})")
        (B.OUT / name).write_text(html)
        print(f"wrote {(B.OUT / name).relative_to(B.HERE.parent)}  ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
