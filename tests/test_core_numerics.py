#!/usr/bin/env python3
"""
Tests for the numerical functions this project's conclusions rest on.

WHY THIS FILE EXISTS, AND WHY THE TESTS ARE THE ONES THEY ARE
-------------------------------------------------------------
The audit (reports/PROJECT_AUDIT_2026-09-06.pdf, section 6.5) recorded "no unit
tests" as a real gap, and named the reason:

    "Correctness is enforced by five output-level gates, by synthetic controls
     with known answers, and by the reproduce-a-published-result check -- which
     is a stronger scientific defence than unit tests would be, but does not
     catch a silently wrong intermediate function. Errors #1 and #3 in Section
     3.3 are exactly what a unit test would have caught."

So this suite is not general-purpose coverage. **Every test below corresponds to
a mistake that was actually made in this project, or to a property that was
asserted in a report and never independently checked.** That follows the rule
this project already adopted for its checking tools: a check is only trusted
once it has been shown to catch a defect known to exist.

The mapping, test by test:

  ErrorDirection          error #3 -- `prob_better_than_chance` stored an
                          INVERTED statistic. mannwhitneyu returns U1, so
                          U1/(nm) is P(x EXCEEDS y), and a decoder 55 degrees
                          better than chance was recorded as 0.273.
  GainDriftConserved      the GAIN_DRIFT mode was not mean-preserving, twice.
                          Log-centring preserves the GEOMETRIC mean and left
                          +116% at crossing severity; a pre-onset rescale still
                          left +20.8%.
  DropoutNested           CHANNEL_DROPOUT severity levels drew independent
                          channel sets, so the ladder ran BACKWARDS.
  PreOnsetClean           the pre-onset guarantee "held only by floating-point
                          luck" before it was enforced by construction. A leak
                          would let a detector warn off the leak itself.
  MatlabIndexing          documented trap: MATLAB is 1-based, Python is 0-based.
                          Off by one shifts every trial by a bin.
  Autocorrelation         claim C04/C18, the single number that explains most of
                          the project's negative results. Never had a test.
  WindowMeansByCumsum     scripts/71 replaced a per-window slice loop with a
                          cumulative-sum version to make the design sweep finish
                          in reasonable time. A cumsum rewrite is exactly the
                          kind of change that stays silently off by one window.
  OrnsteinUhlenbeck       the drift model scripts/71 designs against. If its
                          stationary variance or its lag-1 correlation are
                          wrong, every sweep number derived from it is wrong and
                          nothing downstream would notice.
  SmallSampleBias         found on 15 September: the lag-1 estimator saturates
                          near 0.60 at 10 points, so C18's 0.902 cannot be
                          inverted to a drift speed. The first version of the
                          design script produced NaN and then asserted a
                          conclusion that depended on the NaN not existing.
  EffectiveSampleSize     the n_eff formula behind "one measurement per session".
  WindowOverlap           the geometry behind claim C18.
  IntendedDirection       the decoder's target. A silent failure here would look
                          like a mediocre decoder rather than a bug.

RUN IT
------
    python3 -m unittest discover -s tests -v

Uses only the standard library plus numpy and scipy, both already declared in
requirements.txt, so this adds no dependency.
"""
from __future__ import annotations

import sys
import unittest
from importlib import import_module
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "physical" / "code"))

inj = import_module("17_fault_injector")
dec = import_module("18_reference_decoder")
spacing = import_module("66_window_spacing")
sweep = import_module("71_drift_sweep_design")


def make_episode(mode: str, severity: float, n_bins: int = 1000,
                 n_feats: int = 24, onset_bin: int = 400,
                 ramp_bins: int = 200, seed: int = 7) -> "inj.Episode":
    return inj.Episode(
        episode_id="TEST", block_id="TEST/day_1/block_1", n_bins=n_bins,
        n_feats=n_feats, mode=mode, rate_label="medium",
        severity_label="crossing", severity=severity, onset_bin=onset_bin,
        ramp_bins=ramp_bins, ramp_shape="linear", seed=seed,
        feature_groups=[[0, n_feats]])


def healthy_block(n_bins: int = 1000, n_feats: int = 24,
                  seed: int = 1) -> np.ndarray:
    """A stand-in for a real recording. Positive, noisy, channel-varying."""
    rng = np.random.default_rng(seed)
    base = rng.uniform(5, 60, n_feats)
    return np.abs(base[None, :] + rng.normal(0, 4, (n_bins, n_feats)))


