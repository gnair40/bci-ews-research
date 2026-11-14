# What can be done from a failure point: the published options

Written 14 November 2026, before the design in `02_DESIGN.md`.

The question was put by the researcher: once the project has found the moment
at which decoding fails, can that moment be used to make decoding better. This
note sets out the ways that is done in published work, what each one needs,
and whether this project's bench can test it.

It is a targeted search, not a full review. Every source below was looked up
on the date shown. What was confirmed is its bibliographic record and what its
abstract states. **No full text was read on 14 November**, so nothing here
describes a method in more detail than an abstract supports.

---

## 1. Three different things "better" can mean

They are easy to run together and they are not the same claim.

| Word used here | Meaning | Measured as |
|---|---|---|
| **Recovery** | After the repair, decoding is better than it would have been with no repair. | Degrees of error recovered, above 0 |
| **Restoration** | After the repair, decoding is back to where it was before the fault. | Recovery fraction near 1 |
| **Enhancement** | After the repair, decoding is better than it was before the fault. | Recovery fraction above 1 |

A partial recovery is a real improvement over doing nothing, and it is the
most likely kind. Enhancement is the strongest claim and the least likely,
because a fault usually removes information that no repair can put back.

## 2. The engineering frame

Outside neuroscience this is a standard problem with a standard shape. A
system that tolerates faults has three stages: it **detects** that something is
wrong, it **diagnoses** what, and it **reconfigures** itself to carry on. The
review by Zhang and Jiang (2008) surveys that field under the name
reconfigurable, or active, fault-tolerant control.

The rest of this project is about the first stage. Decoder-guard's named
components are an attempt at the second (`reports/ATTRIBUTION_ACCURACY.md`
gives how often it names the cause correctly). The subphase proposed here is
the third.

## 3. The published ways to repair a decoder

| # | Repair | What it changes | Needs the true direction | Stops the user | Published example |
|---|---|---|---|---|---|
| 1 | **Track each channel's statistics** | The average and spread each channel is compared against | No | No | Jarosiewicz et al. (2015) list "tracking the statistics of the neural activity during self-timed pauses" as one of three innovations of a self-calibrating interface |
| 2 | **Drop the channels that failed and refit** | Which channels the decoder uses | No, if calibration data are kept | No | Ordinary engineering practice. No specific source was confirmed for it on 14 November, so none is cited |
| 3 | **Recalibrate with a set task** | The whole decoder | Yes | Yes | The standard fallback. Wilson et al. (2025) describe decoders that often need daily recalibration during which the device cannot be used freely |
| 4 | **Recalibrate from inferred intentions** | The whole decoder | It is inferred from what the user did | No | Jarosiewicz et al. (2015): calibration from retrospectively inferred targets performed as well as calibration with instructed targets, in four participants. Gilja et al. (2012): a decoder refitted using estimated intentions halved the time to acquire a target, in monkeys |
| 5 | **Align the new activity to the old** | A mapping placed in front of an unchanged decoder | No | No | Degenhart et al. (2020): a stabiliser that aligns low-dimensional spaces of activity recovered control after severe, abrupt instabilities, without knowledge of the user's intent. Karpowicz et al. (2025) and Wilson et al. (2025) are in the same family |
| 6 | **Train the decoder in advance to tolerate change** | How the decoder is fitted, before any fault | No | No | Sussillo et al. (2016): a decoder trained on many recording conditions and on artificially perturbed data stayed usable under conditions that disabled a standard decoder |

### What the list says about enhancement

Two of the sources report a decoder that ended up **better** than the one it
replaced, not merely repaired. Gilja et al. (2012) is the clearest. Degenhart
et al. (2020) state that their stabiliser can outperform supervised
recalibration.

In both, the gain did not come from the fault. It came from a better estimate
of what the user intended, or from using structure in the activity that the
original fit ignored. That is the realistic route to enhancement: the decoder
before the fault was not as good as it could have been, and the repair fixes
that as well. On this project's bench the equivalent is a frozen decoder whose
stored averages have gone stale since calibration.

## 4. Which of these the bench can test

| # | Repair | On the bench | In the proposed subphase |
|---|---|---|---|
| 1 | Track statistics | Yes. Camera channels have an average and a spread like any others. | **R1** |
| 2 | Drop and refit | Yes. Tape over part of the field makes channels go dark. | **R2**, and with R1 as **R3** |
| 3 | Recalibrate with a set task | Yes. The bench knows the true direction on every frame. | **R4** |
| 4 | Recalibrate from inferred intentions | **No.** There is no user and so no intention to infer. R4 uses the true direction and is therefore the most that an intention-based method could achieve. | Not included; R4 stands as its upper bound |
| 5 | Align new activity to old | In principle. It is the natural repair for the rotation fault. It adds a method with several settings of its own. | **Not included in the draft.** Listed as an open decision in `03_PREREGISTRATION_DRAFT.md` |
| 6 | Train for robustness in advance | Yes, but it acts before a failure and not from one. | Out of scope. It answers a different question |

## 5. What the search did not find

No source was found that measures how much decoding is recovered **as a
function of when the repair starts**, relative to a fault whose onset was
fixed in advance. Published repairs are evaluated across days or after an
instability that the experimenters imposed and then corrected, not against a
clock that starts at a sealed onset. That is the same gap the rest of this
project is built around, one step further on. As before, this is a statement
about a short search and not proof that no such measurement exists.

## 6. Sources

Checked on 14 November 2026 by web search: bibliographic record and abstract.

| Source | Confirmed |
|---|---|
| Jarosiewicz, B., et al. (2015). Virtual typing by people with tetraplegia using a self-calibrating intracortical brain-computer interface. *Science Translational Medicine, 7*(313), 313ra179. doi:10.1126/scitranslmed.aac7328 | Record; the three innovations; the result on inferred-target calibration. How velocity bias correction works was **not** confirmed |
| Degenhart, A. D., Bishop, W. E., Oby, E. R., Tyler-Kabara, E. C., Chase, S. M., Batista, A. P., & Yu, B. M. (2020). Stabilization of a brain-computer interface via the alignment of low-dimensional spaces of neural activity. *Nature Biomedical Engineering, 4*(7), 672-685. doi:10.1038/s41551-020-0542-9 | Record; abstract claims |
| Sussillo, D., Stavisky, S. D., Kao, J. C., Ryu, S. I., & Shenoy, K. V. (2016). Making brain-machine interfaces robust to future neural variability. *Nature Communications, 7*, 13749. doi:10.1038/ncomms13749 | Record; abstract claims. Whether loss of electrodes was among the perturbations was **not** confirmed |
| Gilja, V., et al. (2012). A high-performance neural prosthesis enabled by control algorithm design. *Nature Neuroscience, 15*, 1752-1757. doi:10.1038/nn.3265 | Record; the halved acquisition time. The details of the intention-estimation step were **not** confirmed |
| Zhang, Y., & Jiang, J. (2008). Bibliographical review on reconfigurable fault-tolerant control systems. *Annual Reviews in Control, 32*(2), 229-252. doi:10.1016/j.arcontrol.2008.03.008 | Record; that it is a review of reconfigurable fault-tolerant control. No abstract was obtained |

Checked earlier, on 12 and 13 November 2026 (see `poster/README.md`): Wilson
et al. (2025), Karpowicz et al. (2025).

**Before any of these is cited in the paper, its full text should be opened.**
First authors only are given for two entries because the search did not return
the full author lists, and none was filled in from memory.
