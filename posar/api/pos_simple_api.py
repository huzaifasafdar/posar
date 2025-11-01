
import frappe

@frappe.whitelist()
def get_item_by_barcode(barcode):
    """Return item_code by barcode, checking both Item and Item Barcode tables."""

    # 1️⃣ Try matching with Item.item_code
    item = frappe.db.get_value("Item", {"item_code": barcode}, ["name"], as_dict=True)
    if item:
        return {"item_code": item.name}

    # 2️⃣ Try matching with Item Barcode (child table)
    item_barcode = frappe.db.get_value("Item Barcode", {"barcode": barcode}, ["parent"], as_dict=True)
    if item_barcode:
        return {"item_code": item_barcode.parent}

    # Nothing found
    return None
