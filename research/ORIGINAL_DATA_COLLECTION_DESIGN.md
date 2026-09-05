# Original data collection — design, options, and the recommendation

**Written:** 5 September 2026. **Status: DESIGN ONLY — nothing has been built or
measured.** No number in this document is a result.

---

## 1. Why add original data at all

The reason is not "computational projects need hardware." Computational projects
are legitimate on their own. The reason is specific to what this project has
already measured and cannot resolve:

| Gap | Established in | Why archived data cannot close it |
|---|---|---|
| **Five entangled session variables** — decoder error, trace noise, spurious crossings, task geometry, margin over chance, all correlated | `WHAT_DECODER_ERROR_MEANS.md` | Separating them needs sessions where one varies while the others are held fixed. Nobody controlled anything in 2016. |
| **Are injected faults realistic?** Every fault is a mathematical operation on a recorded array | `PROJECT_DEFINITION.md`, the injector | No one has checked whether real hardware degradation resembles `X * (1 - severity*ramp)` |
| **Is lag-1 r = 0.995 a fact about cortex or about drifting arrays generally?** | `AGGREGATION_LIMIT.md` | The scope of the single number that explains most of the project's negative results is unknown |
| **The metric saturates, and its saturation point moves** | `UNAMBIGUOUS_EPISODES.md`, `WHAT_DECODER_ERROR_MEANS.md` | A fix was recommended and could not be tested |

Original data earns its place only if it attacks these. Anything else is
decoration.

## 2. The binding constraint

**No human participants.** Established in Amendment 1 and reaffirmed since. Under
competition rules, data collected from *oneself* is still human participant
research. Every option below is instrumentation-only: no human, no animal, no
hazardous material, no controlled substance.

This rules out, explicitly: EMG, EEG, consumer neuro-headsets (Muse, OpenBCI),
camera-tracked hand movement, reaction-time tasks, and any "just me and two
friends" design.

---

## 3. The candidate designs

### Idea A — Controlled degradation of a physical multichannel array

**Measured.** An N-channel sensor array observes a moving 2D stimulus. A ridge
decoder predicts stimulus direction from array response — structurally identical
to predicting intended cursor direction from firing rates. Dependent variables
unchanged: angular error, session-level AUC, silence-gate pass rate, lag-1
autocorrelation, achieved damage.

**Setup.** A Raspberry Pi camera views an addressable LED matrix producing a known
2D direction each frame. **N virtual channels** are fixed image regions;
frame-averaged region intensity is the "firing rate." A stepper motor rotates the
camera relative to the stimulus.

**Equipment.** Pi 4/5 (~$60), camera module (~$25), WS2812 matrix (~$15), 28BYJ-48
stepper + driver (~$5), neutral-density filter sheet (~$8), cardboard or printed
mount. **≈ $115.** No soldering strictly required.

**Subjects.** None.

**Volume.** At 30 fps with 50 ms bins, one T11-equivalent *session* takes ~20
minutes. Unattended running yields **hundreds of sessions** — an order of
magnitude past the 13 usable days that blocked every session-level analysis.

**Variables.**
- *Manipulated:* fault mode (4, physically realised), severity (3), onset, **and
  baseline SNR and task geometry independently** — the manipulation archived data
  cannot offer
- *Controlled:* channel count set to exactly **384** (T11) or **192** (T5); bin
  width; window geometry; decoder frozen after fitting
- *Constant:* ambient light (enclosure), stimulus speed distribution, frame rate

**Analysis.** The existing pipeline unchanged — injector, reference decoder,
harness, five gates, decoder-guard, the claim verifier. **The analysis code is
already written and already validated by 93 checks.**

**Physical realisation of each injected mode:**

| corpus mode | physical counterpart |
|---|---|
| `CHANNEL_DROPOUT` | occlude specific regions |
| `RATE_LOSS` | neutral-density filter over the whole stimulus |
| `GAIN_DRIFT` | per-region illumination change |
| `GEOMETRY_ROTATION` | **literally rotate the camera** on the stepper |

**Link to the public data.** The neural analysis makes **falsifiable point
predictions** about the rig: lag-1 r ≈ 0.99 within a session; the silence gate
fails; a sharper detector performs worse; the severity ladder degrades as baseline
error rises. Those are preregistered *from the neural findings* and tested on
hardware.

**New insight.** Whether the monitor's failure is a fact about **cortex** or about
**any multichannel array that drifts slowly.** If it reproduces, the negative
result generalises to sensor-array health monitoring in general. If it does not,
the failure is neural-specific and the next BCI attempt needs neural-specific
fixes. Both answers are informative.

