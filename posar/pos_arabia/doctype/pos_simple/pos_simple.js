// Copyright (c) 2025, MAB and contributors
// For license information, please see license.txt


// ============================================================
// POS SIMPLE - BARCODE SCANNER
// ============================================================


/**
 * Focus the barcode input field.
 */
function focusScanField(frm) {
    const scanInput = frm.fields_dict?.scan_barcode?.$input;

    if (!scanInput) {
        console.warn("POS Simple: scan_barcode input not found");
        return;
    }

    setTimeout(() => {
        scanInput.focus();
        scanInput.select();
    }, 50);
}


/**
 * Get the current barcode from the Frappe field/input.
 */
function getScanBarcode(frm) {
    const fieldValue = String(frm.doc.scan_barcode || "").trim();

    if (fieldValue) {
        return fieldValue;
    }

    const scanInput = frm.fields_dict?.scan_barcode?.$input;

    if (scanInput) {
        return String(scanInput.val() || "").trim();
    }

    return "";
}


/**
 * Bind barcode scanner keyboard handler.
 *
 * Most USB barcode scanners work like a keyboard:
 *
 *     6920210412087 + ENTER
 *
 * Therefore we only need to listen for Enter.
 */
function bindScanHandler(frm) {

    const scanInput = frm.fields_dict?.scan_barcode?.$input;

    if (!scanInput) {
        console.warn("POS Simple: scan_barcode input not found");
        return;
    }


    // --------------------------------------------------------
    // Remove any old handler first.
    // This prevents duplicate handlers after refresh.
    // --------------------------------------------------------

    scanInput.off("keydown.pos_scan");


    // --------------------------------------------------------
    // Barcode scanner sends barcode + ENTER
    // --------------------------------------------------------

    scanInput.on("keydown.pos_scan", function (event) {

        if (event.key === "Enter" || event.which === 13) {

            event.preventDefault();
            event.stopPropagation();


            const barcode = getScanBarcode(frm);


            if (!barcode) {
                console.log("POS Simple: empty barcode");
                return;
            }


            console.log(
                "POS Simple: Barcode scanned:",
                barcode
            );


            processBarcodeScan(frm, barcode);
        }
    });


    console.log(
        "POS Simple: Barcode scanner handler attached"
    );
}


/**
 * Process the scanned barcode.
 */
function processBarcodeScan(frm, rawBarcode) {

    const barcode = String(rawBarcode || "").trim();


    // --------------------------------------------------------
    // Empty barcode
    // --------------------------------------------------------

    if (!barcode) {
        return;
    }


    // --------------------------------------------------------
    // Prevent duplicate API calls.
    // --------------------------------------------------------

    if (frm._barcode_scan_in_progress) {

        console.log(
            "POS Simple: Scan already in progress:",
            barcode
        );

        return;
    }


    frm._barcode_scan_in_progress = true;


    console.log(
        "POS Simple: Looking up barcode:",
        barcode
    );


    // --------------------------------------------------------
    // Call Python API
    // --------------------------------------------------------

    frappe.call({

        method: "posar.api.pos_simple_api.get_item_by_barcode",

        args: {
            barcode: barcode
        },


        // ----------------------------------------------------
        // SUCCESS
        // ----------------------------------------------------

        callback: function (r) {

            frm._barcode_scan_in_progress = false;


            console.log(
                "POS Simple: API response:",
                r
            );


            // ------------------------------------------------
            // No item found
            // ------------------------------------------------

            if (!r.message) {

                frappe.show_alert({
                    message:
                        `❌ No item found for barcode: ${barcode}`,
                    indicator: "red"
                });


                console.warn(
                    "POS Simple: No item found:",
                    barcode
                );


                clearScanField(frm);

                return;
            }


            // ------------------------------------------------
            // Item found
            // ------------------------------------------------

            const item = r.message;


            const item_name =
                item.name ||
                item.item_code;


            const item_code =
                item.item_code ||
                item.name;


            console.log(
                "POS Simple: Item found:",
                item
            );


            // ------------------------------------------------
            // Find existing row
            // ------------------------------------------------

            const existing_row =
                (frm.doc.detail_table || []).find(row => {

                    return (
                        row.item === item_name ||
                        row.item === item_code
                    );

                });


            // ------------------------------------------------
            // Existing item
            // Increase quantity
            // ------------------------------------------------

            if (existing_row) {

                const new_quantity =
                    (existing_row.quantity || 0) + 1;


                console.log(
                    "POS Simple: Increasing quantity:",
                    item_code,
                    new_quantity
                );


                frappe.model.set_value(
                    existing_row.doctype,
                    existing_row.name,
                    "quantity",
                    new_quantity
                );

            }


            // ------------------------------------------------
            // New item
            // ------------------------------------------------

            else {

                console.log(
                    "POS Simple: Adding new item:",
                    item_code
                );


                const child =
                    frm.add_child("detail_table");


                frappe.model.set_value(
                    child.doctype,
                    child.name,
                    "item",
                    item_name
                );


                frappe.model.set_value(
                    child.doctype,
                    child.name,
                    "quantity",
                    1
                );
            }


            // ------------------------------------------------
            // Refresh child table
            // ------------------------------------------------

            frm.refresh_field("detail_table");


            // ------------------------------------------------
            // Clear scanner field
            // ------------------------------------------------

            clearScanField(frm);
        },


        // ----------------------------------------------------
        // ERROR
        // ----------------------------------------------------

        error: function (err) {

            frm._barcode_scan_in_progress = false;


            console.error(
                "POS Simple: Barcode API error:",
                err
            );


            frappe.show_alert({
                message:
                    `❌ Error checking barcode: ${barcode}`,
                indicator: "red"
            });


            clearScanField(frm);
        }
    });
}


/**
 * Clear barcode field and put cursor back into it.
 */
function clearScanField(frm) {

    frm.set_value("scan_barcode", "");


    setTimeout(() => {

        focusScanField(frm);

    }, 150);
}


/**
 * Setup the barcode scanner.
 */
function setupBarcodeScanner(frm) {

    setTimeout(() => {

        bindScanHandler(frm);

        focusScanField(frm);

    }, 300);
}


// ============================================================
// FRAPPE FORM EVENTS
// ============================================================

frappe.ui.form.on("POS Simple", {


    // --------------------------------------------------------
    // Form Load
    // --------------------------------------------------------

    onload(frm) {

        console.log(
            "POS Simple: Form loaded"
        );


        setupBarcodeScanner(frm);
    },


    // --------------------------------------------------------
    // Form Refresh
    // --------------------------------------------------------

    refresh(frm) {

        console.log(
            "POS Simple: Form refreshed"
        );


        setupBarcodeScanner(frm);
    }

});