"""
Tests for the degraded-mode extension (Shape B: harden against failure).

These need no running service and no model download. The model signal is
replaced with one that fails (or succeeds) on demand, requests go through
Flask's test client, and the audit log is pointed at a temp file so your real
logs/audit.jsonl is not touched.

    python -m unittest test_degraded -v

They are fast and deterministic, which complements degraded_check.py: that one
breaks the real model on a real running service, this one pins the logic.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as app_module
import config
import detector
import scoring

sys.stdout.reconfigure(errors="replace")

TEXT = "We missed the last train, so we walked home along the canal."
NINE_FIELDS = ["timestamp", "content_id", "creator_id", "guess", "model_score",
               "style_score", "combined_score", "label", "status"]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        log_dir = Path(self.tmp.name)
        for target, value in (("LOG_DIR", log_dir), ("AUDIT_LOG", log_dir / "audit.jsonl")):
            patcher = mock.patch.object(config, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        # One creator_id per request already keeps clear of the per-minute limit,
        # but switching the limiter off makes that independent of test order.
        self._limiter_was = app_module.limiter.enabled if hasattr(app_module.limiter, "enabled") else None
        if self._limiter_was is not None:
            app_module.limiter.enabled = False
            self.addCleanup(setattr, app_module.limiter, "enabled", self._limiter_was)

        # The route logs each model failure as an error, which is correct in
        # the service and just noise in a test run.
        app_module.app.logger.disabled = True
        self.addCleanup(setattr, app_module.app.logger, "disabled", False)

        self.client = app_module.app.test_client()
        self._n = 0

    def submit(self, text=TEXT):
        self._n += 1
        return self.client.post("/submit", json={
            "text": text, "creator_id": f"test_{self.id()}_{self._n}"})

    def log(self):
        path = config.AUDIT_LOG
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def fail_model(self, exc):
        patcher = mock.patch("detector.model_signal", side_effect=exc)
        patcher.start()
        self.addCleanup(patcher.stop)

    def set_style(self, score):
        patcher = mock.patch("stylometry.style_signal", return_value=score)
        patcher.start()
        self.addCleanup(patcher.stop)


class DegradedAnswers(Base):
    """Criterion 6: a model failure still gets an answer, never a 5xx."""

    def test_missing_model_gets_a_200_marked_degraded(self):
        self.fail_model(detector.DetectorUnavailable("model not downloaded"))
        resp = self.submit()
        body = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIs(body["degraded"], True)
        self.assertIsNone(body["model_score"])
        self.assertIsInstance(body["style_score"], float)
        self.assertIn(body["guess"], ("human", "unsure"))

    def test_other_failures_are_handled_the_same_way(self):
        for exc in (RuntimeError("out of memory"), MemoryError(), OSError("disk full")):
            with self.subTest(exc=type(exc).__name__):
                with mock.patch("detector.model_signal", side_effect=exc):
                    resp = self.submit()
                self.assertEqual(resp.status_code, 200)
                self.assertIs(resp.get_json()["degraded"], True)

    def test_response_keeps_every_field_the_tooling_reads(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        body = self.submit().get_json()
        for field in ("content_id", "guess", "confidence", "label",
                      "model_score", "style_score", "degraded"):
            self.assertIn(field, body)

    def test_every_degraded_label_says_part_of_the_check_did_not_run(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        for style in (0.05, 0.5, 0.95):
            with self.subTest(style=style), mock.patch("stylometry.style_signal", return_value=style):
                label = self.submit().get_json()["label"]
                self.assertIn("Only part of our check could run", label)


class DegradedNeverAccuses(Base):
    """Criterion 7, first half: one signal never says 'ai'."""

    def test_a_style_score_in_the_ai_range_comes_back_unsure(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        self.set_style(0.95)    # far above AI_THRESHOLD
        body = self.submit().get_json()
        self.assertEqual(body["guess"], "unsure")
        self.assertNotIn("probably written by AI", body["label"])

    def test_a_style_score_in_the_human_range_still_says_human(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        self.set_style(0.10)
        self.assertEqual(self.submit().get_json()["guess"], "human")

    def test_label_without_model_never_returns_ai_across_the_whole_range(self):
        for i in range(0, 101):
            guess, _ = scoring.label_without_model(i / 100)
            self.assertNotEqual(guess, "ai", f"style score {i / 100}")

    def test_label_without_model_matches_score_to_label_below_the_ai_band(self):
        for score in (0.0, 0.2, config.HUMAN_THRESHOLD, 0.5, config.AI_THRESHOLD - 0.01):
            self.assertEqual(scoring.label_without_model(score)[0], scoring.score_to_label(score)[0])

    def test_confidence_is_scaled_by_the_degraded_factor(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        self.set_style(0.10)
        full = (config.HUMAN_THRESHOLD - 0.10) / config.HUMAN_THRESHOLD
        expected = full * config.DEGRADED_CONFIDENCE_FACTOR
        # The route rounds before and after scaling, so compare to 3 places.
        self.assertAlmostEqual(self.submit().get_json()["confidence"], expected, places=3)


class DegradedLeavesATrace(Base):
    """Criterion 7, second half: every failure is in the audit log."""

    def test_one_entry_with_the_flag_and_a_reason(self):
        self.fail_model(detector.DetectorUnavailable("model not downloaded"))
        content_id = self.submit().get_json()["content_id"]
        entries = [e for e in self.log() if e.get("content_id") == content_id]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertIs(entry["degraded"], True)
        self.assertIn("DetectorUnavailable", entry["degraded_reason"])
        self.assertIn("model not downloaded", entry["degraded_reason"])

    def test_the_nine_required_fields_are_present_and_model_score_is_null(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        self.submit()
        entry = self.log()[0]
        for field in NINE_FIELDS:
            self.assertIn(field, entry)
        self.assertIsNone(entry["model_score"])
        self.assertEqual(entry["status"], "decided")

    def test_a_long_multiline_error_is_kept_to_one_short_line(self):
        self.fail_model(detector.DetectorUnavailable("first line\nsecond line\n" * 100))
        self.submit()
        reason = self.log()[0]["degraded_reason"]
        self.assertNotIn("\n", reason)
        self.assertLessEqual(len(reason), 300)

    def test_a_degraded_decision_can_still_be_appealed(self):
        self.fail_model(detector.DetectorUnavailable("x"))
        content_id = self.submit().get_json()["content_id"]
        resp = self.client.post("/appeal", json={
            "content_id": content_id, "reasoning": "I wrote this myself."})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json().get("status"), "under_review")
        mine = [e for e in self.log() if e.get("content_id") == content_id]
        self.assertEqual(len(mine), 2)    # the decision stays, the appeal sits beside it


class NormalPathIsUnchanged(Base):
    """The extension must not leak into the system it extends."""

    def test_a_working_model_is_not_degraded(self):
        with mock.patch("detector.model_signal", return_value=0.5):
            body = self.submit().get_json()
        self.assertIs(body["degraded"], False)
        self.assertEqual(body["model_score"], 0.5)

    def test_a_normal_audit_entry_has_no_degraded_fields(self):
        with mock.patch("detector.model_signal", return_value=0.5):
            self.submit()
        entry = self.log()[0]
        self.assertNotIn("degraded", entry)
        self.assertNotIn("degraded_reason", entry)

    def test_two_high_scores_still_produce_the_ai_label(self):
        self.set_style(0.9)
        with mock.patch("detector.model_signal", return_value=0.9):
            body = self.submit().get_json()
        self.assertEqual(body["guess"], "ai")

    def test_normal_confidence_is_not_scaled(self):
        self.set_style(0.9)
        with mock.patch("detector.model_signal", return_value=0.9):
            body = self.submit().get_json()
        combined = scoring.combine_signals(0.9, 0.9)
        expected = round((combined - config.AI_THRESHOLD) / (1.0 - config.AI_THRESHOLD), 4)
        self.assertEqual(body["confidence"], expected)

    def test_text_the_model_rejects_is_still_a_400_and_not_degraded(self):
        with mock.patch("detector.model_signal", side_effect=ValueError("too short")):
            resp = self.submit()
        self.assertEqual(resp.status_code, 400)
        entry = self.log()[0]
        self.assertEqual(entry["event"], "rejected")
        self.assertNotIn("degraded", entry)

    def test_input_checks_still_run_before_either_signal(self):
        with mock.patch("detector.model_signal") as model:
            resp = self.client.post("/submit", json={"text": "", "creator_id": "x"})
        self.assertEqual(resp.status_code, 400)
        model.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
