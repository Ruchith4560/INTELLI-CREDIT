import os
import logging
import random
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL LOADER  (cached singleton)
# ─────────────────────────────────────────────────────────────────────────────

_MODEL = None   # cached after first load

def _load_model():
    """
    Loads the XGBoost credit model from models/credit_model.pkl.
    Returns None if file doesn't exist (triggers rule-based fallback).

    To create the model file:
      1. pip install xgboost scikit-learn joblib
      2. Run:  python train_model.py  (from the /backend directory)
    """
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    model_path = "models/credit_model.pkl"
    if not os.path.exists(model_path):
        logger.warning("⚠️  models/credit_model.pkl not found — using rule-based scoring")
        return None

    try:
        import joblib           # pip install joblib
        _MODEL = joblib.load(model_path)
        logger.info("✅ XGBoost credit model loaded successfully")
        return _MODEL
    except Exception as e:
        logger.error(f"Model load error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCORING FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def compute_score(risk_data: Dict, research_data: Dict, qualitative_notes: str = "") -> Dict[str, Any]:
    """
    Hybrid scoring engine:
      - Uses real XGBoost model when models/credit_model.pkl exists
      - Falls back to weighted rule-based scoring otherwise

    Returns: risk_score (0-100), decision, loan_amount, interest_rate, features
    """
    risk_scores = risk_data.get("risk_scores", {})
    anomalies   = risk_data.get("anomalies", [])
    ratios      = risk_data.get("financial_ratios", {})

    # ── Build feature dictionary (used by both ML and rule-based paths) ───────
    features = {
        "debt_to_equity":    ratios.get("debt_to_equity", 1.0),
        "current_ratio":     ratios.get("current_ratio", 1.5),
        "interest_coverage": ratios.get("interest_coverage", 3.0),
        "ebitda_margin":     ratios.get("ebitda_margin", 12.0),
        "gst_mismatch":      risk_data.get("gst_data", {}).get("gstr2a_vs_3b_mismatch_pct", 2.0),
        "bounce_rate":       risk_data.get("bank_data", {}).get("bounce_rate_pct", 1.0),
        "news_sentiment_score": research_data.get("sentiment_score", 0.5),
        "litigation_count":  research_data.get("litigation_count", 0),
    }

    # ── Try real XGBoost model ────────────────────────────────────────────────
    model = _load_model()
    if model is not None:
        weighted_score = _score_with_ml(model, features)
        logger.info(f"XGBoost risk score: {weighted_score:.2f}")
    else:
        weighted_score = _score_with_rules(risk_scores, research_data)
        logger.info(f"Rule-based risk score: {weighted_score:.2f}")

    # ── Anomaly penalties (applied regardless of scoring method) ─────────────
    for anomaly in anomalies:
        if anomaly.get("severity") == "HIGH":
            weighted_score += 8
        elif anomaly.get("severity") == "MEDIUM":
            weighted_score += 4

    # ── Qualitative notes adjustment ──────────────────────────────────────────
    if qualitative_notes:
        qual_adjustment = _qualitative_adjustment(qualitative_notes)
        weighted_score  = max(0, weighted_score + qual_adjustment)
        logger.info(f"Qualitative adjustment: {qual_adjustment:+.1f}")

    # ── Final clamped risk score ──────────────────────────────────────────────
    risk_score   = min(max(round(weighted_score, 2), 1), 100)

    # ── CIBIL-style credit score (inverse: higher = better) ──────────────────
    credit_score = int(min(max(round(900 - risk_score * 5.5), 300), 900))

    # ── Decision thresholds ───────────────────────────────────────────────────
    if risk_score <= 30:
        decision        = "APPROVE"
        loan_multiplier = 4.5
        base_rate       = 8.5
    elif risk_score <= 50:
        decision        = "APPROVE"
        loan_multiplier = 3.0
        base_rate       = 10.5
    elif risk_score <= 65:
        decision        = "REVIEW"
        loan_multiplier = 1.5
        base_rate       = 12.5
    else:
        decision        = "REJECT"
        loan_multiplier = 0.0
        base_rate       = 0.0

    # ── Loan amount = EBITDA × multiplier ────────────────────────────────────
    revenue      = ratios.get("revenue_crore", 200.0)
    ebitda_pct   = ratios.get("ebitda_margin", 12.0) / 100.0
    ebitda       = revenue * ebitda_pct
    loan_amount  = round(ebitda * loan_multiplier, 2) if decision != "REJECT" else 0.0

    # ── Interest rate = base rate + risk premium ──────────────────────────────
    risk_premium  = max(0, (risk_score - 20) * 0.05)
    interest_rate = round(base_rate + risk_premium, 2) if decision != "REJECT" else 0.0

    return {
        "risk_score":      risk_score,
        "credit_score":    credit_score,
        "decision":        decision,
        "loan_amount":     loan_amount,
        "interest_rate":   interest_rate,
        "features":        features,
        "scoring_method":  "XGBoost ML Model" if model is not None else "Rule-Based (Weighted)",
        "decision_reasons": _get_decision_reasons(risk_score, anomalies, ratios, research_data),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SCORING METHODS
# ─────────────────────────────────────────────────────────────────────────────

def _score_with_ml(model, features: Dict) -> float:
    """
    Uses real XGBoost model to predict probability of default.
    Returns a 0-100 risk score.
    """
    try:
        import pandas as pd

        # MUST match the column order used in train_model.py
        MODEL_COLS = [
            "debt_to_equity", "current_ratio", "interest_coverage",
            "ebitda_margin", "gst_mismatch", "bounce_rate",
            "news_sentiment", "litigation_count",
        ]

        row = {
            "debt_to_equity":    features["debt_to_equity"],
            "current_ratio":     features["current_ratio"],
            "interest_coverage": features["interest_coverage"],
            "ebitda_margin":     features["ebitda_margin"],
            "gst_mismatch":      features["gst_mismatch"],
            "bounce_rate":       features["bounce_rate"],
            "news_sentiment":    features["news_sentiment_score"],
            "litigation_count":  features["litigation_count"],
        }
        df = pd.DataFrame([row])[MODEL_COLS]

        prob_default = model.predict_proba(df)[0][1]   # P(default)
        return round(prob_default * 100, 2)

    except Exception as e:
        logger.error(f"ML scoring failed: {e} — falling back to rules")
        return _score_with_rules({}, {})


def _score_with_rules(risk_scores: Dict, research_data: Dict) -> float:
    """
    Weighted rule-based scoring — used when no ML model is available.
    Weights: Financial 35%, GST 20%, Bank 15%, Qualitative 15%, Research 15%
    """
    weights = {
        "financial_risk":   0.35,
        "gst_risk":         0.20,
        "bank_risk":        0.15,
        "qualitative_risk": 0.15,
        "research_risk":    0.15,
    }
    research_risk = research_data.get("overall_risk_score", 25)

    return (
        risk_scores.get("financial_risk",   30) * weights["financial_risk"]   +
        risk_scores.get("gst_risk",         25) * weights["gst_risk"]         +
        risk_scores.get("bank_risk",        20) * weights["bank_risk"]        +
        risk_scores.get("qualitative_risk", 20) * weights["qualitative_risk"] +
        research_risk                            * weights["research_risk"]
    )


def _qualitative_adjustment(notes: str) -> float:
    """
    Adjusts score based on officer's qualitative notes.
    Negative keywords raise score (more risk); positive keywords lower it.
    """
    notes_lower = notes.lower()
    adjustment  = 0.0

    negative_signals = {
        "low capacity": 8, "40% capacity": 10, "50% capacity": 8,
        "poor management": 10, "dispute": 6, "legal notice": 8,
        "declining revenue": 8, "operating at loss": 12,
        "weak":  5, "stressed": 7, "irregular": 6,
        "mismanagement": 10, "family dispute": 8,
    }
    positive_signals = {
        "strong management": -6, "growing": -4, "excellent": -5,
        "modern plant": -4, "expanding": -4, "profitable": -5,
        "new contracts": -4, "export orders": -5, "100% capacity": -6,
        "good track record": -5, "no defaults": -6,
    }

    for kw, delta in negative_signals.items():
        if kw in notes_lower:
            adjustment += delta

    for kw, delta in positive_signals.items():
        if kw in notes_lower:
            adjustment += delta   # delta is already negative

    return round(adjustment, 2)


# ─────────────────────────────────────────────────────────────────────────────
# DECISION REASONS  (human-readable factors)
# ─────────────────────────────────────────────────────────────────────────────

def _get_decision_reasons(risk_score: float, anomalies: list,
                           ratios: Dict, research_data: Dict) -> list:
    reasons = []

    # Positive factors
    ic = ratios.get("interest_coverage", 0)
    cr = ratios.get("current_ratio", 0)
    em = ratios.get("ebitda_margin", 0)

    if ic > 3.5:
        reasons.append({"type": "positive", "factor": "Interest Coverage",
                        "detail": f"Strong interest coverage of {ic:.1f}x (benchmark: >2.5)"})
    elif ic > 2.5:
        reasons.append({"type": "positive", "factor": "Interest Coverage",
                        "detail": f"Adequate interest coverage of {ic:.1f}x"})

    if cr > 1.5:
        reasons.append({"type": "positive", "factor": "Liquidity",
                        "detail": f"Healthy current ratio of {cr:.2f}x ensures short-term solvency"})

    if em > 15:
        reasons.append({"type": "positive", "factor": "Profitability",
                        "detail": f"Strong EBITDA margin of {em:.1f}% reflects operational efficiency"})

    # Negative factors from anomalies
    for anomaly in anomalies:
        reasons.append({"type": "negative", "factor": anomaly["type"],
                        "detail": anomaly["detail"]})

    # Research-based negatives
    lit_count = research_data.get("litigation_count", 0)
    if lit_count > 2:
        reasons.append({"type": "negative", "factor": "Litigation Risk",
                        "detail": f"{lit_count} active legal cases detected in secondary research"})

    ns = research_data.get("sentiment_score", 0.5)
    if ns < 0.3:
        reasons.append({"type": "negative", "factor": "Negative News Sentiment",
                        "detail": "Predominantly negative news coverage detected for company/promoters"})
    elif ns > 0.7:
        reasons.append({"type": "positive", "factor": "Positive News Sentiment",
                        "detail": "Positive media coverage supports management quality assessment"})

    return reasons
