import base64
from datetime import datetime

def tlv(tag, value):
    return bytes([tag, len(value)]) + value

def generate_zatca_qr(seller, vat_no, invoice_datetime, total, vat_amount):
    elements = b"".join([
        tlv(1, seller.encode('utf-8')),
        tlv(2, vat_no.encode('utf-8')),
        tlv(3, invoice_datetime.encode('utf-8')),
        tlv(4, total.encode('utf-8')),
        tlv(5, vat_amount.encode('utf-8')),
    ])
    return base64.b64encode(elements).decode()
