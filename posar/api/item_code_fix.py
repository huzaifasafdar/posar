import frappe

@frappe.whitelist()
def fix_item_codes_from_excel(dry_run=1, limit=None):
    """
    Fix Item.item_code and Item Barcode.barcode
    using Excel authoritative list.

    dry_run: 1 (default) → preview only
             0 → apply changes
    limit  : optional int → test on first N rows
    """

    dry_run = int(dry_run)
    limit = int(limit) if limit else None

    EXCEL_ITEMS = [
        ("000000619639", "BREAD ROLLING PIN WOOD"),
        ("000001318203", "CANDY POT ALUMINIUM 20 cm 131820"),
        ("000001333145", "TOWEL BATH EGYPT 30"),
        ("000001333435", "TOWEL WHITE BATH 90 X 170 MASRI"),
        ("0000101204", "RUBBER BANDS SET IN KEES"),
        ("000021582608", "PERMANENT MARKER ROCO 4 PCS SET 350"),
        ("00002300004", "CAKE BOX PLASTIC ASCAL"),
        ("0000382272507", "NOTE PADE DIAMOND EXTRA"),
        ("00019", "CHARGER 1.0M  EP-AD12-2"),
        ("000209523966", "PAPER A4 COLOR 250 SHEETS ROCO"),
        ("000249745540", "LUKHMA GAME"),
        ("00025586", "PLATE MELAMINE (CC-209)"),
        ("000300597064", "TRAY STEEL SET 3 pcs"),
        ("000302111480", "KNIFE SMALL SLICER"),
        ("000302111497", "KNIFE MEDIUM SLICER"),
        ("000302111503", "KNIFE LARGE SLICER"),
        ("00080096", "BOWL GHADDAR SOUP MELAMINE SMALL 1"),
        ("001006000001", "SCHOOL NOTE BOOK COPY 200PAGES 0001-006"),
        ("001010000004", "NOTE BOOK SILK 80 sheets ARABIC SBC "),
        ("001011000003", "NOTE BOOK SILK 100 sheets ARABIC SBC"),
        ("001014000000", "UNIVERSITY COPY PAPER 200. 0001-014 PERSONALIZE ME"),
        ("001523260377", "MASCO COLOR PENCIL  01015007"),
        ("001523260414", "CRAYONS MASCO 6010"),
        ("001523261480", "DIY VALUE CRAFT MAGIC 1355"),
        ("001523261541", "DIY VALUE CRAFT ITS MAGIC"),
        ("003050222989", "STARGOLD HD MINI RECEIVER  SG-610"),
        ("0051610010019", "VGLAN BODY CREAM 250ML"),
        ("00539462552883", "DSL CABLE 2M UTP CAT6 "),
        ("006523260686", "SHARPENER OFFICE"),
        ("008005000001", "NOTE BOOK SCHOOL 40 sheets ARABIC "),
        ("008006000000", "NOTE BOOK SCHOOL 60 sheets ARABIC "),
        ("008007000009", "NOTE BOOK SCHOOL 80 sheets ARABIC "),
        ("008008000008", "NOTE BOOK SCHOOL 100 sheets ARABIC PHOTO COVER"),
        ("008365284", "NAIL CUTER AND PERSONAL CLIPER SET (ASODA)"),
        ("008365285", "NAIL CUTER AND PERSONAL CLIPER SET (ASODA)"),
        ("008365286", "NAIL CUTER AND PERSONAL CLIPER SET (ASODA)"),
        ("008562000292", "BATTERY AAA SONY"),
        ("008562007642", "BATTERY SONY CR2032"),
        ("009005000008", "NOTE BOOK SCHOOL 40 sheets ARABIC"),
        ("009007000006", "NOTE BOOK SCHOOL 80 sheets ARABIC"),
        ("009008000005", "NOTE BOOK 100 sheets SCHOOL "),
        ("010000000535", "SCHOOL COPY PAPER SHEETS 037108C"),
        ("010000000733", "FLAIR PEACH BLACK 0.7mm 10 pcs"),
        ("010181040009", "PALMERS COCOA  BUTTER  CRM"),
        ("010181066405", "PALMERS  HAIR FOOD CREAM 150ML"),
        ("0104043752177411", "EAR MACHINE BATTRIES"),
        ("0104043752177497", "EAR MACHINE BATTRIES"),
        ("0111919", "LEEFA SOLAF BLACK MAGHRABI A3519"),
        ("0112328", "SOLAF NOSE STRIPS"),
        ("011381000701", "JAR HONEY 1l (ITALY)"),
        ("011381000749", "JAR HONEY 4L (ITALY)"),
        ("011381001548", "WATER GLASS BORMIOLI CAPITOL (3pcs)"),
        ("011381003306", "WATER GLASS SET BORMIOLI ITALY (3pcs)"),
        ("011381009230", "DEDALO  BORMIOLI (3pcs)"),
        ("011381013244", "FRIES CUP BORMOILI GLASS WARE"),
        ("011381019147", "WATER GLASS ITALY AURA (3pcs)"),
        ("011381022116", "WATER GLASS SET BORMIOLI ITALY (3pcs)"),
        ("011381023151", "WATER GLASS SET AURUM ITALY (6pcs)"),
        ("011381023199", "GLASS GAZAZ (3 pcs) MADISON"),
        ("011381023342", "WATER GLASS BORMIOLI ROLLY (3pcs)"),
        ("011381024769", "GLASS GAZAZ (3 pcs) PORTOFINO"),
        ("011381045702", "WATER GLASS ITALY BORMIOLI ELECTRA (6pcs)"),
        ("014425090782", "FLASH TOILET 1180 ML ORIGINAL USA MADE IN SAUDIA AR ABIA"),
        ("015031398675", "SKETCH BOOK TS16D"),
        ("015031398699", "SKETCH BOOK TS40D"),
        ("015031398842", "MASCO OIL PASTELS COLORS"),
        ("015031398866", "MASCO OIL PASTELS COLORS"),
        ("015031399214", "PREMIUM INKJET GLOSST PAPER 20 sheets"),
        ("015031399269", "NOTE BOOK SILK 100-001"),
        ("015031399276", "SCHOOL NOTE PADE SPIRAL MEMO 032-100-002"),
        ("015031399283", "COPY NOTE PADE SPIRAL MEMO 032-100-003"),
        ("015031399436", "NOTE BOOK SILK 40 sheets MATH MASCO"),
        ("015031399542", "GIFT PACKING ROLL VELVET MASCO"),
        ("015031399689", "NOTE PAD LARGE 100A4"),
        ("015031399696", "NOTE PADE A5 100A5 MASCO"),
        ("015031399740", "SCHOOL NOTE COPY 0521A412"),
        ("015031399757", "SCHOOL NOTE COPY  0521A413"),
        ("015031399771", "SKETCH MAP BOOK SILK"),
        ("015031399788", "MAP SKETCH BOOK 6SS"),
        ("015031399795", "SKETCH BOOK MAP 6MN"),
        ("015031399979", "NOTE COPYS GEOGRAPHY+BIOLOGY+COOKING+PATRIOTISM+ALQURAN"),
        ("015031400354", "ALPHABETS LEARNING LETTER 052-100-2001"),
        ("015031400361", "ENGLISH NUMBERS LEARNING 052-100-2002"),
        ("015031400446", "COLOR SKETCH BOOK 025-100-KRB"),
        ("015031400507", "TRANSPARENT POCKET FILES 100 pcs MASCO"),
        ("015032399916", "GLASS MAGNIFYING 60mm"),
        ("015032400841", "ORGANIC GLASS MAGNIFYING 142"),
        ("015032400889", "GLASS MAGNIFYING 146"),
        ("015132404909", "GRAFT LAND MATERIAL 098-100-KA113"),
        ("015132405074", "GRAFT LAND MATERIAL 098-100-KA88"),
        ("017247696774", "TAWA SHINE 35CM"),
        ("018653005358", "SENSODYNE 50ml PASTE EXTRA FRESH"),
        ("019100208360", "JERGENS LOTION (SOFTENING MUSK) 400ml"),
        ("019100208384", "JERGENS LOTION (ORIGINAL SCENT) 400ml"),
        ("019100208483", "JERGENS LOTION  DAILY MOISTURE 400ml"),
        ("019100219366", "JERGENS LOTION 400 ml SKIN FIRMING"),
        ("019780223035", "POM POM HOORAY TEAM 22303"),
        ("020181620606", "PANCAKE BATTER DISPENSER STEEL"),
        ("021200010323", "SCOTCH DOUBLE SIDED TAPE 136"),
        ("021200013393", "SCOTCH DOUBLE FACE TAPE 4.5 kg"),
        ("021276022374", "TRAVEL CONVERTER SAMSONIC"),
        ("021484017346", "PEACOCK HAIR DYE BLACK"),
        ("022200750318", "LADY SPEED STICK (CHEERY) 65g"),
        ("022200750394", "LADY SPEED STICK FRESH ESSENCE 65g"),
        ("022200961516", "LADY SPEED STICK (TEEN SPIRIT) 65g"),
        ("022200962995", "LADY SPEED STICK INVISIBLE DRY 40 g"),
        ("022200963695", "LADY SPEED STICK INVISIBLE DRY 40 g"),
        ("022200964081", "LADY SPEED STICK (PINK CRUSH) 65g"),
        ("02-41085", "AIRTIGHT CONTAINER BASURAH"),
        ("02-41086", "FOOD CONTAINER SET (400+600+950ml)"),
        ("0251465665", "NATURAL FIREWOOD MADE IN VIETNAM 10KG"),
        ("0252000116", "TRAY STEEL SET 3PCS"),
        ("026102257685", "TEA CUP LUMINARC (6 pcs)"),
        ("026102418802", "BOWL GAZAZ SMALL LUMINARC"),
        ("026102824290", "WATER JUG GLASS LUMINARC SET 7PCS"),
        ("027386232856", "CORNER ORGANIZER STAND 200 CLASS"),
        ("028617120911", "PEN LIQUID GOLD DECO COLOUR"),
        ("029820100110", "AIR FRESHNER HOTELS 500 ml ORIGINAL"),
        ("030201544", "ADAPTOR TYPE C 20w ORIGINAL APPLE"),
        ("030975260161", "CAR WAX 47ml"),
        ("034022120583", "SOCKS WINTER 12"),
        ("035017008541", "JOVAN WHITE MUSK PERFUME MADE IN SPAIN 59ML"),
        ("035017009944", "JOVAN MUSK PERFUME MADE IN SPAIN 59ML"),
        ("040120360011", "WALL AZAN CLOCK LSH-004 AL-HARAMEEN"),
        ("041833007002", "ROSE CREAM  CEAR THE SKIN 25 g"),
        ("041976563427", "ALPHABETS LEARNING LETTER"),
        ("041976567821", "CLAY SKETCH PLASTIC T001"),
        ("041976567838", "CLAY SKETCH PLASTIC T002"),
        ("041976567845", "CLAY SKETCH PLASTIC T003"),
        ("041976567852", "MASCO SILSAL ALFAHABED 0041"),
        ("041976567869", "CLAY SKETCH PLASTIC T005"),
        ("041976567883", "CLAY SKETCH PLASTIC T007"),
        ("0449866384006", "SPRAY MOP DA-38400"),
        ("046688100250", "CREAM JOLEN BLEACH LIGHTENS DARK HAIR"),
        ("046688400015", "CREAM JOLEN BLEACH LIGHTENS DARK HAIR"),
        ("049932649543", "SEWANI GLASSWARE"),
        ("049932655490", "HOT POT GAZAZ MARINEX BRAZIL WITH COVER"),
        ("049932666243", "SEWANI BEZAWI GLASSWARE MEDIUM MARINEX"),
        ("049932672268", "SEWANI MARINEX 3 PCS GLASSWARE RECTANGLE"),
        ("049932672466", "SEWANI OVAL 3 pcs GLASSWARE MARINEX"),
        ("050036380577", "HEADPHONE BLUTOOTH TUNE510BT JBL BY HARMAN 40H"),
        ("051141369884", "TAPE DOUBLE SIDED SCOTCH 3 mtr"),
        ("0523229200162", "COOKER BELLY SET 1-5 PAKISTANI GALAXY"),
        ("0534915972", "SAUDIA NUMBER KHUSHNOOD"),
        ("060-07-00", "BOX FILLIN SMALL"),
        ("06280000187025", "SILICONE CUP CAKE 6 PCS (CK1-330)"),
        ("06281006484252", "SOAP LIFEBUOY 70g*6 PKT"),
        ("0638936995086", "FOOD MIXER KION 10 LTR"),
        ("06-422-4851", "WALL LED LAMP 25W CHINA"),
        ("06-518-575", "WALL LAMP 40W CHINA"),
        ("066143190053", "FOX 40 WHISTLE"),
        ("066160422038", "SAHAN RICE SMALL 30 cm OLD AL JABR"),
        ("069301610066", "OVEN BAGS CLASSIC (5pcs)"),
        ("06974038060005", "FACE MASK FR&COM 50 pcs"),
        ("070062125850", "MOP COTTON LARGE AMERICA"),
        ("070330101241", "BIC PEN FRANCE 4 IN 1"),
        ("071153001497", "SHINES TABLOON STP 118 ml"),
        ("071153652545", "SHINE TABLOON SYP 295 ml"),
        ("071153655270", "TIRE CARE STP SON OF GUN 600 ml"),
        ("0722874591346", "CAR MP3"),
        ("073096400405", "RECHARGABLE NI-MH BATTERY 3.6 PANASONIC"),
        ("07-400-615", "BRACKET LAMO (48W) 1200*62*25MM"),
        ("07540446", "VANTILATION FANE 20*20"),
        ("07540447", "VANTILATION FANE 25*25"),
        ("07540448", "VANTILATION FANE 30*30"),
        ("076174100990", "CUTTER KNIFE (18mm) IRON"),
        ("0761862097453", "HD CABLE  1.5 M SENBER"),
        ("0761862097460", "HD CABLE  3 M SENBER"),
        ("076501928662", "KITCHEN DIY CAKE SHAPER"),
        ("077001800069", "GLOVES BLACK 70 PCS BOX  LRGE"),
        ("07702018598533", "RAZOR BLUE  GILLETTE BARBER 50 PCS"),
        ("078257571079", "INTEX SWIMING POOL 57107NP (61*22)cm"),
        ("078257586714", "SWIMING JACKET 50*47 cm "),
        ("078917845977", "SEWANI GLASSWARE SQUARE 1.6 ltr"),
        ("078917849302", "SEWANI GLASSWARE RECTANGLE MEXICO ORIGINAL"),
        ("078917984218", "SAWANI GAZAZ 2 pcs BRAZIL"),
        ("079522999970", "SIMMER RING HEAT DIFFUSER 99997"),
        ("0799439302532", "HAIR COLOUR  APPLE PRO MAX 500 ML+500"),
        ("080576006606", "GLASS VIVA 15300 SET 4 pcs"),
        ("080576062497", "CUP GLASSWARE VIVA MUG BORMIOLI"),
        ("08-50-657", "BASIN MUIXER HOT&COLD (FLAGON)"),
        ("08-51-583", "SHOWER BATH (JI PERMIUM ) 583"),
        ("08-52-832", "SINK MIXER WALL MOUNTED (CHROME)"),
        ("087617855384", "GLUE STICK MASCO 10g"),
        ("087954016875", "GLASS 17490 BORMIOLI SET 6 pcs HABANA "),
        ("087954218828", "BOWL PORCELAIN 11 SPAIN BORMIOLI"),
        ("087954860379", "WATER BLUE GLASS 18230 BORMIOLI SET MURANA"),
        ("088300605514", "UNPLUGGED FOR MEN  EMPER 80ML"),
        ("0883314891614", "PLATE LUMINARC 23 CERAMIC"),
        ("091163708360", "PC CAMERA GENIUS ILOOK 300"),
        ("091511200102", "OLFA CUTTER KNIFE JAPAN L-2"),
        ("09501101530003", "HD CABLE 1.5 m SAFEMORE"),
        ("09501101530004", "HDMI CABLE 3 m SAFEMORE"),
        ("096202004151", "THERMOS SEFYA KHALED SAIF"),
        ("09661223334444", "TISSUE KHIR 500*10 PKT"),
        ("0972980127735", "WELCOME KEES 2 KG"),
        ("097298012839", "PEDI PISTOL 5113 HOME PEDICURE SYSTEM"),
        ("098200054329", "LEAD PENCIL MASCO MS2B SET 12 pcs")
    ]

    results = {
        "updated": [],
        "skipped": [],
        "errors": [],
        "dry_run": bool(dry_run),
    }

    rows = EXCEL_ITEMS[:limit] if limit else EXCEL_ITEMS

    for excel_code, item_name in rows:

        # Canonical numeric code
        try:
            canonical_code = canonical_item_code(excel_code)

            if canonical_code is None:
                # results["skipped"].append({
                #     "reason": "alphanumeric code – already correct",
                #     "excel_code": excel_code,
                #     "item_name": item_name,
                # })
                continue

        except ValueError:
            results["skipped"].append({
                "reason": "non-numeric excel code",
                "excel_code": excel_code,
                "item_name": item_name,
            })
            continue

        items = frappe.get_all(
            "Item",
            filters={
                "item_code": canonical_code,
                "item_name": item_name
            },
            fields=["name", "item_code"]
        )

        if len(items) != 1:
            results["skipped"].append({
                "reason": "match count != 1",
                "excel_code": excel_code,
                "canonical_code": canonical_code,
                "item_name": item_name,
                "matches": len(items),
            })
            continue

        item = items[0]

        if dry_run:
            results["updated"].append({
                "item": item.name,
                "item_code": canonical_code,
                "barcode": canonical_code,
                "update with": excel_code
            })
            continue

        try:
            # Update Item Code
            frappe.db.set_value(
                "Item",
                item.name,
                "item_code",
                excel_code
            )

            # Update Barcode(s)
            frappe.db.sql("""
                UPDATE `tabItem Barcode`
                SET barcode = %s
                WHERE parent = %s
            """, (excel_code, item.name))

            results["updated"].append({
                "item": item.name,
                "item_code": excel_code,
            })

        except Exception as e:
            results["errors"].append({
                "item": item.name,
                "error": str(e),
            })

    if not dry_run:
        frappe.db.commit()

    return results


def canonical_item_code(excel_code: str) -> str | None:
    """
    Returns canonical numeric item_code if fix is required.
    Returns None if item_code should be skipped.
    """

    code = str(excel_code).strip()

    # Only numeric codes need fixing
    if code.isdigit():
        return str(int(code))

    # Alphanumeric codes are already correct in DB
    return None
