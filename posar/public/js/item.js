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
    custom_valuation_rate_with_vat: async function(frm) {
        await calculate_rate_without_vat(frm, "custom_valuation_rate_with_vat", "valuation_rate");
    },
    custom_selling_rate_with_vat: async function(frm) {
        await calculate_rate_without_vat(frm, "custom_selling_rate_with_vat", "standard_rate");
    }
    // // standard_rate: function(frm) {
    // //     discount_perc = frm.doc.discount_percentage || 15
    // //     with_vat_price = frm.doc.standard_rate;

    // //     if (with_vat_price && discount_perc) {
    // //         let discount_factor = with_vat_price * discount_perc / 100;
    // //         if (discount_factor > 0) {
    // //             const calculated_price = with_vat_price - discount_factor;
    // //             frm.set_value('custom_selling_rate_without_vat', calculated_price);
    // //             frappe.show_alert({ message: __("Base price calculated: ") + calculated_price, indicator: "green" });
    // //         }
    // //     }
    // // },
    // // valuation_rate: function(frm) {
    // //     discount_perc = frm.doc.discount_percentage || 15
    // //     with_vat_price = frm.doc.valuation_rate;

    // //     if (with_vat_price && discount_perc) {
    // //         let discount_factor = with_vat_price * discount_perc / 100;
    // //         if (discount_factor > 0) {
    // //             const calculated_price = with_vat_price - discount_factor;
    // //             frm.set_value('custom_valuation_rate_without_vat', calculated_price);
    // //             frappe.show_alert({ message: __("Base price calculated: ") + calculated_price, indicator: "green" });
    // //         }
    // //     }
    // // },
    // selling_rate_with_vat(frm) {
    //     // Get entered VAT-inclusive value
    //     const with_vat = frm.doc.selling_rate_with_vat;

    //     // Get VAT percentage (you can replace with frm.doc.vat_rate if using that)
    //     const vat_percent = frm.doc.discount_percentage || 15;

    //     if (with_vat && vat_percent) {
    //         // Calculate base price (without VAT)
    //         const base_price = with_vat / (1 + vat_percent / 100);

    //         // Update standard_rate field
    //         frm.set_value('standard_rate', base_price.toFixed(6));

    //         // Optional alert for feedback
    //         frappe.show_alert({
    //             message: __("Calculated Base Price (Excl. VAT): ") + base_price.toFixed(6),
    //             indicator: "green"
    //         });
    //     }
    // }  ,
    // valuation_rate_with_vat(frm) {
    //     // Get entered VAT-inclusive value
    //     const with_vat = frm.doc.valuation_rate_with_vat;

    //     // Get VAT percentage (you can replace with frm.doc.vat_rate if using that)
    //     const vat_percent = frm.doc.discount_percentage || 15;

    //     if (with_vat && vat_percent) {
    //         // Calculate base price (without VAT)
    //         const base_price = with_vat / (1 + vat_percent / 100);

    //         // Update standard_rate field
    //         frm.set_value('valuation_rate', base_price.toFixed(6));

    //         // Optional alert for feedback
    //         frappe.show_alert({
    //             message: __("Calculated Base Price (Excl. VAT): ") + base_price.toFixed(6),
    //             indicator: "green"
    //         });
    //     }
    // }      
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