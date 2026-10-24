"""
AgriVersion - Diagnostic PDF Report Generation Service
Generates comprehensive pathology reports using ReportLab with side-by-side images,
Grad-CAM overlays, quantitative lesion metrics, and scientifically verified management advisories.
"""

import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.units import inch

from backend.config import Config


def generate_diagnostic_pdf_report(prediction_data, user_data=None, farm_data=None):
    """
    Creates a downloadable scientific PDF report for a rice disease prediction.
    
    Args:
        prediction_data: dict containing disease, confidence, confidence_level, severity, symptoms, management, etc.
        user_data: dict containing farmer name, email, location.
        farm_data: dict containing farm name, field name, crop variety.
        
    Returns:
        (success: bool, pdf_filename: str, pdf_path: str)
    """
    report_id = f"AGRI-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    pdf_filename = f"Report_{report_id}.pdf"
    pdf_path = os.path.join(Config.REPORTS_FOLDER, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#065f46'),
        alignment=0,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#047857'),
        fontName='Helvetica'
    )
    section_heading = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading2'],
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#065f46'),
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1f2937'),
        fontName='Helvetica'
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Italic'],
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#6b7280'),
        fontName='Helvetica-Oblique'
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("<b>🌾 AgriVersion Diagnostic Suite</b><br/><font size=8 color='#047857'>AI Rice Pathology & Explainable Diagnostic Center</font>", title_style),
            Paragraph(f"<b>Report ID:</b> {report_id}<br/><b>Generated:</b> {datetime.utcnow().strftime('%d-%b-%Y %H:%M UTC')}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 3.0 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#10b981'), spaceAfter=8))

    # 2. Metadata Table
    user_name = user_data.get("full_name", "Registered Farmer") if user_data else "Registered Farmer"
    user_loc = user_data.get("location", "Field Region") if user_data else "Field Region"
    farm_name = farm_data.get("farm_name", "Main Paddy Field") if farm_data else "Main Paddy Field"
    field_name = farm_data.get("field_name", "Plot 1") if farm_data else "Plot 1"
    crop_var = farm_data.get("crop_variety", "Oryza sativa (Paddy)") if farm_data else "Oryza sativa (Paddy)"

    meta_data = [
        [Paragraph("<b>Farmer / Operator:</b>", body_style), Paragraph(user_name, body_style),
         Paragraph("<b>Farm Location:</b>", body_style), Paragraph(user_loc, body_style)],
        [Paragraph("<b>Paddy Farm:</b>", body_style), Paragraph(farm_name, body_style),
         Paragraph("<b>Plot / Field:</b>", body_style), Paragraph(f"{field_name} ({crop_var})", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[1.5 * inch, 2.2 * inch, 1.4 * inch, 2.1 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#a7f3d0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 3. Diagnostic Result Box
    disease_name = prediction_data.get("primary_disease", prediction_data.get("disease_name", "Unknown"))
    conf_val = prediction_data.get("confidence", 90.0)
    conf_level = prediction_data.get("confidence_level", "High" if conf_val >= 85 else ("Moderate" if conf_val >= 60 else "Low"))

    sev_data = prediction_data.get("severity", {})
    if isinstance(sev_data, dict):
        sev_level = sev_data.get("severity_level", prediction_data.get("severity_level", "Low"))
        healthy_pct = sev_data.get("healthy_area_pct", prediction_data.get("healthy_area_pct", 90.0))
        affected_pct = sev_data.get("affected_area_pct", prediction_data.get("affected_area_pct", 10.0))
        lesion_count = sev_data.get("lesion_count", prediction_data.get("lesion_count", 0))
    else:
        sev_level = prediction_data.get("severity_level", "Low")
        healthy_pct = prediction_data.get("healthy_area_pct", 90.0)
        affected_pct = prediction_data.get("affected_area_pct", 10.0)
        lesion_count = prediction_data.get("lesion_count", 0)

    conf_color = "#10b981" if conf_level == "High" else ("#f59e0b" if conf_level == "Moderate" else "#ef4444")
    sev_color = "#10b981" if sev_level == "Healthy" else ("#3b82f6" if sev_level == "Low" else ("#f59e0b" if sev_level == "Mild" else "#ef4444"))

    pathogen_text = f"{prediction_data.get('scientific_name', '')} | {prediction_data.get('pathogen_type', '')}" if disease_name != "Healthy Rice Leaf" else "Normal Foliar Morphology (No Pathogens Detected)"

    diag_data = [
        [
            Paragraph(f"<b>IDENTIFIED CONDITION:</b><br/><font size=13 color='#065f46'><b>{disease_name}</b></font><br/>"
                      f"<font size=8 color='#4b5563'><i>{pathogen_text}</i></font>", body_style),
            Paragraph(f"<b>Model Confidence:</b> <font size=11 color='{conf_color}'><b>{conf_val:.2f}% ({conf_level.upper()})</b></font><br/>"
                      f"<b>Severity Level:</b> <font size=10 color='{sev_color}'><b>{sev_level.upper()}</b></font><br/>"
                      f"<font size=8>Healthy: <b>{healthy_pct}%</b> | Lesion Area: <b>{affected_pct}%</b> | Lesions: <b>{lesion_count}</b></font>", body_style)
        ]
    ]
    diag_table = Table(diag_data, colWidths=[4.2 * inch, 3.0 * inch])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecfdf5')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#10b981')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 8))

    # 4. Side-by-Side Visual Images (Original Leaf + Grad-CAM Heatmap + Mask)
    img_cells = []
    orig_filename = prediction_data.get("image_filename")
    grad_filename = prediction_data.get("gradcam_overlay_filename") or prediction_data.get("gradcam_filename")
    mask_filename = prediction_data.get("severity_mask_filename")

    if orig_filename:
        orig_path = os.path.join(Config.UPLOAD_FOLDER, orig_filename)
        if os.path.exists(orig_path):
            img_cells.append([
                Paragraph("<b>Original Leaf Specimen</b>", body_bold),
                RLImage(orig_path, width=2.3 * inch, height=1.7 * inch)
            ])

    if grad_filename:
        grad_path = os.path.join(Config.UPLOAD_FOLDER, grad_filename)
        if os.path.exists(grad_path):
            img_cells.append([
                Paragraph("<b>AI Attention (Grad-CAM)</b>", body_bold),
                RLImage(grad_path, width=2.3 * inch, height=1.7 * inch)
            ])

    if mask_filename:
        mask_path = os.path.join(Config.UPLOAD_FOLDER, mask_filename)
        if os.path.exists(mask_path):
            img_cells.append([
                Paragraph("<b>Lesion Color Mask</b>", body_bold),
                RLImage(mask_path, width=2.3 * inch, height=1.7 * inch)
            ])

    if len(img_cells) >= 2:
        cols = [img_cells[0][0], img_cells[1][0]]
        imgs = [img_cells[0][1], img_cells[1][1]]
        col_w = [3.6 * inch, 3.6 * inch]
        if len(img_cells) == 3:
            cols.append(img_cells[2][0])
            imgs.append(img_cells[2][1])
            col_w = [2.4 * inch, 2.4 * inch, 2.4 * inch]

        img_table_data = [cols, imgs]
        img_table = Table(img_table_data, colWidths=col_w)
        img_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
            ('TOPPADDING', (0, 1), (-1, 1), 2),
        ]))
        story.append(img_table)
        story.append(Spacer(1, 6))

    # 5. Observed Symptoms (Image-derived)
    story.append(Paragraph("1. Observed Symptoms (From Submitted Image)", section_heading))
    symptoms_text = prediction_data.get("symptoms") or "Visual foliar inspection indicates symptoms consistent with the diagnosed profile."
    story.append(Paragraph(symptoms_text, body_style))
    story.append(Spacer(1, 4))

    # 6. Favorable Conditions & Contributing Factors
    story.append(Paragraph("2. Likely Favorable Environmental & Agronomic Factors", section_heading))
    fav_text = prediction_data.get("favorable_conditions") or "Warm humid weather and prolonged leaf wetness."
    cont_text = prediction_data.get("contributing_factors") or "Soil nutrient imbalances and susceptible cultivars."
    story.append(Paragraph(f"<b>Environmental Conditions:</b> {fav_text}", body_style))
    story.append(Paragraph(f"<b>Possible Contributing Factors:</b> {cont_text}", body_style))
    story.append(Spacer(1, 4))

    # 7. Prevention & Evidence-Based Management
    story.append(Paragraph("3. Preventive Cultural Practices & Evidence-Based Management", section_heading))
    prev_text = prediction_data.get("prevention") or "Maintain balanced N-P-K fertilizer split applications and proper plant spacing."
    mgmt_text = prediction_data.get("management") or "Apply registered fungicides/bactericides according to official extension guidelines."
    story.append(Paragraph(f"<b>Prevention:</b> {prev_text}", body_style))
    story.append(Paragraph(f"<b>Management:</b> {mgmt_text}", body_style))
    story.append(Spacer(1, 4))

    # 8. Expert Consultation
    story.append(Paragraph("4. When to Consult an Agricultural Expert", section_heading))
    exp_text = prediction_data.get("expert_consultation") or "Seek expert agronomist consultation if foliar symptoms exceed economic damage thresholds."
    story.append(Paragraph(exp_text, body_style))
    story.append(Spacer(1, 6))

    # 9. Official Disclaimers
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#d1d5db'), spaceAfter=4))
    disclaimer = (
        "<b>IMPORTANT AGRICULTURAL NOTICE:</b> AgriVersion AI provides image-based automated decision support. "
        "Model confidence represents statistical pattern matching, not a definitive laboratory culture. "
        "Chemical treatments must follow official agricultural authority advice and product container labels."
    )
    story.append(Paragraph(disclaimer, disclaimer_style))

    try:
        doc.build(story)
        return True, pdf_filename, pdf_path
    except Exception as e:
        print(f"PDF Build Error: {e}")
        return False, "", str(e)
