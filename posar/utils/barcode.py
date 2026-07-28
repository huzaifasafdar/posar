import base64
from xml.sax.saxutils import escape

import frappe


CODE128_PATTERNS = (
	"212222",
	"222122",
	"222221",
	"121223",
	"121322",
	"131222",
	"122213",
	"122312",
	"132212",
	"221213",
	"221312",
	"231212",
	"112232",
	"122132",
	"122231",
	"113222",
	"123122",
	"123221",
	"223211",
	"221132",
	"221231",
	"213212",
	"223112",
	"312131",
	"311222",
	"321122",
	"321221",
	"312212",
	"322112",
	"322211",
	"212123",
	"212321",
	"232121",
	"111323",
	"131123",
	"131321",
	"112313",
	"132113",
	"132311",
	"211313",
	"231113",
	"231311",
	"112133",
	"112331",
	"132131",
	"113123",
	"113321",
	"133121",
	"313121",
	"211331",
	"231131",
	"213113",
	"213311",
	"213131",
	"311123",
	"311321",
	"331121",
	"312113",
	"312311",
	"332111",
	"314111",
	"221411",
	"431111",
	"111224",
	"111422",
	"121124",
	"121421",
	"141122",
	"141221",
	"112214",
	"112412",
	"122114",
	"122411",
	"142112",
	"142211",
	"241211",
	"221114",
	"413111",
	"241112",
	"134111",
	"111242",
	"121142",
	"121241",
	"114212",
	"124112",
	"124211",
	"411212",
	"421112",
	"421211",
	"212141",
	"214121",
	"412121",
	"111143",
	"111341",
	"131141",
	"114113",
	"114311",
	"411113",
	"411311",
	"113141",
	"114131",
	"311141",
	"411131",
	"211412",
	"211214",
	"211232",
	"2331112",
)


def get_item_barcode_data_uri(item_code):
	barcode = frappe.db.get_value("Item Barcode", {"parent": item_code}, "barcode") or item_code
	return get_code128_data_uri(barcode)


def get_code128_data_uri(value, height=34, module_width=1.2):
	value = (value or "").strip()
	if not value:
		return ""

	codes = [104]
	for char in value:
		code_point = ord(char)
		if code_point < 32 or code_point > 126:
			continue
		codes.append(code_point - 32)

	if len(codes) == 1:
		return ""

	checksum = codes[0]
	for index, code in enumerate(codes[1:], start=1):
		checksum += code * index
	codes.append(checksum % 103)
	codes.append(106)

	x = 0
	bars = []
	for code in codes:
		for index, width in enumerate(CODE128_PATTERNS[code]):
			bar_width = int(width) * module_width
			if index % 2 == 0:
				bars.append(f'<rect x="{x:.1f}" y="0" width="{bar_width:.1f}" height="{height}" />')
			x += bar_width

	svg_height = height + 12
	svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{x:.1f}" height="{svg_height}" viewBox="0 0 {x:.1f} {svg_height}">
<rect width="100%" height="100%" fill="white"/>
<g fill="black">{''.join(bars)}</g>
<text x="{x / 2:.1f}" y="{height + 10}" text-anchor="middle" font-size="9" font-family="Arial">{escape(value)}</text>
</svg>"""
	encoded = base64.b64encode(svg.encode()).decode()
	return f"data:image/svg+xml;base64,{encoded}"
