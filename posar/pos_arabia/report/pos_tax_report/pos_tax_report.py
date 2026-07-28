import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	columns = get_columns()
	data = get_data(filters)
	summary = get_report_summary(data)

	return columns, data, None, None, summary


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Company is mandatory"))

	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("{0} and {1} are mandatory").format(_("From Date"), _("To Date")))

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))


def get_data(filters):
	data = []

	sales_data = get_sales_tax_data(filters)
	purchase_data = get_purchase_tax_data(filters, is_expense=False)
	expense_data = get_purchase_tax_data(filters, is_expense=True)
	summary_data = get_summary_rows(sales_data, purchase_data, expense_data)

	data.extend(get_section_rows("SALES", sales_data, get_section_totals(sales_data)))
	data.extend(get_section_rows("PURCHASES", purchase_data, get_section_totals(purchase_data)))
	data.extend(get_section_rows("EXPENSES", expense_data, get_section_totals(expense_data)))
	data.extend(
		get_section_rows(
			"SUMMARY",
			summary_data,
			{
				"tax_amount": sum(
					flt(row.get("tax_amount"))
					for row in summary_data
					if row.get("customer_or_supplier") == _("Net Tax")
				)
			},
		)
	)

	return data


def get_section_rows(section, rows, totals=None):
	totals = totals or {}

	return [
		{
			"section": section,
			"taxable_amount": totals.get("taxable_amount"),
			"tax_amount": totals.get("tax_amount"),
			"total_amount": totals.get("total_amount"),
			"is_section": 1,
		},
		*rows,
		{},
	]


def get_section_totals(rows):
	return {
		"taxable_amount": sum(flt(row.taxable_amount) for row in rows),
		"tax_amount": sum(flt(row.tax_amount) for row in rows),
		"total_amount": sum(flt(row.total_amount) for row in rows),
	}


def get_sales_tax_data(filters):
	conditions = get_sales_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			'Sales Invoice' AS document_type,
			si.name AS invoice,
			si.customer_name AS customer_or_supplier,
			NULL AS expense_account,
			stc.account_head AS tax_account,
			stc.rate AS tax_rate,
			si.base_net_total AS taxable_amount,
			stc.base_tax_amount AS tax_amount,
			si.base_grand_total AS total_amount
		FROM
			`tabSales Invoice` si
		INNER JOIN
			`tabSales Taxes and Charges` stc
				ON stc.parent = si.name
				AND stc.parenttype = 'Sales Invoice'
				AND stc.parentfield = 'taxes'
		WHERE
			si.docstatus = 1
			AND si.company = %(company)s
			AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
			{conditions}
		ORDER BY
			si.posting_date, si.name, stc.idx
		""",
		filters,
		as_dict=True,
	)


def get_purchase_tax_data(filters, is_expense=False):
	conditions = get_purchase_conditions(filters)
	item_condition = "pii.item_code IS NULL OR pii.item_code = ''" if is_expense else "ifnull(pii.item_code, '') != ''"

	return frappe.db.sql(
		f"""
		SELECT
			'Purchase Invoice' AS document_type,
			pi.name AS invoice,
			pi.supplier_name AS customer_or_supplier,
			GROUP_CONCAT(DISTINCT pii.expense_account ORDER BY pii.expense_account SEPARATOR ', ') AS expense_account,
			ptc.account_head AS tax_account,
			ptc.rate AS tax_rate,
			pi.base_net_total AS taxable_amount,
			ptc.base_tax_amount AS tax_amount,
			pi.base_grand_total AS total_amount
		FROM
			`tabPurchase Invoice` pi
		INNER JOIN
			`tabPurchase Taxes and Charges` ptc
				ON ptc.parent = pi.name
				AND ptc.parenttype = 'Purchase Invoice'
				AND ptc.parentfield = 'taxes'
		INNER JOIN
			`tabPurchase Invoice Item` pii
				ON pii.parent = pi.name
				AND pii.parenttype = 'Purchase Invoice'
				AND pii.parentfield = 'items'
		WHERE
			pi.docstatus = 1
			AND pi.company = %(company)s
			AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND ({item_condition})
			{conditions}
		GROUP BY
			pi.name, ptc.name
		ORDER BY
			pi.posting_date, pi.name, ptc.idx
		""",
		filters,
		as_dict=True,
	)


def get_sales_conditions(filters):
	conditions = []

	if filters.get("only_pos"):
		conditions.append("si.is_pos = 1")

	if filters.get("pos_profile"):
		conditions.append("si.pos_profile = %(pos_profile)s")

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")

	if filters.get("tax_account"):
		conditions.append("stc.account_head = %(tax_account)s")

	if filters.get("cashier"):
		conditions.append("si.owner = %(cashier)s")

	return " AND " + " AND ".join(conditions) if conditions else ""


def get_purchase_conditions(filters):
	conditions = []

	if filters.get("supplier"):
		conditions.append("pi.supplier = %(supplier)s")

	if filters.get("tax_account"):
		conditions.append("ptc.account_head = %(tax_account)s")

	if filters.get("cashier"):
		conditions.append("pi.owner = %(cashier)s")

	return " AND " + " AND ".join(conditions) if conditions else ""


def get_columns():
	return [
		{"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 130},
		{
			"label": _("Invoice"),
			"fieldname": "invoice",
			"fieldtype": "Dynamic Link",
			"options": "document_type",
			"width": 160,
		},
		{"label": _("Customer / Supplier"), "fieldname": "customer_or_supplier", "fieldtype": "Data", "width": 190},
		{"label": _("Expense Account"), "fieldname": "expense_account", "fieldtype": "Data", "width": 190},
		{"label": _("Tax Account"), "fieldname": "tax_account", "fieldtype": "Data", "width": 190},
		{"label": _("Rate"), "fieldname": "tax_rate", "fieldtype": "Percent", "width": 80},
		{
			"label": _("Taxable"),
			"fieldname": "taxable_amount",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
		{
			"label": _("Tax"),
			"fieldname": "tax_amount",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
		{
			"label": _("Total"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
	]


def get_summary_rows(sales_data, purchase_data, expense_data):
	sales_tax = sum(flt(row.tax_amount) for row in sales_data)
	purchase_tax = sum(flt(row.tax_amount) for row in purchase_data)
	expense_tax = sum(flt(row.tax_amount) for row in expense_data)

	return [
		{"customer_or_supplier": _("Sales Tax"), "tax_amount": sales_tax, "is_summary": 1},
		{"customer_or_supplier": _("Purchase Tax"), "tax_amount": purchase_tax, "is_summary": 1},
		{"customer_or_supplier": _("Expense Tax"), "tax_amount": expense_tax, "is_summary": 1},
		{
			"customer_or_supplier": _("Net Tax"),
			"tax_amount": sales_tax - purchase_tax - expense_tax,
			"is_summary": 1,
		},
	]


def get_report_summary(data):
	summary_rows = [row for row in data if row.get("is_summary")]

	return [
		{"value": row.get("tax_amount"), "label": row.get("customer_or_supplier"), "datatype": "Currency"}
		for row in summary_rows
	]
