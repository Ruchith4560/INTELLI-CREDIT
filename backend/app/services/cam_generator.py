import os
from datetime import datetime
from typing import Dict, Any

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_cam_pdf(report_data: Dict[str, Any], session_id: str) -> str:
    """Generate CAM PDF using ReportLab"""
    output_path = os.path.join(OUTPUT_DIR, f"CAM_{session_id[:8]}.pdf")
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                     fontSize=20, spaceAfter=12,
                                     textColor=colors.HexColor('#1a1a2e'))
        
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                       fontSize=14, spaceAfter=8,
                                       textColor=colors.HexColor('#16213e'),
                                       borderPad=4)
        
        body_style = ParagraphStyle('CustomBody', parent=styles['Normal'],
                                    fontSize=11, spaceAfter=6,
                                    alignment=TA_JUSTIFY)
        
        green_style = ParagraphStyle('Green', parent=styles['Normal'],
                                     fontSize=12, textColor=colors.HexColor('#22c55e'))
        
        red_style = ParagraphStyle('Red', parent=styles['Normal'],
                                   fontSize=12, textColor=colors.HexColor('#ef4444'))
        
        story = []
        company = report_data.get("company_name", "Company Name")
        decision = report_data.get("decision", "REVIEW")
        risk_score = report_data.get("risk_score", 50)
        loan_amount = report_data.get("loan_amount", 0)
        interest_rate = report_data.get("interest_rate", 0)
        
        # Header
        story.append(Paragraph("INTELLI-CREDIT", ParagraphStyle('IC', parent=styles['Title'],
                                fontSize=24, textColor=colors.HexColor('#22c55e'), alignment=TA_CENTER)))
        story.append(Paragraph("AI-Powered Credit Appraisal Memo (CAM)", 
                               ParagraphStyle('Sub', parent=styles['Normal'], fontSize=13,
                               alignment=TA_CENTER, textColor=colors.HexColor('#64748b'))))
        story.append(Spacer(1, 0.2*inch))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#22c55e')))
        story.append(Spacer(1, 0.2*inch))
        
        # Cover Info Table
        cover_data = [
            ["Borrower:", company],
            ["Date:", datetime.now().strftime("%d %B %Y")],
            ["Report ID:", session_id[:12].upper()],
            ["Prepared By:", "Intelli-Credit AI Engine v1.0"],
            ["Classification:", "CONFIDENTIAL"]
        ]
        cover_table = Table(cover_data, colWidths=[2.5*inch, 4*inch])
        cover_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(cover_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Decision Banner
        decision_color = colors.HexColor('#22c55e') if decision == 'APPROVE' else \
                        colors.HexColor('#f59e0b') if decision == 'REVIEW' else \
                        colors.HexColor('#ef4444')
        
        banner_data = [[f"CREDIT DECISION: {decision}  |  Risk Score: {risk_score:.1f}/100  |  {'Loan: ₹' + str(loan_amount) + ' Cr @ ' + str(interest_rate) + '%' if decision != 'REJECT' else 'Application Declined'}"]]
        banner_table = Table(banner_data, colWidths=[6.5*inch])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), decision_color),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 13),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('BORDERRADIUS', (0,0), (-1,-1), 8),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 0.3*inch))
        
        # 1. Executive Summary
        story.append(Paragraph("1. EXECUTIVE SUMMARY", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(report_data.get("explanation_text", "Analysis complete.").replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # 2. Five Cs of Credit
        story.append(Paragraph("2. FIVE Cs OF CREDIT ANALYSIS", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 0.1*inch))
        
        five_cs = report_data.get("risk_breakdown", {}).get("five_cs", {})
        cs_data = [["C Factor", "Score", "Assessment"]]
        cs_names = {"character": "Character", "capacity": "Capacity", "capital": "Capital", 
                   "collateral": "Collateral", "conditions": "Conditions"}
        for key, label in cs_names.items():
            c = five_cs.get(key, {})
            score = c.get("score", 60)
            summary = c.get("summary", "Assessment in progress")[:80]
            cs_data.append([label, f"{score:.0f}/100", summary])
        
        cs_table = Table(cs_data, colWidths=[1.5*inch, 1*inch, 4*inch])
        cs_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(cs_table)
        story.append(Spacer(1, 0.2*inch))
        
        # 3. Financial Ratios
        story.append(Paragraph("3. KEY FINANCIAL RATIOS", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 0.1*inch))
        
        ratios = report_data.get("financial_ratios", {})
        ratio_data = [
            ["Ratio", "Value", "Benchmark", "Status"],
            ["Current Ratio", f"{ratios.get('current_ratio', 'N/A')}", "> 1.3", "✓" if ratios.get('current_ratio', 0) > 1.3 else "✗"],
            ["Debt-to-Equity", f"{ratios.get('debt_to_equity', 'N/A')}", "< 2.0", "✓" if ratios.get('debt_to_equity', 999) < 2.0 else "✗"],
            ["Interest Coverage", f"{ratios.get('interest_coverage', 'N/A')}x", "> 2.5x", "✓" if ratios.get('interest_coverage', 0) > 2.5 else "✗"],
            ["EBITDA Margin", f"{ratios.get('ebitda_margin', 'N/A')}%", "> 10%", "✓" if ratios.get('ebitda_margin', 0) > 10 else "✗"],
            ["Net Profit Margin", f"{ratios.get('net_profit_margin', 'N/A')}%", "> 5%", "✓" if ratios.get('net_profit_margin', 0) > 5 else "✗"],
            ["Revenue Growth", f"{ratios.get('revenue_growth', 'N/A')}%", "> 0%", "✓" if ratios.get('revenue_growth', 0) > 0 else "✗"],
        ]
        
        ratio_table = Table(ratio_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
        ratio_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(ratio_table)
        story.append(Spacer(1, 0.2*inch))
        
        # 4. Risk Breakdown
        story.append(Paragraph("4. RISK BREAKDOWN", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 0.1*inch))
        
        risk_breakdown = report_data.get("risk_breakdown", {}).get("risk_scores", {})
        rb_data = [["Risk Category", "Score", "Level"]]
        for k, v in risk_breakdown.items():
            level = "LOW" if v < 30 else "MEDIUM" if v < 55 else "HIGH"
            rb_data.append([k.replace("_", " ").title(), f"{v:.1f}/100", level])
        
        if len(rb_data) > 1:
            rb_table = Table(rb_data, colWidths=[2.5*inch, 2*inch, 2*inch])
            rb_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            story.append(rb_table)
        
        story.append(Spacer(1, 0.2*inch))
        
        # 5. Final Recommendation
        story.append(Paragraph("5. FINAL RECOMMENDATION", heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Spacer(1, 0.1*inch))
        
        if decision == "APPROVE":
            rec_text = f"""
            Based on the comprehensive AI-driven analysis, the credit application of <b>{company}</b> is 
            recommended for <b>APPROVAL</b> with the following terms:<br/><br/>
            • <b>Sanctioned Limit:</b> ₹{loan_amount:.2f} Crore<br/>
            • <b>Interest Rate:</b> {interest_rate:.2f}% per annum<br/>
            • <b>Risk Score:</b> {risk_score:.1f}/100<br/><br/>
            Standard covenants and quarterly monitoring recommended.
            """
        elif decision == "REVIEW":
            rec_text = f"""
            The credit application requires <b>SENIOR MANAGEMENT REVIEW</b> before proceeding.<br/><br/>
            • <b>Tentative Limit (subject to review):</b> ₹{loan_amount:.2f} Crore<br/>
            • <b>Risk Score:</b> {risk_score:.1f}/100<br/><br/>
            Additional due diligence and clarifications required before final sanction.
            """
        else:
            rec_text = f"""
            Based on the risk assessment, the credit application of <b>{company}</b> has been 
            <b>DECLINED</b> due to high risk indicators.<br/><br/>
            • <b>Risk Score:</b> {risk_score:.1f}/100 (above acceptable threshold)<br/><br/>
            The applicant may reapply after a minimum cooling period of 6 months with improved financials.
            """
        
        story.append(Paragraph(rec_text, body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        story.append(Paragraph(
            f"This CAM was generated by Intelli-Credit AI Engine | Generated: {datetime.now().strftime('%d %b %Y %H:%M')} | CONFIDENTIAL",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                          textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
        ))
        
        doc.build(story)
        
    except ImportError:
        # Fallback: create a simple text file
        output_path = output_path.replace(".pdf", ".txt")
        with open(output_path, "w") as f:
            f.write(f"CREDIT APPRAISAL MEMO\n{'='*50}\n")
            f.write(f"Company: {report_data.get('company_name')}\n")
            f.write(f"Decision: {report_data.get('decision')}\n")
            f.write(f"Risk Score: {report_data.get('risk_score')}\n")
            f.write(f"Loan Amount: {report_data.get('loan_amount')} Crore\n")
            f.write(f"Interest Rate: {report_data.get('interest_rate')}%\n\n")
            f.write(report_data.get("explanation_text", ""))
    
    return output_path
