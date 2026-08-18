import frappe


def _normalize_barcode_variants(code):
	"""Return unique barcode variants for lookup (exact, stripped, EAN-13 padded)."""
	variants = []
	seen = set()

	def add(value):
		value = str(value or "").strip()
		if value and value not in seen:
			seen.add(value)
			variants.append(value)

	add(code)

	if code.isdigit():
		stripped = code.lstrip("0")
		add(stripped)

		if len(code) <= 13:
			add(code.zfill(13))
		if stripped:
			add(stripped.zfill(13))

	return variants


def _get_item_fields(name):
	item = frappe.db.get_value(
		"Item",
		{"name": name},
		["name", "item_code", "item_name"],
		as_dict=True,
	)
	if not item:
		return None

	return {
		"name": item.name,
		"item_code": item.item_code or item.name,
		"item_name": item.item_name,
	}


@frappe.whitelist()
def get_item_by_barcode(barcode):
	"""Return the matching Item document and item code for a scanned barcode."""
	if barcode is None:
		return None

	code = str(barcode).strip()
	if not code:
		return None

	for variant in _normalize_barcode_variants(code):
		item = frappe.db.get_value(
			"Item",
			{"item_code": variant},
			["name", "item_code", "item_name"],
			as_dict=True,
		)
		if item:
			return {
				"name": item.name,
				"item_code": item.item_code or item.name,
				"item_name": item.item_name,
			}

		item = frappe.db.get_value(
			"Item",
			{"name": variant},
			["name", "item_code", "item_name"],
			as_dict=True,
		)
		if item:
			return {
				"name": item.name,
				"item_code": item.item_code or item.name,
				"item_name": item.item_name,
			}

		item_barcode = frappe.db.get_value(
			"Item Barcode",
			{"barcode": variant},
			["parent", "barcode"],
			as_dict=True,
		)
		if item_barcode:
			item_fields = _get_item_fields(item_barcode.parent)
			if item_fields:
				return item_fields

	return None
