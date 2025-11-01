// Copyright (c) 2025, MAB and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Simple", {
    onload(frm) {
        // Focus on scan field when form loads
        setTimeout(() => {
            frm.fields_dict.scan_barcode.$input.focus();
        }, 500);
    },

    scan_barcode(frm) {
        const barcode = frm.doc.scan_barcode;
        if (!barcode) return;

        // 🔹 Call custom backend method to resolve barcode → item_code
        frappe.call({
            method: "posar.api.pos_simle_api.get_item_by_barcode", // you'll create this in Python
            args: { barcode: barcode },
            callback: function (r) {
                if (!r.message) {
                    frappe.show_alert({
                        message: `❌ No item found for barcode: ${barcode}`,
                        indicator: "red"
                    });
                    frm.set_value("scan_barcode", "");
                    return;
                }

                const item_code = r.message.item_code;
                console.log("Found item:", item_code);

                // Check if item already exists in the table
                const existing_row = frm.doc.detail_table?.find(i => i.item_code === item_code);

                if (existing_row) {
                    existing_row.qty += 1;
                } else {
                    const child = frm.add_child("detail_table");
                    frappe.model.set_value(child.doctype, child.name, "item_code", item_code);
                    frappe.model.set_value(child.doctype, child.name, "qty", 1);
                }

                frm.refresh_field("detail_table");
                frm.set_value("scan_barcode", "");
            }
        });
    }
});