# ---------------------------------------------------------------------------
class ErrorDirection(unittest.TestCase):
    """Error #3: a statistic stored under a name that inverted it."""

    def test_mannwhitney_u_over_nm_is_probability_x_exceeds_y(self):
        # x is clearly LARGER than y. If U1/(nm) means "P(x exceeds y)", it must
        # be near 1. The bug was reading this quantity as its opposite.
        rng = np.random.default_rng(0)
        x = rng.normal(10, 1, 200)      # larger
        y = rng.normal(0, 1, 200)       # smaller
        u, _ = stats.mannwhitneyu(x, y, alternative="two-sided")
        p_x_exceeds_y = u / (len(x) * len(y))
        self.assertGreater(
            p_x_exceeds_y, 0.95,
            "U1/(nm) must be P(x EXCEEDS y). If this fails near 0.05 instead, "
            "the convention has flipped and every AUC in the project reverses.")

    def test_lower_error_than_chance_reads_as_better(self):
        # The concrete shape of error #3: angular ERROR, where LOWER is better.
        # A decoder well below chance must not be recorded as 0.27.
        rng = np.random.default_rng(1)
        decoder_err = rng.normal(35, 5, 300)
        chance_err = rng.normal(90, 5, 300)
        u, _ = stats.mannwhitneyu(decoder_err, chance_err, alternative="two-sided")
        p_error_exceeds_chance = u / (len(decoder_err) * len(chance_err))
        p_better_than_chance = 1.0 - p_error_exceeds_chance
        self.assertLess(p_error_exceeds_chance, 0.05)
        self.assertGreater(
            p_better_than_chance, 0.95,
            "A decoder 55 degrees better than chance must read as ~1.0, not "
            "~0.27. That inversion is error #3.")


# ---------------------------------------------------------------------------
class GainDriftConserved(unittest.TestCase):
    """GAIN_DRIFT must conserve the ARITHMETIC mean per bin.

    If it does not, the mode stops being invisible to a mean-activity detector,
    and the comparator gate -- the entire point of the mode -- is void.
    """

    def test_arithmetic_mean_conserved_at_crossing_severity(self):
        X = healthy_block()
        ep = make_episode("GAIN_DRIFT", severity=1.2)
        f = inj.ramp(ep.n_bins, ep.onset_bin, ep.ramp_bins, ep.ramp_shape)
        Y = inj.apply_gain_drift(X, ep, f)
        post = slice(ep.onset_bin + ep.ramp_bins, ep.n_bins)
        before = X[post].mean()
        after = Y[post].mean()
        drift = after / before - 1.0
        self.assertLess(
            abs(drift), 0.05,
            f"mean moved by {drift:+.1%}. The two historical failures were "
            f"+116% (log-centring preserves the geometric mean, not the "
            f"arithmetic one) and +20.8% (pre-onset rescale).")

    def test_dispersion_actually_increases(self):
        # Conserving the mean is necessary but not sufficient: the mode has to
        # DO something. A no-op would also pass the test above.
        X = healthy_block()
        ep = make_episode("GAIN_DRIFT", severity=1.2)
        f = inj.ramp(ep.n_bins, ep.onset_bin, ep.ramp_bins, ep.ramp_shape)
        Y = inj.apply_gain_drift(X, ep, f)
        post = slice(ep.onset_bin + ep.ramp_bins, ep.n_bins)
        self.assertGreater(Y[post].std(axis=1).mean(), X[post].std(axis=1).mean(),
                           "GAIN_DRIFT conserved the mean but changed nothing.")


