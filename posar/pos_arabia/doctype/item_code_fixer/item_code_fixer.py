import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

class ItemCodeFixer(Document):
	pass

@frappe.whitelist()
def run_update(batch_size=500, dry_run=True):
	currentchange = 0

	rows = frappe.db.sql("""
		SELECT ib.parent AS item_name, ib.barcode, ib.idx
		FROM `tabItem Barcode` ib
		JOIN (
			SELECT parent, MIN(idx) AS min_idx
			FROM `tabItem Barcode`
			GROUP BY parent
		) x ON x.parent = ib.parent AND x.min_idx = ib.idx
	""", as_dict=True)

	total = len(rows)
	changed, skipped, conflict = [], [], []

	for r in rows:
		item_name = r["item_name"]
		barcode = (r["barcode"] or "").strip()

		if not item_name or not barcode:
			skipped.append((item_name or "?", barcode, "Missing barcode"))
			continue

		item = frappe.get_value("Item", item_name, ["item_code"], as_dict=True)
		if not item:
			skipped.append((item_name, barcode, "Item not found"))
			continue

		current_code = (item["item_code"] or "").strip()
		if current_code == barcode:
			skipped.append((item_name, barcode, "Already same"))
			continue

		existing = frappe.db.get_value("Item", {"item_code": barcode})
		if existing and existing != item_name:
			conflict.append((item_name, barcode, f"Conflict with {existing}"))
			continue

		if not dry_run:
			try:
				frappe.db.set_value("Item", item_name, "item_code", barcode, update_modified=False)
				changed.append((item_name, barcode, "Updated"))
			except Exception as e:
				skipped.append((item_name, barcode, f"Error: {e}"))
		else:
			currentchange += 1
			changed.append((item_name, barcode, "Would be updated (Dry Run)"))

		if currentchange % batch_size == 0 and not dry_run:
			frappe.db.commit()

	if not dry_run:
		frappe.db.commit()

	# Prepare detailed log
	log_lines = [
		f"--- ITEM CODE FIX REPORT ({now_datetime()}) ---",
		f"Mode: {'DRY RUN' if dry_run else 'LIVE RUN'}",
		f"Total Items: {total}",
		f"Changed: {len(changed)} | Skipped: {len(skipped)} | Conflicts: {len(conflict)}",
		"",
		"--- Changed Items ---"
	]
	for c in changed:
		log_lines.append(f"Item: {c[0]} | Barcode: {c[1]} | Status: {c[2]}")

	log_lines.append("\n--- Skipped Items ---")
	for s in skipped:
		log_lines.append(f"Item: {s[0]} | Barcode: {s[1]} | Reason: {s[2]}")

	log_lines.append("\n--- Conflicts ---")
	for c in conflict:
		log_lines.append(f"Item: {c[0]} | Barcode: {c[1]} | Reason: {c[2]}")

	log_text = "\n".join(log_lines)

	# Store log in Error Log (so you can open from UI → Error Log list)
	frappe.log_error(log_text, "Item Code Fixer Log")

	return log_text
