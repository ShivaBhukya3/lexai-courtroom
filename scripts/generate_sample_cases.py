"""Generate realistic sample Indian court cases with PDFs, images, and metadata."""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("WARNING: reportlab not installed. PDF generation will be skipped.")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNING: Pillow not installed. Image generation will be skipped.")


BASE_DIR = Path(__file__).parent.parent
CASES_DIR = BASE_DIR / "data" / "cases" / "sample_cases"


def create_pdf_styles():
    """Create professional legal document styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CourtHeader",
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    ))
    styles.add(ParagraphStyle(
        name="CaseTitle",
        fontName="Helvetica-Bold",
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor("#2c3e50"),
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
        borderPad=4,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=16,
    ))
    styles.add(ParagraphStyle(
        name="Bold10",
        fontName="Helvetica-Bold",
        fontSize=10,
        spaceAfter=4,
    ))
    return styles


def generate_case_001():
    """Generate Case 001 — Civil Property Dispute (Maharashtra)."""
    case_dir = CASES_DIR / "case_001"
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "evidence_photos").mkdir(exist_ok=True)
    (case_dir / "testimony_audio").mkdir(exist_ok=True)

    # ── 1. Complaint PDF ──────────────────────────────────────────────────
    if REPORTLAB_AVAILABLE:
        _generate_property_complaint_pdf(case_dir)
        print("  [✓] case_001/complaint.pdf created")
    else:
        _generate_text_fallback(
            case_dir / "complaint.txt",
            "Property Dispute Complaint - Case 001",
            _property_complaint_text(),
        )
        print("  [✓] case_001/complaint.txt created (PDF skipped — no reportlab)")

    # ── 2. Evidence images ────────────────────────────────────────────────
    if PIL_AVAILABLE:
        _generate_property_image(
            case_dir / "evidence_photos" / "evidence_01.jpg",
            "PROPERTY SURVEY MAP",
            "Survey No. 145/2A, Village: Nashik\n"
            "Area: 5 Acres, District: Maharashtra\n"
            "Registration: MH-NK-2019-4521\n"
            "[Land boundary demarcation visible]",
            color=(20, 40, 80),
        )
        _generate_property_image(
            case_dir / "evidence_photos" / "evidence_02.jpg",
            "PROPERTY POSSESSION PHOTOGRAPH",
            "Date: 15-Mar-2023\nLocation: Survey No.145/2A\n"
            "Plaintiff in possession of disputed land\n"
            "[Crop cultivation visible — sugarcane field]",
            color=(30, 80, 40),
        )
        print("  [✓] case_001/evidence_photos/*.jpg created")
    else:
        print("  [!] Evidence images skipped (Pillow not installed)")

    # ── 3. Witness testimony (text) ───────────────────────────────────────
    testimony_path = case_dir / "testimony_audio" / "witness_01_testimony.txt"
    testimony_path.write_text(_witness_testimony_case_001(), encoding="utf-8")
    print("  [✓] case_001/testimony_audio/witness_01_testimony.txt created")

    # ── 4. Case metadata ──────────────────────────────────────────────────
    metadata = {
        "case_id": "CASE-2024-CIV-001",
        "case_type": "Civil",
        "sub_type": "Property Dispute",
        "court": "Civil Judge Senior Division, Nashik",
        "judge": "Hon. Justice Priya Deshmukh",
        "plaintiff": {
            "name": "Ramesh Baburao Patil",
            "age": 52,
            "occupation": "Farmer",
            "address": "Gat No. 45, Village Ozar, Nashik District, Maharashtra - 422206",
            "advocate": "Adv. Suresh Kulkarni",
        },
        "defendant": {
            "name": "Suresh Govind Patil",
            "age": 48,
            "occupation": "Businessman",
            "address": "Plot No. 12, Cidco Colony, Nashik - 422009",
            "advocate": "Adv. Meena Sharma",
        },
        "charges": [
            "Recovery of possession of agricultural land",
            "Declaration of title",
            "Permanent injunction",
        ],
        "applicable_law": ["CPC Order VII Rule 1", "Specific Relief Act 1963", "Transfer of Property Act 1882"],
        "survey_numbers": ["145/2A", "146/1"],
        "land_area": "5 Acres",
        "land_value_inr": 8500000,
        "filing_date": "2024-01-15",
        "hearing_dates": [
            "2024-02-20",
            "2024-03-15",
            "2024-04-10",
            "2024-05-22",
        ],
        "next_hearing": "2024-06-18",
        "status": "Evidence Recording Stage",
        "witnesses": [
            {"name": "Govind Tukaram Patil", "relation": "Plaintiff's brother", "type": "fact_witness"},
            {"name": "Ramesh Sarpanch Deshpande", "relation": "Village Sarpanch", "type": "character_witness"},
            {"name": "Land Revenue Inspector", "relation": "Government official", "type": "expert_witness"},
        ],
        "documents": [
            {"name": "7/12 Extract", "type": "revenue_record", "date": "2023-11-20"},
            {"name": "Sale Deed 2001", "type": "ownership_document", "date": "2001-06-15"},
            {"name": "Mutation Entry", "type": "revenue_record", "date": "2019-03-10"},
        ],
        "key_facts": [
            "Plaintiff claims ownership since 2001 via registered sale deed",
            "Defendant occupied land during plaintiff's illness in 2022",
            "5 acres of prime agricultural land in Maharashtra's wine country",
            "Land value approximately ₹85 lakhs at current market rates",
            "Defendant claims adverse possession under Section 27 Limitation Act",
        ],
        "created_at": datetime.now().isoformat(),
        "lexai_version": "1.0.0",
    }
    with open(case_dir / "case_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("  [✓] case_001/case_metadata.json created")


def _property_complaint_text() -> str:
    return """
