from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.schemas.advisor import RecommendationResponse, QuestionnaireInput
from app.core.config import REPORTS_DIR

def generate_pdf_report(rec: RecommendationResponse, q: QuestionnaireInput) -> Path:
    filename = f"CloudForge_Report_{rec.report_id}.pdf"
    pdf_path = REPORTS_DIR / filename
    
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=10
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'BulletPoint',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1e293b')
    )

    story = []

    # Title & Header
    story.append(Paragraph("CloudForge Architecture & Multi-Cloud Specification Report", title_style))
    story.append(Paragraph(f"Report ID: <b>{rec.report_id}</b> &bull; Generated: {rec.created_at[:10]} &bull; Environment: <b>{q.environment.upper()}</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(rec.executive_summary, body_style))
    story.append(Spacer(1, 4))

    # Sizing Summary Cards Table
    summary_data = [
        [
            Paragraph("<b>Recommended Tier</b>", table_cell_style),
            Paragraph(rec.recommended_tier, table_cell_style),
            Paragraph("<b>Est. Monthly Cost</b>", table_cell_style),
            Paragraph(f"<b>${rec.estimated_monthly_cost:.2f} USD</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Compute Sizing</b>", table_cell_style),
            Paragraph(f"{rec.compute_sizing['instance_count']}x {rec.compute_sizing['instance_family']} ({rec.compute_sizing['vcpu_total']} vCPU / {rec.compute_sizing['ram_total_gb']} GB)", table_cell_style),
            Paragraph("<b>Est. Annual Cost</b>", table_cell_style),
            Paragraph(f"${rec.estimated_annual_cost:.2f} USD", table_cell_style),
        ],
        [
            Paragraph("<b>Database</b>", table_cell_style),
            Paragraph(f"{rec.database_sizing['engine'].title()} ({rec.database_sizing['allocated_storage_gb']} GB, Multi-AZ: {rec.database_sizing['multi_az']})", table_cell_style),
            Paragraph("<b>Multi-Cloud Lowest</b>", table_cell_style),
            Paragraph(f"<b>{rec.multi_cloud_comparison.get('cheapest_cloud', 'GCP')} (${rec.multi_cloud_comparison.get('gcp_monthly_usd', rec.estimated_monthly_cost):.2f}/mo)</b>", table_cell_style),
        ]
    ]
    t_sum = Table(summary_data, colWidths=[1.4*inch, 2.3*inch, 1.4*inch, 1.8*inch])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 6))

    # Recommended Services Breakdown
    story.append(Paragraph("2. Recommended Primary Services (AWS Baseline)", h1_style))
    service_table_data = [
        [
            Paragraph("Service", table_header_style),
            Paragraph("Category", table_header_style),
            Paragraph("Configuration Details", table_header_style),
            Paragraph("Rationale", table_header_style),
        ]
    ]
    for s in rec.recommended_services:
        service_table_data.append([
            Paragraph(f"<b>{s.service_name}</b>", table_cell_style),
            Paragraph(s.category, table_cell_style),
            Paragraph(s.configuration_details, table_cell_style),
            Paragraph(s.rationale, table_cell_style),
        ])
    t_services = Table(service_table_data, colWidths=[1.5*inch, 1.0*inch, 2.2*inch, 2.2*inch])
    t_services.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e40af')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_services)
    story.append(Spacer(1, 8))

    # Page Break for clean layout
    story.append(PageBreak())

    # Multi-Cloud Equivalents Table
    story.append(Paragraph("3. Multi-Cloud Architecture Equivalents (AWS vs. Azure vs. GCP)", h1_style))
    story.append(Paragraph("Direct cross-cloud service mappings to facilitate multi-cloud deployment or cloud migration without re-architecting application logic:", body_style))
    
    mc_data = [
        [
            Paragraph("Component Tier", table_header_style),
            Paragraph("AWS Service", table_header_style),
            Paragraph("Azure Equivalent", table_header_style),
            Paragraph("Google Cloud (GCP)", table_header_style),
            Paragraph("Portability Strategy", table_header_style),
        ]
    ]
    for m in rec.multi_cloud_mapping:
        mc_data.append([
            Paragraph(f"<b>{m.tier_component}</b>", table_cell_style),
            Paragraph(m.aws_service, table_cell_style),
            Paragraph(m.azure_service, table_cell_style),
            Paragraph(m.gcp_service, table_cell_style),
            Paragraph(m.portability_guidance, table_cell_style),
        ])
    t_mc = Table(mc_data, colWidths=[1.1*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.6*inch])
    t_mc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f766e')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_mc)
    story.append(Spacer(1, 8))

    # Multi-Cloud Cost Arbitrage Box
    if rec.multi_cloud_comparison:
        story.append(Paragraph("<b>Cross-Cloud Monthly Spend Comparison:</b>", h1_style))
        mcc_data = [
            [
                Paragraph("<b>Amazon Web Services (AWS)</b>", table_cell_style),
                Paragraph(f"${rec.multi_cloud_comparison.get('aws_monthly_usd', 0):.2f} / month", table_cell_style),
                Paragraph("Standard EC2 / gp3 / RDS / ALB baseline", table_cell_style),
            ],
            [
                Paragraph("<b>Microsoft Azure</b>", table_cell_style),
                Paragraph(f"${rec.multi_cloud_comparison.get('azure_monthly_usd', 0):.2f} / month", table_cell_style),
                Paragraph("Standard B/D VM, Flexible Server, Blob Hot", table_cell_style),
            ],
            [
                Paragraph("<b>Google Cloud Platform (GCP)</b>", table_cell_style),
                Paragraph(f"<b>${rec.multi_cloud_comparison.get('gcp_monthly_usd', 0):.2f} / month</b>", table_cell_style),
                Paragraph(f"Lowest on-demand tier (Saves ${rec.multi_cloud_comparison.get('monthly_delta_usd', 0):.2f}/mo vs AWS)", table_cell_style),
            ],
        ]
        t_mcc = Table(mcc_data, colWidths=[2.2*inch, 1.6*inch, 3.1*inch])
        t_mcc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_mcc)
        story.append(Spacer(1, 8))

    # Implementation Roadmap & Security
    story.append(Paragraph("4. Step-by-Step Implementation Roadmap", h1_style))
    for step in rec.step_by_step_implementation_plan:
        story.append(Paragraph(step, bullet_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5. Identified Risks & Potential Bottlenecks", h1_style))
    for rsk in rec.risks_and_bottlenecks:
        story.append(Paragraph(f"&bull; {rsk}", bullet_style))
    story.append(Spacer(1, 10))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94a3b8'), spaceAfter=6))
    story.append(Paragraph(
        "<i>CloudForge Multi-Cloud Architectural Specification. Evaluated with deterministic workload modeling. "
        "Estimated costs reflect official On-Demand published rates for 2026.</i>",
        body_style
    ))

    doc.build(story)
    return pdf_path
