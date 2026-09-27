"""Unit tests for the --read-pass backend command (device calls mocked)."""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aircard_backend


class ReadPassTests(unittest.TestCase):
    def _run(self, udid="udid", card_hash="HASH123"):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            aircard_backend.cmd_read_pass(udid, card_hash)
        return json.loads(buffer.getvalue())

    def test_rejects_hash_containing_slash(self):
        result = self._run(card_hash="../pass.json")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "invalid card hash")

    def test_returns_pass_json_content(self):
        payload = b'{"formatVersion":1,"organizationName":"Bank"}'
        with patch.object(aircard_backend, "read_file", return_value=payload) as mock_read:
            result = self._run()
        self.assertTrue(result["ok"])
        self.assertIn("organizationName", result["content"])
        self.assertEqual(
            result["path"],
            "/var/mobile/Library/Passes/Cards/HASH123.pkpass/pass.json",
        )
        _, target, leaf = mock_read.call_args.args[:3]
        self.assertEqual(target, "/var/mobile/Library/Passes/Cards/HASH123.pkpass")
        self.assertEqual(leaf, "pass.json")

    def test_reports_failure_when_read_returns_none(self):
        with patch.object(aircard_backend, "read_file", return_value=None):
            result = self._run()
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "read_failed")


if __name__ == "__main__":
    unittest.main()
