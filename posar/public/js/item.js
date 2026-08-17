frappe.ui.form.on('Item', {
    refresh(frm) {
        frm.add_custom_button("Print Barcode", () => {

            const barcode = frm.doc.barcode || frm.doc.barcodes?.[0]?.barcode || frm.doc.item_code;

            if (!barcode) {
                frappe.msgprint(__("Please add a barcode before printing."));
                return;
            }

            frappe.prompt(
                { label: "Number of Copies", fieldname: "copies", fieldtype: "Int", default: 1, reqd: 1 },
                ({ copies }) => {
                    const qty = parseInt(copies, 10);

                    if (!Number.isInteger(qty) || qty < 1 || qty > 500) {
                        frappe.msgprint(__("Number of copies must be between 1 and 500."));
                        return;
                    }

                    printBarcodeLabels({
                        companyName: frappe.defaults.get_user_default("Company") || frappe.boot?.sysdefaults?.company || "",
                        itemName: frm.doc.item_name || frm.doc.item_code,
                        barcode: String(barcode),
                        price: frm.doc.standard_rate,
                        copies: qty
                    });
                },
                "Print Barcode",
                "Print"
            );

        });
    },
    before_save: function (frm) {
        const barcodePattern = /^[0-9]+$/; // Example pattern for barcode

        if (frm.doc.item_code && barcodePattern.test(frm.doc.item_code)) {

            // Check if barcodes field exists and create it if not
            if (!frm.doc.barcodes) {
                frm.add_child('barcodes', {
                    barcode: frm.doc.item_code
                });
            } else {
                // Check if item_code is not already in barcodes
                let exists = frm.doc.barcodes.some(b => b.barcode === frm.doc.item_code);
                if (!exists) {
                    frm.add_child('barcodes', {
                        barcode: frm.doc.item_code
                    });
                }
            }
            frm.doc.barcode = frm.doc.item_code;
        }
    },
    item_name: async function (frm) {
        console.log("Item name changed:", frm.doc.item_name);
        if (frm.doc.item_name) {
            frappe.call({
                method: 'posar.api.translate.translate_to_arabic',
                args: { text: frm.doc.item_name },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('custom_item_name_arabic', r.message);
                    }
                }
            });
        }
    },
    // custom_valuation_rate_with_vat: async function(frm) {
    //     await calculate_rate_without_vat(frm, "custom_valuation_rate_with_vat", "valuation_rate");
    // },
    // custom_selling_rate_with_vat: async function(frm) {
    //     await calculate_rate_without_vat(frm, "custom_selling_rate_with_vat", "standard_rate");
    // },
    item_code: function (frm) {
        const barcodePattern = /^[0-9]+$/; // Example pattern for barcode
        if (barcodePattern.test(frm.doc.item_code)) {
            console.log("Item code is a barcode.");
        } else {
            console.log("Item code is a name.");
        }
    }
});
async function calculate_rate_without_vat(frm, source_field, target_field) {
    let vat_rate = 0;

    if (frm.doc.taxes) {
        const tax = frm.doc.taxes.find(t => t.tax_type && t.tax_rate);
        vat_rate = tax ? tax.tax_rate : 15;
    } else {
        vat_rate = 15; // default fallback
    }

    const value_with_vat = frm.doc[source_field];
    if (!value_with_vat) return;

    const base_rate = value_with_vat / (1 + vat_rate / 100);
    frm.set_value(target_field, base_rate.toFixed(2));

    frappe.show_alert({
        message: `${__(target_field.replace("_", " "))} (excl. VAT): ${base_rate.toFixed(2)}`,
        indicator: "green"
    });
}

