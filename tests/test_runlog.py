"""
Tests for the structured run log (runlog.py, the hooks in app.py).

    python tests/test_runlog.py             report, grouped
    python tests/test_runlog.py --plain     the standard unittest output
    python -m unittest discover -s tests    every test in this folder, any runner

No server and no model: the model signal is replaced, requests go through
Flask's test client, and logs go to a temp directory so logs/runs.jsonl and
logs/audit.jsonl are not touched.

The question these answer: does every kind of run, and above all every kind of
failure, leave a record that says what came in, what went out and why?
"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # the project root, where app.py lives

import app as app_module
import config
import runlog

sys.stdout.reconfigure(errors="replace")

TEXT = "We missed the last train, so we walked home along the canal."
FIELDS = ["timestamp", "run_id", "content_id", "route", "status_code", "outcome",
          "creator_id", "input", "output", "duration_ms", "cpu_ms", "model_ms", "style_ms",
          "cold_start", "model_score", "style_score", "combined_score", "degraded",
          "degraded_reason", "exception", "config"]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(config, "LOG_DIR", Path(self.tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(config, "AUDIT_LOG", Path(self.tmp.name) / "audit.jsonl")
        patcher.start()
        self.addCleanup(patcher.stop)

        self._limiter_was = getattr(app_module.limiter, "enabled", None)
        if self._limiter_was is not None:
            app_module.limiter.enabled = False
            self.addCleanup(setattr, app_module.limiter, "enabled", self._limiter_was)

        app_module.app.logger.disabled = True
        self.addCleanup(setattr, app_module.app.logger, "disabled", False)

        self.client = app_module.app.test_client()
        self._n = 0
        patcher = mock.patch("detector.model_signal", return_value=0.5)
        self.model = patcher.start()
        self.addCleanup(patcher.stop)

    def submit(self, text=TEXT, creator=None):
        self._n += 1
        return self.client.post("/submit", json={
            "text": text, "creator_id": creator or f"rl_{self.id()}_{self._n}"})

    def runs(self):
        return runlog.read()

    def only_run(self):
        runs = self.runs()
        self.assertEqual(len(runs), 1, f"expected one run record, got {len(runs)}")
        return runs[0]


class EveryRunIsRecorded(Base):
    """Good runs - Each carries named fields for input, output, duration and settings"""

    def test_a_decided_run_has_every_named_field(self):
        """A decided run has all 21 named fields"""
        self.submit()
        record = self.only_run()
        for field in FIELDS:
            self.assertIn(field, record)
        self.assertEqual(record["outcome"], "decided")
        self.assertEqual(record["status_code"], 200)

    def test_input_and_output_are_recorded(self):
        """The input text and the answer given are both in the record"""
        self.submit()
        record = self.only_run()
        self.assertEqual(record["input"]["preview"], TEXT)
        self.assertEqual(record["input"]["chars"], len(TEXT))
        self.assertEqual(record["input"]["words"], len(TEXT.split()))
        self.assertIn(record["output"]["guess"], ("human", "unsure", "ai"))
        self.assertIsInstance(record["output"]["confidence"], float)
        self.assertTrue(record["output"]["label"])

    def test_durations_are_recorded_for_the_run_and_each_signal(self):
        """Total time and the time in each signal are numbers, total at least the parts"""
        self.submit()
        record = self.only_run()
        for field in ("duration_ms", "model_ms", "style_ms"):
            self.assertIsInstance(record[field], float, field)
        self.assertGreaterEqual(record["duration_ms"], record["model_ms"])

    def test_cpu_time_is_recorded(self):
        """CPU time used by the run is recorded as a number"""
        self.submit()
        record = self.only_run()
        self.assertIsInstance(record["cpu_ms"], float)
        self.assertGreaterEqual(record["cpu_ms"], 0)

    def test_a_slow_model_shows_up_in_model_ms(self):
        """A slow model shows up in model_ms, not in style_ms"""
        self.model.side_effect = lambda text: (time.sleep(0.15), 0.5)[1]
        self.submit()
        record = self.only_run()
        self.assertGreaterEqual(record["model_ms"], 140)
        self.assertLess(record["style_ms"], record["model_ms"])

    def test_scores_and_the_settings_that_produced_them_are_recorded(self):
        """Both scores, the combined score and the config in force are recorded"""
        self.submit()
        record = self.only_run()
        self.assertEqual(record["model_score"], 0.5)
        self.assertIsInstance(record["style_score"], float)
        self.assertIsInstance(record["combined_score"], float)
        self.assertEqual(record["config"]["ai_threshold"], config.AI_THRESHOLD)
        self.assertEqual(record["config"]["human_threshold"], config.HUMAN_THRESHOLD)
        self.assertEqual(record["config"]["detector_model"], config.DETECTOR_MODEL)

    def test_the_content_id_links_to_the_audit_log(self):
        """content_id matches the audit-log entry for the same decision"""
        self.submit()
        record = self.only_run()
        audit_ids = [json.loads(l)["content_id"]
                     for l in config.AUDIT_LOG.read_text(encoding="utf-8").splitlines()]
        self.assertIn(record["content_id"], audit_ids)

    def test_one_json_object_per_line_and_it_reads_back(self):
        """The file is one JSON object per line and reads back with runlog.read"""
        self.submit()
        self.submit()
        lines = (Path(self.tmp.name) / config.RUN_LOG_NAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            json.loads(line)
        self.assertEqual(len(runlog.read()), 2)
        self.assertEqual(len(runlog.read(limit=1)), 1)

    def test_a_cold_start_is_flagged(self):
        """A run that began with the model not loaded is flagged cold_start"""
        with mock.patch("detector._model", None):
            self.submit()
        self.assertIs(self.only_run()["cold_start"], True)

    def test_input_is_cut_to_the_configured_length(self):
        """The input preview is cut to RUN_LOG_INPUT_CHARS, the length is not"""
        long_text = "word " * 400
        with mock.patch.object(config, "RUN_LOG_INPUT_CHARS", 50):
            self.submit(long_text)
        record = self.only_run()
        self.assertEqual(len(record["input"]["preview"]), 50)
        self.assertEqual(record["input"]["chars"], len(long_text))

    def test_zero_keeps_the_length_but_none_of_the_text(self):
        """RUN_LOG_INPUT_CHARS = 0 stores no text at all"""
        with mock.patch.object(config, "RUN_LOG_INPUT_CHARS", 0):
            self.submit()
        record = self.only_run()
        self.assertEqual(record["input"]["preview"], "")
        self.assertEqual(record["input"]["chars"], len(TEXT))

    def test_other_routes_are_not_recorded(self):
        """/ping and /health do not write run records"""
        self.client.post("/ping", json={"message": "hi"})
        self.client.get("/health")
        self.assertEqual(self.runs(), [])


class FailuresAreRecorded(Base):
    """Failures - A run that did not succeed leaves a record that says why"""

    def test_a_model_failure_is_recorded_as_degraded_with_the_reason(self):
        """A model failure is recorded as degraded, with the reason and the time spent"""
        self.model.side_effect = RuntimeError("out of memory")
        self.submit()
        record = self.only_run()
        self.assertEqual(record["outcome"], "degraded")
        self.assertIs(record["degraded"], True)
        self.assertIn("out of memory", record["degraded_reason"])
        self.assertIsNone(record["model_score"])
        self.assertIsInstance(record["model_ms"], float)

    def test_a_rejected_input_is_recorded_with_the_error(self):
        """A rejected input is recorded as rejected, with the error and no signal times"""
        resp = self.client.post("/submit", json={"text": "", "creator_id": "x"})
        self.assertEqual(resp.status_code, 400)
        record = self.only_run()
        self.assertEqual(record["outcome"], "rejected")
        self.assertEqual(record["status_code"], 400)
        self.assertEqual(record["output"]["error"], "invalid_request")
        self.assertTrue(record["output"]["message"])
        self.assertIsNone(record["model_ms"])
        self.assertIsNone(record["style_ms"])
        self.assertIsInstance(record["duration_ms"], float)

    def test_malformed_bodies_are_recorded_too(self):
        """A body that is not an object, or has a non-text input, is recorded"""
        self.client.post("/submit", json=["not", "an", "object"])
        self.client.post("/submit", json={"text": 12345, "creator_id": "x"})
        self.client.post("/submit", json={"creator_id": "x"})
        runs = self.runs()
        self.assertEqual([r["outcome"] for r in runs], ["rejected"] * 3)
        self.assertEqual(runs[1]["input"]["type"], "int")
        self.assertEqual(runs[2]["input"]["type"], "missing")

    def test_text_the_model_refuses_is_recorded_with_its_time(self):
        """Text the model refuses is a recorded rejection and its model time is kept"""
        self.model.side_effect = ValueError("too short to score")
        self.submit()
        record = self.only_run()
        self.assertEqual(record["outcome"], "rejected")
        self.assertIsInstance(record["model_ms"], float)

    def test_a_rate_limited_request_is_recorded(self):
        """A request refused by the rate limiter is recorded as rate_limited"""
        app_module.limiter.enabled = True
        statuses = [self.submit(creator="rate_limit_probe").status_code for _ in range(8)]
        self.assertIn(429, statuses)
        limited = [r for r in self.runs() if r["outcome"] == "rate_limited"]
        self.assertGreaterEqual(len(limited), 1)
        self.assertEqual(limited[0]["status_code"], 429)
        self.assertEqual(limited[0]["creator_id"], "rate_limit_probe")
        self.assertEqual(len(self.runs()), 8)    # every attempt, none lost

    def test_a_crash_flask_turns_into_a_500_is_recorded(self):
        """A crash that Flask turns into a 500 is recorded, with the exception"""
        with mock.patch("stylometry.style_signal", side_effect=RuntimeError("boom in style")):
            resp = self.submit()
        self.assertEqual(resp.status_code, 500)
        record = self.only_run()
        self.assertEqual(record["outcome"], "error")
        self.assertEqual(record["exception"]["type"], "RuntimeError")
        self.assertIn("boom in style", record["exception"]["message"])
        self.assertIn("boom in style", record["exception"]["traceback"])

    def test_a_crash_that_propagates_is_still_recorded(self):
        """A crash that propagates out of Flask, as in debug mode, is still recorded"""
        with mock.patch.dict(app_module.app.config, {"PROPAGATE_EXCEPTIONS": True}):
            with mock.patch("stylometry.style_signal", side_effect=RuntimeError("boom in style")):
                with self.assertRaises(RuntimeError):
                    self.submit()
        record = self.only_run()
        self.assertEqual(record["outcome"], "error")
        self.assertEqual(record["status_code"], 500)
        self.assertEqual(record["exception"]["type"], "RuntimeError")

    def test_an_audit_write_failure_is_recorded(self):
        """If the audit log cannot be written, the run log still says so"""
        with mock.patch("audit.log_decision", side_effect=OSError("disk full")):
            resp = self.submit()
        self.assertEqual(resp.status_code, 500)
        record = self.only_run()
        self.assertEqual(record["outcome"], "error")
        self.assertEqual(record["exception"]["type"], "OSError")
        self.assertEqual(record["input"]["preview"], TEXT)    # what was lost is still known

    def test_every_failure_kind_has_a_reason_to_read(self):
        """Every non-decided record carries something that says why"""
        self.client.post("/submit", json={"text": "", "creator_id": "x"})
        self.model.side_effect = RuntimeError("no model")
        self.submit()
        self.model.side_effect = None
        with mock.patch("stylometry.style_signal", side_effect=ValueError("bad")):
            self.submit()
        for record in self.runs():
            self.assertNotEqual(record["outcome"], "decided")
            why = (record["output"]["message"] or record["degraded_reason"]
                   or (record["exception"] or {}).get("message"))
            self.assertTrue(why, record["outcome"])


class LoggingNeverBreaksTheService(Base):
    """Safety - A problem writing the log does not turn a good answer into an error"""

    def test_an_unwritable_run_log_still_answers_and_says_so(self):
        """An unwritable run log still gets a 200 and the failure is reported, not silent"""
        with mock.patch.object(runlog, "path", return_value=Path(self.tmp.name)):   # a directory
            with self.assertLogs("provenance.runlog", level="ERROR") as logged:
                resp = self.submit()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any("could not write run record" in m for m in logged.output))

    def test_a_malformed_line_does_not_stop_the_log_reading_back(self):
        """A corrupt line is skipped and the rest of the log still reads"""
        self.submit()
        with (Path(self.tmp.name) / config.RUN_LOG_NAME).open("a", encoding="utf-8") as f:
            f.write("{this is not json\n")
        self.submit()
        self.assertEqual(len(runlog.read()), 2)


# ── The readable report ──────────────────────────────────────────────────────

GROUPS = [EveryRunIsRecorded, FailuresAreRecorded, LoggingNeverBreaksTheService]
WIDTH = 72


def _colour_on():
    if os.getenv("NO_COLOR") or not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        os.system("")
    return True


def _paint(text, code, on):
    return f"\033[{code}m{text}\033[0m" if on else text


def report() -> int:
    on = _colour_on()
    green = lambda s: _paint(s, "32;1", on)
    red = lambda s: _paint(s, "31;1", on)
    bold = lambda s: _paint(s, "1", on)
    dim = lambda s: _paint(s, "2", on)

    started = time.time()
    total = passed = 0
    summary = []
    print()
    print(bold("Provenance Guard - structured run log tests"))
    print(dim("No server, no model, temp logs. Your real logs are not touched."))

    for cls in GROUPS:
        title = cls.__doc__.strip()
        print()
        print(bold(title))
        print("-" * WIDTH)
        names = [n for n in cls.__dict__ if n.startswith("test_")]
        group_pass = 0
        for name in names:
            result = unittest.TestResult()
            cls(name).run(result)
            problems = result.failures + result.errors
            what = (getattr(cls, name).__doc__ or name).strip()
            total += 1
            if not problems:
                passed += 1
                group_pass += 1
                print(f"  {green('[PASS]')} {what}")
            else:
                print(f"  {red('[FAIL]')} {what}")
                for _, trace in problems:
                    for ln in [x for x in trace.strip().splitlines() if x.strip()][-3:]:
                        print(red(f"           {ln.strip()[:WIDTH - 11]}"))
        ok = group_pass == len(names)
        summary.append((title, group_pass, len(names), ok))
        print(f"  {dim('=>')} {(green if ok else red)(f'{group_pass}/{len(names)}')}")

    print()
    print("=" * WIDTH)
    print(bold("Summary"))
    for title, got, of, ok in summary:
        print(f"  {green('OK  ') if ok else red('FAIL')} {got:>2}/{of:<2}  {title}")
    print("-" * WIDTH)
    verdict = green("ALL PASSED") if passed == total else red(f"{total - passed} FAILED")
    print(f"  {passed}/{total} tests   {verdict}   {dim(f'({time.time() - started:.1f}s)')}")
    print()
    return 0 if passed == total else 1


if __name__ == "__main__":
    if "--plain" in sys.argv:
        sys.argv.remove("--plain")
        unittest.main(verbosity=2)
    else:
        sys.exit(report())
