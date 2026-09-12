import frappe
from frappe.utils import flt, nowdate


printer_name = 'Zebra GK420t' # exact Windows printer name
zpl_file = 'ITEM001.zpl'


def _get_default_selling_price_list():
    selling_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
    if selling_price_list:
        return selling_price_list

    if frappe.db.exists("Price List", "Standard Selling"):
        return "Standard Selling"

    return frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name")


def _get_current_item_price(item_code, price_list=None, currency=None, uom=None):
    if not item_code:
        return None

    price_list = price_list or _get_default_selling_price_list()
    if not price_list:
        return None

    if not currency:
        currency = frappe.db.get_value("Price List", price_list, "currency")

    params = {
        "item_code": item_code,
        "price_list": price_list,
        "currency": currency or "",
        "uom": uom or "",
        "today": nowdate(),
    }
    currency_condition = "AND currency = %(currency)s" if currency else ""

    rows = frappe.db.sql(
        f"""
        SELECT price_list_rate
        FROM `tabItem Price`
        WHERE
            item_code = %(item_code)s
            AND price_list = %(price_list)s
            AND selling = 1
            {currency_condition}
            AND (valid_from IS NULL OR valid_from <= %(today)s)
            AND (valid_upto IS NULL OR valid_upto = '' OR valid_upto >= %(today)s)
        ORDER BY
            CASE
                WHEN %(uom)s != '' AND IFNULL(uom, '') = %(uom)s THEN 0
                WHEN IFNULL(uom, '') = '' THEN 1
                ELSE 2
            END,
            valid_from DESC,
            modified DESC
        LIMIT 1
        """,
        params,
        as_dict=True,
    )
    return flt(rows[0].price_list_rate) if rows else None


@frappe.whitelist()
def get_item_barcode_print_data(item_code, barcode=None, price_list=None, currency=None, uom=None):
    item = frappe.get_cached_doc("Item", item_code)
    barcode_row = None
    barcode_fields = ["barcode", "uom"]
    if frappe.db.has_column("Item Barcode", "posa_uom"):
        barcode_fields.append("posa_uom")

    if barcode:
        barcode_row = frappe.db.get_value(
            "Item Barcode",
            {"parent": item_code, "barcode": barcode},
            barcode_fields,
            as_dict=True,
        )

    if not barcode_row:
        barcode_row = frappe.db.get_value(
            "Item Barcode",
            {"parent": item_code},
            barcode_fields,
            as_dict=True,
        )

    label_barcode = (barcode_row and barcode_row.barcode) or barcode or item.item_code
    label_uom = uom or (barcode_row and (barcode_row.get("posa_uom") or barcode_row.get("uom"))) or item.stock_uom
    label_price = _get_current_item_price(
        item_code=item.name,
        price_list=price_list,
        currency=currency,
        uom=label_uom,
    )

    return {
        "item_code": item.name,
        "item_name": item.item_name,
        "barcode": label_barcode,
        "uom": label_uom,
        "price": label_price if label_price is not None else item.standard_rate,
        "currency": currency or frappe.db.get_value("Price List", price_list or _get_default_selling_price_list(), "currency") or "",
    }

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