function printBarcodeLabels({ companyName, itemName, barcode, price, copies }) {
    let barcodeSvg;

    try {
        barcodeSvg = createBarcodeSvg(barcode);
    } catch (error) {
        frappe.msgprint(__(error.message));
        return;
    }

    const printWindow = window.open("", "_blank", "width=600,height=600");

    if (!printWindow) {
        frappe.msgprint(__("Please allow pop-ups to print barcode labels."));
        return;
    }

    const safeName = escapeHtml(itemName);
    const safeBarcode = escapeHtml(barcode);
    const safePrice = price != null && price !== ""
        ? escapeHtml(Number(price).toFixed(2))
        : "";
    const labels = Array.from({ length: copies }, () => `
        <section class="label">
            <div class="label-body">
                <div class="company-name">GSPT Co</div>
                ${barcodeSvg}
                <div class="barcode-value">${safeBarcode}</div>
                <div class="item-name">${safeName}</div>
                <div class="price">${safePrice ? `SAR ${safePrice}` : ""}</div>
            </div>
        </section>
    `).join("");

    printWindow.document.open();
    printWindow.document.write(`<!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <title>${__("Print Barcode")}</title>
                <style>
    @page {
        size: 38mm 26mm;
        margin: 0;
    }

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    html,
    body {
        width: 100%;
        min-height: 100%;
        margin: 0;
        padding: 0;

        font-family: "Courier New", monospace;
        color: #000;
        background: #fff;

        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }

    /* CENTER THE ENTIRE STICKER */
    .label {
        position: relative;

        width: 38mm;
        height: 26mm;

        margin-left: auto;
        margin-right: auto;

        overflow: hidden;

        page-break-after: always;
        break-after: page;
    }

    .label:last-child {
        page-break-after: auto;
        break-after: auto;
    }

    .label-body {
        position: absolute;
        top: 0;
        left: 0;

        width: 38mm;
        height: 26mm;
    }

    /* COMPANY */
    .company-name {
        position: absolute;
        top: 1.2mm;
        left: 1.5mm;
        right: 1.5mm;

        height: 2.5mm;

        font-size: 5.5pt;
        font-weight: 700;
        line-height: 2.5mm;
        text-align: center;

        white-space: nowrap;
        overflow: hidden;
    }

    /* BARCODE - CENTER */
    .barcode {
        position: absolute;

        top: 4mm;
        left: 50%;

        width: 32mm;
        height: 7mm;

        margin: 0;
        transform: translateX(-50%);

        display: block;
    }

    /* BARCODE NUMBER - CENTER */
    .barcode-value {
        position: absolute;

        top: 11.5mm;
        left: 50%;

        width: 35mm;
        height: 2.5mm;

        margin: 0;
        transform: translateX(-50%);

        font-size: 7pt;
        font-weight: 800;
        line-height: 2.5mm;
        text-align: center;

        white-space: nowrap;
        overflow: hidden;
    }

    /* ITEM */
    .item-name {
        position: absolute;

        top: 14.2mm;
        left: 1.5mm;
        right: 1.5mm;

        height: 3mm;

        font-size: 5pt;
        font-weight: 700;
        line-height: 3mm;
        text-align: center;

        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* PRICE */
    .price {
        position: absolute;

        top: 17.4mm;
        left: 1.5mm;
        right: 1.5mm;

        height: 2.8mm;

        font-size: 7pt;
        font-weight: 800;
        line-height: 2.8mm;
        text-align: center;

        white-space: nowrap;
        overflow: hidden;
    }

    @media print {
        @page {
            size: 38mm 26mm;
            margin: 0;
        }

        html,
        body {
            width: 100%;
            margin: 0;
            padding: 0;
        }

        .label {
            width: 38mm;
            height: 26mm;

            margin-left: auto;
            margin-right: auto;
        }
    }
</style>
            </head>
            <body>${labels}</body>
        </html>`);
    printWindow.document.close();
    printWindow.focus();
    printWindow.addEventListener("afterprint", () => printWindow.close(), { once: true });
    setTimeout(() => printWindow.print(), 250);
}

function createBarcodeSvg(value) {
    const normalized = String(value || "").trim();
    if (!normalized) {
        throw new Error("Barcode value is required.");
    }

    if (/^\d{12,13}$/.test(normalized)) {
        return buildLinearBarcodeSvg(encodeEan13(normalized));
    }

    return buildLinearBarcodeSvg(encodeCode128(normalized));
}