**Critical assessment.** Strongest option. Real weakness: **it is not neural.** The
defence must be principled — the claim under test was stated at the level of
*multichannel arrays with slow drift*, and no claim is made that a photodiode
resembles a neuron.

---

### Idea B — Longitudinal natural degradation

**Measured.** The same rig with **nothing injected**. It is left to degrade: dust
on the lens, LED phosphor aging, thermal cycling, connector oxidation. The
question is whether *natural* drift carries the same statistical signature as
*simulated* faults.

**Equipment.** Same rig plus a DHT22 temperature/humidity sensor (~$5) as a
covariate.

**Volume.** One session daily for 6–10 weeks = **45–70 sessions**, a drift span
comparable to the 142 days covered on T11.

**Variables.** *Manipulated:* nothing — that is the design. *Measured:* elapsed
time, temperature, humidity. *Controlled:* everything else held rigidly fixed.

**Analysis.** The staleness curve, calibration curve and day-variance scripts
(39–44) unchanged.

**New insight.** **Does simulated fault injection resemble real degradation?** If
natural drift matches one of the four modes, the corpus gains external validity.
If it matches none, that is a significant finding about how such benchmarks are
built — including this one.

**Critical assessment.** Highest novelty here. Binding constraint is **wall-clock
time**: 6+ weeks, not compressible. Runs concurrently with A on the same hardware
at no extra cost.

---

### Idea C — Metric saturation sweep

**Measured.** Baseline SNR swept continuously across its full range, measuring
where angular error saturates and comparing candidate replacement metrics.

**Volume.** ~200 short sessions across ~20 SNR levels — one afternoon, automated.

**New insight.** Directly tests design recommendation #1, which was made in
`UNAMBIGUOUS_EPISODES.md` and could not be tested.

**Critical assessment.** Narrow but nearly free as a sub-study of A. **Not a
standalone project.**

---

## 4. Designs considered and rejected

| Rejected | Reason |
|---|---|
| EMG / EEG / OpenBCI / Muse, on anyone including myself | Human participant research. Excluded by Amendment 1 and would require SRC/IRB review. |
| Camera-tracked hand movement as a "BCI-like" task | Same — still human participant research. |
| More neuron simulation in software | Not data collection. Redundant: a simulation layer already exists and adding another closes none of the four gaps. |
| Accelerometer vibration monitoring of a motor | Standard predictive maintenance, researched since the 1980s, and connected to none of this project's specific findings. |
| Robot arm performing a reaching task | Plausible but muddies the decoder/monitor framing, ~10× the cost, and addresses no documented gap. |

---

## 5. Ranking and recommendation

1. **Idea A** — best combination of novelty, feasibility and rigor. Attacks the
   worst gap, reuses 64 verified scripts, ~$115, two weekends to build, no
   participant paperwork.
2. **Idea B** — higher novelty, gated on 6+ weeks of calendar time. **Start on day
   one, harvest at the end**; it costs nothing extra to run in parallel.
3. **Idea C** — free add-on to A, not standalone.

**These are one rig. Build once, run three studies.**

## 6. The integrated project

**Research question:**

> Is the failure of decoder-health monitoring a property of neural recordings, or
> a general property of any multichannel sensor array that drifts? And do
> simulated faults resemble real degradation?

| Part | Source | Role |
|---|---|---|
| **I. Archived** | MINDFUL T11 + T5 | The real-world instance. Establishes the failure, measures its cause, generates the predictions. |
| **II. Original** | The sensor rig | The controlled instance. Manipulates what cortex will not allow. Tests those predictions. |
| **III. Computational** | The existing pipeline | The shared instrument. Identical analysis on both. |

The structure that makes this unusual: **a computational finding is used to make
falsifiable point predictions about a physical system, which is then built.** It
converts the project's largest weakness — two participants and control over
nothing — into its methodological centrepiece.

## 7. Risks, stated plainly

- **Skill gap.** Hardware is a different skill from running scripts. A half-built
  rig producing noisy data is worse than no rig. Mitigation: build the simplest
  version first — camera, LED matrix, no motor, 16 channels — get it producing
  data end to end, and only then scale to 384 channels and add rotation.
- **It is not neural.** Stated above; must be defended as a claim about a class of
  signal, not as a brain simulation.
- **Timeline.** Idea B is viable only if 6+ weeks remain before the deadline. That
  is unresolved and is the first open question.

## 8. Open decisions before any building starts

1. **Deadline** — decides whether Idea B is in or out.
2. **Whether to build hardware at all** — scientifically the right call; also real
   work. Declining leaves a defensible computational project.
3. **Channel count** — 384 (match T11), 192 (match T5), or both.

**Nothing is built until a preregistration exists**, stating the predictions
derived from the neural findings before a single measurement is taken. That is the
same discipline every study in this project has followed.
