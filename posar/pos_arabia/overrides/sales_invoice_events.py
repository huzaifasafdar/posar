import frappe
import base64
from datetime import datetime
from posar.utils.zatca_qr import generate_zatca_qr
from posar.utils.qr_utils import generate_qr_base64

def before_save_sales_invoice(doc, method):

    # Convert posting date to datetime
    dt = datetime.strptime(doc.posting_date, "%Y-%m-%d") \
         if isinstance(doc.posting_date, str) else doc.posting_date

    # Generate ZATCA TLV QR
    qr_text = generate_zatca_qr(
        seller=doc.company,
        vat_no=doc.tax_id or "",
        invoice_datetime=dt.strftime("%Y-%m-%dT%H:%M:%S"),
        total=str(doc.rounded_total or doc.grand_total),
        vat_amount=str(doc.total_taxes_and_charges)
    )

    # Generate PNG base64
    qr_png_base64 = generate_qr_base64(qr_text)

    # Decode base64 to raw bytes
    png_binary = base64.b64decode(qr_png_base64)

    # Create file name
    filename = f"zatca_qr_{doc.name}.png"

    # Save file to ERPNext File doctype
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        "is_private": 0,         # Public file
        "content": png_binary,
        "attached_to_doctype": "Sales Invoice",
        "attached_to_name": doc.name
    }).insert(ignore_permissions=True)

    # ✅ Set QR text (keep for debugging)
    doc.custom_zatca_qr_code = qr_text

    # ✅ Set Image field to the File URL
    # doc.custom_zatca_qr_png = file_doc.file_url
    doc.custom_zatca_qr_png_path = file_doc.file_url
    frappe.db.commit()
    # frappe.msgprint(f"ZATCA QR code generated and attached to Sales Invoice {doc.name}.")