function buildLinearBarcodeSvg(modules, { moduleWidth = 3, barHeight = 50, quietZone = 13 } = {}) {
    const totalWidth = (quietZone * 2 + modules.length) * moduleWidth;
    let x = quietZone * moduleWidth;
    const rects = [];

    modules.forEach(isBar => {
        if (isBar) {
            rects.push(
                `<rect x="${x}" y="0" width="${moduleWidth}" height="${barHeight}" shape-rendering="crispEdges"/>`
            );
        }
        x += moduleWidth;
    });

    return `<svg class="barcode" xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="${barHeight}" viewBox="0 0 ${totalWidth} ${barHeight}" preserveAspectRatio="xMidYMid meet" aria-label="barcode">${rects.join("")}</svg>`;
}

function encodeEan13(value) {
    const digitsOnly = String(value).replace(/\D/g, "");
    let digits;

    if (digitsOnly.length === 12) {
        digits = digitsOnly + ean13CheckDigit(digitsOnly);
    } else if (digitsOnly.length === 13) {
        digits = digitsOnly;
    } else {
        throw new Error("EAN-13 barcode must contain 12 or 13 digits.");
    }

    const EAN13_L = [
        "0001101", "0011001", "0010011", "0111101", "0100011",
        "0110001", "0101111", "0111011", "0110111", "0001011"
    ];
    const EAN13_G = [
        "0100111", "0110011", "0011011", "0100001", "0011101",
        "0111001", "0000101", "0010001", "0001001", "0010111"
    ];
    const EAN13_R = [
        "1110010", "1100110", "1101100", "1000010", "1011100",
        "1001110", "1010000", "1000100", "1001000", "1110100"
    ];
    const EAN13_PARITY = [
        "LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
        "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"
    ];

    const modules = [];
    const appendPattern = pattern => {
        pattern.split("").forEach(bit => modules.push(bit === "1"));
    };

    appendPattern("101");

    const parity = EAN13_PARITY[Number(digits[0])];
    for (let index = 0; index < 6; index += 1) {
        const digit = Number(digits[index + 1]);
        appendPattern(parity[index] === "L" ? EAN13_L[digit] : EAN13_G[digit]);
    }

    appendPattern("01010");

    for (let index = 0; index < 6; index += 1) {
        appendPattern(EAN13_R[Number(digits[index + 7])]);
    }

    appendPattern("101");
    return modules;
}

function ean13CheckDigit(firstTwelveDigits) {
    let sum = 0;

    for (let index = 0; index < 12; index += 1) {
        sum += Number(firstTwelveDigits[index]) * (index % 2 === 0 ? 1 : 3);
    }

    return String((10 - (sum % 10)) % 10);
}

function encodeCode128(value) {
    const patterns = [
        "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312",
        "132212", "221213", "221312", "231212", "112232", "122132", "122231", "113222",
        "123122", "123221", "223211", "221132", "221231", "213212", "223112", "312131",
        "311222", "321122", "321221", "312212", "322112", "322211", "212123", "212321",
        "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
        "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121",
        "313121", "211331", "231131", "213113", "213311", "213131", "311123", "311321",
        "331121", "312113", "312311", "332111", "314111", "221411", "431111", "111224",
        "111422", "121124", "121421", "141122", "141221", "112214", "112412", "122114",
        "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
        "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112",
        "421211", "212141", "214121", "412121", "111143", "111341", "131141", "114113",
        "114311", "411113", "411311", "113141", "114131", "311141", "411131", "211412",
        "211214", "211232", "2331112"
    ];
    const characters = Array.from(value);

    if (!characters.length || characters.some(character => {
        const code = character.charCodeAt(0);
        return code < 32 || code > 126;
    })) {
        throw new Error("Barcode must contain printable English letters and numbers only.");
    }

    const codes = characters.map(character => character.charCodeAt(0) - 32);
    const checksum = (104 + codes.reduce((sum, code, index) => sum + code * (index + 1), 0)) % 103;
    const encoded = [104, ...codes, checksum, 106];
    const modules = [];

    encoded.forEach(code => {
        patterns[code].split("").forEach((width, index) => {
            const barWidth = Number(width);
            const isBar = index % 2 === 0;

            for (let moduleIndex = 0; moduleIndex < barWidth; moduleIndex += 1) {
                modules.push(isBar);
            }
        });
    });

    return modules;
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}
