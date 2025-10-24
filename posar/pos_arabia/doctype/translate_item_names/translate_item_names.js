// Copyright (c) 2025, MAB and contributors
// For license information, please see license.txt

frappe.ui.form.on("Translate Item Names", {
	refresh(frm) {
        frm.add_custom_button(__('Translate All Items'), () => {
            frm.events.translate_all(frm);
        });
    },

    async translate_all(frm) {
        frappe.show_alert({message: __("Translating all items..."), indicator: "blue"});
        
        try {
            // Call your backend (Python) function
            await frappe.call({
                method: "posar.pos_arabia.doctype.translate_item_names.translate_item_names.translate_all_items",
                args: {},
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(__("Translation completed successfully."));
                        frm.reload_doc();
                    }
                }
            });
        } catch (err) {
            frappe.msgprint(__("Error during translation: ") + err.message);
        }
    }
});