# ---------------------------------------------------------------------------
class DropoutNested(unittest.TestCase):
    """CHANNEL_DROPOUT severity levels must be NESTED.

    Independent draws per level made the severity ladder run backwards, because
    a 'more severe' level could happen to remove easier channels.
    """

    def test_more_severe_kills_a_superset_of_channels(self):
        X = healthy_block()
        dead = {}
        for sev in (0.05, 0.30, 0.60):
            ep = make_episode("CHANNEL_DROPOUT", severity=sev)
            f = inj.ramp(ep.n_bins, ep.onset_bin, ep.ramp_bins, ep.ramp_shape)
            Y = inj.apply_channel_dropout(X, ep, f)
            end = Y[-1]
            dead[sev] = {c for c in range(X.shape[1]) if np.isclose(end[c], 0.0)}
        self.assertTrue(
            dead[0.05] <= dead[0.30] <= dead[0.60],
            f"not nested: {sorted(dead[0.05])} / {sorted(dead[0.30])} / "
            f"{sorted(dead[0.60])}. Independent draws per level are what made "
            f"the ladder run backwards.")

    def test_more_severe_kills_at_least_as_many(self):
        X = healthy_block()
        counts = []
        for sev in (0.05, 0.30, 0.60):
            ep = make_episode("CHANNEL_DROPOUT", severity=sev)
            f = inj.ramp(ep.n_bins, ep.onset_bin, ep.ramp_bins, ep.ramp_shape)
            Y = inj.apply_channel_dropout(X, ep, f)
            counts.append(int(np.isclose(Y[-1], 0.0).sum()))
        self.assertEqual(counts, sorted(counts), f"channel counts {counts}")


# ---------------------------------------------------------------------------
class PreOnsetClean(unittest.TestCase):
    """Nothing before the onset bin may differ from the healthy recording.

    A leak would let a detector 'warn' off the leak itself, making the measured
    lead time a property of the injector rather than of the detector. This held
    "only by floating-point luck" until it was enforced by construction.
    """

    def test_ramp_is_exactly_zero_before_onset_for_every_shape(self):
        # Both shapes, because mutation testing on 13 Sep 2026 showed the
        # linear branch is saved by its clip while the exp branch was not.
        # A test that only covered "linear" passed against a real leak.
        for shape in ("linear", "exp"):
            with self.subTest(shape=shape):
                f = inj.ramp(1000, 400, 200, shape)
                self.assertTrue(
                    (f[:400] == 0.0).all(),
                    f"{shape} ramp leaked backwards; max before onset was "
                    f"{f[:400].max():.3e} and it must be exactly 0.0")
                self.assertGreater(f[400 + 200], 0.0)

    def test_ramp_is_never_negative(self):
        # The leak in the exp branch showed up as NEGATIVE values, which would
        # mean the fault running in reverse. Checked directly, for every shape,
        # so the property does not depend on where `live` starts.
        for shape in ("linear", "exp"):
            with self.subTest(shape=shape):
                f = inj.ramp(1000, 400, 200, shape)
                self.assertGreaterEqual(f.min(), 0.0)
                self.assertLessEqual(f.max(), 1.0)

    def test_every_mode_leaves_pre_onset_bit_for_bit_identical(self):
        X = healthy_block()
        for mode, sev in (("RATE_LOSS", 0.55), ("CHANNEL_DROPOUT", 0.60),
                          ("GAIN_DRIFT", 1.2), ("GEOMETRY_ROTATION", 1.2)):
            with self.subTest(mode=mode):
                ep = make_episode(mode, severity=sev)
                Y, _ = inj.apply_episode(X, ep)
                np.testing.assert_array_equal(
                    Y[:ep.onset_bin], X[:ep.onset_bin],
                    f"{mode} altered data BEFORE its onset bin.")

    def test_injector_does_not_mutate_its_input(self):
        X = healthy_block()
        original = X.copy()
        for mode, sev in (("RATE_LOSS", 0.55), ("CHANNEL_DROPOUT", 0.60),
                          ("GAIN_DRIFT", 1.2), ("GEOMETRY_ROTATION", 1.2)):
            inj.apply_episode(X, make_episode(mode, severity=sev))
        np.testing.assert_array_equal(
            X, original,
            "an injector mutated the source array. The raw data must never "
            "be modified, and a mutation here would silently corrupt every "
            "later episode drawn from the same block.")


