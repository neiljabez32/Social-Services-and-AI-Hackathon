"""
PDF summary sheet generator.

The output is what an applicant takes away from the Oflex session — printed
on a partner agency's printer, or carried on a phone, to bring to a Ministry
worker. It's a one-or-two page document, professional, readable, with no
jargon.
"""

from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


SCOPE_LABELS = {
    "none": "No sharing — Ministry only, not to other agencies",
    "org": "Ministry of Social Development only",
    "cluster": "Agencies with existing data-sharing agreements",
    "ca_table": "Coordinated housing & support network",
    "named_agencies": "Specific named agencies only",
}

SLEEP_LABELS = {
    "shelter": "At a shelter",
    "unsheltered": "Outside (park, doorway, tent, vehicle)",
    "couch": "On a friend's or family member's couch",
    "supportive": "Supportive or transitional housing",
    "institution": "Hospital, jail, or treatment centre",
    "housed": "Own home or rented place",
}

HOUSING_LABELS = {
    "homeless": "Homeless",
    "at_risk": "At risk of homelessness",
    "provisionally_housed": "Provisionally housed",
    "housed": "Housed",
    "unknown": "Unknown",
}

INDIGENOUS_LABELS = {
    "first_nations": "First Nations",
    "metis": "Métis",
    "inuit": "Inuit",
    "none": "Not Indigenous",
    "declined": "Preferred not to say",
}

PURPOSE_LABELS = {
    "case_mgmt": "Case management",
    "coordinated_access": "Coordinated access to housing & services",
    "referral": "Referrals to other agencies",
    "reporting": "Internal Ministry reporting",
    "safety_planning": "Safety planning",
}

DATA_CAT_LABELS = {
    "demographics": "Basic info (name, age, contact)",
    "medical": "Medical history",
    "mental_health": "Mental health history",
    "substance_use": "Substance use history",
    "financial": "Financial situation",
    "family": "Family & children",
    "contact": "Contact information",
}


def _label(value, mapping):
    if value is None or value == "":
        return "—"
    return mapping.get(value, value)


def build_summary_pdf(client_record, consent_record) -> bytes:
    """
    Build a printable PDF summary. Returns the raw PDF bytes.

    Designed to be one or two pages. Top is applicant info; middle is
    privacy choices; bottom is next steps + the toll-free number.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="Oflex — Income Assistance Application Summary",
        author="Oflex",
    )

    # Style sheet
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "OflexH1",
        parent=styles["Heading1"],
        fontSize=18,
        spaceBefore=0,
        spaceAfter=4,
        textColor=colors.HexColor("#1a1a1a"),
    )
    h2 = ParagraphStyle(
        "OflexH2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#2563eb"),
    )
    body = ParagraphStyle(
        "OflexBody",
        parent=styles["Normal"],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1a1a1a"),
    )
    small = ParagraphStyle(
        "OflexSmall",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#666666"),
    )
    caption = ParagraphStyle(
        "OflexCaption",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#888888"),
        alignment=2,  # right
    )

    story = []
    c = client_record
    cns = consent_record

    # Header
    story.append(Paragraph("Oflex", h1))
    story.append(
        Paragraph(
            "Income Assistance Application — Summary Sheet",
            ParagraphStyle("hdr", parent=body, fontSize=11, textColor=colors.HexColor("#444444")),
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            small,
        )
    )
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=0.5))

    # Applicant section
    story.append(Paragraph("Applicant", h2))

    name = f"{c.first_name or ''} {c.last_name or ''}".strip() or "—"
    rows = [
        ["Name:", name],
    ]
    if c.aliases:
        rows.append(["Also known as:", c.aliases])
    if c.dob:
        age_part = f" (age {c.age})" if c.age else ""
        rows.append(["Date of birth:", f"{c.dob}{age_part}"])
    elif c.age:
        rows.append(["Age:", str(c.age)])
    if c.phone:
        rows.append(["Phone:", c.phone])
    if c.email:
        rows.append(["Email:", c.email])

    rows.append(["Where slept last night:", _label(c.current_sleeping_location, SLEEP_LABELS)])
    rows.append(["Housing status:", _label(c.housing_status, HOUSING_LABELS)])

    if c.indigenous_identity and c.indigenous_identity not in (None, "none", "declined"):
        rows.append(["Indigenous identity:", _label(c.indigenous_identity, INDIGENOUS_LABELS)])
        if c.ocap_protected:
            rows.append([
                "Data governance:",
                f"OCAP-protected · Nation: {c.ocap_governing_nation or 'not specified'}",
            ])

    table = Table(rows, colWidths=[1.7 * inch, 4.6 * inch])
    table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a1a")),
        ])
    )
    story.append(table)

    # Privacy section
    story.append(Paragraph("Your privacy choices", h2))
    story.append(
        Paragraph(
            "These choices were made by the applicant and recorded with their "
            "digital signature. They control how this information may be used.",
            small,
        )
    )
    story.append(Spacer(1, 6))

    purpose_codes = (cns.purpose_codes or "").split(";")
    purpose_text = ", ".join(_label(p.strip(), PURPOSE_LABELS) for p in purpose_codes if p.strip()) or "—"

    cat_codes = (cns.data_categories or "").split(";")
    cat_text = ", ".join(_label(cat.strip(), DATA_CAT_LABELS) for cat in cat_codes if cat.strip()) or "—"

    privacy_rows = [
        ["Sharing scope:", _label(cns.sharing_scope_type, SCOPE_LABELS)],
        ["Used for:", purpose_text],
        ["Information shared:", cat_text],
        ["Consent given:", cns.given_date or "—"],
        ["Consent expires:", cns.expiry_date or "Ongoing"],
        ["Consent ID:", cns.consent_id or "—"],
    ]
    ptable = Table(privacy_rows, colWidths=[1.7 * inch, 4.6 * inch])
    ptable.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a1a")),
        ])
    )
    story.append(ptable)

    # Next steps
    story.append(Paragraph("Next steps", h2))
    story.append(
        Paragraph(
            "<b>You have two ways to finish your application:</b>",
            body,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>1. Take this summary to a Ministry worker.</b> "
            "They can use it to fill out the official MySelfServe form with you. "
            "Print this page or show it on your phone.",
            body,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>2. Apply online yourself at myselfserve.gov.bc.ca.</b> "
            "You'll need to make a BCeID account using the email above. "
            "The official application asks the same questions you've already answered.",
            body,
        )
    )

    # Footer / help line in a colored box
    story.append(Spacer(1, 14))
    help_box = Table(
        [[
            Paragraph(
                "<b>Need help?</b><br/>"
                "Ministry of Social Development: <b>1-866-866-0800</b> (toll-free, interpreters available)<br/>"
                "Service BC: <b>1-800-663-7867</b><br/>"
                "Cool Aid Health Centre: 713 Johnson St, Victoria<br/>"
                "Our Place Society: 919 Pandora Ave, Victoria",
                body,
            )
        ]],
        colWidths=[6.3 * inch],
    )
    help_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#2563eb")),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(help_box)

    # Footnote
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "This summary was prepared by the applicant using Oflex. "
            "Nothing has been submitted to the government. The applicant must "
            "complete the official MySelfServe application or work with a Ministry "
            "worker to file it. Generated by Oflex.",
            small,
        )
    )

    doc.build(story)
    return buf.getvalue()
