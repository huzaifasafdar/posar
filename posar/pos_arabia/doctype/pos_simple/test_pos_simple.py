# Copyright (c) 2025, MAB and Contributors
# See license.txt

from pathlib import Path

from frappe.tests.utils import FrappeTestCase


class TestPOSSimple(FrappeTestCase):
	def test_pos_barcode_lookup_uses_correct_backend_method(self):
		js_file = Path(__file__).resolve().parent / "pos_simple.js"
		self.assertTrue(js_file.exists(), "POS Simple JS file not found")
		content = js_file.read_text(encoding="utf-8")
		self.assertIn('method: "posar.api.pos_simple_api.get_item_by_barcode"', content)
		self.assertNotIn("pos_simle_api", content)
