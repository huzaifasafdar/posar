# Copyright (c) 2025, MAB and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from googletrans import Translator
import time
import re

BATCH_SIZE = 100      # commit every 100 items
SLEEP_TIME = 0.3      # 300ms delay between API calls

@frappe.whitelist()
def translate_all_items():
    """Enqueue background translation process."""
    frappe.enqueue(
        "posar.pos_arabia.doctype.translate_item_names.translate_item_names._translate_all_items",
        queue='long',
        timeout=3600 * 6,  # 6 hours
    )

def _translate_all_items():
    translator = Translator()

    # Fetch only items that have NO Arabic name yet
    filters = [["item_name_ar", "in", ["", None]]]


    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=["name", "item_name_ar"],
        order_by="name asc",
        limit_page_length=5000  # adjust if needed
    )

    if not items:
        frappe.logger().info("✅ No untranslated items found.")
        return

    counter = 0
    success = 0
    failed = 0

    frappe.logger().info(f"Starting translation of {len(items)} untranslated items...")

    for item in items:
        try:
            
            english_name = re.sub(r'\s+', ' ', item.name or '').strip()
            
            if not english_name:
                continue

            # Translate and combine
            translated = translator.translate(english_name, src="en", dest="ar").text
            mixed_name = f"{english_name} {translated}"
            if len(mixed_name) > 140:
                mixed_name = mixed_name[:137] + "..."
                
            frappe.db.set_value("Item", item.name, {
                "item_name_ar": translated,
                "item_name": mixed_name
            })

            success += 1
            counter += 1

            # Save progress
            frappe.db.set_single_value("Translation Settings", "last_item_translated", item.name)

            # Periodic commit
            if counter % BATCH_SIZE == 0:
                frappe.db.commit()
                frappe.logger().info(f"✅ Committed {counter} items so far (Last: {item.name})")

            time.sleep(SLEEP_TIME)

        except Exception as e:
            failed += 1
            frappe.log_error(str(e), f"Item Translation Failed: {item.name}")

    frappe.db.commit()
    frappe.logger().info(f"🎯 Finished translating items. Success: {success}, Failed: {failed}")

class TranslateItemNames(Document):
    pass