IN THE COURT OF CIVIL JUDGE SENIOR DIVISION, NASHIK
CIVIL SUIT NO. 45 OF 2024

RAMESH BABURAO PATIL, Age: 52 years, Occupation: Farmer,
R/o: Gat No. 45, Village Ozar, Nashik District - 422206  ... PLAINTIFF

VERSUS

SURESH GOVIND PATIL, Age: 48 years, Occupation: Businessman,
R/o: Plot No. 12, Cidco Colony, Nashik - 422009  ... DEFENDANT

PLAINT FOR RECOVERY OF POSSESSION, DECLARATION OF TITLE
AND PERMANENT INJUNCTION

The Plaintiff above named most respectfully submits as under:

1. FACTS OF THE CASE:
The Plaintiff is the lawful owner of agricultural land bearing Survey
No. 145/2A admeasuring 5 Acres situated at Village Ozar, Taluka Niphad,
District Nashik, Maharashtra. The Plaintiff purchased the said land from
Govind Ramchandra Patil vide Registered Sale Deed dated 15th June 2001,
registered at Sub-Registrar Office, Niphad, Registration No. MH-NK-2001-4521.

2. The Plaintiff has been in continuous, peaceful and uninterrupted possession
of the suit land since 2001 and has been cultivating the same as his primary
agricultural land for growing sugarcane and grapes.
"""


def _generate_property_complaint_pdf(case_dir: Path) -> None:
    styles = create_pdf_styles()
    doc = SimpleDocTemplate(
        str(case_dir / "complaint.pdf"),
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    story = []
    story.append(Paragraph("IN THE COURT OF CIVIL JUDGE SENIOR DIVISION, NASHIK", styles["CourtHeader"]))
    story.append(Paragraph("CIVIL SUIT NO. 45 OF 2024", styles["CaseTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2c3e50")))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(
        "RAMESH BABURAO PATIL, Age: 52 years, Occupation: Farmer, "
        "R/o: Gat No. 45, Village Ozar, Nashik District, Maharashtra – 422206",
        styles["BodyText2"]
    ))
    story.append(Paragraph("<b>... PLAINTIFF</b>", styles["Bold10"]))
    story.append(Paragraph("<b>VERSUS</b>", ParagraphStyle("vs", parent=styles["CaseTitle"], fontSize=11)))
    story.append(Paragraph(
        "SURESH GOVIND PATIL, Age: 48 years, Occupation: Businessman, "
        "R/o: Plot No. 12, Cidco Colony, Nashik – 422009",
        styles["BodyText2"]
    ))
    story.append(Paragraph("<b>... DEFENDANT</b>", styles["Bold10"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2c3e50")))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "PLAINT FOR RECOVERY OF POSSESSION, DECLARATION OF TITLE AND PERMANENT INJUNCTION",
        styles["CaseTitle"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    paragraphs = [
        ("1. FACTS OF THE CASE", (
            "The Plaintiff is the lawful owner and possessor of agricultural land bearing "
            "Survey No. 145/2A admeasuring 5 Acres (Five Acres), situated at Village Ozar, "
            "Taluka Niphad, District Nashik, State of Maharashtra. The Plaintiff purchased "
            "the said land from one Govind Ramchandra Patil (father of the Defendant) vide "
            "Registered Sale Deed dated 15th June 2001, duly registered before the Sub-Registrar, "
            "Niphad, bearing Registration No. MH-NK-2001-4521, Book No. 1, Volume No. 234, "
            "Page Nos. 112-128. The Plaintiff paid full and valuable consideration of "
            "Rs. 3,50,000/- (Rupees Three Lakhs Fifty Thousand only) at the time of execution "
            "of the said Sale Deed."
        )),
        ("2. PLAINTIFF'S CONTINUOUS POSSESSION", (
            "Ever since the execution and registration of the aforesaid Sale Deed in the year 2001, "
            "the Plaintiff has been in open, continuous, peaceful, and uninterrupted possession and "
            "enjoyment of the suit land. The Plaintiff has been cultivating the land as his primary "
            "agricultural holding, growing sugarcane and grapes which are primary cash crops of "
            "Nashik region. The Plaintiff has been paying all land revenue, water charges, and other "
            "statutory dues in respect of the suit land regularly. The 7/12 Extract (Record of Rights) "
            "issued by the Revenue Department stands in the name of the Plaintiff as the lawful owner "
            "and possessor of the said land."
        )),
        ("3. DEFENDANT'S ILLEGAL OCCUPATION", (
            "In or around March 2022, when the Plaintiff was admitted to hospital for treatment of a "
            "serious illness and was unable to personally oversee his agricultural land, the Defendant "
            "— Suresh Govind Patil, being the son of the original vendor and bearing a long-standing "
            "grudge against the Plaintiff — took advantage of the Plaintiff's absence and illegally "
            "trespassed upon and occupied the suit land. The Defendant has, without any right, title, "
            "or interest whatsoever, taken possession of the entire 5 acres of agricultural land and "
            "has been attempting to cultivate the same and is claiming false ownership thereof."
        )),
        ("4. LEGAL TITLE AND OWNERSHIP", (
            "The Plaintiff's title to the suit property is absolute, clear, and marketable. The chain "
            "of title documents clearly establishes: (a) Original Sale Deed dated 15.06.2001 in favour "
            "of Plaintiff; (b) Mutation Entry No. 2345 in Revenue Records; (c) 7/12 Extract clearly "
            "showing Plaintiff as owner; (d) Payment receipts of land revenue from 2001 to 2024; "
            "(e) Agricultural produce records showing Plaintiff's cultivation. The present market value "
            "of the suit property is approximately Rs. 85,00,000/- (Rupees Eighty-Five Lakhs Only) "
            "based on the prevailing market rates in Nashik District."
        )),
        ("5. DEFENDANT'S CLAIM OF ADVERSE POSSESSION (BASELESS)", (
            "The Defendant has falsely and frivolously claimed adverse possession of the suit land under "
            "Section 27 of the Limitation Act, 1963. This claim is entirely baseless and without merit "
            "for the following reasons: (i) The Defendant's occupation commenced only in March 2022, "
            "which is merely 2 years ago — far short of the 12 years required for adverse possession; "
            "(ii) The Plaintiff never abandoned possession voluntarily; (iii) The Plaintiff's possession "
            "was merely disrupted due to medical emergency; (iv) Adverse possession requires open, "
            "hostile, exclusive possession which has never been established."
        )),
        ("6. CAUSE OF ACTION", (
            "The cause of action in this suit arose in March 2022 when the Defendant illegally occupied "
            "the suit land. The cause of action further arose on 10th December 2023 when the Defendant "
            "refused to vacate the property despite receipt of a legal notice dated 25th November 2023 "
            "sent by the Plaintiff through his advocate Adv. Suresh Kulkarni, Nashik."
        )),
        ("7. WITNESSES", (
            "The Plaintiff proposes to examine the following witnesses: (a) Govind Tukaram Patil, "
            "brother of the Plaintiff, who will testify about continuous possession since 2001; "
            "(b) Ramesh Deshpande, Sarpanch of Village Ozar, who will testify about the Plaintiff's "
            "cultivation and possession; (c) Revenue Inspector, Taluka Niphad, who will produce and "
            "verify the official revenue records; (d) Agricultural Officer who will confirm crop records."
        )),
        ("8. RELIEFS CLAIMED", (
            "In view of the foregoing, the Plaintiff humbly prays that this Hon'ble Court be pleased to: "
            "(a) Pass a decree for recovery of possession of the suit land bearing Survey No. 145/2A "
            "admeasuring 5 Acres situated at Village Ozar, Nashik from the Defendant; "
            "(b) Pass a decree declaring that the Plaintiff is the absolute owner of the suit land; "
            "(c) Pass a decree for permanent injunction restraining the Defendant, his servants, "
            "agents, and all persons claiming through him from interfering with the Plaintiff's "
            "peaceful possession and enjoyment of the suit land; "
            "(d) Award mesne profits at the rate of Rs. 2,00,000/- per annum from March 2022 till "
            "delivery of possession; "
            "(e) Award costs of this suit to the Plaintiff; "
            "(f) Pass such other and further orders as this Hon'ble Court may deem fit and proper."
        )),
    ]

    for heading, body in paragraphs:
        story.append(Paragraph(heading, styles["SectionHeader"]))
        story.append(Paragraph(body, styles["BodyText2"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("VERIFICATION", styles["SectionHeader"]))
    story.append(Paragraph(
        "I, Ramesh Baburao Patil, the Plaintiff above named, do hereby verify that the "
        "contents of paragraphs 1 to 8 of this Plaint are true and correct to the best of "
        "my knowledge, belief, and information. No part of it is false and nothing material "
        "has been concealed therefrom.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 0.3 * inch))

    date_data = [
        ["Date: 15th January 2024", "Signature of Plaintiff"],
        ["Place: Nashik", "(RAMESH BABURAO PATIL)"],
    ]
    date_table = Table(date_data, colWidths=[8 * cm, 8 * cm])
    date_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    story.append(date_table)

    doc.build(story)


def _generate_property_image(path: Path, title: str, content: str, color: tuple) -> None:
    img = Image.new("RGB", (800, 600), color=color)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, 800, 80], fill=(color[0] + 20, color[1] + 20, color[2] + 20))
    draw.text((400, 40), title, fill=(255, 215, 0), anchor="mm")

    # Border
    draw.rectangle([20, 100, 780, 580], outline=(200, 180, 100), width=3)

    # Content lines
    y_pos = 130
    for line in content.split("\n"):
        draw.text((400, y_pos), line, fill=(220, 220, 220), anchor="mm")
        y_pos += 40

    # Watermark
    draw.text((400, 540), "LEXAI — EVIDENCE EXHIBIT", fill=(150, 130, 80), anchor="mm")
    img.save(str(path), "JPEG", quality=90)


def _witness_testimony_case_001() -> str:
    return """WITNESS TESTIMONY — CASE NO: CASE-2024-CIV-001
