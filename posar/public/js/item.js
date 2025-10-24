frappe.ui.form.on('Item', {
    item_code: async function(frm) {
        console.log("Item code changed:", frm.doc.item_code);
        if (frm.doc.item_code) {
            frappe.call({
                method: 'posar.api.translate.translate_to_arabic',
                args: { text: frm.doc.item_code },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('item_name_ar', r.message);
                    }
                }
            });
        }
    },

    final_price: function(frm) {
        discount_perc = frm.doc.discount_percentage || 15

        if (frm.doc.final_price ) {
            let discount_factor = 1 - (frm.doc.discount_percentage / 100);
            if (discount_factor > 0) {
                const calculated_price = (frm.doc.final_price / discount_factor).toFixed(2);
                frm.set_value('standard_rate', calculated_price);
                frappe.show_alert({ message: __("Base price calculated: ") + calculated_price, indicator: "green" });
            }
        }
    }
});