// Edit a submitted document in place (Purchase Invoice, Purchase Order, Journal Entry,
// Payment Entry). Server side: posar/edit_after_submit.py
//
// Users with the "Submitted Document Editor" role get an "Edit" button on submitted
// documents. Clicking it makes the form editable; the normal "Update" button then saves
// the changes and the server re-posts the ledgers on the same document.

(() => {
	const ROLE = "Submitted Document Editor";
	const FLAG = "__edit_after_submit";

	// Fields that must not change after submit (the server refuses them as well).
	const LOCKED_FIELDS = {
		"Purchase Invoice": ["company", "is_return", "return_against", "update_stock", "is_paid", "is_opening"],
		"Purchase Order": ["company", "is_subcontracted"],
		"Journal Entry": ["company", "voucher_type", "is_opening"],
		"Payment Entry": ["company", "payment_type"],
	};

	const is_editing = (frm) => frm.__edit_after_submit === frm.doc.name;

	const can_edit = (frm) =>
		frm.doc.docstatus === 1 &&
		!frm.is_new() &&
		frappe.user.has_role(ROLE) &&
		frm.perm[0] &&
		frm.perm[0].write &&
		frm.perm[0].submit;

	// Every docfield object the form consults for this doctype and its child tables:
	// the shared meta plus the per-document copies the form and grids render from.
	function each_docfield(frm, callback) {
		const doctypes = [frm.doctype];
		frappe.get_meta(frm.doctype).fields.forEach((df) => {
			if (frappe.model.table_fields.includes(df.fieldtype) && df.options) {
				doctypes.push(df.options);
			}
		});

		doctypes.forEach((dt) => {
			const seen = new Set();
			const visit = (df) => {
				if (df && !seen.has(df)) {
					seen.add(df);
					callback(df, dt);
				}
			};
			(frappe.get_meta(dt)?.fields || []).forEach(visit);
			(frappe.meta.docfield_list[dt] || []).forEach(visit);
			Object.values(frappe.meta.docfield_copy[dt] || {}).forEach((copy) =>
				Object.values(copy).forEach(visit)
			);
		});
	}

	function enter_edit_mode(frm) {
		const locked = LOCKED_FIELDS[frm.doctype] || [];
		const original = {};

		each_docfield(frm, (df, dt) => {
			const key = `${dt}::${df.fieldname}`;
			if (!(key in original)) original[key] = df.allow_on_submit || 0;
			if (!(dt === frm.doctype && locked.includes(df.fieldname))) {
				df.allow_on_submit = 1;
			}
		});

		frm.__edit_after_submit = frm.doc.name;
		frm.__edit_after_submit_original = original;
		frm.doc[FLAG] = 1;
		frm.refresh();
	}

	function exit_edit_mode(frm) {
		const original = frm.__edit_after_submit_original;
		if (original) {
			each_docfield(frm, (df, dt) => {
				const key = `${dt}::${df.fieldname}`;
				df.allow_on_submit = key in original ? original[key] : 0;
			});
		}
		frm.__edit_after_submit = null;
		frm.__edit_after_submit_original = null;
		if (frm.doc) delete frm.doc[FLAG];
	}

	function show_edit_controls(frm) {
		if (is_editing(frm)) {
			frm.set_intro(
				__(
					"You are editing a submitted document. Make your changes and click Update. Ledger entries and linked documents will be re-posted."
				),
				"orange"
			);
			frm.add_custom_button(__("Discard Edit"), () => {
				exit_edit_mode(frm);
				frm.reload_doc();
			});
			return;
		}

		if (!can_edit(frm)) return;

		frm.add_custom_button(__("Edit"), () => {
			frappe.confirm(
				__(
					"Edit this submitted {0}? When you click Update, its ledger entries will be reversed and posted again with the new values.",
					[__(frm.doctype)]
				),
				() => enter_edit_mode(frm)
			);
		}).addClass("btn-primary");
	}

	const handlers = {
		refresh(frm) {
			// the form object is reused when opening another document: leave edit mode
			if (frm.__edit_after_submit && !is_editing(frm)) {
				exit_edit_mode(frm);
				frm.refresh();
				return;
			}
			// the doc was reloaded (e.g. someone else saved it) and lost the flag
			if (is_editing(frm) && !frm.doc[FLAG]) {
				frm.doc[FLAG] = 1;
			}
			show_edit_controls(frm);
		},

		after_save(frm) {
			if (frm.__edit_after_submit) {
				exit_edit_mode(frm);
				frm.refresh();
			}
		},

		before_cancel(frm) {
			if (frm.__edit_after_submit) {
				exit_edit_mode(frm);
			}
		},
	};

	// This file is the form script of all four doctypes, so it runs once per doctype
	// opened; register the handlers only once each.
	window.__posar_edit_after_submit = window.__posar_edit_after_submit || {};
	Object.keys(LOCKED_FIELDS).forEach((doctype) => {
		if (!window.__posar_edit_after_submit[doctype]) {
			window.__posar_edit_after_submit[doctype] = true;
			frappe.ui.form.on(doctype, handlers);
		}
	});
})();