Name: Govind Tukaram Patil
Relation: Brother of Plaintiff (Ramesh Baburao Patil)
Date of Statement: 20th February 2024
Court: Civil Judge Senior Division, Nashik

SWORN TESTIMONY:

My name is Govind Tukaram Patil and I am 48 years of age. I am the younger brother
of the Plaintiff, Ramesh Baburao Patil. I reside in the same village Ozar and have
been a witness to all events related to the disputed property.

Regarding the purchase of land: I was present on 15th June 2001 when my brother
Ramesh purchased the agricultural land bearing Survey No. 145/2A from Govind
Ramchandra Patil, the father of the Defendant. The sale deed was executed and
registered at Sub-Registrar Office, Niphad in my presence. My brother paid the
full consideration amount and obtained possession of the land on the same day.

Regarding continuous possession: From 2001 to March 2022 — a period of over 21
years — my brother Ramesh was in continuous and uninterrupted possession of the
suit land. He cultivated sugarcane for first 10 years and then shifted to grape
cultivation which is more profitable. I personally helped him in agricultural work
during peak seasons. The Defendant Suresh never made any claim to the land during
this 21-year period.

Regarding the illegal occupation: In March 2022, my brother Ramesh was hospitalized
at Nashik Civil Hospital with severe cardiac issues and was admitted to ICU for
3 weeks. During this period of medical emergency, the Defendant Suresh Govind Patil,
taking advantage of the situation, illegally entered and occupied the suit land.
I personally witnessed Defendant's men ploughing the land on or about 15th March 2022.

