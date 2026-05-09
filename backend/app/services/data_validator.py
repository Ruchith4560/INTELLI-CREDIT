from typing import Dict, Any
import re

def validate_document(extracted: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """Validate extracted document data and compute confidence score"""
    validation = {
        "is_valid": True,
        "confidence_score": 0.0,
        "errors": [],
        "warnings": []
    }
    
    text = extracted.get("text", "")
    if not text or len(text) < 50:
        validation["errors"].append("Insufficient text extracted from document")
        validation["is_valid"] = False
        validation["confidence_score"] = 0.1
        return validation
    
    confidence = 0.5  # base
    
    # Check for financial keywords
    financial_keywords = ["revenue", "profit", "debt", "assets", "liabilities", "turnover", "crore", "lakh"]
    found = sum(1 for kw in financial_keywords if kw.lower() in text.lower())
    confidence += min(found * 0.05, 0.3)
    
    # Doc type specific checks
    if doc_type == "gst":
        if "gstr" not in text.lower() and "gst" not in text.lower():
            validation["warnings"].append("Document may not be a GST filing")
        else:
            confidence += 0.1
    
    if doc_type == "bank_statement":
        if any(w in text.lower() for w in ["balance", "credit", "debit", "account"]):
            confidence += 0.1
    
    # Check for numbers
    numbers = re.findall(r'\d+[\d,\.]*', text)
    if len(numbers) > 10:
        confidence += 0.1
    
    validation["confidence_score"] = min(round(confidence, 2), 1.0)
    return validation