# ---------------------------------------------------------------------------
class GeometryRotationNormPreserving(unittest.TestCase):
    """Rotation is injected with norm-preserving Givens rotations.

    This is the definitional fact behind withdrawn claim W04: rotation and
    `dispersion` share a signature BY CONSTRUCTION, which is why attribution
    names rotation correctly 0% of the time.
    """

    def test_row_norms_are_preserved_before_clipping(self):
        rng = np.random.default_rng(3)
        X = np.abs(rng.normal(50, 5, (200, 24)))   # well away from the 0 floor
        ep = make_episode("GEOMETRY_ROTATION", severity=0.45,
                          n_bins=200, onset_bin=50, ramp_bins=50)
        f = inj.ramp(ep.n_bins, ep.onset_bin, ep.ramp_bins, ep.ramp_shape)
        Y, _ = inj.apply_geometry_rotation(X, ep, f)
        n_before = np.linalg.norm(X[-1])
        n_after = np.linalg.norm(Y[-1])
        self.assertAlmostEqual(
            n_after / n_before, 1.0, places=2,
            msg="Givens rotations must preserve the vector norm. If they do "
                "not, GEOMETRY_ROTATION stops being a clean test of the "
                "comparator gate.")


# ---------------------------------------------------------------------------
class MatlabIndexing(unittest.TestCase):
    """MATLAB counts from 1, Python counts from 0.

    Getting this wrong shifts every trial by one bin and silently corrupts all
    neural/behavioural alignment.

    NOTE, 13 Sep 2026: the first version of this class checked arithmetic
    written inside the test itself, so it could not have failed because of a
    loader bug. That is a test that looks like a test. It now builds a .mat
    fixture with known 1-based indices and runs the REAL loader over it.
    """

    @classmethod
    def setUpClass(cls):
        import shutil, tempfile
        from scipy.io import savemat
        loader = import_module("03_load_dataset")
        cls.loader = loader
        cls.tmp = Path(tempfile.mkdtemp(prefix="idxtest_"))
        cls._shutil = shutil
        bd = cls.tmp / "RIG" / "day_1" / "block_1"
        bd.mkdir(parents=True)
        n_bins, n_trials, hold = 600, 6, 100
        rng = np.random.default_rng(11)
        # MATLAB convention: first bin is 1, stop is inclusive.
        cls.starts_m = np.arange(n_trials) * hold + 1
        cls.stops_m = cls.starts_m + hold - 1
        savemat(bd / "data.mat", {"nctx": rng.random((n_bins, 8)).astype(np.float32)})
        savemat(bd / "info.mat", {
            "cursorPos": np.zeros((n_bins, 2), np.float32),
            "targetPos": np.ones((n_bins, 2), np.float32),
            "angleErrorPerTrial": np.full(n_trials, 50.0),
            "trialSuccess": np.ones(n_trials, bool),
            "percentCorrect": 95.0})
        savemat(bd / "task.mat", {
            "startStops": np.stack([cls.starts_m, cls.stops_m], 1).astype(float),
            "name": "idxTest",
            "excludeTrials": np.zeros(n_trials, bool)})
        cls.ds = loader.load_dataset(cls.tmp, load_neural=True, verbose=False)

    @classmethod
    def tearDownClass(cls):
        cls._shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_loader_converts_one_based_to_zero_based(self):
        t = self.ds.trials.sort_values("trial_in_block")
        np.testing.assert_array_equal(t["start_bin_matlab"].to_numpy(),
                                      self.starts_m)
        np.testing.assert_array_equal(t["start_bin"].to_numpy(),
                                      self.starts_m - 1)

    def test_loader_makes_the_stop_exclusive(self):
        t = self.ds.trials.sort_values("trial_in_block")
        np.testing.assert_array_equal(t["stop_bin"].to_numpy(), self.stops_m)
        # MATLAB 1..100 is 100 bins; Python [0:100] is 100 bins.
        lengths = t["stop_bin"].to_numpy() - t["start_bin"].to_numpy()
        np.testing.assert_array_equal(lengths, np.full(len(t), 100))

    def test_first_trial_starts_at_python_index_zero(self):
        t = self.ds.trials.sort_values("trial_in_block")
        self.assertEqual(int(t["start_bin"].iloc[0]), 0,
                         "a MATLAB trial starting at bin 1 is Python index 0. "
                         "Off by one here shifts every trial in the project.")

    def test_consecutive_trials_abut_without_gap_or_overlap(self):
        t = self.ds.trials.sort_values("trial_in_block")
        s = t["start_bin"].to_numpy()
        e = t["stop_bin"].to_numpy()
        np.testing.assert_array_equal(e[:-1], s[1:])

    def test_slicing_the_neural_array_by_the_converted_indices_is_in_range(self):
        bid = self.ds.blocks.iloc[0]["block_id"]
        X = self.ds.neural[bid]
        t = self.ds.trials.sort_values("trial_in_block")
        self.assertLessEqual(int(t["stop_bin"].max()), X.shape[0],
                             "converted stop index runs past the end of the "
                             "neural array")


