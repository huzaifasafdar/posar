"""Edit submitted documents in place, without Cancel + Amend.

A user with the ``Submitted Document Editor`` role clicks **Edit** on a submitted
Purchase Invoice, Purchase Order, Journal Entry or Payment Entry. The form becomes
editable (see ``public/js/edit_after_submit.js``), and the edited document comes back
here through Frappe's normal "Update after Submit" save, marked with ``EDIT_FLAG``.

For each save the document keeps its name and stays submitted, and:

1. ``before_update_after_submit``: the effects of the *old* version are reversed
   (GL / payment ledger, stock ledger, payment schedule, ...) and the *new* version is
   validated with the doctype's normal ``validate``, exactly as on a fresh save.
2. ``on_update_after_submit``: the effects of the *new* version are posted again and
   every linked document (PO billed/received %, invoice outstanding, bins, ...) is
   recalculated.

Everything runs in the request's single database transaction, so any error rolls the
whole edit back. Frappe's Version log (track_changes) records the before/after values,
and a timeline comment marks the document as edited after submit.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

EDITOR_ROLE = "Submitted Document Editor"
EDIT_FLAG = "__edit_after_submit"

# Fields that must never change on a submitted document, whatever the role.
LOCKED_FIELDS = {
	"Purchase Invoice": ("company", "is_return", "return_against", "update_stock", "is_paid", "is_opening"),
	"Purchase Order": ("company", "is_subcontracted"),
	"Journal Entry": ("company", "voucher_type", "is_opening"),
	"Payment Entry": ("company", "payment_type"),
}


# ---------------------------------------------------------------------------
# doc_events entry points
# ---------------------------------------------------------------------------


def before_update_after_submit(doc, method=None):
	if not is_edit_request(doc):
		return

	if EDITOR_ROLE not in frappe.get_roles():
		frappe.throw(
			_("Only users with the {0} role can edit a submitted {1}.").format(
				frappe.bold(EDITOR_ROLE), _(doc.doctype)
			),
			frappe.PermissionError,
		)

	old = frappe.get_doc(doc.doctype, doc.name)  # the version still in the database
	doc.flags.edit_after_submit = True
	doc.flags.doc_before_edit = old
	doc.flags.ignore_validate_update_after_submit = True

	# ERPNext's own on_update_after_submit (PI / JE / PE) creates a "Repost Accounting
	# Ledger" when account fields change. We re-post the ledgers ourselves, so switch
	# that check off for this one save only.
	doc.check_if_fields_updated = lambda *args, **kwargs: False

	validate_locked_fields(doc, old)
	HANDLERS[doc.doctype].reverse_old(doc, old)
	run_validations(doc)
	HANDLERS[doc.doctype].validate_new(doc, old)


def on_update_after_submit(doc, method=None):
	if not doc.flags.get("edit_after_submit"):
		return

	old = doc.flags.doc_before_edit
	HANDLERS[doc.doctype].post_new(doc, old)
	add_timeline_comment(doc)

	# Values such as outstanding_amount, status, per_billed were written straight to
	# the database by the steps above; reload so the form shows them.
	doc.reload()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def is_edit_request(doc):
	return bool(cint(doc.get(EDIT_FLAG))) and doc.doctype in HANDLERS and doc.docstatus == 1


def validate_locked_fields(doc, old):
	for fieldname in LOCKED_FIELDS.get(doc.doctype, ()):
		if doc.meta.has_field(fieldname) and cstr_value(doc.get(fieldname)) != cstr_value(old.get(fieldname)):
			frappe.throw(
				_("{0} cannot be changed on a submitted {1}. Cancel and amend the document instead.").format(
					frappe.bold(_(doc.meta.get_label(fieldname))), _(doc.doctype)
				)
			)


def cstr_value(value):
	return "" if value is None else str(value)


def run_validations(doc):
	"""Run the same controller validation a normal save runs (including other apps' hooks)."""
	doc.run_method("before_validate")
	doc.run_method("validate")


def as_cancelled(old):
	"""Treat the old version as cancelled, as ERPNext's own on_cancel would see it."""
	old.docstatus = 2
	return old


def reconciled_by_other_vouchers(doc):
	"""Vouchers (other than this one) whose payment ledger is allocated against this one."""
	ple = frappe.qb.DocType("Payment Ledger Entry")
	rows = (
		frappe.qb.from_(ple)
		.select(ple.voucher_type, ple.voucher_no)
		.distinct()
		.where(
			(ple.against_voucher_type == doc.doctype)
			& (ple.against_voucher_no == doc.name)
			& (ple.voucher_no != doc.name)
			& (ple.delinked == 0)
		)
	).run(as_dict=True)
	return rows


def throw_if_reconciled_by_others(doc):
	rows = reconciled_by_other_vouchers(doc)
	if rows:
		links = ", ".join(frappe.utils.get_link_to_form(r.voucher_type, r.voucher_no) for r in rows[:5])
		frappe.throw(
			_(
				"{0} {1} is already allocated against {2}. Unreconcile it first, then edit."
			).format(_(doc.doctype), doc.name, links)
		)


def throw_if_bank_reconciled(doc):
	if doc.get("clearance_date") or frappe.db.exists(
		"Bank Transaction Payments", {"payment_document": doc.doctype, "payment_entry": doc.name}
	):
		frappe.throw(
			_("{0} {1} is reconciled with a bank transaction. Unreconcile it first, then edit.").format(
				_(doc.doctype), doc.name
			)
		)


def throw_if_serial_or_batch(doc):
	for row in doc.get("items"):
		if row.get("serial_and_batch_bundle") or row.get("serial_no") or row.get("batch_no"):
			frappe.throw(
				_(
					"Row #{0}: items with serial or batch numbers cannot be edited after submit. Cancel and amend the document instead."
				).format(row.idx)
			)


def add_timeline_comment(doc):
	doc.add_comment(
		"Edit",
		_("edited this submitted document; ledger entries were re-posted."),
	)


# ---------------------------------------------------------------------------
# Purchase Invoice
# ---------------------------------------------------------------------------


class PurchaseInvoiceHandler:
	@staticmethod
	def reverse_old(doc, old):
		if cint(old.update_stock):
			throw_if_serial_or_batch(old)
			throw_if_serial_or_batch(doc)

		if any(cint(row.get("is_fixed_asset")) for row in (old.items + doc.items)):
			frappe.throw(_("Invoices with fixed asset items cannot be edited after submit."))

		if advances_changed(doc, old):
			frappe.throw(
				_("Advance allocations cannot be changed on a submitted invoice. Use Payment Reconciliation instead.")
			)

		as_cancelled(old)
		if cint(old.update_stock):
			old.update_stock_ledger()
		# reverse GL + payment ledger, without cancelling exchange gain/loss journals
		old.make_gl_entries_on_cancel(from_repost=True)

	@staticmethod
	def validate_new(doc, old):
		frappe.get_doc("Authorization Control").validate_approving_authority(
			doc.doctype, doc.company, doc.base_grand_total
		)

	@staticmethod
	def post_new(doc, old):
		# billed amounts in Purchase Orders / Purchase Receipts (recomputed from the database)
		for d in (old, doc):
			if d.is_return and not d.update_billed_amount_in_purchase_order:
				d.status_updater = []
			else:
				d.update_status_updater_args()
			d.update_prevdoc_status()
			if not d.is_return:
				d.update_billing_status_for_zero_amount_refdoc("Purchase Receipt")
				d.update_billing_status_for_zero_amount_refdoc("Purchase Order")
			d.update_billing_status_in_pr()

		if cint(doc.update_stock):
			doc.update_stock_ledger()

		doc.make_gl_entries()

		if cint(doc.update_stock):
			# re-value later stock transactions from the earlier of the two posting dates
			earliest = old if (str(old.posting_date), str(old.posting_time)) < (
				str(doc.posting_date),
				str(doc.posting_time),
			) else doc
			earliest.repost_future_sle_and_gle(force=True)

		update_last_purchase_rate_if_enabled(doc)

		if frappe.db.get_single_value("Buying Settings", "project_update_frequency") == "Each Transaction":
			old.update_project()
			doc.update_project()

		outstanding = flt(frappe.db.get_value(doc.doctype, doc.name, "outstanding_amount"))
		if not doc.is_return and outstanding < 0:
			frappe.throw(
				_(
					"The new total of {0} is less than the amount already paid against it. Reduce or unreconcile the payment first."
				).format(doc.name)
			)

		doc.reload()
		doc.set_status(update=True)


def advances_changed(doc, old):
	def key(d):
		return sorted(
			(r.reference_type, r.reference_name, r.reference_row, flt(r.allocated_amount))
			for r in d.get("advances") or []
			if flt(r.allocated_amount)
		)

	return key(doc) != key(old)


# ---------------------------------------------------------------------------
# Purchase Order
# ---------------------------------------------------------------------------


class PurchaseOrderHandler:
	@staticmethod
	def reverse_old(doc, old):
		# A Purchase Order has no ledger entries; its effects on bins, Material Requests,
		# Sales Orders and Blanket Orders are recomputed from the database in post_new.
		if cint(old.is_subcontracted):
			frappe.throw(_("Subcontracted Purchase Orders cannot be edited after submit."))

	@staticmethod
	def validate_new(doc, old):
		from erpnext.controllers.accounts_controller import validate_child_on_delete

		old_rows = {row.name: row for row in old.items}
		new_names = {row.name for row in doc.items}
		for row in old.items:
			if row.name not in new_names:
				validate_child_on_delete(row, old)

		for row in doc.items:
			old_row = old_rows.get(row.name)
			if not old_row:
				continue
			received, billed = flt(old_row.received_qty), flt(old_row.billed_amt)
			if received and flt(row.qty) < received:
				frappe.throw(
					_("Row #{0}: Quantity for {1} cannot be less than the received quantity {2}.").format(
						row.idx, row.item_code, received
					)
				)
			if billed and flt(row.rate) > 0 and flt(row.amount) < billed:
				frappe.throw(
					_("Row #{0}: Amount for {1} cannot be less than the billed amount {2}.").format(
						row.idx, row.item_code, billed
					)
				)
			if (received or billed) and row.item_code != old_row.item_code:
				frappe.throw(
					_("Row #{0}: Item cannot be changed because it has already been received or billed.").format(
						row.idx
					)
				)

		if doc.supplier != old.supplier and (flt(old.per_received) or flt(old.per_billed)):
			frappe.throw(_("Supplier cannot be changed after items have been received or billed."))

		frappe.get_doc("Authorization Control").validate_approving_authority(
			doc.doctype, doc.company, doc.base_grand_total
		)
		doc.validate_budget()

	@staticmethod
	def post_new(doc, old):
		# The old version is treated as cancelled first, so rows that were removed or moved
		# to another warehouse / Material Request are recalculated too; then the new version.
		as_cancelled(old)
		for d in (old, doc):
			if d.is_against_so():
				d.update_status_updater()
			d.update_prevdoc_status()
			d.update_requested_qty()
			d.update_ordered_qty()
			d.update_blanket_order()

		update_last_purchase_rate_if_enabled(doc)
		doc.update_receiving_percentage()
		doc.update_billing_percentage()
		doc.reload()
		doc.set_status(update=True)


def update_last_purchase_rate_if_enabled(doc):
	from erpnext.buying.utils import update_last_purchase_rate

	if not doc.get("is_return") and not frappe.db.get_single_value(
		"Buying Settings", "disable_last_purchase_rate"
	):
		update_last_purchase_rate(doc, is_submit=1)


# ---------------------------------------------------------------------------
# Journal Entry
# ---------------------------------------------------------------------------

BLOCKED_JE_TYPES = (
	"Depreciation Entry",
	"Exchange Gain Or Loss",
	"Exchange Rate Revaluation",
	"Deferred Revenue",
	"Deferred Expense",
	"Inter Company Journal Entry",
	"Asset Disposal",
)


class JournalEntryHandler:
	@staticmethod
	def reverse_old(doc, old):
		from erpnext.accounts.general_ledger import make_reverse_gl_entries

		if old.voucher_type in BLOCKED_JE_TYPES or cint(old.get("is_system_generated")):
			frappe.throw(_("{0} journal entries cannot be edited after submit.").format(_(old.voucher_type)))
		if any(
			row.get("reference_type") in ("Asset", "Invoice Discounting") for row in (old.accounts + doc.accounts)
		):
			frappe.throw(_("Journal entries linked to an Asset or Invoice Discounting cannot be edited after submit."))

		throw_if_reconciled_by_others(old)
		throw_if_bank_reconciled(old)

		# reverses GL + payment ledger and restores the outstanding of referenced invoices
		make_reverse_gl_entries(voucher_type=old.doctype, voucher_no=old.name)

	@staticmethod
	def validate_new(doc, old):
		doc.validate_cheque_info()
		doc.check_credit_limit()

	@staticmethod
	def post_new(doc, old):
		doc.make_gl_entries()


# ---------------------------------------------------------------------------
# Payment Entry
# ---------------------------------------------------------------------------


class PaymentEntryHandler:
	@staticmethod
	def reverse_old(doc, old):
		throw_if_reconciled_by_others(old)
		throw_if_bank_reconciled(old)

		as_cancelled(old)
		old.update_payment_requests(cancel=True)
		old.update_payment_schedule(cancel=1)
		# reverses GL, payment ledger, advance ledger and the exchange gain/loss journal;
		# invoice outstanding is restored before the new version is validated against it
		old.make_gl_entries(cancel=1)

	@staticmethod
	def validate_new(doc, old):
		if flt(doc.difference_amount):
			frappe.throw(_("Difference Amount must be zero"))

	@staticmethod
	def post_new(doc, old):
		doc.update_payment_requests()
		doc.update_payment_schedule()
		doc.make_gl_entries()
		doc.update_outstanding_amounts()
		doc.set_status()


HANDLERS = {
	"Purchase Invoice": PurchaseInvoiceHandler,
	"Purchase Order": PurchaseOrderHandler,
	"Journal Entry": JournalEntryHandler,
	"Payment Entry": PaymentEntryHandler,
}
