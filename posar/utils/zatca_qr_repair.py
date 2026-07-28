import base64
import os
from io import BytesIO

import frappe
import qrcode


def get_sales_invoice_qr_data_uri(invoice_name):
	doc = frappe.get_doc("Sales Invoice", invoice_name)
	qr_payload = doc.get("custom_zatca_qr_code") or make_zatca_tlv_payload(doc)
	return make_qr_data_uri(qr_payload)


def repair_sales_invoice_qr(invoice_name):
	doc = frappe.get_doc("Sales Invoice", invoice_name)
	qr_payload = doc.get("custom_zatca_qr_code") or make_zatca_tlv_payload(doc)
	file_name = f"QR_image_{doc.name}.png"
	file_url = f"/files/{file_name}"
	file_path = frappe.get_site_path("public", "files", file_name)

	image = qrcode.make(qr_payload)
	image.save(file_path)

	file_doc = frappe.db.exists(
		"File",
		{
			"attached_to_doctype": "Sales Invoice",
			"attached_to_name": doc.name,
			"file_name": file_name,
		},
	)

	if file_doc:
		frappe.db.set_value("File", file_doc, "file_url", file_url, update_modified=False)
	else:
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"file_url": file_url,
				"attached_to_doctype": "Sales Invoice",
				"attached_to_name": doc.name,
				"is_private": 0,
			}
		).insert(ignore_permissions=True)

	doc.db_set("custom_zatca_qr_png_path", file_url, update_modified=False)
	if not doc.get("custom_zatca_qr_code"):
		doc.db_set("custom_zatca_qr_code", qr_payload, update_modified=False)

	frappe.db.commit()
	return file_url


def repair_missing_sales_invoice_qr_files():
	repaired = []
	files = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Sales Invoice",
			"file_name": ["like", "QR_image_%.png"],
			"is_private": 0,
		},
		fields=["attached_to_name", "file_url"],
	)

	for file in files:
		if not file.attached_to_name or not file.file_url:
			continue

		file_path = frappe.get_site_path("public", "files", file.file_url.rsplit("/", 1)[-1])
		if not os.path.exists(file_path):
			repair_sales_invoice_qr(file.attached_to_name)
			repaired.append(file.attached_to_name)

	return repaired


def make_qr_data_uri(qr_payload):
	image = qrcode.make(qr_payload)
	buffer = BytesIO()
	image.save(buffer, format="PNG")
	encoded = base64.b64encode(buffer.getvalue()).decode()
	return f"data:image/png;base64,{encoded}"


def make_zatca_tlv_payload(doc):
	company_tax_id = doc.company_tax_id or frappe.db.get_value("Company", doc.company, "tax_id") or ""
	timestamp = f"{doc.posting_date}T{str(doc.posting_time or '00:00:00').split('.')[0]}"
	values = [
		doc.company or "",
		company_tax_id,
		timestamp,
		f"{float(doc.grand_total or 0):.2f}",
		f"{float(doc.total_taxes_and_charges or 0):.2f}",
	]

	raw = b"".join(get_tlv(index, value) for index, value in enumerate(values, start=1))
	return base64.b64encode(raw).decode()


def get_tlv(tag, value):
	value = str(value or "").encode("utf-8")
	return bytes([tag, len(value)]) + value