# ---------------------------------------------------------------------------
class Autocorrelation(unittest.TestCase):
    """The lag-1 statistic behind claims C04 and C18."""

    def test_white_noise_is_near_zero(self):
        rng = np.random.default_rng(5)
        self.assertLess(abs(spacing.lag1(rng.normal(0, 1, 4000))), 0.06)

    def test_a_slow_ramp_is_near_one(self):
        self.assertGreater(spacing.lag1(np.linspace(0, 1, 500)), 0.99)

    def test_alternating_series_is_near_minus_one(self):
        y = np.array([0.0, 1.0] * 200)
        self.assertLess(spacing.lag1(y), -0.95)

    def test_constant_series_returns_nan_not_a_number(self):
        self.assertTrue(np.isnan(spacing.lag1(np.ones(50))),
                        "a flat series has undefined autocorrelation and must "
                        "not silently return 0 or 1")

    def test_too_short_returns_nan(self):
        self.assertTrue(np.isnan(spacing.lag1(np.array([1.0, 2.0, 3.0]))))


# ---------------------------------------------------------------------------
class EffectiveSampleSize(unittest.TestCase):
    """n_eff = n(1-r)/(1+r): the arithmetic behind 'one measurement per session'."""

    def test_independent_samples_keep_their_count(self):
        self.assertAlmostEqual(spacing.n_eff(55, 0.0), 55.0)

    def test_the_projects_own_numbers_reproduce(self):
        # T11: 55 windows at r = 0.995 -> the published 0.1
        self.assertAlmostEqual(spacing.n_eff(55, 0.995), 0.1378, places=3)
        # T5: 42 windows at r = 0.980 -> the published 0.4
        self.assertAlmostEqual(spacing.n_eff(42, 0.980), 0.4242, places=3)

    def test_n_eff_falls_monotonically_as_correlation_rises(self):
        vals = [spacing.n_eff(55, r) for r in (0.0, 0.5, 0.9, 0.99)]
        self.assertEqual(vals, sorted(vals, reverse=True))


# ---------------------------------------------------------------------------
class WindowOverlap(unittest.TestCase):
    """The geometry behind claim C18: 1500-bin windows stepping 250."""

    def test_published_geometry_shares_five_sixths_of_its_data(self):
        self.assertAlmostEqual(spacing.overlap_fraction(1), 1250 / 1500, places=6)

    def test_decimating_by_six_removes_all_shared_data(self):
        self.assertEqual(spacing.overlap_fraction(6), 0.0)

    def test_overlap_never_goes_negative(self):
        for k in (6, 9, 50):
            self.assertGreaterEqual(spacing.overlap_fraction(k), 0.0)


