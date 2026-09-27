import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aircard
import aircard_backend


IPHONE_A = {"udid": "A", "product": "iPhone14,5", "name": "iPhone A", "version": "18.0"}
IPHONE_B = {"udid": "B", "product": "iPhone15,2", "name": "iPhone B", "version": "18.1"}
IPAD = {"udid": "C", "product": "iPad13,4", "name": "iPad", "version": "18.0"}


class DeviceSelectionTests(unittest.TestCase):
    def test_udid_selects_that_exact_device(self):
        with patch.object(aircard, "list_devices", return_value=[IPHONE_A, IPHONE_B, IPAD]):
            self.assertEqual(aircard.get_connected_device("B")["udid"], "B")
            self.assertEqual(aircard.get_connected_device("C")["udid"], "C")

    def test_unknown_udid_returns_none(self):
        with patch.object(aircard, "list_devices", return_value=[IPHONE_A, IPHONE_B]):
            self.assertIsNone(aircard.get_connected_device("missing"))

    def test_default_prefers_iphone_over_ipad(self):
        with patch.object(aircard, "list_devices", return_value=[IPAD, IPHONE_A]):
            self.assertEqual(aircard.get_connected_device()["udid"], "A")

    def test_entries_without_product_are_ignored(self):
        broken = {"udid": "D", "product": ""}
        with patch.object(aircard, "list_devices", return_value=[broken, IPHONE_B]):
            self.assertEqual([d["udid"] for d in aircard.list_connected_devices()], ["B"])
            self.assertEqual(aircard.get_connected_device()["udid"], "B")

    def test_no_devices_returns_none(self):
        with patch.object(aircard, "list_devices", return_value=[]):
            self.assertIsNone(aircard.get_connected_device())


class BackendDeviceListTests(unittest.TestCase):
    def test_cmd_devices_marks_each_device_connected(self):
        with patch.object(aircard_backend, "find_device_helper", return_value="/bin/true"), \
                patch.object(aircard_backend, "list_connected_devices",
                             return_value=[dict(IPHONE_A), dict(IPAD)]):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                aircard_backend.cmd_devices()
        payload = json.loads(buffer.getvalue())
        self.assertEqual([d["udid"] for d in payload], ["A", "C"])
        self.assertTrue(all(d["connected"] for d in payload))


if __name__ == "__main__":
    unittest.main()