When I objected, the Defendant threatened me and claimed the land belonged to his
father and that the sale deed of 2001 was a "fraud". This is completely false. My
brother recovered from his illness in April 2022 and immediately sent a legal notice
to the Defendant, but he refused to vacate.

I say that the Defendant has no right, title, or interest in the suit land and his
occupation is completely illegal and unlawful. My brother is the rightful owner and
the Defendant should be ordered to vacate immediately.

EXAMINATION IN CHIEF ENDS.
"""


def generate_case_002():
    """Generate Case 002 — Criminal IPC 420 Fraud Case (Mumbai)."""
    case_dir = CASES_DIR / "case_002"
    case_dir.mkdir(parents=True, exist_ok=True)

    if REPORTLAB_AVAILABLE:
        _generate_fir_report_pdf(case_dir)
        _generate_medical_report_pdf(case_dir)
        _generate_bank_statements_pdf(case_dir)
        print("  [✓] case_002/fir_report.pdf created")
        print("  [✓] case_002/medical_report.pdf created")
        print("  [✓] case_002/bank_statements.pdf created")
    else:
        _generate_text_fallback(case_dir / "fir_report.txt", "FIR Report", "FIR for IPC 420 Fraud Case")
        print("  [✓] case_002/fir_report.txt created (PDF skipped)")

    metadata = {
        "case_id": "CASE-2024-CRM-002",
        "case_type": "Criminal",
        "sub_type": "Cheating and Fraud",
        "fir_number": "FIR No. 234/2024",
        "police_station": "Andheri (West) Police Station, Mumbai",
        "court": "Metropolitan Magistrate Court, Mumbai",
        "judge": "Hon. Magistrate Rajesh Kumar",
        "complainant": {
            "name": "Vikram Mehta",
            "age": 41,
            "occupation": "Software Engineer",
            "address": "Flat 402, Sai Residency, Andheri West, Mumbai - 400058",
        },
        "accused": {
            "name": "Pradeep Kumar Sharma",
            "age": 38,
            "occupation": "Self-proclaimed Financial Advisor",
            "address": "Room 12, Janta Colony, Dharavi, Mumbai - 400017",
            "prior_record": True,
            "bail_status": "In custody",
        },
        "charges": [
            "IPC Section 420 — Cheating and dishonestly inducing delivery of property",
            "IPC Section 468 — Forgery for purpose of cheating",
            "IPC Section 471 — Using as genuine a forged document",
            "IPC Section 120B — Criminal conspiracy",
        ],
        "amount_defrauded_inr": 2500000,
        "modus_operandi": "Fake investment scheme promising 40% annual returns",
        "filing_date": "2024-01-08",
        "arrest_date": "2024-01-10",
        "chargesheet_date": "2024-02-28",
        "hearing_dates": ["2024-03-15", "2024-04-20", "2024-05-10"],
        "next_hearing": "2024-06-25",
        "status": "Trial Stage",
        "witnesses": [
            {"name": "Vikram Mehta", "type": "complainant"},
            {"name": "Sunita Shah", "type": "co-victim", "defrauded_amount": 500000},
            {"name": "Bank Manager, HDFC Andheri", "type": "expert_witness"},
            {"name": "Investigating Officer Patil", "type": "investigating_officer"},
        ],
        "evidence": [
            {"type": "bank_statements", "description": "HDFC and ICICI bank records"},
            {"type": "whatsapp_messages", "description": "Investment promises on WhatsApp"},
            {"type": "fake_certificates", "description": "Forged SEBI registration certificate"},
            {"type": "victim_statement", "description": "Written complaint by Vikram Mehta"},
        ],
        "key_facts": [
            "Accused posed as SEBI-registered financial advisor with forged credentials",
            "Victims transferred ₹25 lakhs over 6 months for fake investment scheme",
            "Accused promised 40% annual returns — far above market rates",
            "Money transferred to multiple accounts to avoid detection",
            "SEBI confirmed no registration of accused or his firm",
        ],
        "created_at": datetime.now().isoformat(),
        "lexai_version": "1.0.0",
    }

    with open(case_dir / "case_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("  [✓] case_002/case_metadata.json created")


def _generate_fir_report_pdf(case_dir: Path) -> None:
    styles = create_pdf_styles()
    doc = SimpleDocTemplate(
        str(case_dir / "fir_report.pdf"),
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    story = []

    story.append(Paragraph("GOVERNMENT OF MAHARASHTRA", styles["CourtHeader"]))
    story.append(Paragraph("MUMBAI POLICE", styles["CourtHeader"]))
    story.append(Paragraph("FIRST INFORMATION REPORT (FIR)", styles["CaseTitle"]))
    story.append(Paragraph("(Under Section 154 Cr.P.C.)", styles["CaseTitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.15 * inch))

    fir_data = [
        ["FIR No.:", "234/2024", "Date:", "08-01-2024"],
        ["Police Station:", "Andheri (West)", "District:", "Mumbai"],
        ["Act & Section:", "IPC 420, 468, 471, 120B", "Cognizable:", "Yes"],
    ]
    fir_table = Table(fir_data, colWidths=[4 * cm, 6 * cm, 3 * cm, 5 * cm])
    fir_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f0f0f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(fir_table)
    story.append(Spacer(1, 0.2 * inch))

    sections_data = [
        ("COMPLAINANT DETAILS", (
            "Name: Vikram Mehta | Age: 41 years | Occupation: Software Engineer\n"
            "Address: Flat 402, Sai Residency, Andheri West, Mumbai – 400058\n"
            "Mobile: 98XXXXXXXX | Email: vikram.mehta@email.com"
        )),
        ("ACCUSED DETAILS", (
            "Name: Pradeep Kumar Sharma | Age: 38 years\n"
            "Occupation: Self-proclaimed Financial Advisor\n"
            "Address: Room 12, Janta Colony, Dharavi, Mumbai – 400017\n"
            "Firm name (fake): 'Sharma Wealth Management Pvt. Ltd.'"
        )),
        ("OFFENCE DETAILS", (
            "Date of Offence: July 2023 to December 2023 (continuous)\n"
            "Place of Offence: Andheri West, Mumbai and Online\n"
            "Amount Defrauded: Rs. 25,00,000/- (Rupees Twenty-Five Lakhs Only)"
        )),
        ("BRIEF FACTS AND COMPLAINT", (
            "The complainant Vikram Mehta states that in July 2023, he was approached by the accused "
            "Pradeep Kumar Sharma who introduced himself as a SEBI-registered financial advisor and "
            "proprietor of 'Sharma Wealth Management Pvt. Ltd.' The accused showed the complainant "
            "fake certificates purportedly issued by SEBI and Reserve Bank of India showing his "
            "registration as a portfolio manager. The accused represented that he had exclusive "
            "access to pre-IPO shares of major companies and could guarantee returns of 35-40% per "
            "annum. "
            "Induced by these fraudulent representations, the complainant transferred a total of "
            "Rs. 25,00,000/- (Rupees Twenty-Five Lakhs) to bank accounts provided by the accused "
            "in six instalments between July 2023 and December 2023. The amounts were transferred "
            "to three different bank accounts — HDFC Bank Account No. 50100XXXXXX in the name of "
            "'Sharma Wealth Management', ICICI Bank Account No. 0262XXXXXX in accused's personal "
            "name, and a Paytm payment bank account. "
            "When the complainant sought returns on his investment in January 2024, the accused "
            "became evasive and later switched off his phone. Upon inquiry with SEBI directly, the "
            "complainant discovered that: (1) No such entity 'Sharma Wealth Management Pvt. Ltd.' "
            "is registered with SEBI; (2) The accused has no SEBI registration; (3) The certificates "
            "shown are forged and fabricated. "
            "The complainant also learned that two other victims — Sunita Shah and Rohit Jain — were "
            "similarly defrauded by the accused with same modus operandi. The total amount defrauded "
            "from all victims is estimated at Rs. 45,00,000/-."
        )),
        ("MODUS OPERANDI", (
            "1. Target identification: Accused targeted middle-class professionals through social "
            "media and word of mouth. 2. Trust building: Showed fake SEBI certificates and "
            "fabricated investment portfolios. 3. Inducement: Promised 35-40% returns which are "
            "illegal under SEBI regulations. 4. Money collection: Collected funds in multiple "
            "accounts to obscure money trail. 5. Disappearance: After collecting substantial amounts, "
            "accused became unavailable."
        )),
        ("SECTIONS APPLICABLE", (
            "IPC Section 420: Cheating and dishonestly inducing delivery of property — "
            "Punishment: Up to 7 years imprisonment + fine. "
            "IPC Section 468: Forgery for purpose of cheating — Punishment: Up to 7 years + fine. "
            "IPC Section 471: Using forged document as genuine — Punishment: Up to 2 years + fine. "
            "IPC Section 120B: Criminal conspiracy — Punishment: As per the offence conspired."
        )),
    ]

    for heading, body in sections_data:
        story.append(Paragraph(heading, styles["SectionHeader"]))
        story.append(Paragraph(body.replace("\n", "<br/>"), styles["BodyText2"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=0.5))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Registered by: Sub-Inspector Ramesh Patil, Andheri (West) PS, Mumbai",
        styles["Bold10"]
    ))
    story.append(Paragraph(
        "Date & Time of Registration: 08-01-2024, 14:30 hrs",
        styles["BodyText2"]
    ))

    doc.build(story)


def _generate_medical_report_pdf(case_dir: Path) -> None:
    styles = create_pdf_styles()
    doc = SimpleDocTemplate(
        str(case_dir / "medical_report.pdf"),
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    story = []

    story.append(Paragraph("MUMBAI POLICE MEDICO-LEGAL CERTIFICATE", styles["CourtHeader"]))
    story.append(Paragraph(
        "Medical Examination Report — Psychological Impact Assessment",
        styles["CaseTitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("PATIENT DETAILS", styles["SectionHeader"]))
    story.append(Paragraph(
        "Name: Vikram Mehta | Age: 41 years | Gender: Male\n"
        "Referred by: Andheri (West) Police Station (FIR No. 234/2024)\n"
        "Date of Examination: 09-01-2024\n"
        "Examining Doctor: Dr. Priya Nair, MD (Psychiatry), KEM Hospital Mumbai",
        styles["BodyText2"]
    ))

    story.append(Paragraph("CLINICAL FINDINGS", styles["SectionHeader"]))
    story.append(Paragraph(
        "Patient presents with symptoms of acute financial trauma and stress disorder following "
        "significant financial fraud. Clinical observations: 1. Marked anxiety and sleep disturbances "
        "reported since January 2024. 2. Patient reports loss of appetite and inability to concentrate "
        "at work. 3. Patient expressed significant distress about loss of life savings amounting to "
        "Rs. 25 Lakhs. 4. No physical injuries observed. 5. Patient is mentally competent to give "
        "testimony and understands the legal proceedings.",
        styles["BodyText2"]
    ))

    story.append(Paragraph("PSYCHOLOGICAL IMPACT ASSESSMENT", styles["SectionHeader"]))
    story.append(Paragraph(
        "The financial fraud has caused considerable psychological harm to the complainant. The loss "
        "of Rs. 25 Lakhs representing the complainant's 8-year savings has resulted in significant "
        "mental distress. The patient will benefit from counselling support. The fraud has also "
        "affected the patient's professional performance as reported by the patient himself.",
        styles["BodyText2"]
    ))

    story.append(Paragraph("OPINION", styles["SectionHeader"]))
    story.append(Paragraph(
        "In my professional medical opinion, the complainant has suffered real and significant "
        "psychological harm as a direct result of the financial fraud. The symptoms observed are "
        "consistent with fraud-induced trauma. The complainant is fit to depose before the court.",
        styles["BodyText2"]
    ))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Dr. Priya Nair, MD (Psychiatry) | KEM Hospital, Mumbai | Date: 09-01-2024",
        styles["Bold10"]
    ))

    doc.build(story)


def _generate_bank_statements_pdf(case_dir: Path) -> None:
    styles = create_pdf_styles()
    doc = SimpleDocTemplate(
        str(case_dir / "bank_statements.pdf"),
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    story = []

    story.append(Paragraph("HDFC BANK — CERTIFIED ACCOUNT STATEMENT", styles["CourtHeader"]))
    story.append(Paragraph(
        "Account Holder: Vikram Mehta | Account No.: XXXX1234 | Branch: Andheri West",
        styles["CaseTitle"]
    ))
    story.append(Paragraph(
        "Statement Period: 01-07-2023 to 31-12-2023 | Certified True Copy for Court Purposes",
        styles["BodyText2"]
    ))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 0.15 * inch))

    transactions = [
        ["Date", "Description", "Debit (Rs.)", "Credit (Rs.)", "Balance (Rs.)"],
        ["01-07-2023", "Opening Balance", "", "", "28,50,000"],
        ["15-07-2023", "NEFT to Sharma Wealth Mgmt HDFC", "5,00,000", "", "23,50,000"],
        ["02-08-2023", "IMPS to Sharma Wealth Mgmt", "4,00,000", "", "19,50,000"],
        ["18-08-2023", "NEFT to Pradeep Kumar Sharma ICICI", "3,50,000", "", "16,00,000"],
        ["05-09-2023", "NEFT to Sharma Wealth Mgmt HDFC", "5,00,000", "", "11,00,000"],
        ["22-10-2023", "IMPS to Paytm Payments Bank", "4,00,000", "", "7,00,000"],
        ["10-12-2023", "NEFT to Sharma Wealth Mgmt HDFC", "3,50,000", "", "3,50,000"],
        ["31-12-2023", "Closing Balance", "", "", "3,50,000"],
        ["TOTAL", "Amount Defrauded", "25,00,000", "", ""],
    ]

    t = Table(transactions, colWidths=[3 * cm, 7 * cm, 3 * cm, 3 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffe0e0")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (4, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f8f8")]),
    ]))
    story.append(t)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "Certified by: Branch Manager, HDFC Bank Andheri West | Date: 12-01-2024\n"
        "This statement is certified true copy produced pursuant to Police requisition under Section 91 CrPC.",
        styles["BodyText2"]
    ))

    doc.build(story)


def _generate_text_fallback(path: Path, title: str, content: str) -> None:
    path.write_text(f"{title}\n{'=' * len(title)}\n\n{content}", encoding="utf-8")


def main():
    print("\n" + "=" * 60)
    print("  LexAI — Sample Case Generator")
    print("=" * 60)

    print("\n[CASE 001] Civil Property Dispute — Nashik, Maharashtra")
    generate_case_001()

    print("\n[CASE 002] Criminal IPC 420 Fraud — Mumbai, Maharashtra")
    generate_case_002()

    print("\n" + "=" * 60)
    print("  Sample cases generated successfully!")
    print(f"  Location: {CASES_DIR}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
