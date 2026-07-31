import frappe
from frappe import _


SALES_RETURN_ACCOUNT_NAME = "Sales Return"
SALES_TAX_LIABILITY_ACCOUNT_NAME = "Sales Tax Liability"


def apply_vat_and_return_accounts(doc, method=None):
	"""Route return income and VAT rows to dedicated accounts before GL is built."""
	if not getattr(doc, "company", None):
		return

	if doc.doctype == "Sales Invoice" and doc.get("is_return"):
		sales_return_account = get_or_create_sales_return_account(doc.company)
		for item in doc.get("items", []):
			item.income_account = sales_return_account

	if doc.doctype in ("Sales Invoice", "Purchase Invoice"):
		vat_account = get_or_create_sales_tax_liability_account(doc.company)
		for tax in doc.get("taxes", []):
			if is_vat_row(tax):
				tax.account_head = vat_account


def get_or_create_sales_return_account(company):
	company_abbr = frappe.get_cached_value("Company", company, "abbr")
	account_name = f"{SALES_RETURN_ACCOUNT_NAME} - {company_abbr}"

	if frappe.db.exists("Account", account_name):
		return account_name

	parent_account = get_income_parent_account(company)
	return create_account(
		account_name=SALES_RETURN_ACCOUNT_NAME,
		company=company,
		parent_account=parent_account,
		root_type="Income",
		account_type="Income Account",
	)


def get_or_create_vat_liability_account(company):
	return get_or_create_sales_tax_liability_account(company)


def get_or_create_sales_tax_liability_account(company):
	company_abbr = frappe.get_cached_value("Company", company, "abbr")
	account_name = f"{SALES_TAX_LIABILITY_ACCOUNT_NAME} - {company_abbr}"

	if frappe.db.exists("Account", account_name):
		return account_name

	parent_account = (
		frappe.db.get_value(
			"Account",
			{
				"company": company,
				"account_name": "Duties and Taxes",
				"root_type": "Liability",
				"is_group": 1,
			},
			"name",
		)
		or get_liability_parent_account(company)
	)

	return create_account(
		account_name=SALES_TAX_LIABILITY_ACCOUNT_NAME,
		company=company,
		parent_account=parent_account,
		root_type="Liability",
		account_type="Tax",
	)


def create_account(account_name, company, parent_account, root_type, account_type):
	account = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": account_name,
			"company": company,
			"parent_account": parent_account,
			"root_type": root_type,
			"account_type": account_type,
			"is_group": 0,
		}
	)
	account.insert(ignore_permissions=True)
	return account.name


def get_income_parent_account(company):
	parent = frappe.db.sql(
		"""
		SELECT name
		FROM `tabAccount`
		WHERE company = %s
			AND root_type = 'Income'
			AND is_group = 1
			AND ifnull(parent_account, '') = ''
		LIMIT 1
		""",
		company,
	)
	if parent:
		return parent[0][0]

	parent = frappe.db.get_value("Account", {"company": company, "root_type": "Income", "is_group": 1}, "name")
	if parent:
		return parent

	frappe.throw(_("No Income group account found for company {0}").format(company))


def get_liability_parent_account(company):
	parent = frappe.db.sql(
		"""
		SELECT name
		FROM `tabAccount`
		WHERE company = %s
			AND root_type = 'Liability'
			AND is_group = 1
			AND ifnull(parent_account, '') = ''
		LIMIT 1
		""",
		company,
	)
	if parent:
		return parent[0][0]

	parent = frappe.db.get_value("Account", {"company": company, "root_type": "Liability", "is_group": 1}, "name")
	if parent:
		return parent

	frappe.throw(_("No Liability group account found for company {0}").format(company))


def is_vat_row(tax):
	values = [
		tax.get("description"),
		tax.get("account_head"),
		tax.get("charge_type"),
	]
	text = " ".join(value or "" for value in values).lower()
	return "vat" in text or "tax" in text
