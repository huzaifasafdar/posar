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
                        frm.set_value('item_name', frm.doc.item_code);
                    }
                }
            });
        }
    },

    standard_rate: function(frm) {
        discount_perc = frm.doc.discount_percentage || 15
        with_vat_price = frm.doc.standard_rate;

        if (with_vat_price && discount_perc) {
            let discount_factor = with_vat_price * discount_perc / 100;
            if (discount_factor > 0) {
                const calculated_price = with_vat_price - discount_factor;
                frm.set_value('custom_selling_rate_without_vat', calculated_price);
                frappe.show_alert({ message: __("Base price calculated: ") + calculated_price, indicator: "green" });
            }
        }
    },
    valuation_rate: function(frm) {
        discount_perc = frm.doc.discount_percentage || 15
        with_vat_price = frm.doc.valuation_rate;

        if (with_vat_price && discount_perc) {
            let discount_factor = with_vat_price * discount_perc / 100;
            if (discount_factor > 0) {
                const calculated_price = with_vat_price - discount_factor;
                frm.set_value('custom_valuation_rate_without_vat', calculated_price);
                frappe.show_alert({ message: __("Base price calculated: ") + calculated_price, indicator: "green" });
            }
        }
    }
});