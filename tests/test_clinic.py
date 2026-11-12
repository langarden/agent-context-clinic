# -*- coding: utf-8 -*-
"""agent-context-clinic tests."""

import json
import os
import tempfile
import unittest

from agent_context_clinic import (
    DEFAULT_WINDOW,
    check_transcript,
    estimate_tokens,
    load_transcript,
    render_markdown,
)


def _transcript(blobs, tokens=None):
    lines = []
    for i, (role, content) in enumerate(blobs):
        rec = {"role": role, "content": content}
        if tokens is not None:
            rec["tokens"] = tokens[i]
        lines.append(json.dumps(rec, ensure_ascii=False))
    return "\n".join(lines) + "\n"


class EstimateTest(unittest.TestCase):
    def test_zero_for_empty(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_cjk_heavier_than_ascii(self):
        cjk = estimate_tokens("中文中文中文中文")
        ascii_ = estimate_tokens("abcd efgh ijkl mnop")
        self.assertGreater(cjk, ascii_)

    def test_positive(self):
        self.assertGreater(estimate_tokens("hello world"), 0)


class LoadTest(unittest.TestCase):
    def test_load_with_explicit_tokens(self):
        path = self._write([("user", "hi"), ("assistant", "yo")], tokens=[10, 20])
        msgs = load_transcript(path)
        self.assertEqual(len(msgs), 2)
        self.assertEqual([m.tokens for m in msgs], [10, 20])

    def test_load_estimates_when_tokens_missing(self):
        path = self._write([("user", "hello there")])
        msgs = load_transcript(path)
        self.assertEqual(len(msgs), 1)
        self.assertGreater(msgs[0].tokens, 0)

    def test_skips_garbage_lines(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as fh:
            fh.write("not json\n{}\n" + _transcript([("user", "ok")]))
            path = fh.name
        try:
            msgs = load_transcript(path)
            self.assertEqual(len(msgs), 1)
        finally:
            os.unlink(path)

    def _write(self, blobs, tokens=None):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(_transcript(blobs, tokens))
            return fh.name


class CheckTest(unittest.TestCase):
    def test_green_small_session(self):
        path = self._write([("user", "hi"), ("assistant", "yo")], tokens=[100, 100])
        report = check_transcript(path, window=200_000)
        self.assertEqual(report.level, "green")
        self.assertEqual(report.total_tokens, 200)
        self.assertGreater(report.score, 80)

    def test_yellow_when_warm(self):
        path = self._write([("user", "a" * 10)], tokens=[150_000])
        report = check_transcript(path, window=200_000)
        self.assertEqual(report.level, "yellow")
        self.assertIn("getting warm", " ".join(report.warnings))

    def test_red_near_overflow(self):
        path = self._write([("user", "a" * 10)], tokens=[190_000])
        report = check_transcript(path, window=200_000)
        self.assertEqual(report.level, "red")
        self.assertTrue(report.compressible_from is not None)

    def test_overflow_detected(self):
        path = self._write([("user", "a" * 10)], tokens=[250_000])
        report = check_transcript(path, window=200_000)
        self.assertEqual(report.level, "overflow")
        self.assertEqual(report.score, 0)

    def test_compressible_range(self):
        path = self._write([("user", str(i)) for i in range(20)],
                           tokens=[50] * 20)
        report = check_transcript(path, window=200_000)
        # earliest span is ~40% of the session (lines 1..7)
        self.assertGreaterEqual(report.compressible_to, 1)
        self.assertLess(report.compressible_to, 10)

    def test_markdown_render(self):
        path = self._write([("user", "hi")], tokens=[100])
        report = check_transcript(path, window=200_000)
        md = render_markdown(report)
        self.assertIn("# Agent Context Clinic Report", md)
        self.assertIn("GREEN", md)

    def test_empty_transcript_warns(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as fh:
            fh.write("\n")
            path = fh.name
        try:
            report = check_transcript(path)
            self.assertEqual(report.messages, 0)
            self.assertTrue(any("no parseable" in w for w in report.warnings))
        finally:
            os.unlink(path)

    def _write(self, blobs, tokens=None):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(_transcript(blobs, tokens))
            return fh.name


class CliAndDemoTest(unittest.TestCase):
    def test_demo_runs(self):
        from agent_context_clinic.cli import main

        rc = main(["check", "--demo"])
        self.assertEqual(rc, 0)

    def test_cli_json_output(self):
        from agent_context_clinic.cli import main

        rc = main(["check", "--demo", "--json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()