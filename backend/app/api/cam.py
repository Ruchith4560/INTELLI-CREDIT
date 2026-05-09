from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os, logging
from app.database import get_db
from app import models
from app.utils.auth import get_current_user
from app.services.cam_generator import generate_cam_pdf

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate/{session_id}")
def generate_cam(
    session_id:   str,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    risk = db.query(models.RiskScore).filter(models.RiskScore.session_id == session_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Analysis not found. Run credit analysis first.")

    feat = db.query(models.ExtractedFeature).filter(
        models.ExtractedFeature.session_id == session_id
    ).first()

    report_data = {
        "company_name":     risk.company_name,
        "risk_score":       risk.risk_score,
        "decision":         risk.decision,
        "loan_amount":      risk.loan_amount,
        "interest_rate":    risk.interest_rate,
        "scoring_method":   risk.scoring_method or "Rule-Based",
        "risk_breakdown":   risk.risk_breakdown  or {},
        "shap_values":      risk.shap_values     or {},
        "explanation_text": risk.llm_explanation or "",
        "news_sentiment":   risk.news_sentiment  or {},
        "litigation_risk":  risk.litigation_risk or {},
        "financial_ratios": feat.financial_ratios  if feat else {},
        "qualitative_notes":feat.qualitative_notes if feat else "",
        "analyst_name":     current_user.name,
    }

    output_path = generate_cam_pdf(report_data, session_id)

    # Remove old record, save new one
    old_cam = db.query(models.CAMReport).filter(models.CAMReport.session_id == session_id).first()
    if old_cam:
        db.delete(old_cam)
        db.commit()

    cam = models.CAMReport(
        session_id   = session_id,
        company_name = risk.company_name,
        file_path    = output_path,
        report_data  = report_data,
    )
    db.add(cam)
    db.commit()

    logger.info(f"✅ CAM generated for {risk.company_name}: {output_path}")
    return {
        "message":      "CAM report generated successfully",
        "download_url": f"/api/cam/download/{session_id}",
        "session_id":   session_id,
        "company_name": risk.company_name,
    }


@router.get("/download/{session_id}")
def download_cam(
    session_id:   str,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cam = db.query(models.CAMReport).filter(
        models.CAMReport.session_id == session_id
    ).order_by(models.CAMReport.id.desc()).first()

    if not cam or not os.path.exists(cam.file_path):
        raise HTTPException(status_code=404, detail="CAM report not found. Generate it first.")

    filename = f"CAM_{cam.company_name.replace(' ', '_')}_{session_id[:8]}.pdf"
    return FileResponse(cam.file_path, media_type="application/pdf", filename=filename)
