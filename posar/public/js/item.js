frappe.ui.form.on('Item', {
    before_save: function(frm) {
        const barcodePattern = /^[0-9]+$/; // Example pattern for barcode

        if (frm.doc.item_code && barcodePattern.test(frm.doc.item_code)) {

            // Check if barcodes field exists and create it if not
            if (!frm.doc.barcodes) {
                frm.add_child('barcodes', {
                    barcode: frm.doc.item_code
                });
            } else {
                // Check if item_code is not already in barcodes
                let exists = frm.doc.barcodes.some(b => b.barcode === frm.doc.item_code);
                if (!exists) {
                    frm.add_child('barcodes', {
                        barcode: frm.doc.item_code
                    });
                }
            }
            frm.doc.barcode = frm.doc.item_code;
        }
    },
    item_name: async function(frm) {
        console.log("Item name changed:", frm.doc.item_name);
        if (frm.doc.item_name) {
            frappe.call({
                method: 'posar.api.translate.translate_to_arabic',
                args: { text: frm.doc.item_name },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('custom_item_name_arabic', r.message);
                    }
                }
            });
        }
    },
    // custom_valuation_rate_with_vat: async function(frm) {
    //     await calculate_rate_without_vat(frm, "custom_valuation_rate_with_vat", "valuation_rate");
    // },
    // custom_selling_rate_with_vat: async function(frm) {
    //     await calculate_rate_without_vat(frm, "custom_selling_rate_with_vat", "standard_rate");
    // },
    item_code: function(frm) {
        const barcodePattern = /^[0-9]+$/; // Example pattern for barcode
        if (barcodePattern.test(frm.doc.item_code)) {
            console.log("Item code is a barcode.");
        } else {
            console.log("Item code is a name.");
        }
    }
});
async function calculate_rate_without_vat(frm, source_field, target_field) {
    let vat_rate = 0;

    if (frm.doc.taxes) {
        const tax = frm.doc.taxes.find(t => t.tax_type && t.tax_rate);
        vat_rate = tax ? tax.tax_rate : 15;
    } else {
        vat_rate = 15; // default fallback
    }

    const value_with_vat = frm.doc[source_field];
    if (!value_with_vat) return;

    const base_rate = value_with_vat / (1 + vat_rate / 100);
    frm.set_value(target_field, base_rate.toFixed(2));

    frappe.show_alert({
        message: `${__(target_field.replace("_", " "))} (excl. VAT): ${base_rate.toFixed(2)}`,
        indicator: "green"
    });
}