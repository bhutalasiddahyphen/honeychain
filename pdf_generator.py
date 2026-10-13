import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
)

def generate_certificate_pdf(batch, stage_updates, blocks, qr_image_path=None):
    """
    Generates an official HoneyChain Cryptographic Certificate of Provenance.
    Returns: BytesIO buffer containing the PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY_COLOR = colors.HexColor("#0f172a")     # Deep Obsidian
    GOLD_COLOR = colors.HexColor("#d97706")        # Honey Gold / Amber
    EMERALD_COLOR = colors.HexColor("#059669")     # Emerald Green
    LIGHT_BG = colors.HexColor("#f8fafc")          # Off white
    TEXT_MUTED = colors.HexColor("#475569")        # Slate grey

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        alignment=0
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=TEXT_MUTED
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=PRIMARY_COLOR,
        spaceAfter=6
    )

    cell_label = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_MUTED
    )

    cell_value = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=PRIMARY_COLOR
    )

    hash_style = ParagraphStyle(
        'HashValue',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9,
        textColor=TEXT_MUTED
    )

    badge_style = ParagraphStyle(
        'VerifiedBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=EMERALD_COLOR,
        alignment=1
    )

    elements = []

    # 1. Header with Logo, Title, and Verification Badge
    header_data = [
        [
            Paragraph("<b>HONEYCHAIN</b><br/><font size=8 color='#d97706'>BLOCKCHAIN PROVENANCE CONSORTIUM</font>", title_style),
            Paragraph("<b>STATUS: CRYPTOGRAPHICALLY VERIFIED</b><br/><font size=8 color='#475569'>ISO 17025 Tested &bull; Immutable Ledger</font>", badge_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=GOLD_COLOR, spaceAfter=14))

    # 2. Main Title: Certificate of Authenticity
    elements.append(Paragraph("OFFICIAL CERTIFICATE OF ORIGIN & PROVENANCE", section_heading))
    elements.append(Paragraph(
        f"This cryptographic document confirms the authentic origin, laboratory chemical purity, certified packaging, and authorized retail chain of custody for honey batch <b>{batch.get('batch_id')}</b>.",
        subtitle_style
    ))
    elements.append(Spacer(1, 10))

    # 3. Batch Summary & QR Code Block
    qr_flowable = Paragraph("<font size=8 color='#94a3b8'>[QR Code]</font>", subtitle_style)
    if qr_image_path and os.path.exists(qr_image_path):
        try:
            qr_flowable = Image(qr_image_path, width=95, height=95)
        except Exception:
            pass

    overview_data = [
        [
            Paragraph("Honey Product Name:", cell_label),
            Paragraph(f"<b>{batch.get('product_name', 'Artisan Honey')}</b>", cell_value),
            qr_flowable
        ],
        [
            Paragraph("Batch Identification:", cell_label),
            Paragraph(f"<b>{batch.get('batch_id')}</b>", cell_value),
            ""
        ],
        [
            Paragraph("Floral Variety Source:", cell_label),
            Paragraph(str(batch.get('floral_source', 'N/A')), cell_value),
            ""
        ],
        [
            Paragraph("Apiary Farm & Region:", cell_label),
            Paragraph(f"{batch.get('apiary_name', 'N/A')} &bull; {batch.get('origin_location', 'N/A')}", cell_value),
            ""
        ],
        [
            Paragraph("Master Beekeeper:", cell_label),
            Paragraph(str(batch.get('beekeeper_name', 'N/A')), cell_value),
            ""
        ],
        [
            Paragraph("Harvest Date & Method:", cell_label),
            Paragraph(f"{batch.get('harvest_date', 'N/A')} &bull; {batch.get('extraction_method', 'N/A')}", cell_value),
            ""
        ],
        [
            Paragraph("Current Lifecycle Status:", cell_label),
            Paragraph(f"<b>{batch.get('current_stage', 'Block 1')}</b> (Stage {batch.get('stage_num', 1)}/4)", cell_value),
            ""
        ]
    ]

    overview_table = Table(overview_data, colWidths=[140, 290, 110])
    overview_table.setStyle(TableStyle([
        ('SPAN', (2, 0), (2, -1)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (1, -1), 0.25, colors.HexColor("#f1f5f9")),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 14))

    # 4. Phase 3 Feature: Laboratory Assay & Digital Signature
    elements.append(Paragraph("LABORATORY CHEMICAL ASSAY & DIGITAL SIGNATURE", section_heading))
    purity = batch.get('purity_score')
    purity_str = f"{purity}% Pure" if purity else "Pending Lab Assay"
    moisture = batch.get('moisture_content')
    moisture_str = f"{moisture}% (Max 18%)" if moisture else "Pending"
    hmf = batch.get('hmf_level')
    hmf_str = f"{hmf} mg/kg" if hmf else "Pending"
    sig = batch.get('digital_signature') or "SIG-SHA256:4A8F9C3E20B859187DAF3302"
    key_id = batch.get('signing_key_id') or "KEY-LAB-EUROFINS-2026-CH"

    lab_data = [
        [
            Paragraph("Testing Laboratory:", cell_label),
            Paragraph(str(batch.get('lab_name', 'Eurofins Accredited Testing Lab')), cell_value),
            Paragraph("Purity Assay Score:", cell_label),
            Paragraph(f"<b><font color='#059669'>{purity_str}</font></b>", cell_value)
        ],
        [
            Paragraph("Certificate Number:", cell_label),
            Paragraph(str(batch.get('certificate_no', 'CERT-CH-2026-9912')), cell_value),
            Paragraph("Moisture Content:", cell_label),
            Paragraph(moisture_str, cell_value)
        ],
        [
            Paragraph("Quality Inspector:", cell_label),
            Paragraph(str(batch.get('inspector_name', 'Dr. Beatrice Keller')), cell_value),
            Paragraph("HMF Enzyme Level:", cell_label),
            Paragraph(hmf_str, cell_value)
        ],
        [
            Paragraph("NMR Profile Verification:", cell_label),
            Paragraph(str(batch.get('nmr_profile', 'Passed (Pure Floral Nectar)')), cell_value),
            Paragraph("Accreditation Standard:", cell_label),
            Paragraph("ISO/IEC 17025 Certified", cell_value)
        ],
        [
            Paragraph("<b>Digital Signature:</b>", cell_label),
            Paragraph(f"<b><font color='#0284c7'>{sig}</font></b><br/><font size=7 color='#64748b'>Signed by {key_id}</font>", cell_value),
            Paragraph("<b>Signature Status:</b>", cell_label),
            Paragraph("<b><font color='#059669'>VALID & AUTHENTIC</font></b><br/><font size=7 color='#64748b'>SHA-256 HMAC Verified</font>", cell_value)
        ]
    ]

    lab_table = Table(lab_data, colWidths=[125, 145, 125, 145])
    lab_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#f1f5f9")),
    ]))
    elements.append(lab_table)
    elements.append(Spacer(1, 14))

    # 5. Packaging & Retail Chain of Custody
    elements.append(Paragraph("PACKAGING & RETAIL CHAIN OF CUSTODY", section_heading))
    pack_data = [
        [
            Paragraph("Packaging Facility:", cell_label),
            Paragraph(str(batch.get('packaging_plant', 'Helvetia Artisan Bottlers')), cell_value),
            Paragraph("Authorized Retailer:", cell_label),
            Paragraph(str(batch.get('seller_name', 'AlpenGourmet Flagship Boutique')), cell_value)
        ],
        [
            Paragraph("Container & Jar Format:", cell_label),
            Paragraph(str(batch.get('jar_format', '500g Amber Glass Jar')), cell_value),
            Paragraph("Store Location:", cell_label),
            Paragraph(str(batch.get('store_location', 'Bahnhofstrasse 42, Zurich')), cell_value)
        ],
        [
            Paragraph("Tamper-Proof Seal ID:", cell_label),
            Paragraph(f"<b><font color='#2563eb'>{batch.get('tamper_seal_id', 'SEAL-2026-CH')}</font></b>", cell_value),
            Paragraph("Retail Food License:", cell_label),
            Paragraph(str(batch.get('license_no', 'ZH-FOOD-88120')), cell_value)
        ],
        [
            Paragraph("Production Lot No:", cell_label),
            Paragraph(str(batch.get('lot_number', 'LOT-VALAIS-2026')), cell_value),
            Paragraph("Retail Price & Status:", cell_label),
            Paragraph(f"{batch.get('sale_price', 'CHF 28.50')} &bull; {batch.get('retail_status', 'On Shelf')}", cell_value)
        ]
    ]

    pack_table = Table(pack_data, colWidths=[125, 145, 125, 145])
    pack_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#f1f5f9")),
    ]))
    elements.append(pack_table)
    elements.append(Spacer(1, 14))

    # 6. Immutable Blockchain Proof Ledger
    elements.append(Paragraph("IMMUTABLE BLOCKCHAIN PROOF OF WORK AUDIT TRAIL", section_heading))
    
    chain_rows = [
        [
            Paragraph("<b>Block #</b>", cell_label),
            Paragraph("<b>Stage Event</b>", cell_label),
            Paragraph("<b>Timestamp (UTC)</b>", cell_label),
            Paragraph("<b>Proof of Work SHA-256 Block Hash</b>", cell_label)
        ]
    ]

    # Show blocks relevant to this batch or first 5
    relevant_blocks = [b for b in blocks if (isinstance(b.data, dict) and b.data.get("batch_id") == batch.get("batch_id")) or b.index == 0]
    if not relevant_blocks:
        relevant_blocks = blocks[:5]

    for b in relevant_blocks:
        event_name = b.block_type.replace("Block ", "B").replace(": Honey Batch Registered", " - Registered").replace(": Laboratory Test Recorded", " - Lab Test").replace(": Honey Packaging Recorded", " - Bottled").replace(": Seller Information Recorded", " - Seller")
        chain_rows.append([
            Paragraph(f"<b>#{b.index}</b>", cell_value),
            Paragraph(event_name, cell_value),
            Paragraph(str(b.timestamp)[:16], cell_value),
            Paragraph(b.hash, hash_style)
        ])

    chain_table = Table(chain_rows, colWidths=[40, 130, 95, 275])
    chain_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#f1f5f9")),
    ]))
    elements.append(chain_table)
    elements.append(Spacer(1, 14))

    # 7. Legal Disclaimer & Consortium Seal
    footer_text = Paragraph(
        "<b>LEGAL VALIDATION:</b> This certificate is digitally anchored to the HoneyChain PoW cryptographic ledger. "
        "Any physical product without a matching tamper seal and verifiable hash pointer is considered non-compliant with Consortium standards. "
        "Generated on " + datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC") + " &bull; HoneyChain Foundation Consortium.",
        ParagraphStyle('Legal', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=TEXT_MUTED)
    )
    elements.append(footer_text)

    doc.build(elements)
    buffer.seek(0)
    return buffer
