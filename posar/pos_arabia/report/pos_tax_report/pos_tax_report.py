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
	conditions = get_conditions(filters)

	return frappe.db.sql(
		f"""
		SELECT
			si.posting_date,
			si.name AS sales_invoice,
			si.customer,
			si.customer_name,
			si.pos_profile,
			si.owner AS cashier,
			stc.account_head AS tax_account,
			stc.description AS tax_description,
			stc.rate AS tax_rate,
			si.base_net_total AS net_total,
			stc.base_tax_amount AS tax_amount,
			stc.base_total AS total_after_tax,
			si.base_grand_total AS grand_total,
			si.is_return
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


def get_conditions(filters):
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


def get_columns():
	return [
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 160,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 140,
		},
		{"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
		{
			"label": _("POS Profile"),
			"fieldname": "pos_profile",
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": 150,
		},
		{
			"label": _("Cashier"),
			"fieldname": "cashier",
			"fieldtype": "Link",
			"options": "User",
			"width": 150,
		},
		{
			"label": _("Tax Account"),
			"fieldname": "tax_account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180,
		},
		{"label": _("Tax Description"), "fieldname": "tax_description", "fieldtype": "Data", "width": 180},
		{"label": _("Tax Rate"), "fieldname": "tax_rate", "fieldtype": "Percent", "width": 90},
		{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
		{
			"label": _("Tax Amount"),
			"fieldname": "tax_amount",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
		{
			"label": _("Total After Tax"),
			"fieldname": "total_after_tax",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 130,
		},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"width": 120,
		},
		{"label": _("Is Return"), "fieldname": "is_return", "fieldtype": "Check", "width": 80},
	]


def get_report_summary(data):
	total_tax = sum(flt(row.tax_amount) for row in data)
	total_net = sum(flt(row.net_total) for row in data)
	total_grand = sum(flt(row.grand_total) for row in data)

	return [
		{"value": total_net, "label": _("Net Total"), "datatype": "Currency"},
		{"value": total_tax, "label": _("Tax Amount"), "datatype": "Currency"},
		{"value": total_grand, "label": _("Grand Total"), "datatype": "Currency"},
	]
