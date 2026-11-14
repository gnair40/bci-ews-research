#!/usr/bin/env python3
"""
make_figures.py -- draw every figure the two documents need that is not a photograph.

    python3 paper/make_figures.py        # writes paper/figures/src/*.svg
    node paper/render_svgs.js            # turns them into paper/figures/*.png

THREE KINDS OF FIGURE, AND WHERE EACH COMES FROM
------------------------------------------------
1. Real charts of the computational results. Drawn by poster/charts.py from
   poster/poster_data.json, which poster/build_poster_data.py recomputes from
   data/processed/ and refuses to write if a value disagrees with the repository's
   own headline. No number is typed here.
2. Diagrams of how the project works (workflow, software, data flow, analysis).
   Drawn here from what the repository's files actually do. Every box names a real
   folder, program or file.
3. Graph TEMPLATES for the bench results. These show the layout of a figure that
   does not exist yet: axes, units, where the marks go. They carry no numbers and
   are stamped as templates, so they cannot be mistaken for results.

The wiring, signal-chain, workflow, calibration and onset drawings are not made
here. They are the repository's own, in physical/figures/, used as they are.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "poster"))
import charts as C  # noqa: E402

SRC = HERE / "figures" / "src"
D = json.loads((REPO / "poster" / "poster_data.json").read_text())
S = D["scalars"]

INK, INK2, INK3 = "#101A24", "#33414D", "#55626E"
RULE, GRID, WASH = "#B9C3CC", "#E2E7EB", "#F1F4F6"
BLUE, BLUE_T = "#1B5A8E", "#E4EDF6"
ORG, ORG_T = "#B24E0A", "#FDF3E9"
WINE, WINE_T = "#8C1D3B", "#F7E6EB"
GREEN, GREEN_T = "#2E6B3A", "#E7F2E9"
FONT = "'Liberation Sans', Arial, Helvetica, sans-serif"
REG = json.loads((HERE / "registry.json").read_text())


def FIG(key: str) -> int:
    return REG["figures"].index(key) + 1


def TAB(key: str) -> int:
    return REG["tables"].index(key) + 1
LOOK = {"n": ("#FFFFFF", INK), "b": (BLUE_T, BLUE), "o": (ORG_T, ORG), "w": (WINE_T, WINE),
        "g": (GREEN_T, GREEN), "q": (WASH, INK3)}


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Dia:
    """A small diagram: boxes with wrapped text, straight or elbowed arrows, frames."""

    def __init__(self, w: int, h: int, label: str):
        self.w, self.h, self.label, self.body = w, h, label, []

    def text(self, x, y, s, size=13, fill=INK, weight=400, anchor="start", italic=False):
        st = ' font-style="italic"' if italic else ""
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
                         f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>'
                         f'{esc(s)}</text>')

    def box(self, x, y, w, h, title, lines="", look="n", size=12.5, dash=False):
        fill, edge = LOOK[look]
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" '
                         f'stroke="{edge}" stroke-width="1.6"{d}/>')
        while True:      # shrink the type until the wrapped text fits inside the box
            per = max(8, int((w - 12) / (size * 0.53)))
            rows = []
            for t in ([title] if isinstance(title, str) else title):
                rows += [(r, 700) for r in textwrap.wrap(t, per, break_long_words=False)]
            for t in ([lines] if isinstance(lines, str) else lines):
                if t:
                    rows += [(r, 400) for r in textwrap.wrap(t, per, break_long_words=False)]
            lh = size * 1.2
            if len(rows) * lh <= h - 8 or size <= 9.5:
                break
            size -= 0.5
        y0 = y + h / 2 - lh * (len(rows) - 1) / 2 + size * 0.36
        for i, (r, wt) in enumerate(rows):
            self.text(x + w / 2, y0 + i * lh, r, size, INK if wt == 700 else INK2, wt, "middle")
        return (x, y, w, h)

    def frame(self, x, y, w, h, title, look="q"):
        fill, edge = LOOK[look]
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="none" '
                         f'stroke="{edge}" stroke-width="1.4" stroke-dasharray="3 4"/>')
        self.text(x + 10, y + 16, title, 12, edge, 700)

    def arrow(self, pts, color=INK2, dash=False, label=None, lpos=None):
        """Polyline through pts, with an arrowhead at the last point."""
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        n = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1
        ux, uy = (x2 - x1) / n, (y2 - y1) / n
        bx, by = x2 - ux * 8, y2 - uy * 8
        d = ' stroke-dasharray="5 4"' if dash else ""
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts[:-1] + [(bx, by)])
        self.body.append(f'<polyline points="{path}" fill="none" stroke="{color}" '
                         f'stroke-width="1.8" stroke-linejoin="round"{d}/>')
        self.body.append(f'<path d="M{x2:.1f} {y2:.1f} L{bx - uy * 4.5:.1f} {by + ux * 4.5:.1f} '
                         f'L{bx + uy * 4.5:.1f} {by - ux * 4.5:.1f} Z" fill="{color}"/>')
        if label:
            lx, ly = lpos or ((x1 + x2) / 2 + 5, (y1 + y2) / 2 - 5)
            self.text(lx, ly, label, 11.5, color, 700)

    def save(self, name: str):
        out = (f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(self.label)}" '
               f'width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
               f'<rect width="{self.w}" height="{self.h}" fill="#FFFFFF"/>' + "".join(self.body)
               + "</svg>")
        (SRC / f"{name}.svg").write_text(out)


def down(a, b, dia, **kw):
    """Arrow from the bottom middle of box a to the top middle of box b."""
    dia.arrow([(a[0] + a[2] / 2, a[1] + a[3]), (b[0] + b[2] / 2, b[1])], **kw)


def right(a, b, dia, **kw):
    dia.arrow([(a[0] + a[2], a[1] + a[3] / 2), (b[0], b[1] + b[3] / 2)], **kw)


# ---------------------------------------------------------------------------
# 1. real charts of the computational results
# ---------------------------------------------------------------------------
def real_charts() -> None:
    C.SCALE = 1.0
    W = 640
    sl = S["session_level_correlation_T11"]
    v = D["fault_mode_auc"]["values"]
    names = {"RATE_LOSS": ("Signal loss", "total falls"),
             "CHANNEL_DROPOUT": ("Dropout", "channels go silent"),
             "GAIN_DRIFT": ("Gain drift", "total unchanged"),
             "GEOMETRY_ROTATION": ("Rotation", "total unchanged")}
    L11 = D["lead_time"]["T11"]
    dvf = D["detection_vs_fa"]
    charts = {
        "c_drift": C.drift_line(W, 212, sl["series"], sl["failure_threshold_deg"]),
        "c_episode": C.episode_compact(D["median_episode"], W, 236),
        "c_modes": C.mode_dumbbell(W, 290, v, D["fault_mode_auc"]["modes"], names),
        "c_lead": C.lead_dots(W, 176, L11["leads_s"], L11["median_s"], top=22, label_gap=12,
                              label_dy=46),
        "c_fa": C.fa_measured(W, 282, S["false_alarms_per_hour"], S["budget_per_hour"],
                              S["silence_fault_free_fraction"], S["fault_free_episodes"]),
        "c_dfa": C.dfa_measured(W, 232, dvf["curves"], {"T11": dvf["best_inside_budget_T11"],
                                                        "T5": dvf["best_inside_budget_T5"]}),
        "c_gap": C.auc_gap(W, 122, S["auc_session"], S["auc_needed_at_budget"]),
        "c_decision": C.decision_measured(W, 236, D["decision_rate"]["curves"]),
    }
    for name, svg in charts.items():
        svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        (SRC / f"{name}.svg").write_text(svg)


# ---------------------------------------------------------------------------
# 2. diagrams
# ---------------------------------------------------------------------------
def d_overview() -> None:
    n = S["episodes"]
    d = Dia(640, 470, "The research in one picture: a problem, one monitor, two validations "
                      "and one verdict rule")
    p = d.box(20, 10, 600, 50, "Problem",
              "A decoder loses accuracy as the recording drifts. No test shows whether a "
              "warning is early enough or rarely wrong.", "w")
    a = d.box(20, 82, 600, 50, "Approach",
              "One monitor (decoder-guard) reading only the recorded signal, scored against "
              "failure times fixed before any detector existed.", "n")
    down(p, a, d)
    d.frame(20, 152, 292, 232, "Computational validation: complete", "b")
    d.frame(328, 152, 292, 232, "Physical validation: preregistered, not built", "o")
    b1 = d.box(34, 176, 264, 40, "Archived recordings, arrays T11 and T5",
               "public and de-identified", "b")
    b2 = d.box(34, 228, 264, 40, f"{n['T11'] + n['T5']:,} planted faults",
               "start times sealed with SHA-256", "b")
    b3 = d.box(34, 280, 264, 40, "Frozen decoder grades the outcome",
               "five gates, test data read once", "b")
    b4 = d.box(34, 332, 264, 40, "Measured: lead time and false alarms", "sections 6 and 7", "b")
    o1 = d.box(342, 176, 264, 40, "Optical test bench", "screen, camera, sealed dark box", "o")
    o2 = d.box(342, 228, 264, 40, "Five acceptance gates, G-a to G-e",
               "must pass before any result is read", "o")
    o3 = d.box(342, 280, 264, 40, "337 sessions in seven experiments",
               "onsets sealed before each recording", "o")
    o4 = d.box(342, 332, 264, 40, "To be measured", "red placeholders in sections 6 to 8", "o",
               dash=True)
    for x, y in ((b1, b2), (b2, b3), (b3, b4), (o1, o2), (o2, o3), (o3, o4)):
        down(x, y, d)
    d.arrow([(166, 132), (166, 152)])
    d.arrow([(474, 132), (474, 152)])
    v = d.box(120, 410, 400, 50, "Comparison and verdict",
              "Same monitor, same 30 s window, same 0.1 per hour budget. The judging rule was "
              "frozen on 24 September 2026.", "g")
    d.arrow([(166, 384), (166, 397), (240, 397), (240, 410)])
    d.arrow([(474, 384), (474, 397), (400, 397), (400, 410)])
    d.save("d_overview")


def d_repo() -> None:
    d = Dia(640, 430, "How the repository is organised and how its parts feed each other")
    raw = d.box(20, 14, 180, 56, "data/raw/", "the archived dataset, downloaded once, "
                                              "read-only", "q")
    scr = d.box(230, 14, 180, 56, "scripts/ 01 to 81", "the computational pipeline and the "
                                                       "checks", "b")
    pro = d.box(440, 14, 180, 56, "data/processed/", "episode scores, summaries, the sealed "
                                                     "injection plan", "b")
    right(raw, scr, d)
    right(scr, pro, d)
    rep = d.box(440, 96, 180, 50, "reports/", "one written report per analysis", "b")
    down(pro, rep, d)
    chk = d.box(230, 96, 180, 50, "tools/check_all.py", "13 checks: tests, recomputed claims, "
                                                        "frozen files", "g")
    tst = d.box(20, 96, 180, 50, "tests/", "50 unit tests, each from a real mistake", "g")
    right(tst, chk, d)
    d.arrow([(410, 121), (440, 121)], dash=True, label="verifies", lpos=(398, 112))
    d.frame(20, 170, 600, 150, "physical/: the bench", "o")
    pd_ = d.box(34, 196, 130, 56, "physical/docs/", "00 to 14: design, build, runbook, "
                                                    "preregistration", "o")
    pc = d.box(180, 196, 130, 56, "physical/code/", "17 programs: record, verify, analyse",
               "o")
    pda = d.box(326, 196, 130, 56, "physical/data/", "onsets, raw, processed, results, figures",
                "o", dash=True)
    pf = d.box(472, 196, 134, 56, "physical/figures/", "wiring and workflow drawings", "o")
    rig = d.box(180, 264, 130, 44, "rig/", "motor.py, logtemp.py: the pins", "o")
    right(pd_, pc, d)
    right(pc, pda, d)
    d.arrow([(245, 264), (245, 252)])
    res = d.box(20, 346, 180, 62, "research/", "research plan, research log, notes, earlier "
                                               "preregistrations", "q")
    pos = d.box(230, 346, 180, 62, "poster/", "the trifold drafts and their checked numbers",
                "q")
    pap = d.box(440, 346, 180, 62, "paper/", "this paper, its manual, and the script that "
                                             "builds them", "n")
    d.arrow([(391, 252), (391, 334), (530, 334), (530, 346)], dash=True)
    d.arrow([(410, 377), (440, 377)])
    d.text(34, 424, "Dashed box and dashed arrows: empty until the bench has recorded.", 11.5,
           INK3, italic=True)
    del res, pos, pap, pf, rig
    d.save("d_repo")


def d_comp() -> None:
    n = S["episodes"]
    d = Dia(640, 300, "The computational workflow, script by script")
    w, h = 140, 78
    xs = [20, 173, 326, 479]
    r1 = [d.box(xs[0], 16, w, h, "01 to 03", "download with checksums, inspect, load the "
                                             "archived recordings", "q"),
          d.box(xs[1], 16, w, h, "17 fault injector", f"plan {n['T11'] + n['T5']:,} episodes, "
                                                      "seal the onsets, verify, apply", "b"),
          d.box(xs[2], 16, w, h, "18 reference decoder", "ridge regression, fitted once, "
                                                         "then frozen", "b"),
          d.box(xs[3], 16, w, h, "19 baselines, 22 decoder-guard", "detectors fitted on healthy "
                                                                   "windows only", "b")]
    r2 = [d.box(xs[3], 196, w, h, "20 evaluation harness", "fit, validation and test splits; "
                                                           "one risk score per window", "b"),
          d.box(xs[2], 196, w, h, "21 score report", "one threshold chosen on validation; "
                                                     "five gates", "b"),
          d.box(xs[1], 196, w, h, "24 benchmark matrix", "all 48 configurations, every one "
                                                         "reported", "b"),
          d.box(xs[0], 196, w, h, "31 verify claims", "102 headline numbers recomputed from "
                                                      "the data files", "g")]
    for a, b in zip(r1, r1[1:]):
        right(a, b, d)
    d.arrow([(549, 94), (549, 196)])
    for a, b in zip(r2, r2[1:]):
        d.arrow([(a[0], a[1] + a[3] / 2), (b[0] + b[2], b[1] + b[3] / 2)])
    d.text(320, 132, "The harness (20) was committed before the monitor (22) was written,", 12,
           INK2, anchor="middle", italic=True)
    d.text(320, 150, "and the onsets (17) before any detector existed.", 12, INK2,
           anchor="middle", italic=True)
    d.save("d_comp")


def d_monitor() -> None:
    d = Dia(640, 176, "The monitor: four named components, the largest reported as the risk")
    a = d.box(16, 44, 116, 88, "384 channels", "log activity in each 30 s window, a new window "
                                               "every 5 s", "n")
    cs = [d.box(160, 14, 150, 64, "level", "total activity has moved", "b"),
          d.box(322, 14, 150, 64, "silence", "channels have gone quiet", "b"),
          d.box(160, 98, 150, 64, "dispersion", "channels drift apart in gain, total "
                                                "unchanged", "b"),
          d.box(322, 98, 150, 64, "profile", "the shape across channels has changed", "b")]
    r = d.box(500, 44, 124, 88, "Risk score", "the largest component, with its name; WARN when "
                                              "it stays above threshold", "n")
    d.arrow([(132, 88), (160, 88)])
    d.arrow([(472, 88), (500, 88)])
    del a, cs, r
    d.save("d_monitor")


def d_dataflow() -> None:
    d = Dia(640, 520, "Where the bench data go: from one recorded session to the numbers in "
                      "the paper")
    d.frame(14, 8, 612, 118, "Recording (on the Raspberry Pi)", "o")
    a = d.box(26, 32, 140, 82, "draw_onset.py", "writes the plan and seals it: "
                                                "onsets/ + MANIFEST.csv", "o")
    b = d.box(180, 32, 140, 82, "run_session.py", "refuses to record without a plan", "o")
    c = d.box(334, 32, 280, 82, "raw/s<session>_b<block>/",
              "capture.npy (frames), capture_t.npy (frame times), stim.csv (what was shown), "
              "session.json (settings, temperature, notes)", "o")
    right(a, b, d)
    right(b, c, d)
    d.frame(14, 138, 612, 100, "Session table (on a laptop)", "b")
    side = d.box(26, 162, 170, 64, "also read", "lag.json, EXCLUSIONS.csv, SESSION_LOG.csv",
                 "q")
    m = d.box(212, 162, 170, 64, "make_session_table.py", "decodes, scores, splits into fit, "
                                                          "val, test", "b")
    t = d.box(398, 162, 216, 64, "sessions.csv",
              "one row per session; plus processed/windows/*.npz and table_meta.json", "b")
    right(side, m, d)
    right(m, t, d)
    d.arrow([(474, 114), (474, 126), (297, 126), (297, 162)])
    d.frame(14, 250, 612, 176, "Analysis: one program per experiment, each writes a report "
                               "and a JSON file in results/", "b")
    progs = [("analyze_falsealarm.py", "P-2: false_alarm.json", 26, 274),
             ("analyze_leadtime.py", "P-3: lead_time.json", 228, 274),
             ("analyze_leadtime.py --undesigned", "P-5: undesigned_faults.json", 430, 274),
             ("analyze_correlation.py", "P-4: correlation_vs_usability.json", 26, 350),
             ("analyze_decision_rate.py", "P-6: decision_rate.json", 228, 350),
             ("analyze_apparatus.py", "P-7: apparatus_variation.json", 430, 350)]
    for name, out, x, y in progs:
        d.box(x, y, 184, 64, name, out, "b", size=12)
    d.arrow([(506, 226), (506, 238), (320, 238), (320, 250)])
    f = d.box(60, 444, 220, 64, "figures.py all", "six figures in physical/data/figures/", "b")
    p = d.box(360, 444, 220, 64, "The paper", f"Tables {TAB('b_gates')} to {TAB('b_app')} and Figures "
                                              f"{FIG('g_session')} to {FIG('g_app')}, by the manual's entries", "g")
    d.arrow([(170, 426), (170, 444)])
    d.arrow([(470, 426), (470, 444)])
    right(f, p, d)
    d.save("d_dataflow")


def d_stats() -> None:
    d = Dia(640, 540, "From each measured quantity to the verdict: the statistic, its "
                      "uncertainty, and the decision fixed in advance")
    heads = [("Quantity", 16, 150), ("Statistic", 176, 150), ("Uncertainty", 336, 140),
             ("Decision fixed in advance", 486, 140)]
    for name, x, w in heads:
        d.text(x + w / 2, 18, name, 12.5, INK, 700, "middle")
    rows = [("False-alarm rate (DV2)", "k warnings in H held-out fault-free hours: k / H",
             "exact Poisson 95% interval; k = 0 gives an upper bound of about 3 / H",
             "upper bound above 0.1 per hour: over budget", "b"),
            ("Silence gate (DV4)", "Kendall tau of risk against time, per fault-free session",
             "share of sessions with p below 0.05; raw and after removing a line",
             "more than 10% trending: gate fails", "b"),
            ("Lead time (DV1)", "failure time minus warning time, per session; then the median",
             "bootstrap 95% interval, 5,000 resamples, only if 3 or more",
             "median at or below 0 s: warns too late", "b"),
            ("Detection rate (DV3)", "sessions warned after onset / degraded sessions",
             "Wilson 95% interval; by fault type and by severity",
             "severity 1.0 must exceed 0.25 (manipulation check)", "b"),
            ("Correlation (DV5)", "Spearman: raw, with time removed, and on first differences",
             "three values with their p values",
             "any magnitude at or above 0.70: strong", "b")]
    ys = []
    for i, (q, s_, u, dec, look) in enumerate(rows):
        y = 30 + i * 82
        ys.append(y)
        cells = [d.box(16, y, 150, 70, q, "", "n"), d.box(176, y, 150, 70, "", s_, look),
                 d.box(336, y, 140, 70, "", u, look), d.box(486, y, 140, 70, "", dec, "o")]
        for a, b in zip(cells, cells[1:]):
            right(a, b, d)
    y = 30 + 5 * 82 + 6
    d.arrow([(556, 30 + 4 * 82 + 70), (556, y)])
    d.box(60, y, 566, 84, "Verdict rule (preregistration, section 1)",
          ["Unusable: median lead time at or below 0, or the false-alarm upper bound above "
           "budget.",
           "Supported: strong and unusable. Falsified: strong and usable on both counts. "
           "Inconclusive: no correlation reaches 0.70."], "g")
    d.save("d_stats")


def d_roadmap() -> None:
    d = Dia(640, 330, "From today's documents to the finished paper: thirteen stages")
    steps = [("1 Existing documents", "plan, preregistration, code", "g"),
             ("2 Prepare the apparatus", "parts, computer, enclosure", "o"),
             ("3 Acceptance gates", "G-a to G-e, calibration", "o"),
             ("4 Record", "337 sessions, sealed onsets", "o"),
             ("5 Organise the raw data", "copy, never edit; log sheets", "o"),
             ("6 Process", "build the session table", "b"),
             ("7 Analyse", "five analysis programs", "b"),
             ("8 Figures", "figures.py and the templates", "b"),
             ("9 Results", f"fill Tables {TAB('b_gates')} to {TAB('b_app')}", "n"),
             ("10 Discussion", "predictions, then meaning", "n"),
             ("11 Conclusion", "the verdict by rule", "n"),
             ("12 Abstract", "written last", "n"),
             ("13 Finished paper", "no red text left", "g")]
    w, h, gx, gy = 112, 62, 12, 34
    pos = []
    for i, (t, s_, look) in enumerate(steps):
        row, col = divmod(i, 5)
        if row == 1:
            col = 4 - col
        x, y = 16 + col * (w + gx), 14 + row * (h + gy)
        pos.append(d.box(x, y, w, h, t, s_, look, size=11.5))
    for i in range(len(pos) - 1):
        a, b = pos[i], pos[i + 1]
        if abs(a[1] - b[1]) < 1:
            if b[0] > a[0]:
                right(a, b, d)
            else:
                d.arrow([(a[0], a[1] + h / 2), (b[0] + w, b[1] + h / 2)])
        else:
            down(a, b, d)
    d.box(16, 300 - 6, 14, 14, "", "", "g")
    d.text(36, 300 + 5, "done or final", 11.5, INK2)
    d.box(136, 300 - 6, 14, 14, "", "", "o")
    d.text(156, 300 + 5, "at the bench", 11.5, INK2)
    d.box(250, 300 - 6, 14, 14, "", "", "b")
    d.text(270, 300 + 5, "by program, on a laptop", 11.5, INK2)
    d.box(430, 300 - 6, 14, 14, "", "", "n")
    d.text(450, 300 + 5, "writing, in the paper", 11.5, INK2)
    d.save("d_roadmap")


def d_photomap() -> None:
    d = Dia(640, 470, "Which photograph or screenshot fills which figure of the paper")
    rows = [("PH-1  All parts, laid out and labelled", "ph_parts", "before building"),
            ("PH-2  Six single-component photographs", "ph_components", "before building"),
            ("PH-3  Whole apparatus, enclosure open", "ph_open", "after building"),
            ("PH-4  Whole apparatus, sealed, as run", "ph_sealed", "after gate G-a"),
            ("PH-5  Header and jumper wires, from above", "ph_header", "after wiring"),
            ("PH-6  Same view, annotated beside the drawing", "ph_annotated", "after wiring"),
            ("PH-7  Sensor wires and the power supply", "ph_sensor", "after wiring"),
            ("PH-8  Inside: screen, camera mount, filter", "ph_inside", "before sealing"),
            ("SS-1  Terminal and stimulus during a session", "ss_session", "during recording"),
            ("SS-2  Output of bench.py check", "ss_check", "after the gates pass")]
    rows = [(a, f"Figure {FIG(k)}", w) for a, k, w in rows]
    d.text(20, 18, "Take this", 12.5, INK, 700)
    d.text(382, 18, "It becomes", 12.5, INK, 700)
    d.text(500, 18, "When", 12.5, INK, 700)
    for i, (ph, fig, when) in enumerate(rows):
        y = 30 + i * 43
        a = d.box(16, y, 330, 34, ph, "", "o" if ph.startswith("PH") else "b", size=12)
        b = d.box(376, y, 110, 34, fig, "", "n", size=12)
        right(a, b, d)
        d.text(500, y + 21, when, 12, INK2)
    d.text(16, 462, "PH = photograph. SS = screenshot. No person appears in any of them.", 11.5,
           INK3, italic=True)
    d.save("d_photomap")


# ---------------------------------------------------------------------------
# 3. templates for the bench figures: layout only, no numbers
# ---------------------------------------------------------------------------
def template(name: str, title: str, xlab: str, ylab: str, draw) -> None:
    W, H = 320, 220
    d = Dia(W, H, f"Template for {title}: layout only, not data")
    x0, y0, x1, y1 = 50, 34, W - 14, H - 44
    d.text(W / 2, 16, title, 12, INK, 700, "middle")
    d.body.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#FFFFFF" '
                  f'stroke="{RULE}" stroke-width="1.2"/>')
    draw(d, x0, y0, x1, y1)
    d.text((x0 + x1) / 2, H - 24, xlab, 11, INK2, anchor="middle")
    d.body.append(f'<text x="14" y="{(y0 + y1) / 2}" font-family="{FONT}" font-size="11" '
                  f'fill="{INK2}" text-anchor="middle" transform="rotate(-90 14 '
                  f'{(y0 + y1) / 2})">{esc(ylab)}</text>')
    d.text(W / 2, H - 7, "TEMPLATE: layout only, no data", 10.5, ORG, 700, "middle")
    d.save(name)


def line(d, x1, y1, x2, y2, c=INK3, w=1.5, dash=None):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    d.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" '
                  f'stroke-width="{w}"{ds}/>')


def dot(d, x, y, r=4, c=INK3, fill=None):
    d.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill or c}" stroke="{c}" '
                  f'stroke-width="1.5"/>')


def templates() -> None:
    def t_session(d, x0, y0, x1, y1):
        pts = [(x0 + (x1 - x0) * i / 20, y1 - 8 - (0 if i < 9 else min(1, (i - 9) / 6)) * (y1 - y0 - 30))
               for i in range(21)]
        d.body.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                      + f'" fill="none" stroke="{INK3}" stroke-width="2"/>')
        line(d, x0, y0 + 42, x1, y0 + 42, INK3, 1.2, "5 4")
        d.text(x1 - 4, y0 + 38, "warning threshold", 10, INK2, anchor="end")
        for fx, lab in ((0.42, "onset"), (0.58, "failure"), (0.66, "warning")):
            x = x0 + (x1 - x0) * fx
            line(d, x, y0, x, y1, ORG, 1.5)
            d.text(x + 3, y0 + 12 + (14 if lab == "warning" else 0), lab, 10, ORG, 700)

    def t_fa(d, x0, y0, x1, y1):
        pts = [(x0 + (x1 - x0) * i / 12, y0 + 14 + (y1 - y0 - 30) * (i / 12) ** 0.55)
               for i in range(1, 13)]
        d.body.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                      + f'" fill="none" stroke="{INK3}" stroke-width="2"/>')
        line(d, x0, y1 - 22, x1, y1 - 22, ORG, 1.5, "5 4")
        d.text(x0 + 6, y1 - 26, "budget 0.1 per hour", 10, ORG, 700)
        d.text(x1 - 6, y0 + 30, "upper bound, 3 / hours", 10, INK2, anchor="end")

    def t_lead(d, x0, y0, x1, y1):
        zx = x0 + (x1 - x0) * 0.55
        d.body.append(f'<rect x="{x0}" y="{y0}" width="{zx - x0}" height="{y1 - y0}" '
                      f'fill="{WASH}"/>')
        line(d, zx, y0, zx, y1, INK, 2)
        for i, k in enumerate((1, 2, 3, 5, 6, 4, 3, 2, 2, 1, 1)):
            x = x0 + 14 + i * (x1 - x0 - 28) / 10
            for j in range(k):
                dot(d, x, y1 - 8 - j * 9, 3)
        d.text(x0 + 6, y0 + 14, "warning after failure", 10, INK2)
        d.text(x1 - 6, y0 + 14, "warning first", 10, INK2, anchor="end")
        d.text(zx, y1 + 12, "0", 10.5, INK, 700, "middle")

    def t_sev(d, x0, y0, x1, y1):
        xs = [x0 + (x1 - x0) * f for f in (0.2, 0.5, 0.85)]
        for k, (off, c) in enumerate(((0, INK3), (16, INK2))):
            ys = [y1 - 22 - off - f * (y1 - y0 - 60) for f in (0.15, 0.5, 0.85)]
            d.body.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
                          + f'" fill="none" stroke="{c}" stroke-width="1.8"/>')
            for x, y in zip(xs, ys):
                line(d, x, y - 9, x, y + 9, c, 1.2)
                dot(d, x, y, 3.5, c, "#FFFFFF" if k else None)
        for x, lab in zip(xs, ("0.25", "0.5", "1.0")):
            d.text(x, y1 + 12, lab, 10.5, INK2, anchor="middle")
        d.text(x1 - 6, y0 + 14, "one line per fault type", 10, INK2, anchor="end")

    def t_corr(d, x0, y0, x1, y1):
        mid = (x0 + x1) / 2
        line(d, mid, y0, mid, y1, RULE, 1.2)
        for i, lab in enumerate(("raw", "partial", "diff.")):
            x = x0 + 22 + i * 34
            hgt = (y1 - y0 - 34) * (0.8, 0.5, 0.6)[i]
            d.body.append(f'<rect x="{x - 11}" y="{y1 - hgt}" width="22" height="{hgt}" '
                          f'fill="{INK3}"/>')
            d.text(x, y1 + 12, lab, 10, INK2, anchor="middle")
        line(d, x0, y1 - (y1 - y0 - 34) * 0.7, mid, y1 - (y1 - y0 - 34) * 0.7, ORG, 1.5, "5 4")
        d.text(x0 + 4, y1 - (y1 - y0 - 34) * 0.7 - 4, "0.70", 10, ORG, 700)
        d.text(mid + 8, y0 + 30, "median lead time: s", 10.5, INK2)
        d.text(mid + 8, y0 + 48, "with its 95% interval", 10, INK3)
        d.text(mid + 8, y0 + 82, "false alarms: per hour", 10.5, INK2)
        d.text(mid + 8, y0 + 100, "with its upper bound", 10, INK3)
        d.text(x0 + (mid - x0) / 2, y0 + 12, "what the field reports", 10, INK2, anchor="middle")
        d.text(mid + (x1 - mid) / 2, y0 + 12, "what decides usability", 10, INK2,
               anchor="middle")

    def t_rate(d, x0, y0, x1, y1):
        xs = [x0 + 16 + i * (x1 - x0 - 32) / 5 for i in range(6)]
        ys = [y0 + 40 + 10 * ((i * 7) % 3) for i in range(6)]
        d.body.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
                      + f'" fill="none" stroke="{INK3}" stroke-width="1.8"/>')
        for x, y in zip(xs, ys):
            line(d, x, y - 16, x, y + 16, INK3, 1.2)
            dot(d, x, y, 3.5)
        d.text(xs[0], y1 + 12, "1 per session", 10, INK2, anchor="middle")
        d.text(xs[-1], y1 + 12, "720 per hour", 10, INK2, anchor="middle")
        d.text(x1 - 6, y1 - 8, "bars: Wilson 95% interval", 10, INK2, anchor="end")

    def t_app(d, x0, y0, x1, y1):
        line(d, x0, y1 - (y1 - y0) * 0.4, x1, y1 - (y1 - y0) * 0.4, INK, 1.5)
        d.text(x1 - 4, y1 - (y1 - y0) * 0.4 - 4, "0 s", 10, INK, 700, "end")
        for i, lab in enumerate("ABCD"):
            x = x0 + 34 + i * (x1 - x0 - 68) / 3
            y = y1 - (y1 - y0) * (0.5, 0.36, 0.6, 0.3)[i]
            line(d, x, y - 20, x, y + 20, INK3, 1.2)
            dot(d, x, y, 4)
            d.text(x, y1 + 12, lab, 10.5, INK2, anchor="middle")
        d.text(x0 + 6, y0 + 14, "one point per configuration, never an average", 10, INK2)

    def t_cmp(d, x0, y0, x1, y1):
        for i, (lab, c) in enumerate((("T11", BLUE), ("T5", BLUE), ("bench", ORG))):
            y = y0 + 34 + i * 34
            x = x0 + (x1 - x0) * (0.3, 0.2, 0.5)[i]
            line(d, x - 26, y, x + 26, y, c, 1.4, None if i < 2 else "4 3")
            dot(d, x, y, 4.5, c, c if i < 2 else "#FFFFFF")
            d.text(x0 + 6, y + 4, lab, 10.5, c, 700)
        zx = x0 + (x1 - x0) * 0.62
        line(d, zx, y0, zx, y1, INK, 1.5)
        d.text(zx, y1 + 12, "0 s", 10.5, INK, 700, "middle")
        d.text(x1 - 6, y1 - 8, "filled: measured. open: to add", 10, INK2, anchor="end")

    template("t_session", "One session in detail", "time in the session (s)", "risk score",
             t_session)
    template("t_fa", "False-alarm evidence", "held-out fault-free hours",
             "upper bound on the rate (per hour)", t_fa)
    template("t_lead", "Lead-time distribution", "lead time (s); one dot per detected session",
             "sessions", t_lead)
    template("t_sev", "Detection against severity", "severity of the imposed fault",
             "sessions detected (%)", t_sev)
    template("t_corr", "Correlation against usability", "", "correlation magnitude", t_corr)
    template("t_rate", "Detection against decision rate", "decisions per hour (log scale)",
             "sessions detected (%)", t_rate)
    template("t_app", "Four apparatus configurations", "configuration",
             "median lead time (s)", t_app)
    template("t_cmp", "Archived recordings and the bench", "median lead time (s), 95% interval",
             "", t_cmp)


def main() -> int:
    SRC.mkdir(parents=True, exist_ok=True)
    real_charts()
    for fn in (d_overview, d_repo, d_comp, d_monitor, d_dataflow, d_stats, d_roadmap,
               d_photomap):
        fn()
    templates()
    print(f"wrote {len(list(SRC.glob('*.svg')))} drawings to {SRC.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
