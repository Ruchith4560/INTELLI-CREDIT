import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def generate_explanation(score_result: Dict, risk_data: Dict, company_name: str) -> Dict[str, Any]:
    """
    Generates two types of explanation:
      1. SHAP values   — uses real XGBoost model if available, else formula
      2. LLM narrative — uses real OpenAI GPT if key set, else template
    """
    features   = score_result.get("features", {})
    decision   = score_result["decision"]
    risk_score = score_result["risk_score"]

    shap_values      = _compute_shap(features, risk_score, decision)
    explanation_text = _generate_llm_explanation(company_name, decision, risk_score, features, risk_data)

    return {
        "shap_values":              shap_values,
        "explanation_text":         explanation_text,
        "feature_importance_ranking": sorted(
            shap_values.items(), key=lambda x: abs(x[1]), reverse=True
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SHAP VALUES
# Real: uses XGBoost model  (created by train_model.py)
# Install: pip install shap xgboost joblib
# Fallback: formula-based approximation
# ─────────────────────────────────────────────────────────────────────────────

def _compute_shap(features: Dict, risk_score: float, decision: str) -> Dict[str, float]:
    """
    Computes SHAP feature importance values.
    Uses real SHAP library + XGBoost model when models/credit_model.pkl exists.
    Falls back to formula approximation otherwise.
    """
    model_path = "models/credit_model.pkl"

    if not os.path.exists(model_path):
        logger.warning("⚠️  No ML model found — using formula SHAP. Run train_model.py to fix.")
        return _shap_formula(features)

    try:
        import shap                   # pip install shap
        import joblib                 # pip install joblib
        import pandas as pd

        model = joblib.load(model_path)

        # Build feature DataFrame matching training column order
        MODEL_COLS = [
            "debt_to_equity", "current_ratio", "interest_coverage",
            "ebitda_margin", "gst_mismatch", "bounce_rate",
            "news_sentiment", "litigation_count",
        ]

        row = {
            "debt_to_equity":    features.get("debt_to_equity", 1.0),
            "current_ratio":     features.get("current_ratio", 1.5),
            "interest_coverage": features.get("interest_coverage", 3.0),
            "ebitda_margin":     features.get("ebitda_margin", 12.0),
            "gst_mismatch":      features.get("gst_mismatch", 2.0),
            "bounce_rate":       features.get("bounce_rate", 1.0),
            "news_sentiment":    features.get("news_sentiment_score", 0.5),
            "litigation_count":  features.get("litigation_count", 0),
        }
        df = pd.DataFrame([row])[MODEL_COLS]

        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(df)

        # For binary classifier shap_values is a list [class0_vals, class1_vals]
        if isinstance(shap_vals, list):
            vals = shap_vals[1][0]   # class 1 = default/reject
        else:
            vals = shap_vals[0]

        result = {col: round(float(vals[i]), 4) for i, col in enumerate(MODEL_COLS)}
        logger.info("✅ Real SHAP values computed from XGBoost model")
        return result

    except Exception as e:
        logger.error(f"SHAP computation failed: {e} — using formula fallback")
        return _shap_formula(features)


def _shap_formula(features: Dict) -> Dict[str, float]:
    """
    Formula-based SHAP approximation used when no ML model exists.
    Positive value = factor increases risk (pushes toward REJECT).
    Negative value = factor decreases risk (pushes toward APPROVE).
    """
    de  = features.get("debt_to_equity", 1.0)
    cr  = features.get("current_ratio", 1.5)
    ic  = features.get("interest_coverage", 3.0)
    em  = features.get("ebitda_margin", 12.0)
    gst = features.get("gst_mismatch", 2.0)
    br  = features.get("bounce_rate", 1.0)
    ns  = features.get("news_sentiment_score", 0.5)
    lit = features.get("litigation_count", 0)

    return {
        "debt_to_equity":    round((de  - 1.0)  *  8.0, 4),   # >1 increases risk
        "current_ratio":     round((cr  - 1.5)  * -5.0, 4),   # >1.5 reduces risk
        "interest_coverage": round((ic  - 2.5)  * -4.0, 4),   # >2.5 reduces risk
        "ebitda_margin":     round((em  - 10.0) * -0.5, 4),   # >10 reduces risk
        "gst_mismatch":      round(gst           *  1.5, 4),   # any mismatch increases risk
        "bounce_rate":       round(br             *  2.0, 4),   # higher bounce = higher risk
        "news_sentiment":    round((0.5 - ns)    * 10.0, 4),   # negative sentiment increases risk
        "litigation_count":  round(lit            *  3.0, 4),   # more cases = more risk
    }


# ─────────────────────────────────────────────────────────────────────────────
# LLM EXPLANATION
# Real: OpenAI GPT-3.5 / GPT-4
# Get key: https://platform.openai.com  → API Keys → Create
# Add to .env:  OPENAI_API_KEY=sk-...
# Install: pip install openai
# Cost: ~$0.002 per analysis on GPT-3.5-turbo  |  ~$0.05 on GPT-4
# Fallback: professional template text
# ─────────────────────────────────────────────────────────────────────────────

def _generate_llm_explanation(
    company_name: str,
    decision: str,
    risk_score: float,
    features: Dict,
    risk_data: Dict,
) -> str:
    """
    Generates a professional credit appraisal narrative.
    Uses OpenAI GPT when OPENAI_API_KEY is set; otherwise uses template.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        logger.warning("⚠️  OPENAI_API_KEY not set — using template explanation")
        return _template_explanation(company_name, decision, risk_score, features, risk_data)

    try:
        from openai import OpenAI    # pip install openai
        client = OpenAI(api_key=api_key)

        ratios    = risk_data.get("financial_ratios", {})
        anomalies = risk_data.get("anomalies", [])
        gst       = risk_data.get("gst_data", {})
        five_cs   = risk_data.get("five_cs", {})

        anomaly_lines = "\n".join(
            [f"  - [{a['severity']}] {a['type']}: {a['detail']}" for a in anomalies]
        ) if anomalies else "  - None detected"

        five_cs_lines = "\n".join(
            [f"  - {k.title()}: {v.get('score', 60):.0f}/100 — {v.get('summary', '')}"
             for k, v in five_cs.items()]
        )

        prompt = f"""You are a Senior Credit Analyst at a leading Indian bank (like SBI or HDFC Bank).
Write a professional Credit Appraisal Explanation for the following borrower.
Use formal banking language. Reference India-specific terms (CIBIL, GSTR, RBI, NPA, EBITDA).
Format headings using **bold** markdown syntax.

═══════════════════════════════════════════════════
BORROWER:     {company_name}
AI DECISION:  {decision}
RISK SCORE:   {risk_score:.1f} / 100
CREDIT GRADE: {'A+' if risk_score < 25 else 'A' if risk_score < 35 else 'BBB' if risk_score < 50 else 'BB' if risk_score < 65 else 'B / CCC'}
═══════════════════════════════════════════════════

FINANCIAL RATIOS:
  - Current Ratio:      {ratios.get('current_ratio', 'N/A')}   (Benchmark: > 1.3)
  - Debt-to-Equity:     {ratios.get('debt_to_equity', 'N/A')}x  (Benchmark: < 2.0)
  - Interest Coverage:  {ratios.get('interest_coverage', 'N/A')}x  (Benchmark: > 2.5)
  - EBITDA Margin:      {ratios.get('ebitda_margin', 'N/A')}%   (Benchmark: > 10%)
  - Net Profit Margin:  {ratios.get('net_profit_margin', 'N/A')}%
  - Revenue Growth:     {ratios.get('revenue_growth', 'N/A')}%
  - ROE:                {ratios.get('roe', 'N/A')}%
  - ROCE:               {ratios.get('roce', 'N/A')}%

GST COMPLIANCE:
  - GSTR-2A vs 3B Mismatch: {gst.get('gstr2a_vs_3b_mismatch_pct', 'N/A')}%
  - Filing Status:           {gst.get('filing_compliance', 'N/A')}
  - Circular Trading Signal: {gst.get('circular_trading_signal', False)}

ANOMALIES DETECTED:
{anomaly_lines}

FIVE Cs OF CREDIT:
{five_cs_lines}

═══════════════════════════════════════════════════

Write exactly 4 paragraphs with these bold headers:
**1. Credit Decision Summary**
**2. Financial Health Analysis**
**3. Compliance & External Risk Assessment**
**4. Final Recommendation & Conditions**

Be specific — reference actual numbers from the data above.
Keep total length under 450 words.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",       # Change to "gpt-4" for higher quality
            messages=[
                {
                    "role":    "system",
                    "content": (
                        "You are a senior Indian bank credit analyst with 20 years of experience. "
                        "You write clear, factual, professional credit appraisal memos. "
                        "You cite specific numbers and use terms like CIBIL, GSTR, RBI, NPA, DSCR, FOIR."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.25,     # Low temperature for consistent, factual output
        )

        explanation = response.choices[0].message.content.strip()
        logger.info("✅ OpenAI GPT explanation generated successfully")
        return explanation

    except Exception as e:
        logger.error(f"OpenAI API error: {e} — using template fallback")
        return _template_explanation(company_name, decision, risk_score, features, risk_data)


def _template_explanation(
    company_name: str,
    decision: str,
    risk_score: float,
    features: Dict,
    risk_data: Dict,
) -> str:
    """
    High-quality template explanation used when OpenAI key is not configured.
    This is the current working fallback — looks professional in demo.
    """
    ratios    = risk_data.get("financial_ratios", {})
    anomalies = risk_data.get("anomalies", [])
    five_cs   = risk_data.get("five_cs", {})
    gst       = risk_data.get("gst_data", {})

    ic  = features.get("interest_coverage", 3.0)
    de  = features.get("debt_to_equity", 1.0)
    cr  = features.get("current_ratio", 1.5)
    gst_mismatch = features.get("gst_mismatch", 2.0)

    credit_grade = (
        "A+"  if risk_score < 25 else
        "A"   if risk_score < 35 else
        "BBB" if risk_score < 50 else
        "BB"  if risk_score < 65 else "B"
    )

    decision_text = {
        "APPROVE": "APPROVED for lending",
        "REJECT":  "REJECTED",
        "REVIEW":  "flagged for SENIOR MANAGEMENT REVIEW",
    }.get(decision, decision)

    anomaly_text = ""
    if anomalies:
        details = [a["detail"] for a in anomalies[:3]]
        anomaly_text = f" Key concerns flagged: {'; '.join(details)}."

    capacity_summary = five_cs.get("capacity", {}).get("summary", "")
    capital_summary  = five_cs.get("capital",  {}).get("summary", "")

    if decision == "APPROVE":
        recommendation = (
            f"Based on the comprehensive multi-source analysis, {company_name} meets the "
            f"lending criteria of this institution. The financial metrics are within acceptable "
            f"parameters and GST compliance is satisfactory. Lending is recommended subject to "
            f"standard covenants: quarterly financial reporting, maintenance of current ratio "
            f"above 1.2x, and D/E ratio below 2.5x throughout the loan tenure."
        )
    elif decision == "REVIEW":
        recommendation = (
            f"The credit profile of {company_name} is mixed and requires senior management "
            f"review before sanction.{anomaly_text} The risk score of {risk_score:.1f}/100 "
            f"places this application in the REVIEW band. Additional due diligence is advised "
            f"including a fresh site visit and clarification of the flagged anomalies."
        )
    else:
        recommendation = (
            f"The credit application of {company_name} has been declined. The risk score of "
            f"{risk_score:.1f}/100 exceeds the institutional threshold.{anomaly_text} "
            f"The applicant may reapply after a minimum seasoning period of 6 months with "
            f"demonstrably improved financials and resolution of the flagged issues."
        )

    return f"""**Credit Appraisal Decision: {decision_text}**

**Risk Score: {risk_score:.1f}/100** | Credit Grade: {credit_grade} | Prepared by: Intelli-Credit AI Engine

**1. Credit Decision Summary**
The Intelli-Credit AI Engine has evaluated {company_name} using multi-source financial intelligence including annual reports, GST filings, bank statements, and external research. The application has been **{decision_text}** with a composite risk score of {risk_score:.1f}/100.

**2. Financial Health Analysis**
{capacity_summary} {capital_summary} The current ratio of {cr:.2f}x (benchmark: >1.3) indicates {'adequate' if cr > 1.3 else 'stressed'} short-term liquidity. Interest coverage of {ic:.1f}x suggests the company {'can comfortably service' if ic > 2.5 else 'may struggle to service'} its debt obligations from operating earnings. Debt-to-equity of {de:.2f}x reflects {'conservative' if de < 0.5 else 'moderate' if de < 1.0 else 'elevated'} leverage.

**3. Compliance & External Risk Assessment**
GSTR-2A vs GSTR-3B mismatch of {gst_mismatch:.1f}% was detected — {'within acceptable thresholds, indicating transparent GST reporting' if gst_mismatch < 5 else 'elevated above the 5% threshold, warranting further investigation for potential revenue inflation or circular trading patterns'}. Bank statement analysis shows {'regular' if features.get('bounce_rate', 1) < 2 else 'irregular'} repayment behaviour with a cheque bounce rate of {features.get('bounce_rate', 1):.1f}%.{anomaly_text}

**4. Final Recommendation**
{recommendation}

*This analysis was generated by Intelli-Credit AI Engine. Add OPENAI_API_KEY to .env for GPT-4 powered explanations. All decisions require human review before disbursement.*"""


def _get_rationale(decision: str, risk_score: float, anomaly_text: str) -> str:
    """Helper for rationale text"""
    if decision == "APPROVE":
        return (f"Based on comprehensive analysis, the borrower presents acceptable credit risk "
                f"(score: {risk_score:.1f}/100). Financial metrics are within lending parameters "
                f"and GST compliance is satisfactory.{anomaly_text}")
    elif decision == "REVIEW":
        return (f"The analysis reveals a mixed credit profile (risk score: {risk_score:.1f}/100). "
                f"Certain risk factors require senior management review before disbursement.{anomaly_text}")
    else:
        return (f"The credit application has been declined (score: {risk_score:.1f}/100). "
                f"The identified risks exceed the acceptable threshold.{anomaly_text}")
