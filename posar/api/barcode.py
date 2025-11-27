import frappe


printer_name = 'Zebra GK420t' # exact Windows printer name
zpl_file = 'ITEM001.zpl'

@frappe.whitelist()
def print_item_barcode(item_code, item_name, barcode, price):
    barcode = barcode or item_code or""
    price = price or ""

    # Label size: 50x25mm (adjust as needed)
    # 203 DPI → 8 dots per mm → 50mm ≈ 400 dots
    zpl = f"""
    ^XA
    ^PW400
    ^LH0,0

    ^CF0,30
    ^FO20,20^FD{item_name}^FS

    ^BY2,3,60
    ^FO20,70^BCN,60,Y,N,N
    ^FD{barcode}^FS

    ^CF0,25
    ^FO20,150^FDPrice: {price}^FS

    ^XZ
    """

    return zpl
