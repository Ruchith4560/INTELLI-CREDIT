from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db
from app import models
from app.utils.auth import get_current_user
from app.services.risk_analyzer  import analyze_risk
from app.services.scoring_engine import compute_score
from app.services.explainability import generate_explanation
from app.agents.research_agent   import run_research_agents

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalysisRequest(BaseModel):
    session_id:         str
    company_name:       str
    qualitative_notes:  Optional[str]  = ""
    run_web_research:   Optional[bool] = True


@router.post("/run")
def run_analysis(
    request:      AnalysisRequest,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # ── 1. Load documents ────────────────────────────────────────────────────
    docs = db.query(models.UploadedDocument).filter(
        models.UploadedDocument.session_id == request.session_id
    ).all()
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for this session. Upload documents first.")

    all_text  = " ".join([d.extracted_text or "" for d in docs])
    doc_types = {d.doc_type: d.extracted_text for d in docs}
    logger.info(f"🔍 Running analysis for {request.company_name} | docs={len(docs)}")

    # ── 2. Risk Analysis (financial ratios, GST, bank, anomalies, Five Cs) ──
    risk_data = analyze_risk(all_text, doc_types, request.qualitative_notes or "")

    # ── 3. Research Agents (News, Litigation, Regulatory, Sector) ───────────
    research_data = run_research_agents(request.company_name) if request.run_web_research else {
        "news_sentiment": {}, "regulatory_risk": {}, "litigation_risk": {},
        "sector_analysis": {}, "overall_risk_score": 25, "sentiment_score": 0.5, "litigation_count": 0,
    }

    # ── 4. Scoring Engine (XGBoost or rule-based) ────────────────────────────
    score_result = compute_score(risk_data, research_data, request.qualitative_notes or "")

    # ── 5. Explainability (SHAP + LLM) ───────────────────────────────────────
    explanation = generate_explanation(score_result, risk_data, request.company_name)

    # ── 6. Persist to database ────────────────────────────────────────────────
    # Remove old record for this session if re-running
    old = db.query(models.RiskScore).filter(models.RiskScore.session_id == request.session_id).first()
    if old:
        db.delete(old)
        db.commit()

    rs = models.RiskScore(
        session_id      = request.session_id,
        company_name    = request.company_name,
        risk_score      = score_result["risk_score"],
        decision        = score_result["decision"],
        loan_amount     = score_result["loan_amount"],
        interest_rate   = score_result["interest_rate"],
        risk_breakdown  = risk_data,
        shap_values     = explanation["shap_values"],
        llm_explanation = explanation["explanation_text"],
        news_sentiment  = research_data.get("news_sentiment", {}),
        litigation_risk = research_data.get("litigation_risk", {}),
        scoring_method  = score_result.get("scoring_method", "Rule-Based"),
    )
    db.add(rs)

    # Features record
    old_feat = db.query(models.ExtractedFeature).filter(
        models.ExtractedFeature.session_id == request.session_id
    ).first()
    if old_feat:
        db.delete(old_feat)
        db.commit()

    feat = models.ExtractedFeature(
        session_id        = request.session_id,
        company_name      = request.company_name,
        feature_data      = score_result.get("features", {}),
        financial_ratios  = risk_data.get("financial_ratios", {}),
        gst_data          = risk_data.get("gst_data", {}),
        qualitative_notes = request.qualitative_notes,
    )
    db.add(feat)

    # Explainability audit log
    exp_log = models.ExplainabilityLog(
        session_id       = request.session_id,
        decision         = score_result["decision"],
        shap_features    = explanation["shap_values"],
        explanation_text = explanation["explanation_text"],
        audit_trail      = {
            "user_id":        current_user.id,
            "user_name":      current_user.name,
            "company":        request.company_name,
            "scoring_method": score_result.get("scoring_method"),
            "openai_used":    "OPENAI_API_KEY" in __import__("os").environ and bool(__import__("os").environ.get("OPENAI_API_KEY")),
        },
    )
    db.add(exp_log)
    db.commit()

    logger.info(f"✅ Analysis complete: {request.company_name} → {score_result['decision']} (score={score_result['risk_score']})")

    return {
        "session_id":       request.session_id,
        "company_name":     request.company_name,
        "risk_score":       score_result["risk_score"],
        "credit_score":     score_result.get("credit_score", 700),
        "decision":         score_result["decision"],
        "loan_amount":      score_result["loan_amount"],
        "interest_rate":    score_result["interest_rate"],
        "scoring_method":   score_result.get("scoring_method"),
        "decision_reasons": score_result.get("decision_reasons", []),
        "risk_breakdown":   risk_data,
        "shap_values":      explanation["shap_values"],
        "explanation_text": explanation["explanation_text"],
        "feature_importance_ranking": explanation.get("feature_importance_ranking", []),
        "news_sentiment":   research_data.get("news_sentiment", {}),
        "litigation_risk":  research_data.get("litigation_risk", {}),
        "regulatory_risk":  research_data.get("regulatory_risk", {}),
        "sector_analysis":  research_data.get("sector_analysis", {}),
        "financial_ratios": risk_data.get("financial_ratios", {}),
    }


@router.get("/result/{session_id}")
def get_result(
    session_id:   str,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    r = db.query(models.RiskScore).filter(models.RiskScore.session_id == session_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    feat = db.query(models.ExtractedFeature).filter(
        models.ExtractedFeature.session_id == session_id
    ).first()
    return {
        "session_id":       r.session_id,
        "company_name":     r.company_name,
        "risk_score":       r.risk_score,
        "decision":         r.decision,
        "loan_amount":      r.loan_amount,
        "interest_rate":    r.interest_rate,
        "scoring_method":   r.scoring_method,
        "risk_breakdown":   r.risk_breakdown,
        "shap_values":      r.shap_values,
        "explanation_text": r.llm_explanation,
        "news_sentiment":   r.news_sentiment,
        "litigation_risk":  r.litigation_risk,
        "financial_ratios": feat.financial_ratios if feat else {},
        "created_at":       str(r.created_at),
    }


@router.get("/history")
def get_history(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    results = db.query(models.RiskScore).order_by(
        models.RiskScore.created_at.desc()
    ).limit(30).all()
    return {
        "history": [
            {
                "session_id":     r.session_id,
                "company_name":   r.company_name,
                "risk_score":     r.risk_score,
                "decision":       r.decision,
                "loan_amount":    r.loan_amount,
                "interest_rate":  r.interest_rate,
                "scoring_method": r.scoring_method,
                "created_at":     str(r.created_at),
            }
            for r in results
        ]
    }
