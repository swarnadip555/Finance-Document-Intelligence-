import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sample_pdfs():
    output_dir = Path("data/uploads")
    output_dir.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#475569'),
        spaceAfter=14
    )
    heading2_style = ParagraphStyle(
        'Head2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    # 1. Apex Global Technologies FY 2024-25
    pdf_path_1 = output_dir / "apex_technologies_annual_report_fy25.pdf"
    doc1 = SimpleDocTemplate(str(pdf_path_1), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story1 = []

    # Page 1: Cover & MD&A
    story1.append(Paragraph("APEX GLOBAL TECHNOLOGIES LIMITED", title_style))
    story1.append(Paragraph("Annual Integrated Report & Financial Statements | Fiscal Year 2024-25 (Figures in ₹ Crores)", subtitle_style))
    story1.append(Spacer(1, 10))
    story1.append(Paragraph("Management Discussion & Analysis (MD&A)", heading2_style))
    story1.append(Paragraph(
        "During FY 2024-25, Apex Global Technologies continued its expansion into artificial intelligence enterprise platforms "
        "and digital engineering solutions. Consolidated revenues increased through strong order bookings across North America and Europe. "
        "The company maintained a resilient balance sheet characterized by conservative leverage and sustained investments in research and development. "
        "Working capital management remained a key focus area, ensuring liquidity despite industry-wide software project billing cycles.",
        body_style
    ))
    story1.append(Paragraph(
        "Risk Factors and Forward-Looking Disclosures:\n"
        "Key risks monitored by the Board include foreign currency fluctuations against the US Dollar and Euro, geopolitical supply friction "
        "in semiconductor procurement, and competitive wage pressures for elite machine learning talent. Operating cash conversion was impacted "
        "by delayed milestone receivables from select public-sector clients.",
        body_style
    ))
    story1.append(PageBreak())

    # Page 2: Statement of Profit and Loss (Income Statement)
    story1.append(Paragraph("Statement of Profit and Loss", heading2_style))
    story1.append(Paragraph("For the year ended March 31, 2025 (All amounts in ₹ Crores)", subtitle_style))

    pnl_data = [
        ["Particulars", "FY 2024-25", "FY 2023-24"],
        ["Revenue from operations", "14,500.00", "12,200.00"],
        ["Other income", "420.00", "350.00"],
        ["Total Revenue", "14,920.00", "12,550.00"],
        ["Cost of goods sold", "8,200.00", "7,100.00"],
        ["Gross Profit", "6,300.00", "5,100.00"],
        ["Operating Expenses", "2,600.00", "2,200.00"],
        ["Operating Profit (EBIT)", "3,700.00", "2,900.00"],
        ["Finance costs", "240.00", "210.00"],
        ["Depreciation and amortisation", "680.00", "580.00"],
        ["Profit before tax", "3,200.00", "2,460.00"],
        ["Tax expense", "780.00", "600.00"],
        ["Net Profit for the year", "2,420.00", "1,860.00"]
    ]
    t_pnl = Table(pnl_data, colWidths=[240, 140, 140])
    t_pnl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
    ]))
    story1.append(t_pnl)
    story1.append(PageBreak())

    # Page 3: Balance Sheet
    story1.append(Paragraph("Balance Sheet (Statement of Financial Position)", heading2_style))
    story1.append(Paragraph("As at March 31, 2025 (All amounts in ₹ Crores)", subtitle_style))

    bs_data = [
        ["Particulars", "FY 2024-25", "FY 2023-24"],
        ["Total Current Assets", "8,900.00", "7,400.00"],
        ["Cash and cash equivalents", "2,150.00", "1,820.00"],
        ["Trade receivables", "3,450.00", "2,880.00"],
        ["Inventories", "1,200.00", "980.00"],
        ["Non-Current Assets", "11,600.00", "10,200.00"],
        ["Total Assets", "20,500.00", "17,600.00"],
        ["Total Current Liabilities", "4,800.00", "4,100.00"],
        ["Short-term borrowings", "1,100.00", "950.00"],
        ["Trade payables", "2,400.00", "2,150.00"],
        ["Long-term borrowings", "2,200.00", "1,900.00"],
        ["Total Borrowings (Debt)", "3,300.00", "2,850.00"],
        ["Total Liabilities", "8,500.00", "7,300.00"],
        ["Shareholders' Equity", "12,000.00", "10,300.00"],
        ["Total Liabilities & Equity", "20,500.00", "17,600.00"]
    ]
    t_bs = Table(bs_data, colWidths=[240, 140, 140])
    t_bs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
    ]))
    story1.append(t_bs)
    story1.append(PageBreak())

    # Page 4: Cash Flow Statement
    story1.append(Paragraph("Statement of Cash Flows", heading2_style))
    story1.append(Paragraph("For the year ended March 31, 2025 (All amounts in ₹ Crores)", subtitle_style))

    cf_data = [
        ["Particulars", "FY 2024-25", "FY 2023-24"],
        ["Operating cash flow (CFO)", "2,850.00", "2,310.00"],
        ["Net cash used in investing activities", "-1,420.00", "-1,150.00"],
        ["Purchase of property, plant and equipment", "-1,100.00", "-890.00"],
        ["Net cash used in financing activities", "-1,100.00", "-920.00"],
        ["Net change in cash", "330.00", "240.00"],
        ["Closing Cash and Cash Equivalents", "2,150.00", "1,820.00"]
    ]
    t_cf = Table(cf_data, colWidths=[240, 140, 140])
    t_cf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
    ]))
    story1.append(t_cf)
    doc1.build(story1)

    # 2. BlueHorizon Maritime Logistics (Higher risk demo document)
    pdf_path_2 = output_dir / "bluehorizon_maritime_credit_report_fy25.pdf"
    doc2 = SimpleDocTemplate(str(pdf_path_2), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story2 = []
    story2.append(Paragraph("BLUEHORIZON MARITIME LOGISTICS CORP", title_style))
    story2.append(Paragraph("Credit Assessment & Annual Financial Filing | FY 2024-25 (Amounts in USD Millions)", subtitle_style))
    story2.append(Spacer(1, 10))
    story2.append(Paragraph("Business Summary & Industry Challenges", heading2_style))
    story2.append(Paragraph(
        "BlueHorizon Maritime Logistics operates container feeder routes across Southeast Asia. "
        "During FY25, spot container charter rates experienced severe downward volatility while bunker fuel costs rose sharply. "
        "To finance fleet modernization, short-term and syndicated long-term debt facilities were tapped, leading to higher financial leverage. "
        "Operating cash flows declined due to delayed port turnarounds and customer credit extension.",
        body_style
    ))
    story2.append(PageBreak())

    story2.append(Paragraph("Consolidated Statement of Operations", heading2_style))
    pnl2_data = [
        ["Particulars", "FY 2024-25", "FY 2023-24"],
        ["Total Revenue", "850.00", "980.00"],
        ["Cost of goods sold", "690.00", "710.00"],
        ["Gross Profit", "160.00", "270.00"],
        ["Operating Expenses", "95.00", "90.00"],
        ["Operating Profit (EBIT)", "65.00", "180.00"],
        ["Finance costs", "48.00", "32.00"],
        ["Net Profit", "12.00", "110.00"]
    ]
    t2_pnl = Table(pnl2_data, colWidths=[240, 140, 140])
    t2_pnl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
    ]))
    story2.append(t2_pnl)
    story2.append(Spacer(1, 15))

    story2.append(Paragraph("Consolidated Balance Sheet", heading2_style))
    bs2_data = [
        ["Particulars", "FY 2024-25", "FY 2023-24"],
        ["Total Current Assets", "210.00", "280.00"],
        ["Cash and cash equivalents", "35.00", "75.00"],
        ["Trade receivables", "125.00", "140.00"],
        ["Total Assets", "1,250.00", "1,180.00"],
        ["Total Current Liabilities", "260.00", "210.00"],
        ["Total Borrowings (Debt)", "680.00", "520.00"],
        ["Total Liabilities", "870.00", "710.00"],
        ["Shareholders' Equity", "380.00", "470.00"]
    ]
    t2_bs = Table(bs2_data, colWidths=[240, 140, 140])
    t2_bs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
    ]))
    story2.append(t2_bs)
    story2.append(Spacer(1, 15))

    story2.append(Paragraph("Operating Cash Flows", heading2_style))
    cf2_data = [
        ["Particulars", "FY 2024-25", "FY 2023-24"],
        ["Operating cash flow", "4.50", "95.00"],
        ["Capital expenditure", "-120.00", "-80.00"]
    ]
    t2_cf = Table(cf2_data, colWidths=[240, 140, 140])
    t2_cf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
    ]))
    story2.append(t2_cf)
    doc2.build(story2)

    print("Sample PDFs successfully created:")
    print(" -", pdf_path_1)
    print(" -", pdf_path_2)

if __name__ == "__main__":
    generate_sample_pdfs()