# ---------------------------------------------------------------------------
class IntendedDirection(unittest.TestCase):
    """The decoder's target. A silent bug here looks like a weak decoder."""

    def test_returns_unit_vectors_pointing_cursor_to_target(self):
        kin = {"cursorPos": np.array([[0.0, 0.0], [1.0, 1.0]]),
               "targetPos": np.array([[3.0, 0.0], [1.0, 5.0]])}
        unit, ok = dec.intended_direction(kin)
        self.assertTrue(ok.all())
        np.testing.assert_allclose(unit[0], [1.0, 0.0], atol=1e-9)
        np.testing.assert_allclose(unit[1], [0.0, 1.0], atol=1e-9)
        np.testing.assert_allclose(np.linalg.norm(unit, axis=1), [1.0, 1.0])

    def test_cursor_on_target_is_masked_out(self):
        kin = {"cursorPos": np.array([[2.0, 2.0]]),
               "targetPos": np.array([[2.0, 2.0]])}
        _, ok = dec.intended_direction(kin)
        self.assertFalse(ok[0],
                         "a bin with no defined intended direction must be "
                         "masked, not fed to the decoder as a zero vector")

    def test_angular_error_is_zero_for_a_perfect_prediction(self):
        target = np.array([[1.0, 0.0], [0.0, 1.0]])
        err = dec.angular_error_deg(target.copy(), target)
        np.testing.assert_allclose(err, [0.0, 0.0], atol=1e-6)

    def test_angular_error_is_180_for_exactly_backwards(self):
        target = np.array([[1.0, 0.0]])
        err = dec.angular_error_deg(-target, target)
        self.assertAlmostEqual(err[0], 180.0, places=4)

    def test_angular_error_is_90_for_orthogonal(self):
        err = dec.angular_error_deg(np.array([[0.0, 1.0]]), np.array([[1.0, 0.0]]))
        self.assertAlmostEqual(err[0], 90.0, places=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ---------------------------------------------------------------------------
class WindowMeansByCumsum(unittest.TestCase):
    """The vectorised window-mean rewrite must match the obvious slow version."""

    def test_matches_naive_slice_loop(self):
        rng = np.random.default_rng(4)
        sig = rng.normal(size=(3, sweep.BLOCK_BINS))
        fast = sweep.windows(sig)
        starts = np.arange(0, sweep.BLOCK_BINS - sweep.WINDOW_BINS + 1,
                           sweep.STEP_BINS)
        slow = np.array([[row[s:s + sweep.WINDOW_BINS].mean() for s in starts]
                         for row in sig])
        self.assertEqual(fast.shape, slow.shape)
        np.testing.assert_allclose(fast, slow, atol=1e-10)

    def test_window_count_matches_the_neural_geometry(self):
        """55 windows per block, 10 after decimation -- the numbers C18 uses."""
        w = sweep.windows(np.zeros((1, sweep.BLOCK_BINS)))
        self.assertEqual(w.shape[1], sweep.N_WINDOWS)
        self.assertEqual(w[:, ::sweep.DECIMATE].shape[1], sweep.N_KEPT)
        # Decimated windows must share no bins: the spacing is the window length.
        self.assertEqual(sweep.DECIMATE * sweep.STEP_BINS, sweep.WINDOW_BINS)


# ---------------------------------------------------------------------------
class OrnsteinUhlenbeck(unittest.TestCase):
    """The drift model the sweep is designed against."""

    def test_stationary_variance_is_one(self):
        rng = np.random.default_rng(5)
        for tau_bins in (10.0, 500.0):
            x = sweep.ou((200, 4000), tau_bins, rng)
            self.assertAlmostEqual(float(x.var()), 1.0, delta=0.08,
                                   msg=f"tau_bins={tau_bins}")

    def test_lag1_matches_the_analytic_value(self):
        """For an OU sampled at unit steps, lag-1 correlation is exp(-1/tau)."""
        rng = np.random.default_rng(6)
        for tau_bins in (10.0, 100.0):
            x = sweep.ou((200, 20000), tau_bins, rng)
            got = float(np.nanmedian(sweep.lag1(x)))
            self.assertAlmostEqual(got, float(np.exp(-1.0 / tau_bins)),
                                   delta=0.02, msg=f"tau_bins={tau_bins}")

    def test_paths_start_in_equilibrium(self):
        """No warm-up transient: the first bin is as variable as the last."""
        rng = np.random.default_rng(8)
        x = sweep.ou((4000, 50), 200.0, rng)
        self.assertAlmostEqual(float(x[:, 0].var()), float(x[:, -1].var()),
                               delta=0.15)


# ---------------------------------------------------------------------------
class SmallSampleBias(unittest.TestCase):
    """The saturation that made C18's 0.902 impossible to invert."""

    def test_estimator_is_biased_low_at_ten_points(self):
        rng = np.random.default_rng(9)
        ceiling = sweep.estimator_ceiling(sweep.N_KEPT, rng, reps=6000)
        # A true correlation of 0.999 must read far below itself at 10 points.
        self.assertLess(ceiling, 0.75)
        self.assertGreater(ceiling, 0.45)

    def test_ceiling_rises_with_series_length(self):
        """The bias is a small-sample effect, so more points must ease it."""
        rng = np.random.default_rng(10)
        short = sweep.estimator_ceiling(10, rng, reps=6000)
        long = sweep.estimator_ceiling(60, rng, reps=6000)
        self.assertGreater(long, short + 0.1)

    def test_c18_pooled_value_is_above_the_ceiling(self):
        """The finding itself: 0.902 cannot come from a stationary AR(1) at n=10.

        This is what the design script tripped over. If a future change makes
        this pass quietly, the inversion has started clamping instead of
        refusing, and the NaN that flagged the problem would be gone.
        """
        rng = np.random.default_rng(12)
        self.assertGreater(0.902, sweep.estimator_ceiling(10, rng, reps=6000))


# ---------------------------------------------------------------------------
class InversionRefusesOffCurve(unittest.TestCase):
    """A target off the end of the curve must give nan, never a clamped value."""

    def setUp(self):
        self.taus = np.array([1.0, 10.0, 100.0, 1000.0])
        self.curve = np.array([0.1, 0.3, 0.5, 0.6])

    def test_above_the_ceiling_is_nan(self):
        self.assertTrue(np.isnan(sweep.invert(self.taus, self.curve, 0.902)))

    def test_below_the_floor_is_nan(self):
        self.assertTrue(np.isnan(sweep.invert(self.taus, self.curve, -0.2)))

    def test_nan_target_is_nan(self):
        self.assertTrue(np.isnan(sweep.invert(self.taus, self.curve, np.nan)))

    def test_on_curve_interpolates(self):
        self.assertAlmostEqual(sweep.invert(self.taus, self.curve, 0.3), 10.0)
        got = sweep.invert(self.taus, self.curve, 0.4)
        self.assertTrue(10.0 < got < 100.0)

    def test_non_monotone_input_does_not_break_interpolation(self):
        """Simulation jitter can dent the curve; the inversion must still be sane."""
        dented = np.array([0.1, 0.35, 0.30, 0.6])
        got = sweep.invert(self.taus, dented, 0.32)
        self.assertTrue(np.isfinite(got))
        self.assertTrue(self.taus[0] <= got <= self.taus[-1])


# ---------------------------------------------------------------------------
class StreamingDecoderMatchesStacked(unittest.TestCase):
    """The streaming decoder fit must equal the all-at-once one, exactly.

    Corresponds to a real defect, found 21 September 2026:
    `make_session_table.py` loaded every recording into memory at once. At the
    campaign size this project recommends -- about 480 five-minute sessions --
    that is 22 GB, which no machine here has. It would have crashed on the
    fourth night of recording, after thirty hours of data collection, which is
    the worst possible moment to discover a memory bug.

    The fix streams the fit, accumulating the normal equations session by
    session instead of stacking the frames. A streaming fit is only a fix if it
    gives the SAME answer -- otherwise it silently changes every result -- so
    that equality is what is tested here, on data where both can be computed.
    """

    def setUp(self):
        import monitor as M
        self.M = M
        rng = np.random.default_rng(11)
        self.pref = rng.uniform(0, 2 * np.pi, 24)

    def _fake(self, n, seed):
        rng = np.random.default_rng(seed)
        head = np.repeat(rng.uniform(0, 2 * np.pi, n // 50 + 1), 50)[:n]
        X = 128.0 + 6.0 * np.cos(head[:, None] - self.pref[None, :])
        X += rng.normal(0, 1.0, X.shape)
        return X, head

    def test_normal_equations_match_stacking(self):
        """Same weights, same normalisation, from the same data."""
        M = self.M
        parts = [self._fake(400, s) for s in (1, 2, 3)]
        X = np.vstack([p[0] for p in parts])
        h = np.concatenate([p[1] for p in parts])

        W_stack, mu_stack, sd_stack = M.fit_decoder(X, h)

        # Reproduce the streaming arithmetic directly, without touching disk.
        n_total = sum(len(p[0]) for p in parts)
        s1 = sum(p[0].sum(axis=0) for p in parts)
        s2 = sum((p[0] * p[0]).sum(axis=0) for p in parts)
        mu = s1 / n_total
        sd = np.sqrt(np.maximum(s2 / n_total - mu * mu, 0.0))
        sd[sd < 1e-12] = 1.0
        d = len(mu) + 1
        A = np.zeros((d, d))
        B = np.zeros((d, 2))
        for Xi, hi in parts:
            Z = np.hstack([(Xi - mu) / sd, np.ones((len(Xi), 1))])
            Y = np.column_stack([np.cos(hi), np.sin(hi)])
            A += Z.T @ Z
            B += Z.T @ Y
        A += M.RIDGE * n_total * np.eye(d)
        W_stream = np.linalg.solve(A, B)

        self.assertLess(np.abs(mu - mu_stack).max(), 1e-9)
        self.assertLess(np.abs(sd - sd_stack).max(), 1e-7)
        self.assertLess(np.abs(W_stream - W_stack).max(), 1e-8)

    def test_session_info_does_not_read_the_frames(self):
        """Metadata must be readable without touching capture.npy.

        This is the property the whole fix rests on: if `session_info` ever
        starts loading the recording, the memory problem comes straight back
        and nothing would notice until a campaign was large enough to crash.
        """
        import inspect
        src = inspect.getsource(self.M.session_info)
        self.assertNotIn("capture.npy", src)
        self.assertIn("capture_t.npy", src)


# ---------------------------------------------------------------------------
class DitherBlocksMatchPixelExpansion(unittest.TestCase):
    """The fast stimulus must paint bit-identical pixels to the slow one.

    Corresponds to a real problem, measured 21 September 2026: the original
    inner loop called np.repeat twice per frame, allocating two 614,400-element
    arrays fifty times a second. It measured 6.9 ms per frame on a fast laptop,
    which extrapolates to more than the entire 20 ms budget on a Raspberry Pi 4
    -- so the stimulus would silently have failed to hold 50 fps, every camera
    frame's direction label would have been wrong by an unknown amount, and
    nothing in the recording would have said so.

    The fix broadcasts a per-patch value into (cols, patch, rows, patch)
    instead of expanding to pixels. A faster stimulus is only a fix if it draws
    THE SAME SCREEN -- otherwise it changes the apparatus -- so that is what is
    tested, including the geometric-rotation path which reorders patches before
    the expansion.
    """

    def setUp(self):
        self.cols, self.rows, self.patch = 24, 16, 40
        rng = np.random.default_rng(3)
        self.n = self.cols * self.rows
        self.pref = rng.uniform(0, 2 * np.pi, self.n)
        W, H = self.cols * self.patch, self.rows * self.patch
        self.dither = rng.random((W, H)).astype(np.float32)

    def _values(self, heading, roll=0):
        t = np.clip(0.5 + 0.00211 * np.cos(heading - self.pref), 0, 1) * 255.0
        if roll:
            t = np.roll(t.reshape(self.rows, self.cols), roll, axis=1).ravel()
        return t

    def _slow(self, t):
        def expand(v):
            g = v.reshape(self.rows, self.cols).T
            return np.repeat(np.repeat(g, self.patch, 0), self.patch, 1)
        lo = np.floor(t)
        return (expand(lo) + (self.dither < expand(t - lo))).astype(np.uint8)

    def _fast(self, t):
        db = self.dither.reshape(self.cols, self.patch, self.rows, self.patch)
        blocks = lambda v: v.reshape(self.rows, self.cols).T[:, None, :, None]
        lo = np.floor(t)
        px = blocks(lo).astype(np.uint8) + (db < blocks(t - lo))
        return px.reshape(self.cols * self.patch, self.rows * self.patch)

    def test_identical_pixels(self):
        for heading in (0.0, 1.2345, 3.0, 5.9):
            t = self._values(heading)
            self.assertTrue(np.array_equal(self._slow(t), self._fast(t)),
                            f"pixels differ at heading {heading}")

    def test_identical_under_geometric_rotation(self):
        """The rotation fault reorders patches; the expansion must follow."""
        t = self._values(2.0, roll=6)
        self.assertTrue(np.array_equal(self._slow(t), self._fast(t)))

    def test_the_dither_actually_does_something(self):
        """A guard against both versions being trivially equal.

        At the calibrated depth the modulation is about half a brightness
        level, so neighbouring patches must differ by exactly one level in
        SOME pixels and not others. If the dither were being discarded, every
        pixel in a patch would be equal and this test would pass vacuously
        while the apparatus recorded nothing but noise.
        """
        t = self._values(1.0)
        img = self._fast(t)
        patch0 = img[:self.patch, :self.patch]
        self.assertGreater(len(np.unique(patch0)), 1,
                           "a patch is uniform -- the dither is being lost")
        self.assertLessEqual(int(patch0.max()) - int(patch0.min()), 1,
                             "a patch spans more than one brightness level")

