frappe.ui.form.on("Item Code Fixer", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Run Update"), function () {
				frappe.prompt(
					[
						{
							label: "Test Run Only (Dry Run)",
							fieldname: "dry_run",
							fieldtype: "Check",
							default: 1,
						},
						{
							label: "Batch Size",
							fieldname: "batch_size",
							fieldtype: "Int",
							default: 500,
						},
					],
					function (values) {
						frappe.call({
							method: "posar.pos_arabia.doctype.item_code_fixer.item_code_fixer.run_update",
							freeze: true,
							freeze_message: __("Processing... Please wait"),
							args: {
								batch_size: values.batch_size,
								dry_run: values.dry_run,
							},
							callback: function (r) {
								if (r.message) {
									frm.set_value("last_run_log", r.message);
									frm.save();
									frappe.show_alert({
										message: __("✅ Task completed"),
										indicator: "green",
									});
								}
							},
						});
					},
					__("Confirm Run"),
					__("Start")
				);
			});
		}
	},
});
